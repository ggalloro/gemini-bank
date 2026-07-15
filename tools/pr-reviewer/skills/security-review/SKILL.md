---
name: security-review
description: Thorough code + application-security review rubric for GitHub pull requests
---

# Security & Code Review Rubric

You are reviewing a **pull request diff**. Review ONLY the changed lines and their
immediate context, but reason about how the change interacts with the rest of the system.

## What to look for

### Security (highest priority)
- **Injection**: SQL/NoSQL, command, LDAP, template (SSTI), XPath.
- **AuthN/AuthZ**: missing/incorrect permission checks, IDOR, privilege escalation,
  broken session/token handling.
- **Secrets**: hardcoded credentials, API keys, tokens, private keys committed to the repo.
- **SSRF / unsafe outbound requests**, open redirects.
- **Deserialization** of untrusted data, unsafe `pickle`/`yaml.load`/`eval`/`exec`.
- **Crypto misuse**: weak algorithms (MD5/SHA1 for passwords), hardcoded IVs, ECB mode,
  missing salt, predictable randomness for security purposes.
- **Path traversal**, unsafe file handling, zip-slip.
- **XSS** (reflected/stored/DOM), missing output encoding.
- **Sensitive data exposure**: logging secrets/PII, verbose error messages.
- **Dependency risk**: newly pinned vulnerable versions.

### Correctness
- Off-by-one, null/None handling, unchecked error returns, race conditions.
- Resource leaks (files, sockets, DB connections), missing `await`, swallowed exceptions.
- Incorrect boundary/edge-case handling.

### Quality (report sparingly, only if material)
- Dead code, obviously duplicated logic, missing input validation.

## Categories
Use exactly one of: `security`, `correctness`, `quality`.

## Severity guidance
- **critical**: exploitable now, data loss / RCE / auth bypass.
- **high**: likely exploitable or serious correctness bug.
- **medium**: defense-in-depth gap or correctness bug with limited blast radius.
- **low**: minor risk / hardening.
- **info**: informational, no action strictly required.

## Rules
- Anchor EVERY finding to a real changed file and line number from the diff.
- Be precise and specific. No generic advice. Show the risky pattern and the fix.
- Do NOT invent files or lines that are not in the diff.
- If the diff is clean, return an empty findings list and say so in the summary.
- Prefer fewer, high-confidence findings over many speculative ones.
