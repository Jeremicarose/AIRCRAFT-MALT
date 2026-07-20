# Five-Minute Evidence Demo

This recording is a proof walk-through, not a feature tour. Record only after
`./run-live.sh` passes its launch gates and a trusted reference window is ready.

## Before recording

- Show the current commit hash in a terminal.
- Keep `/app/pipeline.html`, `/app/localization.html`, and
  `/app/analytics.html` open.
- Use a clean `benchmark/captures/<timestamp>` directory.
- Keep receiver transaction hashes and the registry type hash available.
- Do not use replay footage in a recording labeled live.

## Shot sequence

1. **CKB identity and discovery, 45 seconds**
   - Show the receiver cells in the explorer.
   - Open Receiver Registry and match canonical IDs to the runtime receivers.
   - Open Pipeline and show registration and discovery as verified.

2. **Live observation ingest, 45 seconds**
   - Show receiver observations increasing on Pipeline.
   - Point out the live provenance label and latest signal age.
   - Show at least four synchronized receivers.

3. **MLAT output, 60 seconds**
   - Open Localization and select an aircraft.
   - Show receiver support, solver method, uncertainty, and freshness.
   - Open the same aircraft through the public API.

4. **Storage and delivery, 45 seconds**
   - Return to Pipeline and show correlation, solve, storage, API, and dashboard.
   - Open `/api/pipeline` so the machine-readable status is visible.

5. **Measured evidence, 75 seconds**
   - Open System Metrics and show throughput, freshness, solve latency, memory,
     sampled availability, and external accuracy.
   - Open the timestamped evidence manifest and input hashes.

6. **Close, 30 seconds**
   - State the product accurately: decentralized receiver registry and aviation
     data control plane, with off-chain observation processing and MLAT.
   - State the measured window, receiver count, reference source, and visible
     limitations without extrapolating beyond the report.

## Required final frame

Show the evidence bundle path, its `manifest.json`, the published commit hash,
and the Pipeline verdict together. A reviewer should be able to reproduce every
number shown in the recording from that bundle.
