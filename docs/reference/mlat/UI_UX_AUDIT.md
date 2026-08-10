# MLAT Airspace Console UI/UX Audit

## Scope

This review covers the Next.js operator console under `reference/mlat/frontend`. It evaluates visual hierarchy, component consistency, accessibility, information architecture, interaction design, responsive behavior, and operational usefulness.

## Ranked Findings

| Rank | Impact | Finding | Resolution |
| --- | --- | --- | --- |
| 1 | Critical | Status and interaction semantics were incomplete. Segmented controls did not expose pressed state, sortable columns did not expose sort order, and warning or neutral timeline entries rendered success checkmarks. | Resolved with shared segmented controls, `aria-sort`, tone-accurate status glyphs, table labels, and explicit non-color state text. |
| 2 | Critical | Metrics presented eight equal chart panels, making throughput, latency, solve quality, and secondary diagnostics compete at the same visual weight. | Resolved with a dominant throughput workspace, compact latency and distribution diagnostics, a three-part quality band, and a separate resource and service-objective region. |
| 3 | High | Search, filter, switch, progress, metric-strip, and preference-row styles were duplicated across pages. This invited state and spacing drift. | Resolved with shared `SearchField`, `SegmentedControl`, `Switch`, `ProgressBar`, `StatStrip`, `PreferenceRow`, and `Skeleton` components. |
| 4 | High | Pipeline stage names truncated inside the primary flow, repeated status badges created noise, and the headline claimed the pipeline was operational while evidence blockers remained open. | Resolved with wrapping stage labels, restrained textual stage state, one summary chip, a shared progress component, and a truthful processing/evidence headline. |
| 5 | High | Settings used less than half of a desktop viewport and offered no operational memory of local changes. | Resolved with a configuration workspace, browser capability posture, and device-local preference history. No server audit history is fabricated. |
| 6 | High | Motion timing ranged from 200ms to 1.6s, including continuously moving pipeline dots and 500ms chart transitions. | Resolved with one 180ms operational easing contract, static flow state, reduced-motion handling, and 180ms map and chart transitions. |
| 7 | Medium | Environment repeated a status badge on every configuration row, giving routine state the same weight as missing trust configuration. | Resolved with compact tone glyphs and visible values; chips remain for states that need explicit emphasis. |
| 8 | Medium | Lazy chart fallbacks used a fixed 220px height even when the destination chart was smaller, causing avoidable layout movement. | Resolved with height-aware lazy wrappers and stable chart frames. |
| 9 | Medium | The activity feed looked alive but did not support investigation. | Resolved by linking aircraft and receiver events directly to their relevant investigation route with visible keyboard focus. |
| 10 | Medium | The global sidebar shortcut could fire while focus was inside an interactive control, and the displayed command shortcut implied macOS only. | Resolved by ignoring interactive targets and displaying the supported Command/Ctrl shortcut. |

## Remaining Product Gaps

- Receiver CPU, disk, packet loss, uptime history, transfer history, and revocation history are not exposed by the current receiver API. The console states this explicitly.
- Processor CPU samples are not emitted by the metrics evidence API. Metrics treats this as an instrumentation gap rather than showing synthetic data.
- Incident history remains bounded by the data currently returned by the operational APIs. A durable cross-session incident log requires a backend event contract.

## Design-System Contract

- Graphite surfaces remain flat at rest; shadows are reserved for overlays and map controls.
- Signal blue indicates selection and primary commands.
- Trust cyan indicates cryptographic identity only.
- Green, yellow, orange, and red retain their health, attention, replay, and failure meanings.
- Data series use separate teal, violet, and gold colors unless the series itself represents a semantic status.
- All state transitions complete in 180ms or less and honor reduced-motion preferences.
