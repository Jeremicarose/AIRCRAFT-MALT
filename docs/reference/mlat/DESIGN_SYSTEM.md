---
name: MLAT Airspace Console
description: Aircraft tracking infrastructure with cryptographic proof.
colors:
  graphite-deep: "#080a0d"
  graphite: "#0d1014"
  graphite-raised: "#14181e"
  graphite-hover: "#1b2028"
  line: "#2a3039"
  ink: "#f1f4f8"
  ink-secondary: "#aab2bd"
  ink-quiet: "#7f8996"
  signal-blue: "#5b9cff"
  trust-cyan: "#68d5e8"
  healthy: "#4fd18b"
  attention: "#e6c45d"
  replay: "#ef9b55"
  failure: "#ef6b72"
  series-teal: "#4bb6a3"
  series-violet: "#9b8cf4"
  series-gold: "#c7a85b"
typography:
  headline:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "0"
  title:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0"
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  label:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 550
    lineHeight: 1.35
    letterSpacing: "0"
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  xxl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.signal-blue}"
    textColor: "{colors.graphite-deep}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
    height: "36px"
  button-secondary:
    backgroundColor: "{colors.graphite-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
    height: "36px"
  panel:
    backgroundColor: "{colors.graphite}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "16px"
  input:
    backgroundColor: "{colors.graphite-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
    height: "36px"
---

# Design System: MLAT Airspace Console

This design system applies only to the MLAT reference operator console. It does
not define the Registry V2 protocol or change the Registry-first product
boundary recorded in [ADR 0002](../../adr/0002-registry-primary-mlat-reference.md).

## Overview

**Creative North Star: "The Quiet Control Room"**

The interface is designed for an operator seated in a dim operations room, monitoring a high-volume system for hours without fatigue. Deep neutral surfaces reduce glare, airspace and evidence receive the strongest visual hierarchy, and color appears only when it communicates selection, trust, mode, or health.

This is a restrained product system, not a cinematic concept. Navigation, inspectors, tables, and charts use familiar infrastructure-software patterns with exact spacing and fast state transitions. The product rejects blockchain explorer conventions, gaming RGB treatments, generic card grids, and marketing-page composition.

**Key Characteristics:**

- Airspace-led layouts with compact evidence inspectors
- Tonal depth with thin separators and rare shadows
- One sans-serif family with tabular numerals
- Semantic color backed by text and icon cues
- Motion limited to state, focus, and spatial continuity

## Colors

The palette combines neutral graphite working surfaces with a restrained signal blue, a quiet trust accent, and unmistakable semantic states.

### Primary

- **Signal Blue:** Current selection, primary commands, links, focus rings, and active map geometry.

### Secondary

- **Trust Cyan:** Cryptographic verification and receiver identity accents only. It is never a health status.

### Tertiary

- **Healthy Green:** Healthy runtime and completed stages.
- **Attention Yellow:** Degraded state and operator attention.
- **Replay Orange:** Replay and benchmark context.
- **Failure Red:** Failed stages, unavailable services, and destructive actions.

### Neutral

- **Deep Graphite:** Page canvas and map chrome.
- **Working Graphite:** Primary panels and sidebar.
- **Raised Graphite:** controls, selected rows, and inspectors.
- **Operational Ink:** primary content.
- **Secondary Ink:** supporting labels and metadata.

### Data visualization

- **Series Teal:** Secondary operational series such as position throughput.
- **Series Violet:** Comparative latency and availability series.
- **Series Gold:** Resource and uncertainty series.

Chart colors are not status. Semantic green, yellow, orange, and red appear in charts only when the data itself represents healthy, attention, replay, or failure state.

**The Rare Accent Rule.** Signal blue and trust cyan together occupy less than ten percent of a screen. Their scarcity makes them useful.

**The Status Contract.** Green means healthy, yellow means attention, orange means replay, red means failure, blue means selection, and gray means neutral. No substitutions.

## Typography

**Display Font:** Inter with system-ui fallback
**Body Font:** Inter with system-ui fallback
**Label/Mono Font:** SFMono-Regular for identifiers and exact evidence values only

**Character:** One technical sans family keeps the interface coherent and legible. Weight and fixed size establish hierarchy; UI typography never scales with viewport width.

