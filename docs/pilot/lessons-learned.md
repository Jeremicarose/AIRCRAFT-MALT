# Lessons Learned

These are pre-pilot engineering findings. They are not participant feedback.

## Confirmed

1. The historical Pudge deployment cannot support the planned write pilot. It
   uses `hash_type=type`, which lets the contract code cell change without
   changing the Registry script hash. The SDK and UI now treat it as read-only,
   and strict MLAT mode rejects it.
2. A successful periodic Registry refresh is enough to apply revocation,
   transfer, metadata, and membership changes without restarting MLAT. A failed
   refresh previously left old Registry receivers active. The runtime now
   removes them until complete discovery recovers.
3. Payload identity validation is insufficient when one WebSocket connection is
   allowed to represent several receivers. WebSocket configuration now requires
   one connection per receiver identity.
4. The Rust, Python, and TypeScript implementations agree on the current schema:
   57 shared cases produce 171 passing assertions.
5. Historical lifecycle evidence is internally consistent and independently
   recalculated by the offline verifier. It proves a technical lifecycle, not a
   live pilot or physical receiver truth.

## Unknown until external sessions

- Whether operators experience a serious cross-network identity problem.
- Whether public owner locks and lifecycle history are more useful than a
  coordinator-managed database.
- Whether MLAT makes the Registry value easier to understand.
- Whether wallet and cell-capacity costs are acceptable.
- Which fields and integration surfaces real networks need.
- Whether anyone will take a concrete follow-up action.

Update this document after each completed participant record. Label every lesson
as confirmed, contradicted, or still uncertain, and cite the participant IDs
that support it.
