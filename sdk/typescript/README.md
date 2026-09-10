# CKB Receiver Registry V2 TypeScript SDK

This package creates, discovers, updates, transfers, and revokes receiver
identities on CKB Pudge testnet. It builds transactions through a CKB-CCC
`Signer`, so the connected wallet reviews and signs every write.

The SDK never accepts a private key or seed phrase. Do not put either one in
source code, environment variables, command arguments, issue reports, or test
fixtures.

## Support boundary

- Network: CKB Pudge testnet only for the documented journey.
- Runtime: Node.js 22.23.1, as pinned in the repository's `.nvmrc`.
- Package status: public-release ready, but not yet published to npm.
- Contract status: testnet-only and not independently audited.
- Dependency status: the current CCC chain has the low-severity upstream
  `elliptic` advisory documented in the repository's `SECURITY.md`.

The bundled `REGISTRY_V2_PUDGE_2026_07_30` deployment is the historical
deployment proven by the repository's signed evidence. It was built from
contract commit `61ab011de58397cb8d6ca3cecb5c659c69e2fc8c`. Its type-hash code
binding allows the implementation cell to be replaced without changing the
receiver type hash, so `RegistryV2Sdk.testnet()` supports discovery but rejects
all writes. Do not bypass that guard.

The current contract source is a stricter, undeployed review candidate. The
create-to-revoke journey requires that binary to be independently reviewed and
deployed on Pudge with an immutable `data1` code hash. The SDK then needs only
the deployment's three public manifest values: binary code hash, deployment
transaction hash, and output index.

## 1. Install

Install Node.js 22.23.1 with your normal Node version manager or installer.
Then clone this repository and pin the commit you reviewed. The SDK path can be
absolute or relative to the application. If `nvm` is already installed, the
repository's `.nvmrc` selects the exact version:

```bash
git clone https://github.com/Jeremicarose/AIRCRAFT-MALT.git
cd AIRCRAFT-MALT
git checkout YOUR_REVIEWED_COMMIT
nvm install
nvm use
```

After the first public release, install the SDK and CCC wallet connector from
npm:

```bash
npm install @aircraft-malt/registry-v2@0.1.0 \
  @ckb-ccc/connector-react@1.1.9
```

Until that release exists, install the reviewed repository checkout directly.
For a React application using the CCC wallet dialog:

```bash
npm install /absolute/path/to/AIRCRAFT-MALT/sdk/typescript \
  @ckb-ccc/connector-react@1.1.9
```

For a Node.js read-only application that does not need a wallet dialog:

```bash
npm install /absolute/path/to/AIRCRAFT-MALT/sdk/typescript \
  @ckb-ccc/core@1.19.1
```

The explicit CCC dependency matters for local linked packages. Installing only
the SDK does not make a direct `@ckb-ccc/core` import available to the
application.

To verify the SDK inside this repository:

```bash
cd sdk/typescript
npm ci
npm test
```

The reference application at `/app/registry` exposes public historical
discovery by default. Start it from `reference/mlat/frontend` with `npm run dev`
and open the route. Owner actions remain disabled until the application is
configured with a reviewed immutable deployment. Once configured, it uses the
SDK for lifecycle rules and waits for public-indexer visibility before it shows
a write as complete.

## 2. Configure a testnet signer

Wrap the React application in the CCC provider. The provider below fixes the
wallet dialog and client to Pudge testnet:

```tsx
"use client";

import { ccc } from "@ckb-ccc/connector-react";
import type { ReactNode } from "react";

const testnetClient = new ccc.ClientPublicTestnet();

export function CkbProvider({ children }: { children: ReactNode }) {
  return (
    <ccc.Provider
      name="CKB Receiver Registry"
      defaultClient={testnetClient}
    >
      {children}
    </ccc.Provider>
  );
}
```

Inside a client component, open the wallet dialog and use its signer:

