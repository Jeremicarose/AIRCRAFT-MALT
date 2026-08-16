# Readsb / Dump1090 Beast To JSONL Mapping

## Why Beast is the first live source

MLAT needs one raw Mode-S observation and one precise receive time from each
physical receiver. Beast TCP preserves the receiver's 48-bit sample counter;
aircraft-state JSON, SBS rows, and map tracks do not preserve the input needed
for multilateration.

Beast counters from different receivers are not comparable by themselves. Each
counter must be calibrated onto the same timebase before localization.

## Required MLAT record

```json
{
  "receiver_id": "0x1111111111111111111111111111111111111111111111111111111111111111",
  "timestamp_ns": 1714400000123456789,
  "timestamp": 1714400000.1234567,
  "message": "8D4840D6202CC371C32CE0576098",
  "clock_synchronized": true,
  "clock_source": "gpsdo-nyc",
  "clock_uncertainty_ns": 50
}
```

- `receiver_id` is the immutable 32-byte Registry V2 identity from the CKB type
  script arguments. `RECV_NYC_001` is only the human Receiver Label.
- `timestamp_ns` is an integer arrival timestamp on a common receiver timebase.
  A decimal string is also accepted by the JSON bridge without losing bits.
- `timestamp` is Unix seconds for display and freshness checks. It is not used
  for TDOA when `timestamp_ns` is present.
- `message` is the complete uppercase Mode-S frame as hex.
- `clock_synchronized` must be exactly `true`.
- `clock_source` identifies the measured calibration source.
- `clock_uncertainty_ns` must be present and no greater than
  `MAX_CLOCK_UNCERTAINTY_NS` (100 ns by default).

Mixed precision groups, epoch float timestamps without `timestamp_ns`, missing
clock qualification, and excessive declared uncertainty all fail closed before
the solver runs.

## Beast clock calibration

The included adapter applies this affine mapping:

```text
timestamp_ns = anchor_time_ns
             + (frame_tick - anchor_tick) * 1,000,000,000 / frequency_hz
```

The tick subtraction is wrap-aware for the 48-bit Beast counter. A receiver
configuration looks like:

```json
{
  "enabled": true,
  "source": "gpsdo-nyc",
  "frequency_hz": 12000000,
  "anchor_tick": 123456,
  "anchor_time_ns": 1714400000123456789,
  "uncertainty_ns": 50,
  "valid_from_ns": 1714400000000000000,
  "valid_until_ns": 1714403600000000000,
  "evidence": {
    "method": "gpsdo-1pps-calibration",
    "file": "clock-evidence/receiver-1.json",
    "sha256": "replace-with-the-file-sha256"
  }
}
```

An anchor is evidence only when it comes from an actual clock synchronization
process, such as a GPS-disciplined receiver or a separately validated timing
service. This repository maps and enforces calibration metadata; it does not
infer a trustworthy clock offset from ordinary network packet arrival.

The strict field-trial bridge additionally requires the clock's declared
validity interval to include launch time. These values are launch controls, not
cryptographic proof that the underlying hardware is synchronized. Preserve the
clock-source logs and measurement method in the field evidence package. Strict
config validation requires each log/report to exist and match its declared
SHA-256 before the bridge starts.

## Diagnostic fallback

When calibration is absent, the Beast adapter emits:

```json
{
  "timestamp_ns": null,
  "clock_synchronized": false,
  "clock_source": "network-arrival",
  "clock_uncertainty_ns": null
}
```

This lets operators inspect the feed while making it impossible for that data
to be mistaken for MLAT-capable timing. The runtime rejects the group.

## Field mapping

- Beast payload bytes -> `message`
- Beast 48-bit counter plus receiver calibration -> `timestamp_ns`
- Adapter wall clock -> diagnostic `timestamp` only when uncalibrated
- Local receiver configuration -> `receiver_id` and clock metadata
- Beast signal byte -> optional `signal_level`

Do not send decoded positions, SBS aircraft-state rows, aggregated track
objects, or multiple frames per JSON line. The unit of input remains one
receiver, one receive time, one raw frame.

## Multi-receiver bridge

Use [`reference/mlat/config/beast-receivers.example.json`](../../../reference/mlat/config/beast-receivers.example.json)
with `tools/mlat/multi_receiver_beast_bridge.py`. Keep its example clocks disabled
until real anchors are supplied. See
[Live Ingest](./LIVE_INGEST.md) for the launch command
and runtime evidence checks.
