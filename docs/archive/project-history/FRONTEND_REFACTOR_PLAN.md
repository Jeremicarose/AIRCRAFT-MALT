# Frontend Refactor Plan

## Goal

Refactor the current single-page MLAT Airspace Console into a multi-page dashboard architecture where each page has a focused responsibility.

The main objective is to improve:

- clarity
- maintainability
- scalability
- user navigation
- future module growth

without breaking the current API-driven functionality.

---

## Current problem

The current dashboard is carrying too many responsibilities in one surface:

- overview metrics
- mode / readiness context
- connection controls
- map visualization
- aircraft focus
- receiver focus
- live/polling delivery behavior

This makes the page useful for a demo, but structurally too dense for a growing product.

---

## Recommended page model

### 1. Dashboard / Home

Purpose:

- high-level system status
- quality / freshness / reliability summary
- top metrics
- current mode
- quick navigation to deeper surfaces

### 2. Aircraft Management

Purpose:

- active aircraft list
- aircraft details
- aircraft history
- quality / uncertainty view per aircraft

### 3. Receiver Registry

Purpose:

- receiver list
- receiver status
- receiver metadata
- receiver contribution context

### 4. Localization

Purpose:

- map-first localization view
- recent track geometry
- receiver overlays
- live/replay position context

### 5. Payments

Purpose:

- Fiber / premium access / settlement story
- payment and entitlement visibility
- placeholder until live payment data exists

### 6. AI Agent

Purpose:

- show autonomous/runtime reasoning surfaces if expanded later
- current automation / ingest / benchmark actions
- structured activity and safety state

### 7. Analytics

Purpose:

- quality trends
- freshness trends
- reliability metrics
- benchmark summaries

### 8. Settings

Purpose:

- API base and connection config
- blockchain settings
- runtime flags
- premium/access configuration

---

## Recommended frontend structure

```text
src/visualization/
  app/
    shell.html
    nav.js
    shared.js
    shared.css
    pages/
      overview.html
      aircraft.html
      receivers.html
      localization.html
      payments.html
      agent.html
      analytics.html
      settings.html
  dashboard.html          # legacy/compat entry, redirects or embeds overview
  dashboard.js            # legacy compatibility layer or bootstrap
  index.html              # product/landing page
  styles.css              # current styles, to be gradually split
  vendor/
```

---

## Recommended routing model

Keep it simple and static-first.

### Public product pages

- `/`
- `/dashboard.html`

### App pages

- `/app/overview.html`
- `/app/aircraft.html`
- `/app/receivers.html`
- `/app/localization.html`
- `/app/payments.html`
- `/app/agent.html`
- `/app/analytics.html`
- `/app/settings.html`

This works well with the current Flask file-serving model and does not require a SPA router rewrite.

---

## Shared shell responsibilities

The shared app shell should own:

- page navigation
- active nav state
- mode pill
- global connection state
- top summary metrics
- common styling primitives

Each page should only own its local content and behavior.

---

## Component reuse targets

Reusable shared UI pieces should include:

- top navigation
- status pills
- metric cards
- section headers
- empty states
- receiver cards
- aircraft cards
- connection control group

Reusable data helpers should include:

- `fetchJson`
- mode loading
- health/readiness loading
- formatting helpers
- connection status helpers

---

## Incremental refactor plan

### Phase 1

- add shared app shell
- add shared CSS/JS
- create overview page
- keep current dashboard route working

### Phase 2

- move aircraft-focused UI into aircraft page
- move receiver-focused UI into receivers page
- keep map in localization page

### Phase 3

- add analytics page using current health/statistics/readiness data
- add settings page using current config surfaces

### Phase 4

- add payments and AI agent placeholder surfaces that are honest about current maturity

---

## Important constraints

### Do not break

- `/`
- `/dashboard.html`
- existing API endpoints
- existing benchmark/readiness surfaces

### Keep compatibility

The current dashboard route should remain usable while the new pages are introduced.

---

## Immediate implementation step

The first concrete step should be:

> add a shared app shell and an `/app/overview.html` page, then preserve the current `/dashboard.html` as a compatibility route while responsibilities are split gradually.
