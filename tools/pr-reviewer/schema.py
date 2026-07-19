"""Base system instruction and the JSON contract the agent must return.

The base instruction is deliberately REVIEW-TYPE-AGNOSTIC: what the review
looks for, its categories, and its severity semantics are defined entirely by
the pluggable review skill (skills/<name>/SKILL.md) appended to it at runtime.
Swap the skill to run a different kind of review — no code change needed.
"""

SYSTEM_INSTRUCTION = (
    "You are an automated reviewer for GitHub pull requests. "
    "What to review for — the focus areas, finding categories, severity "
    "semantics, and rules — is defined by the review skill below; apply it "
    "faithfully and only report findings that belong to it. "
    "You MUST respond with a single JSON object that matches the requested "
    "schema and nothing else — no prose, no markdown fences. "
    "Anchor every finding to a real changed file and line from the PR diff."
)

# JSON contract for structured output. `category` is a free string on purpose:
# each review skill defines its own category set.
FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "1-3 sentence overall verdict for the PR thread.",
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "file path from the diff"},
                    "line": {"type": "integer", "description": "line number on the NEW side of the diff"},
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                    },
                    "category": {
                        "type": "string",
                        "description": "one of the categories defined by the review skill",
                    },
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "recommendation": {"type": "string"},
                    "suggestion": {
                        "type": "string",
                        "description": (
                            "OPTIONAL. Exact replacement code for the anchored "
                            "line(s): complete lines, correct indentation, no "
                            "diff markers. Include ONLY when the fix is a "
                            "precise, self-contained replacement of those "
                            "lines; GitHub renders it as a one-click 'Commit "
                            "suggestion'. Omit when the fix needs changes "
                            "beyond the anchored lines."
                        ),
                    },
                    "start_line": {
                        "type": "integer",
                        "description": (
                            "OPTIONAL, only with suggestion. First line of a "
                            "multi-line replacement; `line` is then the LAST "
                            "replaced line. Omit for single-line suggestions."
                        ),
                    },
                },
                "required": [
                    "file", "line", "severity", "category",
                    "title", "detail", "recommendation",
                ],
            },
        },
    },
    "required": ["summary", "findings"],
}

SEVERITY_EMOJI = {
    "critical": "\U0001F534",  # red
    "high": "\U0001F7E0",      # orange
    "medium": "\U0001F7E1",    # yellow
    "low": "\U0001F535",       # blue
    "info": "⚪",               # white
}

# Worst-first ordering for posting.
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
