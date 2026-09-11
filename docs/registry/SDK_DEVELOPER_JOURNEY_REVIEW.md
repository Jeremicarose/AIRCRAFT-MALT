# Registry V2 SDK Developer Journey Review

Review date: 2026-09-09

## Scope and safety boundary

This review started from a temporary empty npm project and used only repository
documentation to attempt this path:

```text
install -> configure signer -> create -> discover -> update -> transfer
        -> discover transferred identity -> revoke -> verify inactive
```

The review used CKB Pudge testnet only. It did not request, read, store, or expose
a private key or seed phrase.

This SDK review did not submit a signed write lifecycle. That still requires a
funded, user-controlled testnet wallet and explicit approvals in that wallet.
The historical mutable type-hash deployment is discovery-only. Since the
review, the current contract has been deployed immutably with `data1` and
exercised through a separate CKB CLI-signed lifecycle. That proves the contract
path, but does not turn this review into an SDK-driven transaction run.

## Problems found and resolved

| Journey point | What happened on first use | Why it matters | Resolution |
|---|---|---|---|
| Install | The guide showed how to run tests inside the SDK, but not how to install it in another project. | A developer could not complete the first step from the published instructions. | Added exact local-path installation commands for React and Node.js consumers. |
| Install | The required Node version was only in package metadata. Node 20 installed with an engine warning. | The warning looks like a package defect on a clean machine. | Documented Node 22.23.1 and the repository `.nvmrc` before installation. |
| Install | Installing only the linked SDK made the SDK import work, but the guide's direct `@ckb-ccc/core` import failed. | npm does not promise that an application can import a transitive dependency directly. | Documented the required direct CCC dependency for each application type. |
| Install | The package was private and is not yet published to npm. | `npm install @aircraft-malt/registry-v2` cannot work until the first release. | Removed the publication block, added public package metadata and a protected provenance-backed release workflow, documented the one-time npm scope approval, and retained a commit-pinned local install before release. |
| Install | npm reported the known low-severity `elliptic` advisory through the CCC dependency chain. | A developer could mistake an upstream advisory for an unreviewed local dependency choice. | The risk and rejected breaking downgrade are documented in `SECURITY.md`; CI fails on moderate-or-higher findings and the low exception must be rechecked on dependency updates. |
| Configure signer | The example used an undefined `walletSigner`. | A developer had to leave the guide and inspect the frontend or CCC examples. | Added a complete `@ckb-ccc/connector-react` provider and `useCcc()` signer setup. |
| Configure signer | The guide did not prove the client and wallet were on the same network. | A mainnet signer could be connected to a testnet deployment configuration. | Added `RegistryV2Sdk.testnet()` and lifecycle network checks. |
| Configure signer | Funding requirements were not explained. | Creation needs storage capacity and a fee-paying plain CKB cell. | Added the public-address funding prerequisite and a clear no-capacity error. |
| Deployment | Applications had to copy a code hash and contract outpoint by hand. One frontend copy contained a different transaction hash. | A wrong dependency makes every prepared lifecycle transaction invalid. | Added one exported deployment constant tied to the evidence manifest and a test that compares every value. |
| Deployment | The docs did not clearly separate the historical deployed binary from stricter current source. | A developer could assume the current source produced the bundled testnet code hash. | Added an explicit support boundary in the SDK and integration guides. |
| Deployment | The historical receiver type hash identifies a replaceable contract cell by its type script. | The code could change without changing the receiver type hash, so new writes cannot treat that deployment as immutable. | Marked the deployment discovery-only, made every lifecycle method require `data1`, and added `writableTestnet()` so applications provide only three public manifest values. Before signing, the SDK confirms the dependency is live and its binary hashes to the configured code hash. |
| Create | Callers had to provide `schema_version`, `sequence`, and `updated_at`. | These are protocol lifecycle fields, not normal registration choices. | The SDK now supplies version 2, sequence 0, and the timestamp by default. |
| Submit | The example discovered immediately after `sendTransaction`. | Transaction submission does not mean the block and public indexer are ready. | Added `waitForIndexedTransaction()`, which waits for commitment and the exact indexed output. |
| Discover | The example used the first item in the whole directory. | That can select another developer's receiver. | Added exact `findByIdentity()` lookup and documented directory failures. |
| Update | The caller copied the whole record and manually incremented sequence and time. | This exposes contract rules and makes off-by-one or stale-state errors likely. | Updates now accept a metadata patch and derive the next lifecycle fields. |
| Update | “Allowed metadata” was not listed. | Developers could try to change the immutable label or put arbitrary metadata on chain. | Documented every mutable field and the role of `metadata_hash`. |
| Transfer | The guide required an undefined `recipientLock`. | Constructing a CKB lock script requires knowledge an application user should not need. | Transfer now accepts the recipient's public `ckt...` address and validates its network. |
| Transfer | The guide did not explain who signs after ownership changes. | The old owner cannot authorize later updates or revocation. | Documented the owner-signs-transfer, recipient-signs-next-action handoff. |
| Discover transfer | There was no confirmation or exact lookup step after transfer. | The application could show stale ownership while the indexer catches up. | Added the confirmation helper and a transferred-identity lookup using provenance. |
| Revoke | The example required a manual timestamp and an undefined `currentOwnerSigner`. | This repeats protocol work and hides the required signer handoff. | Revocation now derives time; the guide reconnects the recipient signer explicitly. |
| Verify revoked | The guide said how to include revoked records, but did not define a complete verification. | “Not listed” alone could also mean an indexer failure or wrong identity. | The final check requires normal lookup to return nothing and revoked lookup to return a tombstone. |
| Errors | Indexer delay, wrong network, bad recipient address, and missing capacity were not translated into actions. | Developers could resubmit, switch tools, or inspect source unnecessarily. | Added contextual SDK messages and a troubleshooting table. |
| Live verifier | A TLS certificate failure produced a long Python traceback. | The developer had to decode Python networking internals to learn that the RPC was never reached. | The verifier now fails closed with a short RPC and certificate explanation, covered by a regression test. |
| Low-level tooling | The integration guide placed manual Python transaction assembly near the main workflow. | SDK users could conclude that `ckb-cli` or hand-built transactions were still required. | Reclassified those commands as contract-maintainer tooling and made the SDK path primary. |
| Tests | Lifecycle builders were tested separately against one static cell, not as one changing owner/state journey. | Sequence, signer handoff, confirmation, and final filtering could regress independently. | Added a stateful create-to-revoke test that follows the documented journey in order. |
| Reference app | The wallet screen manually rebuilt records, lifecycle counters, timestamps, and recipient lock scripts. | The real browser path could drift away from the SDK journey even while the SDK tests passed. | The screen now passes create/update fields and the public recipient address to the SDK, waits for the exact indexed transaction before refreshing, uses the current immutable deployment, and rejects the historical mutable deployment. |

## Verification evidence

- A clean local-path install succeeded after building the package.
- The first install exposed the undocumented Node engine warning and missing
  direct CCC import described above.
- The historical evidence verifier passed all saved create, update, transfer,
  revoke, ownership, sequence, and inactive-discovery checks.
- A live SDK query against the public Pudge indexer found Receiver Identity
  `0xcca658ee811707def01d466b16b9b3ee133c3f6952388c78a5f90a5c273749e8`
  only when revoked records were requested. It returned `status: revoked` and
  `sequence: 3`; normal active discovery did not return it.
- The original Python live-verifier attempt exposed a local CA-store problem.
  The corrected command later passed 100 checks against the public RPC with TLS
  verification enabled; certificate verification was not disabled.

The deterministic SDK, Python, Rust, documentation, and clean-package checks are
listed in the final review result and should remain CI requirements.
