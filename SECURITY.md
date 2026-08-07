# Security Policy

LLM Errata is currently a public concept proposal and may later include schemas, conformance tests, adapters, or reference implementations. Security reports are welcome for any versioned artifact in this repository.

## Supported versions

Until a later policy states otherwise, only the latest released version is eligible for security fixes.

| Version | Supported |
|---|---|
| 0.1.x | Yes |
| Earlier or unreleased revisions | No |

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for this repository:

1. Open the repository's **Security** tab.
2. Select **Report a vulnerability**.
3. Submit the report privately with the information listed below.

If the private reporting option is not available, do not publish exploit details, secrets, personal data, or proof-of-concept material in a public issue. Open a minimal public issue stating only that a private security-reporting channel is required. A maintainer can then enable or identify an appropriate private channel.

Include, where applicable:

- the affected version, file, component, or protocol field;
- the security boundary or invariant that fails;
- prerequisites and a minimal reproduction;
- likely impact and affected data or actors;
- suggested mitigation;
- whether the finding has been disclosed elsewhere.

Use synthetic data and redact tokens, credentials, personal information, proprietary material, and customer data.

## Response expectations

This independent project does not promise a fixed response or remediation time. A maintainer will attempt to acknowledge a complete private report, assess reproducibility and impact, coordinate a correction when appropriate, and credit the reporter if requested. Public disclosure should be coordinated only after a mitigation or an agreed disclosure date.

## Scope

Security-relevant findings include, but are not limited to:

- signature, sequence, replay, or receipt-validation bypasses;
- incomplete quarantine or descendant-repair closure;
- false `verified` status for unknown, partially covered, or untested stores;
- cross-tenant, identity-binding, or authorization failures;
- leakage of memory contents, provenance, or deletion requests;
- unsafe reference code or conformance tooling added to the repository.

Factual disagreements, prior-art reports, and specification design proposals are not vulnerabilities; submit them through the normal contribution process.
