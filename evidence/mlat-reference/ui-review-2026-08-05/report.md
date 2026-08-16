# UI Review Record: MLAT Airspace Console

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **App URL** | http://127.0.0.1:3000 |
| **Session** | mlat-console |
| **Source commit** | `ba0f87fb58572f8db9213418c05798a96dd99fc0` |
| **Worktree** | Dirty; the TypeScript redesign was not committed at capture time |
| **Evidence class** | `validation_only` |
| **Scope** | Visual route coverage at desktop-sized viewports |

## Summary

Eleven screenshots record the overview, live map, aircraft, receivers,
pipeline, metrics, environment, settings, and command-palette states. The
captures range from 1280x639 to 1440x1000. File hashes and dimensions are in
`manifest.json`; `checksums.sha256` protects the report, manifest, and images.

No unresolved visual issue was recorded during this capture. That statement is
only a session note, not a finding that the interface is defect-free.

## Supported Claims

- the listed routes rendered during a local UI review
- replay and operational-state labels were visible in the captured interface
- the captured files have the hashes recorded in this package

## Unsupported Claims

- synchronized physical receiver operation or MLAT accuracy
- live CKB receiver discovery or transaction verification
- mobile or tablet usability
- WCAG conformance, complete keyboard support, or screen-reader compatibility
- performance, cross-browser compatibility, availability, or absence of defects
- correspondence between every displayed value and an independently verified
  backend response

This package is supporting presentation evidence only. The deterministic MLAT
benchmark and future physical field-trial bundles use separate evidence classes
and verifiers.

## Verify

From this directory, run:

```bash
shasum -a 256 -c checksums.sha256
```
