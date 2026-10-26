# Security threat model

Reviewed 19 October 2026. Assets: owner authority, authoritative registry state,
feed credentials, timing/identity integrity, stored provenance, API access and
availability. Attackers include malicious registrants, feeds, anonymous API
clients, stale/faulty indexers and compromised dependencies. Operators, approved
bridge executables, database administrators and the configured chain node are
trusted but still require deployment controls.

## Boundaries and evidence

| Threat | Existing or repaired control | Verification / remaining limit |
| --- | --- | --- |
| Unauthorized create/update/transfer/revoke | Type-ID and cell-group rules; input lock signatures; SDK compares signer locks | CKB-VM unauthorized-signature tests; SDK lifecycle tests; no fresh signing performed |
| Duplicate label used as identity | Canonical 32-byte identity; labels are not security keys | Shared conformance vectors, Python and SDK tests |
| Stale indexer retains revoked/spent state | **Repaired:** fresh `get_live_cell` comparison of bytes, lock/type and liveness | New Python/SDK regressions, runtime buffer removal, read-only testnet verification |
| Partial discovery or stalled RPC | Page/cell/response bounds, cursor-cycle rejection; **added total scan deadline** | Timeout and pagination regressions; cached authority not reused on failure |
| Ambiguous JSON, oversized data | Duplicate-key rejection, strict schema, bounded RPC/record/feed/API inputs | Contract conformance; input-security tests; JSON parser has a payload bound, normalization depth bound and recursion handling |
| Feed impersonation or geometry override | Connection-bound/allowed identities; geometry from current registry | Feed identity-binding tests and chain-to-API synthetic integration |
| SSRF or credential forwarding | Exact approved WebSocket URLs, no redirect following, credentials only on primary URL | Existing transport regressions. Approved DNS/host and network egress policy remain operator trust |
| Shell/path injection | Argument-list subprocess execution; fixed proxy origin; parameterized SQL | Source review and transport/API tests. Configured bridge itself is privileged |
| Replay/stale timing or fabricated observations | Integer timing, valid original frame, age/future bounds, duplicate/order rejection, clock qualification | Input/runtime/correlation regressions; per-receiver clock statements still require independent evidence |
| Unauthorized continued streaming | **Repaired:** recheck key, account, plan and entitlement before every update | Four formerly failing revocation/expiry cases now pass; storage failure withholds delivery |
| Streaming state exhaustion | **Added:** 100 aircraft/session, 10,000 tracked subscriptions/process, disconnect cleanup | Bound/cleanup regression; edge connection and message-rate limits still required |
| Credential exposure through diagnostic text/logs | Nested export schema; **removed arbitrary clock-source text**; rejected feed IDs/record parser errors no longer echoed | Formerly failing URL-sentinel tests now pass. Bundle still contains public receiver identifiers and timestamps |
| Mixed/relabelled source data | Database mode binding; per-row provenance; UNKNOWN legacy data | Storage and historical replay tests |
| Failed write reported as successful delivery | Separate solve/store counters; write failure flag; no created-position event on failure | Storage-failure and recovery tests |
| Queue/CPU/disk exhaustion | 1 MiB feed input, 1,024 normalized records, 20,000 buffered signals/keys, bounded queues and reads | Load tests cover a bounded local profile. Disk quotas and live retention remain operational requirements |
| Dependency compromise | Hash-locked Python, npm lockfiles, commit-pinned CI actions, current advisory scans | Runtime Python: zero known advisories; npm: only low-severity wallet-chain advisories; not a proof against unknown flaws |

The configured node remains the chain authority. The CKB RPC definition of a
live cell and the distinction between live/dead/unknown status are documented in
the [upstream RPC reference](https://github.com/nervosnetwork/ckb/tree/develop/rpc).
The installed CCC 1.19.1 implementation was inspected: `getCellLive` invokes a
fresh node request, unlike a general cached cell lookup.

## Confirmed defects fixed in this audit

1. Indexer-only discovery and lifecycle preparation could accept stale state.
   Fresh node checks now reject spent/unknown cells and mismatching content or
   ownership. The node request is outside the per-record parsing exception handler,
   so outages invalidate the entire discovery rather than silently selecting a subset.
2. Many individually bounded requests could keep a scan alive too long. Total
   discovery deadlines now fail closed. An already-running Python thread/SDK HTTP
   request may finish after cancellation; it cannot publish a timed-out snapshot.
3. Field-name allowlisting did not make a feed's arbitrary clock-source text safe
   for diagnostic sharing. That text is omitted from export. Identity rejection
   logs no longer repeat arbitrary feed strings. RPC errors use a fixed message.
4. Socket.IO checked authorization only when joining a room. Revoked/expired
   sessions are now removed before subsequent position delivery. In-memory state
   stores an internal key ID, never a raw API key, and has explicit limits.

## Controls required before exposure

Use an authenticated TLS gateway for any private live data. The public demo API
is intentionally readable without an API key; CORS is not an authentication
mechanism. Keep administrative cleanup disabled unless explicitly needed, use a
separate admin secret, and never put secrets in `NEXT_PUBLIC_*` variables.

Run one API worker until rate limiting and Socket.IO coordination are shared.
The HTTP limiter is process-local and sees the peer address, so behind the Next.js
proxy users can share one bucket. It does not constrain Socket.IO events or the
number of network connections. Add edge limits for both HTTP and WebSockets,
including body size, connection count, message rate, idle timeout and CPU/memory.

Keep diagnostics within the authorized test group. The shareable endpoint omits
feed URLs, wallet material, argv and environment dumps, but receiver identifiers
and arrival times are operational metadata. Raw service logs can contain aircraft
positions, host paths and exception traces; they are not a sanitized diagnostic
bundle. Restrict access and retention. Do not send raw logs to testers by default.

A 30-second discovery deadline is deliberately conservative and may reject very
large registries; capacity planning must measure the intended registry size and
RPC latency. There is no independent chain finality/reorganization policy, no
independent contract audit, no attested physical receiver campaign, and no
validated multi-node deployment. These remain Gate C blockers.

No repository secret values were printed or used. This was source-bound secret
handling review, not a claim that the entire Git history passed a dedicated
credential scanner. CodeQL workflows exist but were not executed locally. Cargo audit is not
installed, so a fresh Rust dependency advisory scan remains NOT RUN.
