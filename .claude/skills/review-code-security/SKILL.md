---
name: review-code-security
description: Reviews a code diff for security vulnerabilities — injection, auth, secrets, crypto misuse, SSRF, deserialization, and dependency risk. Use when the user asks for a security review, threat check, or vulnerability scan of a diff or PR.
---

# Reviewing Code for Security

## When to use

The user wants a security-focused review of a code change. For general correctness, use `review-code-correctness`. For performance, use `review-code-performance`.

## Inputs required

- The diff or PR
- Trust boundaries crossed by the change (user input → server, server → DB, server → third party)
- Whether the affected component is internet-facing

If trust boundaries are unclear, infer from the diff and state assumptions explicitly.

## Procedure

1. Map data flow in the diff: where untrusted input enters, where it is validated, where it leaves to a sensitive sink (SQL, shell, file, network, eval).
2. Walk the OWASP-aligned checklist below.
3. Report findings with file:line, the vulnerability class, and a concrete exploit sketch.

## Security checklist

**Injection sinks**
- SQL built by string concatenation; missing parameterization
- Shell commands assembled from input (use argv arrays, not strings)
- Template rendering with autoescape off
- Dynamic code execution: `eval`, `exec`, `Function`, `pickle.load`, Java deserialization
- Path traversal: untrusted segments joined into filesystem paths
- XXE: XML parsers with DTD/external entity expansion enabled

**Authn / authz**
- Endpoints added without auth middleware
- Authorization checks done at the controller but not at the service / data layer
- IDOR: object access keyed on user-supplied ID without ownership check
- Privilege escalation through mass-assignment of role / admin fields
- JWT verification skipped, alg=none accepted, weak secret

**Secrets and crypto**
- Hard-coded credentials, tokens, keys, connection strings
- Secrets logged or returned in error responses
- Custom crypto, ECB mode, MD5/SHA1 for security purposes, fixed IV/nonce
- Passwords stored without a modern KDF (argon2, scrypt, bcrypt)

**Web specifics**
- Reflected/stored XSS: untrusted data into HTML/JS context without escaping
- CSRF on state-changing routes without token or SameSite cookie protection
- Open redirect: user-controlled URL passed to `Location`
- SSRF: outbound HTTP to a user-controlled URL without an allowlist
- CORS: `*` with credentials, or reflecting Origin without validation

**Dependencies and supply chain**
- New dependency from an untrusted source
- Pinned to a vulnerable version
- Postinstall scripts in package additions

**Logging and PII**
- Sensitive data logged (passwords, tokens, full card numbers, full SSN)
- Errors include stack traces in user responses

## Severity

- **Critical**: exploitable now, no auth needed, high impact
- **High**: exploitable with conditions or by authenticated user
- **Medium**: weakness with limited reach
- **Low**: hardening, defense-in-depth
- **Info**: observation

## Output contract

```
| Severity | File:line | Class | Finding | Exploit sketch | Suggested fix |
```

End with overall risk verdict and a list of trust-boundary assumptions made.

## Stopping conditions

Stop if:
- The change touches cryptographic protocol design (escalate to a security engineer)
- The diff includes binary or generated files that cannot be reviewed
- Required context about user roles or threat model is missing
