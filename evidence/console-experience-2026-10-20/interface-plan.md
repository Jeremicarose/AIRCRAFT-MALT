# Interface scope — 20 October 2026

User request: finish locally actionable readiness work, smooth navigation, and gamify the project.
Audience and style are taken from existing PRODUCT.md: receiver owners and coordinators, calm and precise operation, accessible to first-time technical users.

Changes:
- Persistent Next.js console layout; existing pages render workspace content only.
- Navigation pending feedback, bounded 180 ms content motion, reduced-motion alternative, heading focus and modal closure on route change.
- Six optional local learning missions (300 XP total), named badges, progress levels, pause/reset and idempotent completion. No tokens, on-chain rewards, or readiness score.
- Points require a correct knowledge answer or actual receiver/stage inspection/valid diagnostic export. Historical replay qualification remains unmodified.
- Diagnostic export has explicit pending/error/completion feedback. Registry evidence can recover from a transient server fetch failure.

Acceptance:
- The same sidebar DOM node survives forward/back and normal navigation.
- Navigation remains available during loading; one main landmark and one h1 per console route.
- Wrong answers, failed exports, mere page visits and paused missions do not award points.
- Duplicate actions do not increase points; corrupt/blocked storage cannot crash or inflate progress.
- Keyboard, mobile, reduced motion and accessibility checks pass.
- Existing registry, aircraft, pipeline, provenance and historical browser cases remain valid.

The earlier public-push rejection and external reviewer/wallet/feed/host requirements are unchanged. No external action is implied by local mission completion.
