"""Review a GitHub pull request with a Gemini managed agent, from GitHub Actions.

Flow (runs inside the Actions job):
  1. Read PR context from Actions env vars (or PR_NUMBER for manual runs).
  2. Fetch the PR metadata + per-file diff from the GitHub API.
  3. Create a managed-agent interaction whose sandbox has the repository
     PRE-MOUNTED via the `repository` environment source; the agent brings it
     to the exact PR state with a cheap `git fetch origin pull/<N>/head` and
     reviews the diff in context.
  4. The review rubric is PLUGGABLE: skills/<REVIEW_SKILL>/SKILL.md is appended
     to a review-type-agnostic base system instruction and mounted into the
     sandbox. Swap the skill to run a different kind of review.
  5. FOLLOW-UP REVIEWS remember the previous round: the tool stores the
     interaction/environment ids in a hidden marker inside the summary comment
     it posts, and the next run on the same PR resumes the conversation via
     previous_interaction_id (sandbox reuse too, for public repos).
  6. The agent gets an authenticated GitHub CLI through a shim wrapper
     (bin/gh-shim.sh mounted at /workspace/bin/gh): a dummy token satisfies the
     CLI locally while the egress proxy injects the real job token at the
     network layer. The agent uses it read-only for context (linked issues,
     earlier comments, CI checks); posting stays in this script.
  7. Parse the agent's JSON and post a summary comment + line-anchored review
     comments back on the PR.

Required env: GEMINI_API_KEY, GITHUB_TOKEN, GITHUB_REPOSITORY, and the PR
number (PR_NUMBER, or GITHUB_EVENT_PATH from the pull_request event).
Optional env: REVIEW_SKILL (default "security-review"), BASE_AGENT,
PERSIST=0 to disable follow-up memory, AGENT_GH=0 to remove the GitHub CLI
from the sandbox, GITHUB_API_URL / GITHUB_SERVER_URL (set by Actions),
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
SHIM_SOURCE = pathlib.Path(__file__).parent / "bin" / "gh-shim.sh"
REPO_MOUNT = "/workspace/repo"
GH_WRAPPER = "/workspace/bin/gh"
STATE_MARKER_RE = re.compile(r"<!-- github-pr-reviewer:state (\{.*?\}) -->")


# --------------------------------------------------------------------------- #
# Skill loading (the pluggable part)
# --------------------------------------------------------------------------- #
def load_skill(name: str) -> tuple[str, str]:
    """Return (title, rubric text) for skills/<name>/SKILL.md."""
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
# Follow-up state (persisted as a hidden marker in the summary comment)
# --------------------------------------------------------------------------- #
def build_state_marker(state: dict[str, Any]) -> str:
    return f"<!-- github-pr-reviewer:state {json.dumps(state)} -->"


def find_state(gh: GitHub, pr_number: int, skill_name: str) -> dict[str, Any] | None:
    """Latest persisted state for this PR + skill, from past summary comments."""
    try:
        comments = gh.list_issue_comments(pr_number)
    except Exception as exc:
        print(f"⚠️  could not list PR comments for state recovery: {exc}", file=sys.stderr)
        return None
    for c in reversed(comments):
        m = STATE_MARKER_RE.search(c.get("body") or "")
        if not m:
            continue
        try:
            state = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if state.get("skill") == skill_name and state.get("interaction_id"):
            return state
    return None


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
def build_environment(
    clone_url: str,
    skill_name: str,
    skill_text: str,
    gh_token: str,
    private: bool,
    enable_gh: bool,
) -> dict[str, Any]:
    """Fresh sandbox config: repo + skill (+ gh shim) mounted, scoped egress.

    Auth headers ride in the network allowlist `transform`s (a LIST of
    {header: value} dicts on google-genai >= 2.10.0): the egress proxy injects
    them outside the sandbox, so the token never enters the VM.
    """
    github_entry: dict[str, Any] = {"domain": "github.com"}
    if private or enable_gh:
        # Basic auth authenticates the repository-source clone/fetch (private
        # repos) and gh's git operations.
        github_entry["transform"] = [
            {"Authorization": build_basic_auth_header(gh_token)}
        ]

    allowlist: list[dict[str, Any]] = [github_entry]
    sources: list[dict[str, Any]] = [
        {"type": "repository", "source": clone_url, "target": REPO_MOUNT},
        # The review skill is mounted (.agents/skills/ is auto-registered by
        # the runtime); the same text rides in the system_instruction so the
        # rubric applies unconditionally.
        {
            "type": "inline",
            "target": f".agents/skills/{skill_name}/SKILL.md",
            "content": skill_text,
        },
    ]

    if enable_gh:
        allowlist.append(
            {
                "domain": "api.github.com",
                "transform": [{"Authorization": f"Bearer {gh_token}"}],
            }
        )
        # gh release tarball downloads redirect to the GitHub assets CDN.
        allowlist.append({"domain": "*.githubusercontent.com"})
        sources.append(
            {
                "type": "inline",
                "target": "bin/gh",
                "content": SHIM_SOURCE.read_text(encoding="utf-8"),
            }
        )

    return {
        "type": "remote",
        "sources": sources,
        "network": {"allowlist": allowlist},
    }


def build_prompt(
    repo: str,
    pr_number: int,
    pr_title: str,
    base_branch: str,
    head_branch: str,
    head_sha: str,
    diff_prompt: str,
    enable_gh: bool,
    follow_up: bool,
) -> str:
    parts = [
        f"You are reviewing GitHub pull request #{pr_number} of {repo} "
        f"(\"{pr_title}\"), targeting branch '{base_branch}' from "
        f"'{head_branch}'.\n"
    ]
    if follow_up:
        parts.append(
            f"You reviewed an earlier version of this pull request; your "
            f"previous findings are in the conversation history. New commits "
            f"may have been pushed since (current head: {head_sha}). After "
            f"checking out the current PR state, focus on what changed since "
            f"your last review: state in the summary which of your previous "
            f"findings are fixed and which remain open, and raise new findings "
            f"only for issues visible in the current diff.\n"
        )
    parts.append(
        f"The repository is mounted at {REPO_MOUNT}. Bring it to the exact PR "
        f"state by running:\n"
        f"   git -C {REPO_MOUNT} fetch origin pull/{pr_number}/head\n"
        f"   git -C {REPO_MOUNT} checkout --detach FETCH_HEAD\n"
        f"(Authentication, if needed, is injected automatically; never add "
        f"credentials.)\n"
    )
    if enable_gh:
        parts.append(
            f"An authenticated GitHub CLI is available through the wrapper at "
            f"{GH_WRAPPER} (run it as: bash {GH_WRAPPER} <args>). Use it "
            f"READ-ONLY when extra context helps the review: linked issues, "
            f"earlier review comments, CI check status (for example: bash "
            f"{GH_WRAPPER} pr view {pr_number} --repo {repo} --comments). Do "
            f"not post comments, approve, or modify anything with it; the "
            f"workflow posts the review.\n"
        )
    parts.append(
        f"The unified diff of the pull request is below. Review THESE changes. "
        f"Use the mounted repository to read the surrounding code the changes "
        f"touch or depend on, and any spec/README/docs describing intended "
        f"behavior — read only what you need, be efficient. "
        f"If a file's diff below is marked as truncated or has no textual "
        f"diff, get the full change for that file with:\n"
        f"   git -C {REPO_MOUNT} diff origin/{base_branch}...HEAD -- <path>\n\n"
        f"{diff_prompt}\n\n"
        f"Apply the review skill in your instructions. Return ONLY the JSON "
        f"object described by this schema (anchor each finding to a file path "
        f"and line that appear in the diff):\n\n"
        f"{json.dumps(FINDINGS_SCHEMA)}"
    )
    return "\n".join(parts)


def run_review(
    client: genai.Client,
    environment: dict[str, Any],
    prompt: str,
    skill_text: str,
    prior_state: dict[str, Any] | None,
    private: bool,
) -> tuple[dict[str, Any], str | None, str | None, str]:
    """Run the review with a resume cascade.

    Attempts, in order:
      1. Reuse the previous sandbox AND conversation (public repos only: a
         reused environment carries the previous job's expired token in its
         auth transform, so private repos skip this).
      2. Fresh sandbox, resumed conversation (previous_interaction_id).
      3. Fresh sandbox, cold start.

    Returns (findings, environment_id, interaction_id, mode).
    """
    system_instruction = f"{SYSTEM_INSTRUCTION}\n\n# Review skill\n\n{skill_text}"

    attempts: list[tuple[str, dict[str, Any] | str, str | None]] = []
    if prior_state:
        if not private and prior_state.get("environment_id"):
            attempts.append(
                ("resumed sandbox + conversation",
                 prior_state["environment_id"], prior_state["interaction_id"])
            )
        attempts.append(
            ("fresh sandbox + resumed conversation",
             environment, prior_state["interaction_id"])
        )
    attempts.append(("cold start", environment, None))

    last_exc: Exception | None = None
    for mode, env, prev_id in attempts:
        try:
            kwargs: dict[str, Any] = {}
            if prev_id:
                kwargs["previous_interaction_id"] = prev_id
            interaction = client.interactions.create(
                agent=BASE_AGENT,
                system_instruction=system_instruction,
                input=prompt,
                environment=env,
                **kwargs,
            )
            result = _parse_json(_extract_text(interaction))
            return (
                result,
                getattr(interaction, "environment_id", None),
                getattr(interaction, "id", None),
                mode,
            )
        except Exception as exc:
            last_exc = exc
            print(f"⚠️  attempt '{mode}' failed: {exc}", file=sys.stderr)
    raise last_exc  # every attempt failed


# --------------------------------------------------------------------------- #
# Posting
# --------------------------------------------------------------------------- #
def post_results(
    gh: GitHub,
    pr_number: int,
    head_sha: str,
    skill_title: str,
    result: dict[str, Any],
    state_marker: str = "",
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
        f"relying on it.</sub>\n"
        f"{state_marker}",
    )

    overflow: list[str] = []
    for f in findings:
        body = render_finding_comment(f, SEVERITY_EMOJI.get(f.get("severity", "info"), ""))
        anchored = False
        try:
            start_line = f.get("start_line")
            anchored = gh.post_review_comment(
                pr_number, head_sha, f["file"], int(f["line"]), body,
                start_line=int(start_line) if start_line else None,
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
    persist = os.environ.get("PERSIST", "1") == "1"
    enable_gh = os.environ.get("AGENT_GH", "1") == "1"

    pr_number = resolve_pr_number()
    skill_title, skill_text = load_skill(skill_name)
    gh = GitHub(api_url, repo, gh_token)

    print(f"Fetching PR #{pr_number} of {repo} …")
    pr = gh.get_pr(pr_number)
    files = gh.get_pr_files(pr_number)
    diff_prompt = build_diff_prompt(files)
    private = bool(gh.get_repo().get("private"))

    prior_state = None
    if persist and not dry_run:
        prior_state = find_state(gh, pr_number, skill_name)
        if prior_state:
            print(f"Found previous review state (head {prior_state.get('head_sha', '?')[:7]}) — running as a follow-up.")

    environment = build_environment(
        clone_url=f"{server_url}/{repo}.git",
        skill_name=skill_name,
        skill_text=skill_text,
        gh_token=gh_token,
        private=private,
        enable_gh=enable_gh,
    )
    prompt = build_prompt(
        repo=repo,
        pr_number=pr_number,
        pr_title=pr.get("title", ""),
        base_branch=pr["base"]["ref"],
        head_branch=pr["head"]["ref"],
        head_sha=pr["head"]["sha"],
        diff_prompt=diff_prompt,
        enable_gh=enable_gh,
        follow_up=bool(prior_state),
    )

    print(
        f"Reviewing PR #{pr_number} ({pr['head']['ref']} → {pr['base']['ref']}) "
        f"with skill '{skill_name}' ({len(files)} changed file(s), "
        f"{'private' if private else 'public'} repo) …"
    )
    client = genai.Client()
    result, env_id, int_id, mode = run_review(
        client, environment, prompt, skill_text, prior_state, private
    )
    print(f"Review completed ({mode}).")

    if dry_run:
        print(json.dumps(result, indent=2))
        return 0

    state_marker = ""
    if persist and int_id:
        state_marker = build_state_marker(
            {
                "v": 1,
                "skill": skill_name,
                "interaction_id": int_id,
                "environment_id": env_id,
                "head_sha": pr["head"]["sha"],
            }
        )

    print("Posting results …")
    post_results(gh, pr_number, pr["head"]["sha"], skill_title, result, state_marker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
