---
status: accepted
---

# Use Type-ID-style receiver identities and terminal revocation

Registry V2 identifies a receiver lifecycle by a unique 32-byte type-script
argument derived from the first creation input and output index. The
human-readable Receiver Label remains immutable but is not globally unique;
discovery keys by Receiver Identity. Updates require exactly one input and one
output with a sequence increment, ownership transfer changes only the output
lock, and revocation creates an irreversible tombstone. This rejects the V1
design where empty type arguments and self-declared timestamps allowed identity
collisions and record takeover.

## Consequences

Registry V1 cells cannot be interpreted as V2 identities and require explicit
re-registration. Globally unique human-readable labels would require a separate
namespace allocation mechanism and are intentionally outside this contract.
