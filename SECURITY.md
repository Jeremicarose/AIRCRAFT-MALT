# Security Policy

## Supported Code

Security fixes target the current default branch. No released version is yet
supported because the project has not published a tagged release.

The testnet evidence package is historical and must not be rewritten. The
current source includes contract hardening that postdates that package and is
not deployed. A security fix that changes the contract requires a new binary,
deployment, and evidence package.

## Reporting A Vulnerability

Use GitHub private vulnerability reporting for the repository when available.
If it is not enabled, contact the repository owner through a private channel
listed on the GitHub profile. Do not include private keys, live feed credentials,
or exploitable transaction details in a public issue.

Include:

- affected commit and module
- impact and required attacker capabilities
- minimal reproduction or transaction
- whether the issue affects the deployed testnet binary
- suggested embargo needs

No response-time SLA is currently offered.

## Security Model

Registry V2 relies on CKB lock scripts for authorization. The type script checks
identity and lifecycle continuity; it does not authenticate physical hardware or
validate real-world metadata.

Enforced by the current contract source candidate:

- Type-ID-derived creation identity
- exact input/output group cardinality
- immutable label and identity continuity
- monotonic exact sequence progression
- owner-lock authorization through normal CKB transaction validation
- terminal revocation and no burn
- bounded 16 KiB cell-data loading before JSON decoding
- strict JSON spelling shared with the Python and TypeScript implementations

Not guaranteed:

- receiver existence, position, custody, or clock quality
- stream endpoint safety or availability
- honesty of off-chain metadata
- uniqueness of human-readable labels
- resistance to a compromised owner key
- correctness beyond the tested, unaudited contract

## Current Security Posture

- No private-key, common provider-token, or literal secret-assignment pattern
  was found in tracked project files during the audit refreshed on 2026-09-08.
- `.env`, databases, deployment scratch files, `ckb-cli`, build targets, Python
  bytecode, Next caches, and `node_modules` are ignored.
- GitHub Actions use `contents: read` and full commit-SHA action pins.
- Admin routes default off; an admin key is required when enabled.
- The MLAT command adapter uses argument parsing and direct process execution,
  not a shell.
- Registry discovery never silently substitutes simulated records.
- Strict live ingest pins each observation to a bounded clock calibration and
  hashed receiver timing artifact; expired timing fails closed before solving.
- GitHub workflows define CodeQL scanning, pull-request dependency review,
  SPDX SBOM generation, and GitHub artifact attestations using commit-pinned
  actions.
- On 2026-09-09, both locked npm graphs passed `npm audit
  --audit-level=moderate`: there were no moderate, high, or critical findings.
  The frontend was upgraded to Next.js 16.3.4, MapLibre 6.8.0, and Sharp
  0.35.4 to remove newly reported critical and high advisories before this pass.
  npm reported one low-severity `elliptic` advisory through the latest CKB-CCC,
  JoyID, and Nervos SDK dependency chain: 4 instances in the Registry SDK and 21
  in the wallet-enabled frontend. The only automated remedy offered was a
  breaking downgrade to an old CCC prerelease, so the finding remains an
  explicit upstream risk rather than an unsafe forced update.

Known risks:

- The contract has no independent audit.
- The JSON/floating-point schema is comparatively complex for on-chain parsing.
- `CKB_SSL_VERIFY=false` disables TLS certificate validation and must not be used
  in production.
- The Flask API has a bounded, process-local sliding-window rate limiter when
  `RATE_LIMIT_ENABLED=true`; strict production mode requires it. It is not an
  account lockout or a shared limiter for multi-worker deployments.
- SQLite and a shared local volume are single-node operational dependencies.
- Security/SBOM workflow execution and branch-protection enforcement must be
  confirmed after the reorganized branch is pushed.
- `ckb-cli` is an external operator dependency with no repository-managed binary
  provenance.
- An independent security reviewer is absent.
- The current CKB-CCC dependency chain still includes the low-severity
  `elliptic` advisory described above. Recheck it on every dependency update and
  remove the exception when upstream publishes a compatible fix.

## Deployment Requirements

- Keep `STRICT_PRODUCTION_MODE=true` for live claims.
- Keep `SIMULATE_IF_UNAVAILABLE=false` and `CKB_SSL_VERIFY=true`.
- Use a reviewed standard CKB lock, multisig, or OmniLock policy.
- Separate contract-owner keys, feed credentials, API keys, and deployment keys.
- Terminate TLS at a maintained proxy and restrict CORS to actual frontend origins.
- Keep admin APIs disabled unless operationally required.
- Back up and restore-test SQLite before relying on retained data.
- Verify contract and dependency artifacts before deployment.

The external contract review scope is in
[docs/registry/SECURITY_REVIEW_REQUEST.md](docs/registry/SECURITY_REVIEW_REQUEST.md).
