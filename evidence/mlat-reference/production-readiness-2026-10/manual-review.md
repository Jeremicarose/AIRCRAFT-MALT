# Manual browser review

Reviewed the actual locally served application with Agent Browser, in addition
to Playwright. Synthetic inspection used an isolated generated-data database;
historical inspection used the 362-event compact replay database. No wallet
transaction or external message was sent.

## Observed

- Synthetic overview visibly labelled SYNTHETIC; separate Registry and MLAT state.
- Aircraft positions, contributor buttons, residual and heuristic quality wording.
- Historical event 5711382: 5 original receiver arrival times, calculated position,
  3.17 m residual, 6 best-candidate iterations, and explicit absent clock/frame proof.
- Clicking the actual Next stage control changed the text from ingestion to
  validation. Published correlation remains explicitly distinct from raw-frame work.
- Rejected event 26543 at 390px viewport: no aircraft position claimed, altitude
  rejection explained, observations still inspectable, no horizontal page overflow.
- The historical desktop map displayed real background tiles and the dataset
  receiver geometry, with OpenStreetMap attribution. The mobile screenshot also
  demonstrates that event details remain visible while the lazy map loads.
- No uncaught page errors were reported by the browser during these inspections.

## Screenshots

- [Synthetic overview](screenshots/synthetic-overview.png)
- [Historical desktop](screenshots/historical-desktop.png)
- [Stage inspection](screenshots/historical-stage-inspection.png)
- [Mobile rejected event](screenshots/historical-mobile-rejection.png)

The automated suites additionally exercise Registry forms, contribution navigation,
API-refresh recovery, map failure isolation, keyboard use and accessibility. They
are local tests with explicit fixtures, not a real wallet or physical receiver trial.

A resumed session initially had missing files in its temporary Python installation,
which made its disposable test server fail. The environment was rebuilt under
ignored workspace artifacts; the historical browser inspection above then succeeded.
