# Console navigation and explorer missions — 20 October 2026

This work follows the request to improve page transitions and gamify controlled
testing. It preserves the existing registry/MLAT interfaces and numerical behavior.
The [earlier release blockers](blocker-resolution-2026-10-19.md) still require
public-export approval, an independent reviewer, operator-managed wallet actions,
authorized physical receivers/reference data, and a target deployment host.

## What changed

The console now uses a shared Next.js layout. Its sidebar, header, wallet surface,
query provider and investigation state remain mounted between routes. Individual
pages stream workspace content, with a small loading skeleton instead of replacing
the entire application. The shell loads health asynchronously so a backend outage
does not prevent the local guide or settings from opening.

Navigation has pending feedback, a 180 ms content transition, heading focus after
route changes, and a reduced-motion alternative. A modal investigation inspector
closes when following its link to another workspace; the investigation itself is
retained. Wide-screen inline inspectors can remain visible. Errors stay inside
the workspace, leaving navigation available.

`/app/guide` provides six optional learning missions:

| Mission | Completion evidence | Points |
| --- | --- | ---: |
| Know your source | Correct answer about recorded owner lock/lifecycle rules | 25 |
| Meet a receiver | User selects an available receiver row | 50 |
| Follow the signal | User selects an available pipeline stage | 50 |
| Read beyond the score | Correct interpretation of a displayed benchmark residual | 50 |
| Investigate a recorded event | User inspects the solver stage of an actual historical event | 75 |
| Prepare a useful report | Valid diagnostic response prepared for browser download | 50 |

Points unlock named badges and levels from New observer to Console navigator.
Each mission counts once. Wrong answers, failed downloads, mere visits and paused
missions do not award points. A historical rejection is valid learning material;
it is never turned into a successful solve. Mission completion does not change
receiver qualification, registry state or release readiness.

Progress persists only in the browser, with known mission IDs and a pause flag.
No receiver IDs, coordinates, wallet addresses, API tokens or feed URLs are stored
in the progress record. Invalid/duplicate saved IDs cannot inflate points; storage
failure falls back to in-memory progress for the current visit. Users can pause
missions and confirm a reset without affecting application data. There are no
tokens, wallet rewards, leaderboards or required transactions.

The diagnostic export button now reports preparation, success and failure. It
awards its badge only after a valid report is prepared; the browser still controls
whether the user saves the download. Saved registry evidence can retry/recover
from a transient first-load failure while remaining explicitly historical evidence.

## Verification and measured limits

Unit coverage checks score boundaries, duplicate actions, pause/reset and storage
sanitization. Browser coverage includes persistent frame identity, route changes,
back/forward, slow loading, modal inspector navigation, offline APIs, failed versus
successful exports, actual receiver/stage actions, historical rejections, mobile,
keyboard, reduced motion and accessibility.

The first full browser run caught a selector error in the new receiver test and
an actual modal-inspector persistence regression. Both were corrected without
weakening behavior assertions. A saved-evidence initial-load failure led to bounded
client recovery. Failed reports remain in the dated artifacts directory.

Production browser testing also caught a startup mismatch: the server rendered
“Refresh map” while the shell’s shared request cache caused the browser to render
“Refreshing”. A browser-debugger capture confirmed both values on the same text
node. Development reloads did not reproduce it; an initial first-render guard
was insufficient and was removed. The shell now has its own query keys so its
background polling cannot change a streamed workspace’s initial data/loading state.
This adds separate shell status requests at bounded 10–30 second intervals; it
does not change workspace polling or suppress hydration errors. The existing map
regression and additional cold-load coverage retain error-free rendering assertions.

A small local comparison used the same synthetic backend and desktop Chromium:
five transitions in the prior candidate and five with the shared layout. The old
sidebar was replaced in all five; the new sidebar survived all five. Heading
visibility ranged about 498–846 ms before and 97–231 ms after in this observation.
These measurements describe visible navigation feedback, not complete data readiness,
and are too small for a production latency claim. Reports include the raw timings.

Final checks and source identity are recorded in the corresponding evidence package.
Local artifacts, screenshots and intermediate failures are under
`artifacts/experience-2026-10-20/`. No external publication or on-chain operation
is part of this interface change.
