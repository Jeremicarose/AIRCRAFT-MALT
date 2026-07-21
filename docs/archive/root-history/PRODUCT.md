# Product

## Product name
MLAT Airspace Console

## Users
Primary users are operators, product evaluators, and aviation-data teams who need to inspect derived aircraft outputs rather than raw receiver traffic.

This includes:

- teams evaluating MLAT-backed aviation products
- operators reviewing replay or live traffic quality
- internal stakeholders validating reliability and packaging
- engineers integrating downstream APIs or streams

## Product purpose
Provide a control surface and delivery layer for derived aviation outputs so users can judge:

- where the aircraft estimate is
- how good the estimate looks
- how recent the estimate is
- which receivers supported it
- what level of access the consumer has

The product should make quality, freshness, and trust legible without forcing users to read logs or internal runtime details.

## Product promise
The platform sells on:

- quality of derived outputs
- explainability of each estimate
- operational visibility
- packaging for public/demo and premium consumers

It does **not** sell blockchain as the primary customer-facing story.

## Infrastructure positioning
CKB is supporting infrastructure for receiver identity and registry workflows.

That means:

- it can help explain where receiver metadata comes from
- it should not dominate the homepage or primary product narrative
- product-facing surfaces should lead with outputs, trust, and operations

## Brand personality
Technical, composed, aviation-native, trustworthy.

## Anti-references
Avoid:

- toy map demos
- crypto-first storytelling
- loud speculative blockchain framing
- over-gamified telemetry UIs
- flashy visuals that make operational data feel less credible

## Design principles
- Put the map first because airspace context is the fastest explanation of product value.
- Make replay, demo, and live modes explicit before users interpret traffic.
- Show trust signals such as uncertainty, receiver support, and quality next to the estimate.
- Keep blockchain and registry detail available, but secondary.
- Prefer operational clarity over decorative complexity.
- Keep the interface credible for both internal review and customer-facing walkthroughs.

## Packaging principles
- Public/demo access should feel useful but intentionally shallow.
- Premium access should map to deeper history, richer metrics, and live delivery features.
- Packaging language should describe output depth and operational value, not just implementation detail.

## Accessibility and inclusion
Target WCAG AA contrast, preserve keyboard access for controls, maintain readable density on smaller screens, and avoid motion that is required to understand system state.
