"""Review a GitHub pull request with a Gemini managed agent, from GitHub Actions.

Flow (runs inside the Actions job):
  1. Read PR context from Actions env vars (or PR_NUMBER for manual runs).
  2. Fetch the PR metadata + per-file diff from the GitHub API.
  3. Create a managed-agent interaction whose sandbox has the repository
     PRE-MOUNTED via the `repository` environment source (GitHub-native path);
     the agent brings it to the exact PR state with a cheap
     `git fetch origin pull/<N>/head` and reviews the diff in context.
  4. The review rubric is PLUGGABLE: skills/<REVIEW_SKILL>/SKILL.md is appended
     to a review-type-agnostic base system instruction. Swap the skill to run a
     different kind of review — no code change.
  5. Parse the agent's JSON and post a summary comment + line-anchored review
     comments back on the PR.

Required env: GEMINI_API_KEY, GITHUB_TOKEN, GITHUB_REPOSITORY, and the PR
number (PR_NUMBER, or GITHUB_EVENT_PATH from the pull_request event).
Optional env: REVIEW_SKILL (default "security-review"), BASE_AGENT,
GITHUB_API_URL / GITHUB_SERVER_URL (set by Actions; default to github.com),
DRY_RUN=1 to print findings instead of posting.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys
from typing import Any

from google import genai

from github_client import (
    GitHub,
    build_basic_auth_header,
    build_diff_prompt,
    render_finding_comment,
)
from schema import (
    FINDINGS_SCHEMA,
    SEVERITY_EMOJI,
    SEVERITY_ORDER,
    SYSTEM_INSTRUCTION,
)

BASE_AGENT = os.environ.get("BASE_AGENT", "antigravity-preview-05-2026")
SKILLS_DIR = pathlib.Path(__file__).parent / "skills"
REPO_MOUNT = "/workspace/repo"


# --------------------------------------------------------------------------- #
# Skill loading (the pluggable part)
# --------------------------------------------------------------------------- #
def load_skill(name: str) -> tuple[str, str]:
    """Return (title, rubric text) for skills/<name>/SKILL.md.

    The whole file (frontmatter included) is sent to the agent; the title shown
    in the PR comment comes from the frontmatter `name:` when present.
    """
    path = SKILLS_DIR / name / "SKILL.md"
    if not path.is_file():
        available = sorted(p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md"))
        raise SystemExit(
            f"❌ Review skill '{name}' not found at {path}. Available: {available}"
        )
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
    return (m.group(1).strip() if m else name), text


# --------------------------------------------------------------------------- #
# Agent reply extraction / parsing
# --------------------------------------------------------------------------- #
def _extract_text(interaction: Any) -> str:
    text = getattr(interaction, "output_text", None)
    if text:
        return text
    steps = getattr(interaction, "steps", None) or []
    for step in reversed(steps):
        try:
            joined = "".join(
                part.text
                for part in (step.content or [])
                if getattr(part, "text", None)
            )
            if joined.strip():
                return joined
        except (AttributeError, IndexError, TypeError):
            pass
    return str(interaction)


def _parse_json(raw: str) -> dict[str, Any]:
    """Parse the agent reply into a findings dict, tolerating ```json fences
    and invalid backslash escapes (regex/code echoed into strings)."""
    raw = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1)
    else:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        repaired = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", raw)
        data = json.loads(repaired)
    data.setdefault("summary", "")
    data.setdefault("findings", [])
    return data


# --------------------------------------------------------------------------- #
# The review interaction
# --------------------------------------------------------------------------- #
def run_review(
    client: genai.Client,
    clone_url: str,
    pr_number: int,
    pr_title: str,
    base_branch: str,
    head_branch: str,
    diff_prompt: str,
    skill_name: str,
    skill_text: str,
    git_auth_header: str | None = None,
) -> dict[str, Any]:
    # The repo is mounted at provision time via the GitHub-native `repository`
    # source (default branch). The agent only runs a cheap fetch/checkout of
    # refs/pull/<N>/head to reach the exact PR state — no full in-sandbox clone.
    # For private repos, auth is injected by the egress proxy via the
    # github.com allowlist `transform` (a LIST of {header: value} dicts on
    # google-genai >= 2.10.0); credentials never enter the sandbox.
    github_entry: dict[str, Any] = {"domain": "github.com"}
    if git_auth_header:
        github_entry["transform"] = [{"Authorization": git_auth_header}]

    environment = {
        "type": "remote",
        "sources": [
            {"type": "repository", "source": clone_url, "target": REPO_MOUNT},
            # The review skill is also mounted into the sandbox as an inline
            # source (.agents/skills/ is auto-registered by the runtime); the
            # same text rides in the system_instruction below so the rubric is
            # applied unconditionally.
            {
                "type": "inline",
                "target": f".agents/skills/{skill_name}/SKILL.md",
                "content": skill_text,
            },
        ],
        "network": {"allowlist": [github_entry]},
    }

    prompt = (
        f"You are reviewing GitHub pull request #{pr_number} (\"{pr_title}\"), "
        f"targeting branch '{base_branch}' from '{head_branch}'.\n\n"
        f"The repository is already mounted at {REPO_MOUNT} (default branch). "
        f"Bring it to the exact PR state by running:\n"
        f"   git -C {REPO_MOUNT} fetch origin pull/{pr_number}/head\n"
        f"   git -C {REPO_MOUNT} checkout --detach FETCH_HEAD\n"
        f"(Authentication, if needed, is injected automatically; never add "
        f"credentials.)\n\n"
        f"The unified diff of the pull request is below. Review THESE changes. "
        f"Use the mounted repository to read the surrounding code the changes "
        f"touch or depend on, and any spec/README/docs describing intended "
        f"behavior — read only what you need, be efficient.\n\n"
        f"{diff_prompt}\n\n"
        f"Apply the review skill in your instructions. Return ONLY the JSON "
        f"object described by this schema (anchor each finding to a file path "
        f"and line that appear in the diff):\n\n"
        f"{json.dumps(FINDINGS_SCHEMA)}"
    )

    system_instruction = f"{SYSTEM_INSTRUCTION}\n\n# Review skill\n\n{skill_text}"

    interaction = client.interactions.create(
        agent=BASE_AGENT,
        system_instruction=system_instruction,
        input=prompt,
        environment=environment,
    )
    return _parse_json(_extract_text(interaction))


# --------------------------------------------------------------------------- #
# Posting
# --------------------------------------------------------------------------- #
def post_results(
    gh: GitHub,
    pr_number: int,
    head_sha: str,
    skill_title: str,
    result: dict[str, Any],
) -> None:
    findings = sorted(
        result.get("findings", []),
        key=lambda f: SEVERITY_ORDER.get(f.get("severity", "info"), 9),
    )

    counts: dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "info")
        counts[sev] = counts.get(sev, 0) + 1
    counts_line = (
        " · ".join(
            f"{SEVERITY_EMOJI.get(s, '')} {n} {s}"
            for s, n in sorted(counts.items(), key=lambda kv: SEVERITY_ORDER.get(kv[0], 9))
        )
        or "no findings"
    )
    gh.post_issue_comment(
        pr_number,
        f"## 🔍 Automated review — {skill_title}\n\n"
        f"{result.get('summary', '(no summary)')}\n\n"
        f"**Findings:** {counts_line}\n\n"
        f"<sub>🤖 Reviewed by a Gemini managed agent · advisory, verify before "
        f"relying on it.</sub>",
    )

    overflow: list[str] = []
    for f in findings:
        body = render_finding_comment(f, SEVERITY_EMOJI.get(f.get("severity", "info"), ""))
        anchored = False
        try:
            anchored = gh.post_review_comment(
                pr_number, head_sha, f["file"], int(f["line"]), body
            )
        except Exception as exc:  # keep posting the rest
            print(f"⚠️  inline comment failed for {f.get('file')}:{f.get('line')}: {exc}",
                  file=sys.stderr)
        if not anchored:
            overflow.append(f"`{f.get('file')}:{f.get('line')}`\n\n{body}")

    if overflow:
        gh.post_issue_comment(
            pr_number,
            "### Additional findings (could not be anchored to a diff line)\n\n"
            + "\n\n---\n\n".join(overflow),
        )

    print(f"Posted {len(findings)} finding(s) to PR #{pr_number}.")


# --------------------------------------------------------------------------- #
def resolve_pr_number() -> int:
    if os.environ.get("PR_NUMBER"):
        return int(os.environ["PR_NUMBER"])
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and pathlib.Path(event_path).is_file():
        event = json.loads(pathlib.Path(event_path).read_text(encoding="utf-8"))
        number = (event.get("pull_request") or {}).get("number") or (
            event.get("issue") or {}
        ).get("number")
        if number:
            return int(number)
    raise SystemExit(
        "❌ Cannot determine the PR number: set PR_NUMBER or run from a "
        "pull_request event."
    )


def main() -> int:
    try:
        repo = os.environ["GITHUB_REPOSITORY"]
        gh_token = os.environ.get("GITHUB_TOKEN") or os.environ["GH_TOKEN"]
        os.environ["GEMINI_API_KEY"]  # fail fast; the client reads it itself
    except KeyError as exc:
        print(f"❌ Missing required env variable: {exc}", file=sys.stderr)
        return 1

    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    skill_name = os.environ.get("REVIEW_SKILL", "security-review")
    dry_run = os.environ.get("DRY_RUN", "0") == "1"

    pr_number = resolve_pr_number()
    skill_title, skill_text = load_skill(skill_name)
    gh = GitHub(api_url, repo, gh_token)

    print(f"Fetching PR #{pr_number} of {repo} …")
    pr = gh.get_pr(pr_number)
    files = gh.get_pr_files(pr_number)
    diff_prompt = build_diff_prompt(files)
    private = bool(gh.get_repo().get("private"))

    print(
        f"Reviewing PR #{pr_number} ({pr['head']['ref']} → {pr['base']['ref']}) "
        f"with skill '{skill_name}' ({len(files)} changed file(s), "
        f"{'private' if private else 'public'} repo) …"
    )
    client = genai.Client()
    result = run_review(
        client,
        clone_url=f"{server_url}/{repo}.git",
        pr_number=pr_number,
        pr_title=pr.get("title", ""),
        base_branch=pr["base"]["ref"],
        head_branch=pr["head"]["ref"],
        diff_prompt=diff_prompt,
        skill_name=skill_name,
        skill_text=skill_text,
        git_auth_header=build_basic_auth_header(gh_token) if private else None,
    )

    if dry_run:
        print(json.dumps(result, indent=2))
        return 0

    print("Posting results …")
    post_results(gh, pr_number, pr["head"]["sha"], skill_title, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