### Hierarchy

- **Headline** (650, 1.5rem, 1.2): page titles and inspector entities.
- **Title** (600, 0.875rem, 1.35): panel, stage, and table titles.
- **Body** (400, 0.875rem, 1.5): concise operational descriptions, limited to 72 characters where prose appears.
- **Label** (550, 0.75rem, 1.35): metadata and control labels without artificial tracking.
- **Metric** (650, 1.75rem, 1.1): important values with tabular numerals.

**The One-Family Rule.** Serif display faces, decorative monospace, fluid headings, and negative letter spacing are prohibited.

## Elevation

The system is flat by default. Depth comes from tonal layering and separators. Shadows appear only under overlays, floating map controls, and elevated inspectors where spatial separation is necessary.

### Shadow Vocabulary

- **Overlay:** A compact dark shadow for command palette, menus, and tooltips.
- **Map Control:** A tight shadow that keeps controls readable over variable map tiles.

**The Structural Depth Rule.** A resting panel uses a separator or a tonal change, never a decorative border and wide shadow together.

## Components

### Buttons

- **Shape:** Compact corners (6px), with a stable 32px or 36px control height.
- **Primary:** Signal blue fill, dark graphite text, and concise icon-plus-command labels.
- **Hover / Focus:** 180ms ease-out tonal shift; a two-pixel signal-blue focus ring remains visible.
- **Secondary / Ghost:** Raised graphite or transparent surfaces with operational ink.

### Chips

- **Style:** Status chips are compact text-and-dot indicators on a subtle semantic tint.
- **State:** Selection chips use signal blue; trust chips use trust cyan; health chips obey the status contract.

### Cards / Containers

- **Corner Style:** Restrained corners (8px).
- **Background:** Working or raised graphite based on hierarchy.
- **Shadow Strategy:** Flat at rest, elevated only for overlays.
- **Border:** One-pixel separators distinguish adjacent data regions.
- **Internal Padding:** 12px for dense controls, 16px for standard panels, 24px for primary work regions.

### Inputs / Fields

- **Style:** Raised graphite, one-pixel separator, 6px corners, and a minimum 36px height.
- **Focus:** Signal-blue ring and border shift without layout movement.
- **Error / Disabled:** Failure tint plus text for errors; neutral dimming with preserved legibility for disabled fields.

### Segmented Controls / Switches

- **Segmented Controls:** One shared compact control with `aria-pressed` on every option. Selection uses a raised neutral surface rather than a decorative accent.
- **Switches:** One shared binary control with native switch semantics, visible focus, disabled state, and a stable 36px track vocabulary.

### Stat Strips

Stat strips summarize related live values in one bounded band. They use internal separators, one consistent type scale, semantic icons only when the metric has a state, and optional fixed-size sparklines that never shift layout after lazy loading.

### Navigation

The permanent left sidebar groups routes by operator workflow. Active routes use a raised surface, signal-blue icon, and ink text. The collapsed state keeps icons and tooltips. Tablet layouts convert the sidebar to a controlled sheet without horizontal page scrolling.

### Inspector

Inspectors use a compact two-column fact layout, sticky entity header, contextual actions beside the affected field, and disclosure sections for deeper evidence. Only one pipeline stage expands at a time.

## Do's and Don'ts

### Do:

- **Do** make the map the largest visual region on overview and live-map routes.
- **Do** pair every semantic color with an icon or text label.
- **Do** keep transitions at or below 180ms with an ease-out curve.
- **Do** reveal evidence progressively from summary to exact provenance.
- **Do** keep healthy state quiet and make operator actions explicit on exceptions.

### Don't:

- **Don't** resemble a blockchain explorer, a wallet, or a transaction feed.
- **Don't** use a gaming RGB dashboard, decorative gradients, gradient text, or glowing ornament.
- **Don't** build generic card-grid admin pages or nest cards inside cards.
- **Don't** use marketing landing-page composition, oversized glass cards, or walls of explanatory copy.
- **Don't** use serif display typography, repeated status badges, or decorative motion.
- **Don't** use cyan as a status color; it is reserved for cryptographic trust.
- **Don't** use border-left or border-right accents wider than one pixel.
