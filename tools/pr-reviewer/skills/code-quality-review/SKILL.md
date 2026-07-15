---
name: code-quality-review
description: Maintainability, design and test-coverage review rubric for GitHub pull requests
---

# Code Quality Review Rubric

You are reviewing a **pull request diff** for long-term maintainability — NOT for
security (a separate review covers that; only flag a security issue if it is so
glaring that staying silent would be negligent). Review the changed lines and
their immediate context, using the mounted repository to judge consistency with
the existing codebase.

## What to look for

### Design & simplicity
- Needless complexity: over-abstraction, premature generalization, layers that add
  nothing; code that could be half the size with the same behavior.
- Duplication of logic that already exists in the codebase (point to the existing
  helper/module the change should reuse).
- Wrong altitude: business logic in controllers/handlers, I/O in pure logic, etc.
- Public API shape: confusing signatures, boolean flags that should be two
  functions, leaky abstractions.

### Readability & consistency
- Naming that misleads or contradicts the codebase's conventions.
- Comments that restate the code, or missing explanation for genuinely
  non-obvious constraints.
- Inconsistency with the repo's established patterns, style, and idioms
  (check neighboring files in the mounted repo before flagging).

### Tests
- Changed or new behavior with no test coverage; tests that assert nothing
  meaningful; tests coupled to implementation details that will break on any
  refactor.
- Missing edge/boundary cases for the specific logic introduced.

### Performance & resources (only when material)
- Obvious N+1 patterns, unbounded growth, work inside hot loops that can be
  hoisted, sync blocking in async paths.

## Categories
Use exactly one of: `design`, `readability`, `tests`, `performance`, `consistency`.

## Severity guidance
- **critical**: will actively mislead or break maintainers (e.g. API that lies about behavior).
- **high**: significant maintainability debt or missing tests for core new behavior.
- **medium**: real but contained issue; worth fixing before merge.
- **low**: polish; nice to fix.
- **info**: observation, no action strictly required.

## Rules
- Anchor EVERY finding to a real changed file and line number from the diff.
- Ground consistency claims in the actual codebase (read the neighboring code first).
- Suggest the concrete better version, not just the objection.
- Do NOT invent files or lines that are not in the diff.
- If the change is clean, return an empty findings list and say so in the summary.
- Prefer fewer, high-confidence findings over many speculative ones.
