# Pilot Video Storyboard

This folder contains nine ordered 16:9 images for a 60-90 second overview of CKB
Receiver Registry V2 and its proposed product-validation pilot.

Upload the PNG files from `frames/` in filename order. The matching editable SVG
files are in `sources/`.

## Storyboard

| Scene | File | Suggested time | Narration |
|---:|---|---:|---|
| 1 | `01-title.png` | 6-8 seconds | CKB Receiver Registry gives a receiver one stable identity while its owner, metadata, network, or operating status changes. |
| 2 | `02-coordination-problem.png` | 8-10 seconds | Receivers move, are replaced, change owners, and retire. Separate systems may keep different identifiers and outdated records. |
| 3 | `03-registry-lifecycle.png` | 9-11 seconds | Registry V2 records each owner-authorized change in order. Updates and transfers preserve the identity. Revocation permanently retires it. |
| 4 | `04-registry-mlat-boundary.png` | 9-11 seconds | CKB verifies the Registry lifecycle, not physical hardware, coordinates, clocks, or feeds. MLAT separately estimates aircraft position from qualified observations. |
| 5 | `05-receiver-workflow.png` | 10-13 seconds | The reference workflow discovers current records, checks receiver readiness, correlates one transmission, compares reception times, and preserves contributing identities. |
| 6 | `06-directory-outcome.png` | 8-10 seconds | Coordinators discover current records, inspect ownership history, and export validated JSON without knowing blockchain storage locations in advance. |
| 7 | `07-pilot-scope.png` | 8-10 seconds | The pilot tests usability, wallet burden, discovery, and follow-up behavior. It does not claim live accuracy, hardware attestation, or safety use. |
| 8 | `08-participants.png` | 8-10 seconds | The study needs four receiver operators and two coordinators. No blockchain experience or physical receiver connection is required. |
| 9 | `09-next-step.png` | 7-9 seconds | Participants apply, confirm eligibility, complete one observed session, and return within seven days. The evidence determines whether the product continues, changes, or stops. |

The complete suggested narration is about 172 words. At a calm technical pace of
130-145 words per minute, it produces roughly 71-79 seconds of speech. Allowing
brief pauses at scene changes keeps the finished video within the 60-90 second
target.

## Upload Folder

Use only the files in `frames/` when the video tool asks for images:

1. `01-title.png`
2. `02-coordination-problem.png`
3. `03-registry-lifecycle.png`
4. `04-registry-mlat-boundary.png`
5. `05-receiver-workflow.png`
6. `06-directory-outcome.png`
7. `07-pilot-scope.png`
8. `08-participants.png`
9. `09-next-step.png`

## Before Publishing

- Put the real application link and contact address in the video description.
- State that the proposed $30 incentive is conditional on grant approval.
- Do not describe researched leads as confirmed participants.
- Do not describe the software as audited, production-ready, mainnet-ready, or
  physically field-validated.
- Keep the video labeled as a testnet product-validation pilot.