```tsx
import {
  RegistryV2Sdk,
  type WritableRegistryV2TestnetDeployment,
} from "@aircraft-malt/registry-v2";
import { ccc } from "@ckb-ccc/connector-react";
import { useMemo } from "react";

const { client, signerInfo, open } = ccc.useCcc();
const reviewedDeployment = {
  contractCodeHash: process.env.NEXT_PUBLIC_REGISTRY_CODE_HASH!,
  contractTransactionHash: process.env.NEXT_PUBLIC_REGISTRY_CONTRACT_TX_HASH!,
  contractIndex: Number(process.env.NEXT_PUBLIC_REGISTRY_CONTRACT_INDEX!),
} satisfies WritableRegistryV2TestnetDeployment;
const registry = useMemo(
  () => RegistryV2Sdk.writableTestnet(client, reviewedDeployment),
  [client],
);
const signer = signerInfo?.signer;

// Call open() from a user-initiated button click when signer is undefined.
```

Copy those three values exactly from the reviewed deployment manifest. They are
public identifiers, not wallet secrets. The factory derives `hashType: data1`,
the contract cell dependency, and the exact script configuration. It rejects
missing or malformed hashes, an invalid output index, and a mainnet client.
Lifecycle methods also reject a signer connected to a different CKB network.
The first write verifies that the dependency is still live and hashes its cell
data to confirm that it contains the configured binary. Applications can run
the same check earlier with `await registry.verifyWritableDeployment()`.

For historical read-only discovery, use `RegistryV2Sdk.testnet(client)` without
a deployment. Any lifecycle method on that instance fails before asking the
wallet to sign.

The owner wallet needs a plain testnet CKB cell for storage capacity and fees.
Fund the public testnet address shown by the wallet, then wait for that funding
transaction to appear in the wallet. No `ckb-cli` step is needed.

Ownership transfer needs two wallet users:

1. The recipient shares only their public `ckt...` address.
2. The current owner signs the transfer.
3. The recipient connects their own wallet before revoking or updating later.

Never ask the recipient for a private key or seed phrase.

## 3. Create and submit

The SDK fills the schema version, initial sequence, timestamp, Type ID, output
capacity, dependencies, and fee inputs. `registry` below must be the writable
instance configured in the previous section:

```ts
if (!signer) throw new Error("Connect a Pudge testnet wallet first");

const created = await registry.create(signer, {
  receiver_id: "RECV_NAIROBI_001",
  latitude: -1.286389,
  longitude: 36.817223,
  altitude: 1795,
  status: "online",
  capabilities: ["mode-s", "mlat"],
});

const createdReceiver = await registry.waitForIndexedTransaction(
  created.receiver_identity,
  created.transactionHash,
);
```

`create()` prepares the transaction to the wallet and returns after submission.
`waitForIndexedTransaction()` then waits for CKB commitment and for the public
indexer to expose that exact output. Use it before the next lifecycle action.

## 4. Discover

Find the identity created above without scanning application state:

```ts
const discovered = await registry.discovery.findByIdentity(
  created.receiver_identity,
);
if (!discovered) throw new Error("Created receiver is not active");
```

To list the public active directory:

```ts
const directory = await registry.discovery.discover();
if (directory.failures.length > 0) {
  throw new Error(directory.failures.map((failure) => failure.message).join("; "));
}
```

Normal discovery returns only records with `status: "online"`.
`includeInactive: true` adds offline and degraded records.
`includeRevoked: true` adds revocation tombstones.

## 5. Update allowed metadata

Pass only the fields that need to change. The SDK preserves the immutable
Receiver Identity and Receiver Label, increments `sequence` by one, and chooses
a non-decreasing timestamp:

```ts
const updateHash = await registry.update(signer, created.receiver_identity, {
  altitude: 1801,
  metadata_hash: "0x" + "ab".repeat(32),
});

const updatedReceiver = await registry.waitForIndexedTransaction(
  created.receiver_identity,
  updateHash,
);
```

Allowed update fields are `latitude`, `longitude`, `altitude`, `status`,
`capabilities`, `stream_endpoint`, `stream_protocol`, `stream_format`,
and `metadata_hash`. The metadata hash is a 32-byte commitment to off-chain
metadata; arbitrary metadata is not stored in the Registry cell.

`receiver_id`, `schema_version`, and `sequence` are lifecycle fields. Normal
updates must not change them. Omit unused stream fields instead of passing empty
strings.

## 6. Transfer ownership

Use the recipient's public Pudge address. In the example below,
`recipientTestnetAddress` is the public `ckt...` string collected from the
application's recipient-address field. The SDK converts it to the correct CKB
lock script and rejects mainnet or malformed addresses:

