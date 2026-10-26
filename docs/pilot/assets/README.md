# Pilot Visual Assets

These diagrams use the project's operational design system and preserve the
boundary between Registry V2 claims and MLAT reference claims. The SVG files are
the editable sources. Matching PNG files are provided for forms, presentations,
and platforms that do not accept SVG.

| Asset | Purpose | Recommended use |
|---|---|---|
| `registry-lifecycle.svg` | Explains registration, active discovery, repeatable update or transfer, and terminal revocation | Pilot introduction, lifecycle documentation, presentation |
| `registry-mlat-boundary.svg` | Separates what CKB Registry V2 verifies from what the MLAT reference calculates | Public one-pager, partner introduction, architecture overview |
| `receiver-workflow.svg` | Shows the nine-stage path from aircraft transmission to a position estimate with receiver provenance | Technical presentation and implementation documentation |

## Claim Boundaries

- Registry V2 verifies contract-valid identity and lifecycle transitions. It
  does not verify physical receiver existence, coordinates, clocks, or feeds.
- Runtime qualification checks feed identity, freshness, timing, and geometry.
  These are MLAT application checks, not CKB claims.
- The solver estimates an aircraft position from correlated observations made by
  at least four suitably placed, synchronized receivers.
- Mode S is not described as always carrying an aircraft position. The workflow
  treats the radio message as input to an MLAT estimate.

Keep these statements intact when adapting the diagrams. Do not add production,
security-audit, hardware-attestation, live-accuracy, sustainability, scalability,
or interoperability claims without separate evidence.
