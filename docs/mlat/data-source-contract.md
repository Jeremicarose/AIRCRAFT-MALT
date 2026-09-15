# Production MLAT Data-Source Contract

Audit date: 2026-09-14

This document describes the contract enforced by the current repository. It is
not a proposed format and it does not relax any production validation.

## End-to-End Path

```text
CKB Registry V2 discovery
  -> active receiver cache and coordinates
live JSON/JSONL or Beast-derived record
  -> feed normalization
  -> RawSignal
  -> exact-frame correlation
  -> clock qualification
  -> SignalObservation
  -> RobustMLATSolver
  -> database/API/frontend
```

The feed alone is not the complete input. Receiver coordinates, lifecycle
state, capabilities, and the canonical runtime identity come from Registry V2.
The feed observation must bind to that discovered identity.

## Field Contract

| Field | Source | Type | Validation | Where consumed | Mandatory? | Failure when missing or invalid |
|---|---|---|---|---|---|---|
| `receiver_id` on an observation | Feed record, normally bound to a discovered receiver connection | `str` | A `0x` identity must be a normalized 32-byte hex value. A claimed ID that differs from the connection-bound ID, or is not in the allowed set, is dropped. Receiver IDs in one solve must be unique. | `feed_transports.py:108-118,167-201`; `base.py:99-125`; `correlator.py:232-234`; `robust.py:201-204` | Yes | The normalizer returns no record; an unknown or lifecycle-excluded ID is ignored; a duplicate-ID solve is rejected. |
| `receiver_identity` | CKB Type ID script arguments, not receiver-supplied observation data | `str`, `0x` plus 64 hex characters | Normalized by `normalize_receiver_identity`. Registry-backed `ReceiverInfo` cannot exist without it. It becomes `ReceiverInfo.runtime_id`, which is the observation routing ID. | `record.py:47-51`; `discovery.py:47-58,300-307,345-359` | Yes for a Registry-backed production receiver | The Registry cell is rejected or the receiver cannot enter the active cache. A source-local serial is not a substitute. |
| `message` | Live observation | `str` | The normalizer accepts `message`, nested `message.hex/raw/frame`, `hex`, `raw`, `frame`, or `payload`; it drops an empty value. The correlator uses exact string equality. | `feed_transports.py:120-135,162`; `correlator.py:144-147`; `runtime.py:466,478-481` | Yes | The record is dropped before correlation. Different representations of the same frame do not correlate. |
| Original Mode-S frame semantics | Data provider/receiver | Complete frame represented by the `message` string | The code does **not** currently validate hex syntax, frame length, parity, or CRC. Nevertheless, genuine production correlation requires the original common transmission. A dataset row ID, aircraft ID, or decoded state is not that transmission. | Exact `message` grouping in `correlator.py:144-147`; stored aircraft key currently uses `message[2:8]` in `runtime.py:478-481` | Yes for a defensible production run | A missing frame is dropped. A substituted group ID could make code run but would bypass validation of actual frame correlation and is therefore not acceptable evidence. |
| `timestamp_ns` | Receiver arrival timestamp or a documented conversion from a receiver hardware counter | Positive integer nanoseconds | JSON ingest accepts only a positive integer. Production clock qualification requires it. The solver requires all observations to use it or all to use legacy relative floats; it subtracts integers before converting to seconds. | `feed_transports.py:137-150,204-211`; `runtime.py:348-355`; `robust.py:162-190` | Yes in production | A group fails the production clock gate. Mixed precision or epoch-float-only observations fail solver timing validation. |
| `timestamp` | Derived as `timestamp_ns / 1e9`; otherwise parsed from feed time or local arrival time | `float`, seconds | There is no strict input range at normalization. The correlator orders/buffers on it and the solver rejects observation spans over 100 ms. Production should derive it from the qualified integer timestamp. | `feed_transports.py:138-147,224-230`; `base.py:103-123`; `correlator.py:67-85`; `robust.py:205-210` | Yes in the models; derived in a compliant feed | If both source time forms are absent, ingest inserts local time, but `timestamp_ns` remains absent and the production clock gate later rejects the group. |
| `clock_synchronized` | Feed or Beast clock normalization | `bool` | JSON normalization sets it true only when `timestamp_ns` exists and the input value is exactly `true`. Runtime requires true for every signal in a group. | `feed_transports.py:148-150`; `runtime.py:348-355,445-452` | Yes in production | The entire correlated group is rejected before the solver. |
| `clock_source` | Provider documentation; for Beast, receiver clock configuration | `str` | Runtime rejects empty, `unknown`, and `network-arrival`. The Beast field-trial validator also rejects placeholder names. | `feed_transports.py:158`; `runtime.py:348-355`; `tools/mlat/receiver_config.py:82-84` | Yes in production | The entire correlated group is clock-rejected. |
| `clock_uncertainty_ns` | Provider measurement/attestation or validated receiver clock configuration | finite non-negative `float` | Runtime requires a value at or below `max_clock_uncertainty_ns`, currently 100 ns. Beast launch validation applies the same maximum. | `feed_transports.py:159-161,214-221`; `runtime.py:84,103,348-355`; `tools/mlat/receiver_config.py:98-104` | Yes in production | Missing, non-finite, negative, or over-limit values make the group fail clock qualification. |
| Clock counter frequency and anchor | Beast receiver configuration | Positive `frequency_hz`, 48-bit `anchor_tick`, positive `anchor_time_ns` | Used to convert the Beast 48-bit counter without passing through a coarse floating-point epoch. | `beast_tcp_adapter.py:95-120`; `tools/mlat/receiver_config.py:86-96` | Required only when adapting Beast counters into qualified absolute nanoseconds | Without a valid calibration, Beast data is emitted as unsynchronized `network-arrival` timing and production rejects it. |
| Clock validity window and evidence | Beast receiver configuration | Positive integer range plus evidence method/file/SHA-256 | Production field-trial configuration requires the calibration to cover launch time and requires a present, non-empty, hash-verified evidence file. | `tools/mlat/receiver_config.py:119-155`; `beast_tcp_adapter.py:122-140` | Required by the production-ready multi-receiver Beast bridge | Configuration loading stops before any receiver connection is opened. |
| Receiver latitude | Registry V2 record | finite number, decimal degrees | `-90 <= latitude <= 90`. Discovery also checks the bounds before activation. | `record.py:190-203`; `discovery.py:348-353,441-448`; `runtime.py:261-267`; `robust.py:106-110` | Yes | Invalid records are rejected or skipped. Without a cached position, no solver observation is built. |
| Receiver longitude | Registry V2 record | finite number, decimal degrees | `-180 <= longitude <= 180`. | `record.py:190-203`; `discovery.py:348-353,449-455`; `runtime.py:261-267`; `robust.py:106-110` | Yes | Invalid records are rejected or skipped. Without a cached position, no solver observation is built. |
| Receiver altitude | Registry V2 record | finite number, metres | Registry schema accepts `-500 <= altitude <= 20,000`. It is converted with latitude/longitude to Earth-centred coordinates by the solver. | `record.py:190-203`; `discovery.py:348-353`; `runtime.py:261-267`; `robust.py:106-110` | Yes | Invalid Registry records are rejected. Missing geometry prevents observation construction. |
| Receiver `status` | Registry V2 lifecycle record | `online`, `offline`, `degraded`, or `revoked` | Discovery excludes revoked receivers and, by default, any status other than online. The MLAT client selects only online receivers. | `record.py:205-211`; `discovery.py:393-403`; `client.py:129-139` | Yes | Receiver is absent from the active cache; later observations under that ID are ignored. |
| Receiver `capabilities` | Registry V2 lifecycle record | List of 1-8 normalized strings | Registry records must include `mode-s`; discovery checks it; MLAT selection additionally requires `mlat`. | `record.py:212-222`; `discovery.py:405-412`; `client.py:129-139` | Yes | Record creation fails without `mode-s`; a receiver without `mode-s` or `mlat` does not participate. |
| `signal_strength` | Receiver/feed | optional number | Present in `RawSignal`, but current generic normalizer does not forward an RSSI field and runtime sets zero in `handle_incoming_signal`. It is not used by the solver. | `correlator.py:14-25`; `base.py:103-112` | No | No MLAT failure. |
| Ground-truth aircraft position | Independent truth source or ADS-B position for a controlled benchmark | Not part of production observation | Used only to score a validation result. It must not be used to create arrival times, receiver metadata, frame identity, or a solution being scored. | Not consumed by production pipeline | No for solving; required to measure accuracy | Positions may still be computed, but no accuracy claim can be made. |

