# Maintainers

## Current Ownership

The current repository maintainer is:

- [@Jeremicarose](https://github.com/Jeremicarose): repository administration,
  Registry V2, evidence releases, and MLAT reference maintenance

This is a single-maintainer pre-release project. No other person should be
presented as an approver, security contact, or release authority without their
explicit agreement.

## Decision Authority

The maintainer approves:

- contract and lifecycle changes
- evidence publication
- release tags and artifacts
- security embargoes and disclosures
- new maintainers and code owners

Contract schema or lifecycle changes require an ADR, CKB-VM tests, a new code
hash, a new deployment, and a new evidence package. Historical evidence is
immutable.

## Review Expectations

- No author approves their own security-critical contract change without an
  independent reviewer.
- Release tags require the checklist in [RELEASE.md](RELEASE.md).
- Vulnerabilities follow [SECURITY.md](SECURITY.md), not public issue triage.
- Maintainer succession must update this file and `.github/CODEOWNERS` together.

There is currently no response-time or long-term-support commitment.
