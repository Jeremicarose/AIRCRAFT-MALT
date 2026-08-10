# MLAT Reference Operator Console

## Status

This console is the operator surface for the MLAT reference implementation. It
is not the repository's primary product and it is not evidence that a physical
MLAT trial occurred. Registry V2 remains the primary product under
[ADR 0002](../../adr/0002-registry-primary-mlat-reference.md).

## Users

The MLAT Airspace Console is intended for aviation operators, infrastructure
engineers, blockchain developers, and security reviewers working from laptops
and wide control-room displays. Their core jobs are to monitor aircraft and
receiver coverage, validate localization confidence, detect processing
failures, inspect supporting evidence, and decide whether the reference runtime
is ready for live operation.

## Product Purpose

The console turns receiver observations and off-chain MLAT results into an
inspectable operational picture. It exposes quality, readiness, evidence, and
failure state without overstating what cryptographic identity proves. CKB
establishes receiver identity and lifecycle authorization underneath the
workflow; it does not prove receiver location, clock accuracy, stream
authenticity, or aircraft position.

## Brand Personality

Calm, precise, assured. The product should feel engineered for continuous use in an aviation operations center: quiet under normal conditions, explicit when attention is required, and confident without decorative spectacle.

## Anti-references

The console must not resemble a blockchain explorer, a wallet, a hackathon demo, a gaming RGB dashboard, a generic card-grid admin template, or a marketing landing page. Avoid decorative gradients, repeated status badges, oversized glass cards, walls of explanatory copy, serif display typography, and motion that does not communicate state.

## Design Principles

1. **Airspace first.** Aircraft, receivers, confidence, and coverage lead every operational workflow; registry details appear only where trust must be inspected.
2. **One screen, one decision.** Each route owns a single operator job and excludes unrelated information.
3. **Confidence is visible.** Freshness, uncertainty, provenance, and readiness are presented beside the data they qualify.
4. **Exceptions earn attention.** Healthy state stays quiet. Warning and failure states identify cause, evidence, and the next operator action.
5. **Progressive evidence.** Summaries support rapid scanning; technical proof and lifecycle detail remain one deliberate action away.

## Accessibility & Inclusion

Meet WCAG 2.2 AA contrast and interaction requirements. Every workflow must support keyboard navigation, visible focus, semantic labels, screen readers, reduced motion, and non-color status cues. Layouts must remain usable without horizontal page scrolling from tablet through ultra-wide desktop viewports.
