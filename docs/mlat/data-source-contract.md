# MLAT observation contract

**VALIDATED in automated tests:** live input parsing, identity binding, bounded
buffers, clock gates, correlation and storage. **NOT YET VALIDATED:** physical
receiver truth and a synchronized field window.

```json
{
  "receiver_id": "0x<64 hexadecimal digits from the discovered Registry identity>",
  "timestamp_ns": "1791450000123456789",
  "message": "8D4840D6202CC371C32CE0576098",
  "clock_synchronized": true,
  "clock_source": "gps-disciplined-beast",
  "clock_uncertainty_ns": 50
}
```

The example time is illustrative; live ingestion checks current time. Decimal
timestamp strings preserve nanoseconds in JavaScript clients. Never send
nanoseconds as a floating-point number.

| Field | Enforced rule |
|---|---|
| Receiver ID | Must match the connection identity or operator-configured bridge pool. CKB identity is a normalized 32-byte Type ID, not a label. Unknown/revoked identities never reach correlation. |
| Arrival time | Positive u64 integer or canonical decimal string. Fractional, Boolean, oversized and non-finite values are rejected. Missing time is never replaced with current wall time. |
| Live time window | Default 120 seconds old to 5 seconds ahead. Timestamp fields must agree within one microsecond when both reach the runtime. Duplicate/non-increasing qualified receiver timestamps are rejected within a session. |
| Message | Complete 14- or 28-hex-character Mode-S frame with matching format length. DF17/DF18 CRC must pass. Other formats use overlaid parity and are not independently parity-verified here. |
| Clock synchronized | Boolean true and an integer timestamp are required for qualification. |
| Clock source | Bounded nonempty name other than unknown/network-arrival. Synthetic/replay sources cannot qualify live operation. A name is not independent attestation. |
| Clock uncertainty | Finite non-negative number at or below MAX_CLOCK_UNCERTAINTY_NS, default 100 ns. Missing/excessive uncertainty quarantines observations. |
| Receiver geometry | Comes from validated receiver configuration/Registry discovery, never observation payloads. |

JSON payloads are limited to 1 MiB, batches to 1,024 records and normalization
nesting to eight levels. Duplicate keys and non-finite JSON constants are rejected.

## Dispositions

- **Rejected:** malformed identity/frame/time/clock metadata, forbidden timestamp
  order, or unknown receiver. Does not update receiver freshness.
- **Quarantined:** valid frame and operational arrival context, but insufficient
  clock evidence. May show an online feed; never enters solver correlation.
- **Accepted:** clock-qualified observation admitted to correlation.
- **Correlated:** distinct receivers observed the same frame within the time window.
- **Solver-qualified:** the group passes current geometry and clock gates.
- **Contributing:** observations produced a position that was successfully stored.

Registry lifecycle state, operational freshness and MLAT qualification are separate.
A registered online receiver can remain UNQUALIFIED. Qualification expires with
freshness and resets on owner/geometry/sequence changes. Buffered observations
do not inherit a new owner's authority.

## Transport trust and bounds

Registry endpoints are untrusted metadata. Operators approve exact WebSocket URLs
using FOURDSKY_ALLOWED_ENDPOINTS; FOURDSKY_ENDPOINT is also allowed. Redirects are
forbidden. Auth headers and subscription data go only to FOURDSKY_ENDPOINT. For
independently authenticated feeds, configure a local bridge that binds each feed
to its receiver identity. Explicit broken live configuration never selects simulation.

Command adapters use argument lists without a shell. They are privileged local
operator configuration, never commands obtained from Registry records. Arbitrary
stderr and command arguments are not logged. Shutdown terminates, then kills a
child that fails to exit within three seconds.

Correlation retains at most 20,000 signals and 20,000 processed keys. Exact duplicate
observations are deduplicated; conflicting arrival claims reject the group.
Completed groups are consumed together so partial expiry cannot create another
solve. Overload drops are counted.

## Historical and synthetic sources

Synthetic feeds persist SYNTHETIC. Historical compact replay persists
HISTORICAL_REPLAY in a separate database and retains original relative timestamps.
The compact source lacks raw frames and clock uncertainty: grouping is
PUBLISHED_GROUP and eligibility is BENCHMARK_ONLY. It never passes the live input
qualification gate. See [historical replay](HISTORICAL_REPLAY.md).

CKB verifies Registry state, authorization and lifecycle. It does not verify
hardware existence, coordinates, honesty, clock accuracy or observations.
External timing evidence and field validation remain necessary for live accuracy claims.