Paths in the table are relative to `src/mlat_reference`, `src/ckb_registry`, or
the repository root as indicated by the filename.

## Group-Level Requirements

One individually valid observation is not enough. A production solve also
requires all of the following:

- At least four distinct active receiver identities. The production runtime
  constructs both the correlator and solver with `min_receivers=4`
  (`runtime.py:86-91`).
- The exact same `message` string at those receivers. Correlation does not
  group by aircraft ID or by nearby time alone (`correlator.py:144-147`).
- A maximum 5 ms correlation span in the production runtime
  (`runtime.py:86-90`). The solver has a looser 100 ms safety check, but that
  does not replace correlation.
- Qualified clock metadata on every contributing signal. One unqualified
  signal rejects the whole group (`runtime.py:445-452`).
- Unique receiver IDs. Duplicate observations from one receiver do not count
  as additional geometry (`correlator.py:232-234`; `robust.py:201-204`).

## Beast Feed Meaning

The existing Beast bridge preserves the raw Mode-S bytes and the 48-bit Beast
counter. Beast itself does not provide a CKB identity or prove a common clock.
The bridge therefore uses explicit receiver configuration for the Registry
identity and clock calibration.

If clock calibration is absent, the bridge deliberately emits:

```json
{
  "timestamp_ns": null,
  "clock_synchronized": false,
  "clock_source": "network-arrival",
  "clock_uncertainty_ns": null
}
```

That behavior is enforced in `tools/mlat/beast_tcp_adapter.py:226-260`. It
prevents network arrival time from being presented as receiver arrival time.

## What A Source Must Prove

A candidate source satisfies this contract only when it can provide the
original frame and receiver-level arrival record, preserve a stable receiver
relationship, provide usable geometry, and document how the receiver clocks
share a comparable timebase within the 100 ns gate. Nanosecond *units* alone do
not prove nanosecond *accuracy*.

Registry participation is a separate proof. The CKB record proves the on-chain
identity, current owner lock, metadata, and lifecycle state represented by the
cell. It does not prove physical receiver existence, physical location, clock
accuracy, feed honesty, or observation truth.
