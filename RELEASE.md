# Release Process

No release may be published until the copyright holder adds an approved
`LICENSE`. Registry V2 remains a testnet prototype until an independent contract
review and remediation cycle are published.

## Preconditions

- release commit is on the protected default branch with a clean worktree
- `LICENSE`, `SECURITY.md`, `MAINTAINERS.md`, and current status/audit documents
  are present
- Python, Registry V2, frontend, container, security, and evidence workflows pass
- changelog describes every user-visible and contract-affecting change
- no private keys, feed credentials, `.env`, databases, or deployment scratch
  are tracked
- contract changes have a new version, code hash, deployment, ADR, cycle result,
  and signed evidence package
- the maintainer explicitly approves the GitHub `release` environment

## Versioning

Use semantic version tags such as `v0.2.0`. Until compatibility commitments are
published, all releases remain `0.x` and may change off-chain interfaces between
minor versions. A deployed contract binary is immutable even during `0.x`;
changing its behavior always creates a new contract version and code hash.

## Procedure

1. Update `CHANGELOG.md`, `docs/PROJECT_STATUS.md`, and evidence claim limits.
2. Run every command in `CONTRIBUTING.md` from the supported toolchains.
3. Merge through review and confirm all required GitHub checks are green.
4. Create an annotated tag: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
5. Push only that tag: `git push origin vX.Y.Z`.
6. Approve the protected `release` environment after reviewing its commit.
7. Let `.github/workflows/release.yml` build, hash, attest, and publish assets.
8. Download the release assets and independently verify checksums and
   attestations.

## Release Assets

The workflow publishes:

- source archive for the tagged commit
- Registry V2 RISC-V contract binary
- deterministic MLAT benchmark package
- SPDX JSON software bill of materials
- SHA-256 checksum file
- GitHub artifact provenance and SBOM attestations

Verify online provenance:

```bash
gh attestation verify receiver-registry-v2 -R Jeremicarose/AIRCRAFT-MALT
gh attestation verify ckb-registry-v2-vX.Y.Z.tar.gz \
  -R Jeremicarose/AIRCRAFT-MALT \
  --predicate-type https://spdx.dev/Document/v2.3
```

Verification of a release does not convert self-produced evidence into an
independent security audit or physical field validation.
