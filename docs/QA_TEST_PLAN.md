# Production Readiness Test Plan

Last run: 2026-09-09

`PASS` means the workflow was executed successfully in this session. `PARTIAL`
means a real part of the workflow works, but an end-to-end requirement remains.
`NOT RUN` means the required external access or user-owned wallet was not
available.

| Test | Expected result | Status | Verification |
|---|---|---|---|
| Open application | Live Map is the first operational screen | PASS | Root, `/app`, and legacy `/dashboard` redirect to `/app/localization`; the Registry route remains available for identity and lifecycle work |
| Direct route and refresh | Every major URL renders without client navigation | PASS | Registry, MLAT overview, map, aircraft, receivers, pipeline, metrics, diagnostics, and settings returned HTTP 200 |
| Navigate with browser history | Back and forward restore the expected route | PASS | Settings and Live Map restored in order |
| Load map | Geographic base map, controls, markers, and attribution render | PASS | OpenStreetMap context plus 3 aircraft and 5 receiver markers rendered |
| Zoom map | Map camera changes without resizing the layout | PASS | Selected marker screen position changed after zoom |
| Select receiver marker | Map, URL, context bar, and inspector select the same receiver | PASS | New York marker selected `RECV_NYC_001` everywhere |
| Select receiver row | Table, URL, map, and inspector select the same receiver | PASS | Washington selection persisted through direct refresh |
| Keyboard receiver selection | Arrow keys move focus and Enter selects | PASS | Focus and selection moved from Boston to Washington |
| Search receiver | Matching receiver appears and can be selected | PASS | `PHL` selected Philadelphia from the map search |
| Empty receiver search | Empty state explains how to recover | PASS | Non-existent query showed a clear reset instruction |
| Filter aircraft | Filter changes active state and visible rows | PASS | Attention filter became pressed and reduced the queue |
| Select aircraft | Queue, inspector, charts, and global state agree | PASS | `D4E5F6` became selected in all checked surfaces |
| Select pipeline stage | Detail and accessible state change together | PASS | MLAT solve became pressed and opened MLAT solve details |
| Change metrics range | Selected range changes and charts remain rendered | PASS | Changed 24h to 1h; 8 chart surfaces remained |
| Change settings | Preference persists and changes runtime behavior | PASS | Saved 35-second polling and compact rows; map reported 35-second polling |
| Open mobile navigation | Drawer fits, traps interaction, and closes | PASS | Tested at 390 by 844 pixels |
| Open mobile inspector | Inspector fits and retains selected context | PASS | Drawer width 366.6 pixels in a 390-pixel viewport |
| Mobile receiver workspace | Core flow works without document overflow | PASS | Document width equaled 390 pixels; map height was 320 pixels |
| Tablet live map | Map fills its panel without blank space | PASS | Region, MapLibre container, and canvas each measured 620 pixels high |
| Backend unavailable | Page remains usable and explains recovery | PASS | Clear 503 message and retry action; no raw error exposed |
| Backend recovery | Existing page resumes without full reload | PASS | Polling restored 3 aircraft and 5 receivers; alert cleared |
| Connect CKB wallet | Real connector opens on clearly labeled testnet | PARTIAL | CCC dialog listed six wallets; no user wallet was connected in this session |
| Create receiver in browser | Build, sign, submit, confirm, and refresh state | BLOCKED | SDK-backed form is read-only on the historical mutable deployment; a reviewed data1 deployment and funded signer are required |
| Update receiver in browser | Sign successor cell and increment sequence | BLOCKED | Requires the reviewed data1 deployment and a funded owner signer |
| Transfer receiver in browser | Current owner signs and owner lock changes | BLOCKED | Requires the reviewed data1 deployment and two funded test owner signers |
| Revoke receiver in browser | Owner signs terminal tombstone | BLOCKED | Requires the reviewed data1 deployment and a disposable owner identity |
| Verify lifecycle evidence | Create, update, transfer, and revoke hashes resolve | PASS | Offline verifier passed; CKB testnet explorer loaded the create transaction |
| Contract lifecycle | Valid transitions pass and invalid transitions fail | PASS | 5 host and 11 CKB-VM tests passed after the CKB target build |
| Cross-language SDK | Protocol vectors and transaction preparation agree | PASS | 69 TypeScript SDK tests and 171 shared runtime assertions passed |
| Frontend receiver state | Invalid, future, and stale observations fail closed; exact `u64` values are not rounded | PASS | 9 focused precision, freshness, receiver-reference, and standalone-asset tests passed |
| Python application | Registry, API, MLAT, database, and evidence tests pass | PASS | 168 tests passed |
| Production build | Optimized Node 22 build completes | PASS | Next.js 16.3.4 Webpack build generated all 16 routes |
| Production console | No critical browser errors or development overlay | PASS | Desktop and mobile production console/error checks were empty |
| Production response security | Basic security headers present; framework hidden | PASS | `nosniff`, `DENY`, referrer, and permissions policies present; no `X-Powered-By` |
| Production dependency audit | No critical, high, or moderate advisories | PASS | Updated Next.js to 16.3.4, MapLibre to 6.8.0, and Sharp to 0.35.4; npm then reported only 21 low findings in the current CCC transitive chain |
| Public deployment | Shareable hosted frontend URL is live | NOT RUN | Render blueprint is configured, but no Render account/deployment access was provided |

## Performance Sample

Local optimized production overview at 1440 by 1000 pixels:

| Metric | Result |
|---|---:|
| Time to first byte | 19.3 ms |
| First contentful paint | 248 ms |
| Largest contentful paint | 248 ms |
| Cumulative layout shift | 0 |

These local measurements verify frontend behavior. They do not predict public
Render cold-start time or internet latency.
