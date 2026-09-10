# Product

## Register

product

## Users

The primary users are independently operating ADS-B / Mode S receiver owners and
the coordinators of networks that consume those receivers. A receiver owner needs
to create one stable receiver identity, update its operational metadata, transfer
it to another owner, or revoke it. A coordinator needs to discover the current
directory, inspect ownership and lifecycle evidence, and export records for use
by an MLAT or another receiver network.

Users may arrive with no knowledge of CKB cells, Type IDs, lock scripts, or
blockchain transaction states. The product must explain those ideas only when
they affect a decision.

## Product Purpose

CKB Registry V2 lets a receiver keep one stable identity while its metadata,
status, or owner changes. CKB verifies the ordered lifecycle and the current
owner's authorization without requiring one network administrator to control
every change. The pilot exists to test whether independently owned receiver
networks find that shared control useful enough to justify using a blockchain
instead of a spreadsheet or central database.

The pilot application starts in the Receiver directory so owners and
coordinators meet the primary product first. Success means a first-time user can
discover a receiver by its stable CKB identity, inspect its owner and lifecycle,
export the current directory, connect a testnet wallet, complete an authorized
action, and verify the transaction. The MLAT area then demonstrates how one
receiver network can consume the same identities.

The application must distinguish live Registry V2 discovery, saved testnet
evidence, and synthetic MLAT replay data. It must not imply that CKB proves a
receiver's physical location, clock quality, hardware identity, or stream
honesty. Coordinates are public registry metadata and remain visible in
historical transactions, so every write flow must explain the privacy impact.

## Brand Personality

Precise, calm, and operational. The product should communicate the confidence
of a professional aviation or vehicle operations console while remaining clear
to a first-time technical user.

## Anti-references

Do not resemble a speculative blockchain dashboard, a collection of unrelated
analytics pages, or a marketing site disguised as an application. Avoid neon
crypto visuals, decorative data, unexplained hashes, fake wallet actions,
gratuitous animation, excessive cards, and mock data presented as live data.

## Design Principles

1. Start with the Receiver directory during the pilot: make stable identity,
   ownership, lifecycle, and coordinator export the clearest first actions.
2. Preserve investigation context: one selected receiver controls the map,
   inspector, lifecycle, ownership, metadata, and evidence views.
3. Separate owner and coordinator jobs: wallet-owned receivers and lifecycle
   actions belong together; discovery and export must work without a wallet.
4. Make provenance explicit: label testnet, replay, saved evidence, unavailable,
   and live states wherever they affect interpretation.
5. Explain state before implementation detail: show what happened and what the
   user can do next, with CKB-specific details available progressively.
6. Never imply functionality: an unavailable action must say why it is
   unavailable and what prerequisite is missing.
7. Keep Registry and MLAT visibly connected. MLAT is one practical reference
   consumer; Registry identity and lifecycle remain the primary product.

## Accessibility & Inclusion

Target WCAG 2.2 AA. All core workflows must support keyboard navigation,
visible focus, semantic labels, sufficient contrast, non-color status cues, and
reduced motion. Layouts must remain usable on touch devices and at 200 percent
zoom. Technical language must be explained the first time it appears, and raw
errors belong in optional technical details rather than primary messages.
