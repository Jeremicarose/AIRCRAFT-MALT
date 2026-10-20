# Failures found while implementing the console experience

The earlier readiness evidence is preserved. These results concern the new shared
console layout and learning missions. A successful diagnostic script exit does not
mean that the application passed: diagnostic probes can intentionally capture errors.
The actual browser reports carry explicit passed/failed counts.

## Application fixes

- The old modal investigation panel stayed open after following its receiver link
  because the new shared layout preserved it. The panel then covered the destination.
  Route changes now close a modal panel while preserving investigation context.
  The existing aircraft → receiver → aircraft browser scenario passes.
- A failed first server request for saved registry evidence left that section empty.
  A bounded client retry and an explicit error/retry control now allow recovery.
  Saved evidence remains separate from authoritative live discovery.
- Production map loading could render “Refreshing” in the browser against the
  server's “Refresh map” text. The browser debugger captured both values on the
  same React text node. The shared shell started a request using a workspace's
  cache key before that workspace became interactive. Separate shell query keys
  resolve the collision. The original map regression and cold-load checks pass.
  Thirty development-mode probes did not reproduce it; a first-render guard alone
  failed and was removed. No hydration warning was suppressed.

## Test corrections

- The first new receiver mission test looked for an aircraft-page control on the
  receiver page. It now selects the actual receiver row and still requires an
  earned mission after a user action.
- The mobile mission keyboard check initially focused a control before hydration
  enabled it. It now verifies that the control is enabled and focused before
  pressing Enter. The same badge and accessibility requirements remain.
- Streamed responses can temporarily include hidden content outside the main
  workspace. Unscoped text selectors matched both the visible warning and a hidden
  copy in benchmark/replay tests. Assertions now select the main workspace and
  still require the real warning to be visible. Counts, solve outcomes and
  qualification assertions were not relaxed.
- A static source test was updated for the named inspection handler. The handler
  still selects the requested stage, and the existing browser behavior test passes.

## External and execution failures

One full browser run failed when the public CKB indexer did not return a receiver
directory. The page correctly showed “Indexer unavailable” and excluded those
receivers. The unchanged targeted test passed after service recovery; the complete
38-test run then passed. This suite uses synthetic MLAT data but includes public
CKB read-only discovery. It is not a fully offline test suite or wallet rehearsal.

An early container build was stopped when the VM was shut down during investigation.
Its exit 255 is retained as a canceled/superseded run, not a successful build.
The first development reproduction timed out while compiling. A browser-debugger
probe failed to serialize circular React objects; the revised probe captured the
relevant text values. These failures remain in the exact command inventory.

The unit runner emits Node's existing experimental TypeScript-transform warning.
Browser tooling emits a color-environment warning. They are preserved in logs.

The source lesson was also corrected during review: the record's owner lock and
lifecycle rules do not establish that today's owner personally signed every earlier
state. No contract, SDK, solver, fixture, or on-chain deployment was changed.