```ts
const transferHash = await registry.transfer(
  signer,
  created.receiver_identity,
  recipientTestnetAddress,
);

const transferredReceiver = await registry.waitForIndexedTransaction(
  created.receiver_identity,
  transferHash,
);
```

The current owner signs this transaction. After it commits, that signer is no
longer authorized to change the identity.

## 7. Discover the transferred identity

```ts
const transferred = await registry.discovery.findByIdentity(
  created.receiver_identity,
  { includeInactive: true },
);
if (!transferred) throw new Error("Transferred identity was not discovered");

console.log(transferred.provenance.ownerLock);
```

The Receiver Identity and Receiver Label remain unchanged. The owner lock in
`provenance` changes to the recipient.

## 8. Revoke as the new owner

Disconnect the previous owner and connect the recipient's Pudge wallet. Then use
the recipient signer:

```ts
const recipientSigner = signerInfo?.signer;
if (!recipientSigner) throw new Error("Connect the recipient Pudge wallet");

const revokeHash = await registry.revoke(
  recipientSigner,
  created.receiver_identity,
);

const tombstone = await registry.waitForIndexedTransaction(
  created.receiver_identity,
  revokeHash,
);
if (tombstone.record.status !== "revoked") {
  throw new Error("Indexer did not return the revocation tombstone");
}
```

Revocation is permanent. The tombstone cannot be updated, deleted, or restored.

## 9. Verify it is no longer active

Check both sides of the rule: normal discovery must hide the identity, while an
explicit revoked lookup must still find its tombstone:

```ts
const active = await registry.discovery.findByIdentity(
  created.receiver_identity,
);
const revoked = await registry.discovery.findByIdentity(
  created.receiver_identity,
  { includeRevoked: true },
);

if (active !== undefined) throw new Error("Revoked identity is still active");
if (revoked?.record.status !== "revoked") {
  throw new Error("Revocation tombstone is missing");
}
```

## Common errors

| Error text | Meaning | Action |
|---|---|---|
| `historical and read-only` | The SDK is using the mutable July deployment or another non-`data1` deployment. | Stop. Configure a reviewed immutable Pudge deployment; do not bypass the guard. |
| `contract dependency is not a live Pudge cell` | The configured deployment outpoint is wrong or has been spent. | Compare all three values with the reviewed deployment manifest. |
| `deployment code hash mismatch` | The outpoint exists, but its binary does not match the configured `data1` hash. | Stop before signing and correct the deployment configuration. |
| `no plain CKB testnet capacity cell` | The wallet has no spendable plain testnet cell for storage and fees. | Fund the wallet's public Pudge address and wait for indexing. |
| `Connected signer uses ... but the Registry client uses ...` | The wallet and client are on different networks. | Switch both to Pudge testnet. |
| `Recipient must be a valid ckt address` | The transfer address is malformed or belongs to another network. | Ask for the recipient's public Pudge address. |
| `does not own the current Registry V2 cell` | The connected wallet is not the current owner. | Connect the owner wallet. After transfer, connect the recipient. |
| `No live Registry V2 cell found` | The identity is wrong, or the previous transaction is not indexed yet. | Confirm the identity and call `waitForIndexedTransaction()` after writes. |
| `Duplicate live Registry V2 cells` | The indexer returned an invalid ambiguous state. | Stop and investigate; the SDK will not choose one cell. |
| `committed but was not indexed before timeout` | CKB accepted the transaction, but the public indexer is lagging. | Keep the transaction hash, check the explorer, and retry the lookup. Do not resubmit immediately. |

Wallet rejection and RPC transport errors come from the connected CCC wallet or
public CKB service. Preserve the transaction hash when one exists.

## Prepare without submitting

Every write method has a `prepare...` counterpart. These methods return a CCC
transaction without asking the wallet to sign or broadcasting it:

- `prepareCreate`
- `prepareUpdate`
- `prepareTransfer`
- `prepareRevoke`

This is useful for a transaction review screen. Application developers do not
need to manually construct the Registry type script, derive the Type ID, balance
capacity, add dependencies, or invoke `ckb-cli`.

The sequential SDK journey is regression-tested in
`test/lifecycle.test.ts`. The historical signed testnet lifecycle is stored in
`../../evidence/registry-v2-testnet-2026-07-30-final/`.
