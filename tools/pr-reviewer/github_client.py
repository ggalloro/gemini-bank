"""GitHub REST helpers for the PR reviewer: PR context, diff prompt, posting."""

from __future__ import annotations

import base64
import textwrap
from typing import Any

import requests


class GitHub:
    """Minimal GitHub REST v3 client scoped to one repository."""

    def __init__(self, api_url: str, repo: str, token: str):
        self.api = api_url.rstrip("/")
        self.repo = repo  # "owner/name"
        self.s = requests.Session()
        self.s.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    # ------------------------------------------------------------------ #
    def _url(self, path: str) -> str:
        return f"{self.api}/repos/{self.repo}{path}"

    def get_repo(self) -> dict[str, Any]:
        r = self.s.get(self._url(""))
        r.raise_for_status()
        return r.json()

    def get_pr(self, number: int) -> dict[str, Any]:
        r = self.s.get(self._url(f"/pulls/{number}"))
        r.raise_for_status()
        return r.json()

    def get_pr_files(self, number: int) -> list[dict[str, Any]]:
        """All changed files of the PR (paginated; `patch` is the per-file diff)."""
        files: list[dict[str, Any]] = []
        page = 1
        while True:
            r = self.s.get(
                self._url(f"/pulls/{number}/files"),
                params={"per_page": 100, "page": page},
            )
            r.raise_for_status()
            batch = r.json()
            files.extend(batch)
            if len(batch) < 100:
                return files
            page += 1

    # ------------------------------------------------------------------ #
    def post_issue_comment(self, number: int, body: str) -> None:
        """A plain comment in the PR conversation (used for the summary)."""
        r = self.s.post(self._url(f"/issues/{number}/comments"), json={"body": body})
        r.raise_for_status()

    def post_review_comment(
        self, number: int, commit_id: str, path: str, line: int, body: str
    ) -> bool:
        """One line-anchored review comment on the PR diff.

        Returns False (instead of raising) when GitHub rejects the anchor —
        typically because the line isn't part of the diff — so the caller can
        fall back to the summary thread.
        """
        r = self.s.post(
            self._url(f"/pulls/{number}/comments"),
            json={
                "commit_id": commit_id,
                "path": path,
                "line": line,
                "side": "RIGHT",
                "body": body,
            },
        )
        if r.status_code == 422:
            return False
        r.raise_for_status()
        return True


# ---------------------------------------------------------------------- #
def build_diff_prompt(files: list[dict[str, Any]], max_chars_per_file: int = 20000) -> str:
    """Render the PR's per-file diffs into a compact prompt block.

    `patch` can be absent (binary or very large files) — flagged rather than
    silently skipped, so the reviewer knows the file changed.
    """
    parts: list[str] = []
    for f in files:
        path = f.get("filename") or "unknown"
        status = f.get("status", "modified")
        patch = f.get("patch")
        if patch is None:
            parts.append(f"### FILE: {path} [{status}] (no textual diff — binary or too large)")
            continue
        if len(patch) > max_chars_per_file:
            patch = patch[:max_chars_per_file] + "\n... [diff truncated] ..."
        parts.append(f"### FILE: {path} [{status}]\n```diff\n{patch}\n```")
    if not parts:
        return "(no file changes in this pull request)"
    return "\n\n".join(parts)


def build_basic_auth_header(token: str, username: str = "x-access-token") -> str:
    """Basic auth header for git-over-HTTPS on GitHub.

    `x-access-token` works for GitHub Actions installation tokens; for classic
    PATs GitHub accepts any username, so the same header works for both.
    """
    return f"Basic {base64.b64encode(f'{username}:{token}'.encode()).decode()}"


def render_finding_comment(f: dict[str, Any], emoji: str) -> str:
    """Format one finding as a GitHub markdown comment body."""
    return textwrap.dedent(
        f"""\
        {emoji} **[{f['severity'].upper()} · {f['category']}] {f['title']}**

        {f['detail']}

        **Recommendation:** {f['recommendation']}

        <sub>🤖 Automated review by a Gemini managed agent · advisory, verify before relying on it.</sub>"""
    )
