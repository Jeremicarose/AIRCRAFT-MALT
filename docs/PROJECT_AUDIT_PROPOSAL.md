# Project Audit And Proposal

## Executive Summary

This project is building a **distributed aircraft localization and aviation data platform** centered on three layers:

- **receiver discovery and identity** via a CKB-backed registry
- **signal ingestion and multilateration processing** off-chain
- **operational and commercial data delivery** through an API and dashboard

The clearest current value proposition is not "blockchain for tracking data", but:

> use CKB to manage receiver identity and registry state, use off-chain infrastructure to ingest and process telemetry, and sell high-quality derived aviation data products through a modern API and operations console.

The commercial case should be judged primarily on four dimensions:

- **quality**: how accurate and trustworthy are the outputs?
- **latency / freshness**: how old is the data when the customer sees it?
- **reliability**: does the service remain available and usable consistently?
- **packaging**: is the output delivered in a form buyers can easily adopt, compare, and pay for?

At its strongest, this becomes:

- a **receiver network control plane**
- a **multilateration data product**
- a **commercial API platform**

The project is already meaningfully beyond concept stage:

- real CKB contract deployed on testnet
- real on-chain receiver registration working
- real CKB receiver discovery working
- hybrid demo mode producing live aircraft outputs for UI/demo purposes
- API, database, processor, and dashboard integrated locally

The major remaining gap is **commercial and operational hardening**, not architectural imagination.

In practice, that means the next phase is not “more architecture.”
It is proving:

- better or at least acceptable **quality**
- measurable **freshness**
- dependable **reliability**
- clearer **packaging** for paying customers

---

## 1. What Problem Exists Today?

Several related problems exist in aviation data and distributed receiver infrastructure today:

### 1. Aircraft tracking often depends on self-reported aircraft positions

Many systems rely heavily on ADS-B / GNSS-derived broadcasts from the aircraft itself. That creates blind spots when:

- the aircraft is not broadcasting a reliable position
- position quality is degraded
- only Mode-S style observations are available
- downstream systems want an independently derived position layer

### 2. Receiver networks are usually controlled centrally or informally

Receiver discovery and operational metadata are often managed via:

- internal spreadsheets
- private service directories
- hardcoded infrastructure
- ad hoc onboarding workflows

That becomes operationally painful when the network is:

- geographically distributed
- contributor-operated
- multi-tenant
- economically incentivized

### 3. There is a gap between raw receiver signals and usable data products

Collecting radio observations is not the same as delivering:

- usable aircraft positions
- historical tracks
- premium API outputs
- quality metrics
- operator tooling

The missing middle layer is:

- correlation
- solve logic
- trust and quality screening
- storage
- access control
- monetization

---

## 2. Why Is It A Problem?

It is a problem because it creates:

- lower trust in the resulting position layer
- higher integration cost for operators and platform teams
- weak receiver fleet management
- poor portability between transport providers
- weak commercial packaging of the output data

In practical terms:

- **operators** struggle to scale receiver participation cleanly
- **platform teams** must reinvent registry, processing, and API layers
- **customers** cannot easily buy refined MLAT-derived data as a product

---

## 3. Who Experiences The Problem?

The problem is experienced by multiple roles:

### Receiver-network operators

They need:

- clean onboarding of receivers
- visibility into receiver status and metadata
- a way to coordinate distributed contributors

### Aviation data platform builders

They need:

- a processing pipeline from raw observations to usable outputs
- a system that is not tightly bound to one central vendor design

### Researchers and protocol experimenters

They want:

- testable decentralized discovery
- repeatable MLAT infrastructure
- an auditable architecture for experiments

### Future commercial data buyers

They care about:

- high-quality positions
- API access
- filters
- history
- reliability

They do not primarily care about the blockchain mechanics. They care about the resulting service.

---

## 4. How Are They Solving It Now?

Today, the problem is typically solved through combinations of:

- centralized receiver registries
- proprietary tracking backends
- direct vendor integrations
- self-hosted signal ingestion stacks
- manually managed receiver directories
- standard cloud APIs selling processed flight/position data

Common current-state substitutes include:

- fully centralized flight tracking platforms
- private internal receiver fleets
- cloud database plus manually maintained config
- raw ADS-B aggregation without a distinct MLAT registry model

---

## 5. Who Pays?

There are two different economic layers:

### Supply-side payers

These are the people funding infrastructure:

- network operators
- platform builders
- research teams
- future marketplace operators

They pay for:

- receiver deployment
- infrastructure
- development
- operations

### Demand-side payers

These are the people who could pay for the output:

- aviation analytics customers
- commercial API customers
- downstream application builders
- enterprise users needing premium aircraft movement data

They would pay for:

- premium API access
- live stream access
- historical data
- analytics
- geographic or quality-tier access

---

## 6. Who Uses It?

Current likely users:

- internal operators
- engineers validating the network
- contributors / receiver operators
- demo reviewers / technical stakeholders

Future likely users:

- API consumers
- partner integrators
- enterprise data customers

---

## 7. Are They The Same Person?

Not always.

### In the current stage

The payer and user are often the same:

- the builder runs it
- the builder validates it
- the builder pays for the infrastructure

### In the commercial stage

They diverge:

- **buyer**: a company or platform team
- **user**: developers, analysts, operations staff, or downstream applications

This matters because the product must eventually satisfy both:

- economic buyer logic
- end-user operational utility

---

## 8. What Exactly Is Being Sold?

The clearest long-term sale is:

### A high-quality aviation data service

Not the blockchain itself.

More specifically:

- MLAT-derived aircraft position outputs
- receiver-backed coverage intelligence
- premium live or historical aviation data APIs
- quality / uncertainty-aware tracking outputs

Secondary saleable components:

- receiver network operations tooling
- premium analytics
- receiver contribution / incentive infrastructure

---

## 9. What Does The Customer Receive?

A customer would receive some combination of:

- recent aircraft positions
- historical track data
- low-latency aircraft updates
- uncertainty and quality metadata
- filtered feeds by region / aircraft / time window
- access to a premium stream or premium endpoints

Internally, operators also receive:

- receiver discovery
- receiver metadata visibility
- system state visibility
- a control-plane view of the network

---

## 10. Why Would Someone Choose This Over Alternatives?

Potential reasons:

### 1. Separation of concerns

This system clearly separates:

- registry state
- transport
- processing
- storage
- presentation
- future billing

That is cleaner than many tightly coupled alternatives.

### 2. Receiver registry portability

The project uses CKB as a **registry**, not as a telemetry database.
That is a more defensible blockchain role than trying to force all tracking data on-chain.

### 3. Premium data product potential

The architecture can evolve into a real API/data business, especially if combined with Fiber for low-cost access settlement.

### 4. Hybrid mode for go-to-market

The project can demo and validate:

- real receiver discovery
- simulated telemetry
- UI and API behavior

before every live component is ready.

---

## 11. What Is Unique?

The most unique thing is not “MLAT exists.”

MLAT itself is not unique.

What is more distinctive is the combination of:

- CKB-backed receiver registry
- off-chain MLAT runtime
- hybrid live/simulated operating mode
- future monetization path using Fiber for premium access and/or receiver rewards

The strongest unique positioning is:

> a decentralized receiver registry and incentive-ready control plane for aviation data infrastructure, with off-chain MLAT processing and a commercial API path.

---

## 12. What Are The Inputs?

There are several inputs:

### On-chain inputs

- receiver registration records
- receiver metadata
- receiver ownership / lock context

### Off-chain telemetry inputs

- Mode-S / ADS-B / MLAT-capable signal observations
- timestamps per receiver
- receiver positional metadata

### Configuration inputs

- registry type hash
- network endpoints
- transport selection
- simulation settings

---

## 13. Who Generates Them?

### Receiver registry records

Generated by:

- receiver operators
- network operators
- automated registration tooling

### Telemetry observations

Generated by:

- aircraft transmissions
- receiver hardware/software stacks
- transport adapters / feeds

### Derived state

Generated by:

- the correlator
- the MLAT solver
- the database layer
- statistics and dashboard logic

---

## 14. Can We Trust Them?

### On-chain receiver metadata

Partially trusted.

We can trust:

- the record exists on-chain
- ownership and script identity are verifiable
- the schema can be validated by the contract

We cannot automatically trust:

- the receiver is honest
- the location is physically correct
- the operator is truthful about capabilities

### Telemetry data

Also only partially trusted.

Receiver observations may be:

- malformed
- spoofed
- low quality
- stale
- inconsistent

So trust comes from:

- multi-receiver corroboration
- correlation quality
- solver residuals
- uncertainty metrics
- future scoring / reputation systems

---

## 15. What Processing Happens?

### 1. Receiver discovery

The system queries CKB / indexer for cells matching the registry type hash.

### 2. Record parsing and validation

Receiver records are decoded from canonical JSON and validated for:

- required fields
- coordinates
- capabilities
- status
- timestamp bounds

### 3. Receiver selection

The network client selects online, MLAT-capable receivers and can supplement them with simulated peers in hybrid mode.

### 4. Signal ingestion

Signals are received through:

- simulation transport
- websocket JSON transport
- command/jsonl bridge transport

### 5. Correlation

Signals are clustered into groups believed to belong to the same aircraft transmission.

### 6. Position solving

The solver uses multilateration / TDOA logic to estimate:

- latitude
- longitude
- altitude
- uncertainty

### 7. Persistence and API serving

Positions, receivers, and stats are stored and then exposed via REST endpoints and dashboard views.

---

## 16. What Calculations Happen?

The main calculations are:

### Coordinate transforms

- geodetic to ECEF
- ECEF back to geodetic

### TDOA calculations

- time-of-arrival differences
- range differences derived from signal timing

### Iterative solve logic

- Gauss-Newton / robust MLAT solving

### Quality calculations

- uncertainty
- residuals
- receiver contribution count

### Operational summaries

- active aircraft
- recent positions
- average uncertainty
- receiver counts

---

## 17. What Intelligence Is Added?

The intelligence is not in the raw data itself.
It is added by the system.

That includes:

- signal grouping/correlation
- aircraft position estimation
- quality scoring via uncertainty/residuals
- choosing which receivers are considered active/useful
- future monetizable packaging of the outputs

In business terms, the **intelligence layer** is what turns raw observations into something sellable.

---

## 18. What Data Must Persist?

Based on the actual implementation, the system persists:

### Positions

Each stored position includes:

- aircraft id
- timestamp
- latitude
- longitude
- altitude
- uncertainty
- number of receivers
- receiver ids
- residual
- created_at

### Receivers

The receiver cache persisted in SQLite includes:

- receiver id
- latitude
- longitude
- altitude
- status
- last_seen
- capabilities
- updated_at

### Statistics snapshots

- total signals
- total positions
- active aircraft
- active receivers
- average uncertainty
- created_at

---

## 19. Where Is It Stored?

### On-chain

Receiver registry metadata is stored on CKB as receiver-registry cells.

### Off-chain

Operational data is stored locally in SQLite.

The current implementation uses:

- `positions` table
- `receivers` table
- `statistics` table

This is appropriate for prototype/demo and early pilot stages.

Long-term, production may want:

- PostgreSQL / TimescaleDB or similar
- object storage for archives
- dedicated event pipelines

---

## 20. For How Long?

Current persistence behavior:

- positions and statistics can be cleaned up by age
- admin cleanup endpoint defaults to days-based deletion
- receiver state is updated in-place

So the current answer is:

- **indefinite until cleanup**

This is not yet a finalized retention policy.

A future commercial version should define explicit retention tiers, for example:

- 24 hours hot data
- 30 days standard history
- paid long-term archive

---

## 21. Who Pays? When Do They Pay? For What?

### Today

The builder/operator pays:

- development time
- infrastructure
- testnet experimentation

### Future commercial model

The most credible answer is:

#### Who pays?

- API customers
- stream consumers
- enterprise analytics buyers

#### When do they pay?

- before or during premium API/stream usage
- monthly subscription
- prepaid credit model
- off-chain metered settlement

#### For what?

- premium query access
- higher rate limits
- lower latency data
- historical access
- premium geographies / premium datasets
- quality-enriched MLAT outputs

The most promising payment rail here is Fiber, but for **billing and settlement**, not raw signal transport.

---

## 22. What Breaks If We Remove The Blockchain?

This is an important test.

If blockchain is removed:

### What still works

- the MLAT solver
- signal correlation
- local database
- API
- dashboard
- simulated feeds
- even live feed ingestion, if receivers are configured some other way

### What breaks or degrades

- decentralized/public receiver registry
- on-chain verifiable receiver identity/state
- ownership and registry auditability
- future composability with on-chain incentive or settlement systems

### Conclusion

The blockchain is **not required for MLAT math**.

It is required for this project’s specific design goal of:

> decentralized receiver discovery and identity management

That is a valid role.

It also means the blockchain is **important but not central to every layer**.

That is actually good architecture.

---

## 23. What Is The User Journey?

### Current technical user journey

1. operator configures the stack
2. receiver records exist on CKB
3. processor discovers receivers
4. transport starts
5. signals are correlated and processed
6. positions are stored
7. operator views outputs in API/dashboard

### Future commercial buyer journey

1. buyer lands on hosted product surface
2. buyer understands registry + tracking + data product story
3. buyer requests premium access or self-serve API account
4. buyer pays via subscription / credits / Fiber-backed billing
5. buyer integrates premium endpoints
6. buyer uses tracks/positions/analytics in their own product

---

## 24. What Are The Risks?

The risks break into technical, legal, data quality, and business categories.

---

## 24A. Accuracy, Coverage, Availability, And Freshness

Before this becomes a serious commercial data product, four operational questions must be answered with evidence rather than architecture alone:

1. **How close is the calculated position to reality?**
2. **Where can the system localize aircraft reliably?**
3. **Is the system available consistently enough to sell?**
4. **How old is the position when the customer sees it?**

These are not optional. Customers do not pay for an elegant design if:

- the position is wrong
- the coverage is patchy
- the service is frequently unavailable
- the data arrives too late

### A. How close is our calculated position to reality?

Today, the repo demonstrates:

- working solver architecture
- working signal correlation
- real receiver discovery from CKB
- hybrid demo generation

But it does **not yet provide a defensible public benchmark** for live production-grade aircraft localization accuracy.

That means the honest current answer is:

> the system has not yet been benchmarked enough against trusted external sources to claim a stable accuracy figure for commercial use.

### What should be compared against trusted sources?

To answer this properly, compare your derived positions against:

- trusted ADS-B / GNSS-reported positions where available
- known flight tracks from reputable commercial or public sources
- reference datasets from controlled test windows
- ideally, aircraft with dense receiver coverage and well-known trajectories

### Minimum accuracy study needed

For each solved position, compute:

- horizontal error in meters
- altitude error in meters
- time offset between your position and the reference position
- uncertainty vs actual error correlation

Then report:

- median horizontal error
- 95th percentile horizontal error
- median altitude error
- 95th percentile altitude error
- solve success rate under different receiver counts

### Why this matters

If the system says uncertainty is ±150m but the actual error is often kilometers, then the output is not commercially trustworthy even if the dashboard looks convincing.

---

### B. Where can we localize aircraft reliably?

The right answer is not “wherever receivers exist.”

Reliable localization depends on:

- receiver density
- receiver geometry
- timestamp quality
- aircraft altitude
- obstruction / terrain / RF environment
- traffic density and message quality

So the system needs a **coverage map of reliability**, not just a map of receivers.

### The honest current state

The repo currently proves:

- real registry-backed receiver discovery
- hybrid demo operation

It does **not yet prove** live reliable MLAT localization across a defined geography.

### What should be measured?

Define coverage by region/corridor and track:

- solve success rate per area
- median uncertainty per area
- receiver count per successful solve
- time-of-day / traffic effects
- altitude bands where performance changes

### Commercial implication

You should eventually be able to say something like:

> “We localize aircraft reliably in these corridors, above this receiver density, with this median horizontal error.”

Until that exists, geographic claims should stay conservative.

---

### C. Availability: is the system always working?

This is one of the most important business questions.

Customers do not pay for:

- a feed that disappears
- an API that times out unpredictably
- a dashboard that is only sometimes live
- a solver that silently stops producing positions

### Current honest answer

The current repo is operationally promising, but it is **not yet production-proven for always-on commercial availability**.

Reasons:

- the stack still contains simulation/hybrid modes
- it currently runs primarily as a local/demo-oriented deployment
- there is no demonstrated long-term uptime evidence in the repo

### Uptime metrics you should measure

At minimum:

- **API uptime**
- **dashboard uptime**
- **MLAT processor uptime**
- **receiver uptime**

And ideally:

- **receiver discovery uptime**
- **ingestion transport uptime**
- **successful solve pipeline uptime**

### Recommended definitions

#### API uptime

Percent of time the API responds successfully to health and premium data routes.

#### Dashboard uptime

Percent of time the operator dashboard loads and refreshes correctly.

#### MLAT uptime

Percent of time the processor is actively ingesting, correlating, and storing outputs without fatal interruption.

#### Receiver uptime

Percent of time a receiver remains discoverable and contributes usable observations.

### Important business nuance

A system can have:

- high API uptime
- but low MLAT output uptime

That is still a commercial failure if the buyer cares about actual position data.

So in this project, **position-delivery uptime** may matter more than plain HTTP uptime.

---

### D. Freshness: how fast is the data?

Another question customers will ask immediately is:

> how old is the position when I receive it?

This must be answered in measured latency terms, not architecture language.

### Freshness has multiple components

The age of a position at customer view time includes:

1. receiver observation delay
2. transport delay
3. correlation/solve delay
4. storage delay
5. API delivery delay
6. dashboard refresh delay

### Current honest state

The project can produce live-looking outputs in hybrid mode, but it does **not yet publish a measured freshness SLA** for real production data.

### What should be measured?

For every delivered position, compute:

- event time at observation
- solve completion time
- database write time
- API response time
- dashboard display time

Then derive:

- **observation-to-solve latency**
- **solve-to-store latency**
- **store-to-API latency**
- **end-to-customer latency**

### Customer-facing metric

The most important commercial metric is:

> **age of position when the customer sees it**

That should eventually be reported as:

- median age
- p95 age
- worst-case age under load

### Commercial reality

If the data is:

- highly accurate
- but 90 seconds old

some customers will reject it.

If it is:

- very fresh
- but low-confidence or intermittent

they will also reject it.

So **accuracy, coverage, uptime, and freshness must be evaluated together**, not independently.

---

### E. Recommendation: what must happen before charging?

Before commercial launch, this project should produce a formal operational benchmark covering:

#### Accuracy benchmark

- compare solves against trusted sources
- publish median and p95 error

#### Coverage benchmark

- define the geographies and flight conditions where localization is reliable

#### Availability benchmark

- measure API, dashboard, MLAT, and receiver uptime over meaningful intervals

#### Freshness benchmark

- measure end-to-customer age of position

Until those exist, the project is best described as:

> a strong technical and architectural foundation with real registry proof, but not yet a fully benchmarked commercial aviation data service.

---

## 24B. Completeness, Record Quality, Analytics Value, And Competitive Proof

Operational proof is not only about accuracy and uptime.

A buyer will also ask:

- are you missing aircraft?
- how trustworthy is each position record?
- what insights do I get beyond raw positions?
- why should I replace an incumbent with this?

These questions are commercially decisive.

---

### A. Completeness: are we missing aircraft?

This is one of the hardest and most important questions.

A system may localize some aircraft accurately and still fail commercially if it misses too many aircraft in the area of interest.

The right question is:

> **Of all aircraft in a target area, how many do we actually track?**

### Current honest answer

The repo does not yet provide a validated completeness benchmark against a trusted live reference set.

That means it is not yet possible to honestly claim:

- market-leading coverage
- complete airspace visibility
- replacement-grade aircraft detection in a region

### What should be measured?

For a defined geography and time window:

- total aircraft seen by trusted reference source
- total aircraft seen by this system
- overlap set
- missing set
- extra set

From that, compute:

- **coverage ratio**
- **capture rate by aircraft class**
- **capture rate by altitude band**
- **capture rate by region / corridor / airport area**

### Why completeness matters commercially

Some customers tolerate slightly worse accuracy if:

- coverage is broader
- cost is lower
- latency is better

But most customers will not tolerate a feed that simply misses too many relevant aircraft.

So completeness is a first-order buying criterion.

---

### B. Data quality metrics for every position record

A serious system should not output positions as if they are all equally trustworthy.

For every position record, the system should track and expose at least:

- **position confidence**
- **receiver count**
- **timestamp accuracy**
- **MLAT residual error**

### 1. Position confidence

This should summarize how trustworthy the position is overall.

It may be derived from:

- receiver geometry
- residuals
- uncertainty
- receiver quality history
- timing quality

### 2. Receiver count

Already partially available in the current implementation.

This matters because:

- a 4-receiver solve is different from an 8-receiver solve
- more receivers do not guarantee correctness, but they often improve confidence when geometry is sound

### 3. Timestamp accuracy

This is critical for MLAT quality.

If timestamps are noisy, the solve may be poor even when the UI looks normal.

This metric should eventually capture:

- observed timestamp jitter
- source clock quality
- synchronization assumptions

### 4. MLAT residual error

Residuals are one of the best direct internal quality signals.

A commercially mature system should retain and analyze them systematically.

### Recommendation

Expose a **quality model** in the product so premium customers can choose between:

- all positions
- high-confidence positions only
- region-specific high-confidence tiers

That is far more valuable than a flat undifferentiated feed.

---

### C. Analytics value: what insights can customers get?

If the product only provides positions, it competes as a commodity feed.

The stronger business moves happen when the platform provides insights beyond the raw track.

The right question is:

> **What insights can customers get?**

### Potential analytics value layers

- coverage heatmaps
- receiver contribution analysis
- solve confidence distributions
- corridor activity analysis
- anomaly detection
- track density by time/region
- latency and freshness analytics
- uptime and service-quality analytics
- premium quality-filtered exports

### Why this matters

Analytics are often easier to defend commercially than raw data alone.

A buyer may already have access to some form of aircraft positions.

They may pay for:

- better quality scoring
- better operational context
- better workflow integration
- better decision support

That means the platform should aim to sell:

- **positions**
- **confidence**
- **coverage intelligence**
- **operational insights**

not just a stream of coordinates.

---

### D. Customer test: would someone pay for this?

This is the most important commercial question.

The right test is not:

> “Is the architecture interesting?”

It is:

> **Would someone pay for this?**

### Current honest answer

The project is not yet commercially proven.

It has:

- strong architectural differentiation
- real receiver discovery proof
- a credible future billing path

But it does **not yet have evidence** that a customer would switch budgets to this product at scale.

### What would create that proof?

- first external design partner
- first premium API consumer
- repeated usage of premium outputs
- willingness to pay for better quality, better cost, or better structure

Until then, the commercial case remains promising, not proven.

---

### E. The “replace me” test

This is the most important framing discipline for product strategy.

Ask:

> **If a customer stopped using FlightRadar24 or OpenSky and switched to us, what would they gain?**

If the answer is unclear, the product is not yet differentiated enough.

### Possible gains

A customer might switch if they gain one or more of:

- lower cost
- more flexible access
- better quality controls
- better uncertainty/confidence handling
- better receiver-backed provenance
- more useful analytics
- better regional coverage in a target market
- easier integration into their own system

### Important caution

“Uses blockchain” is not itself a meaningful gain to most buyers.

The gain must be something operational or economic the customer can feel.

---

### F. Comparative quality proof: compared to what?

When someone says:

> “We have high-quality aviation data.”

the immediate next question should be:

> **Compared to what?**

That comparison set likely includes:

- FlightRadar24
- OpenSky
- ADS-B Exchange
- local aviation authorities
- existing commercial feeds

### The right comparative dimensions

You should not claim superiority in general terms.

You should compare on explicit axes:

- **more accurate**
- **more complete**
- **cheaper**
- **faster**
- **better coverage**
- **better analytics**

### Current honest state

The repo does not yet contain a formal benchmark proving superiority on any of those dimensions versus incumbents.

So the project should not currently market itself as:

- better than FlightRadar24
- better than OpenSky
- better than ADS-B Exchange

without measured evidence.

### Recommended benchmark table

For each reference competitor or trusted source, track:

- position error comparison
- capture/completeness comparison
- freshness comparison
- uptime comparison
- cost comparison
- analytics/metadata comparison

This is the only credible way to make “high-quality aviation data” a commercial claim instead of a slogan.

---

### G. What would make the project clearly compelling?

The project becomes genuinely compelling if it can prove at least one of these in a target segment:

- **more accurate**
- **more complete**
- **cheaper**
- **faster**
- **better coverage**
- **better analytics**

The strongest near-term path is probably not “beat every incumbent on every axis.”

It is:

> win on a narrow segment with a strong combination of quality transparency, registry-backed coordination, and better commercial packaging.

That is a much more realistic path than trying to outcompete every broad aviation feed immediately.

---

## 25. Technical Risks

### Live solver quality risk

The hybrid mode is currently proving the product surface, but not yet proving real live MLAT solve performance at production quality.

### Receiver trust risk

On-chain registration does not guarantee physical truth of receiver claims.

### Transport integration risk

The full real 4DSky or equivalent live feed path is not yet the dominant validated mode in this repo.

### Scaling risk

SQLite is fine now, but not a final multi-tenant production backbone for serious throughput/history.

### Payment/entitlement integration risk

If Fiber is added, it introduces:

- channel liquidity concerns
- entitlement reconciliation complexity
- failure modes between billing and delivery

---

## 26. Legal Risks

### Aviation data rights / licensing

Depending on jurisdiction, source, and commercial model, aviation data licensing may matter.

### Privacy / surveillance concerns

Aircraft movement data can raise:

- regulatory
- contractual
- sensitivity

questions depending on market and use.

### Export / sanctions / jurisdiction

Cross-border telemetry products can create jurisdictional constraints.

### Token/payment regulation risk

If Fiber-based micropayments are used commercially, legal review is needed on:

- payment treatment
- invoicing
- custody assumptions
- financial/compliance exposure

---

## 27. Data Quality Risks

### Bad receiver metadata

Receivers may be:

- mislocated
- stale
- misclassified

### Bad timing quality

MLAT quality depends heavily on timestamp quality and receiver geometry.

### Sparse coverage

A small or uneven network reduces solve reliability.

### Synthetic/live mismatch

Hybrid demo mode is great for product validation, but it can mask real-world solver limitations if misunderstood.

---

## 28. Business Risks

### Blockchain may not matter to buyers

Customers may care about:

- quality
- latency
- reliability
- pricing

and not about the decentralized registry story.

That means blockchain must support the business, not be the business.

### Existing alternatives are strong

Centralized incumbents already sell aviation data and tracking services.

### Two-sided network risk

If the project evolves into a marketplace:

- supply side must be strong enough
- demand side must be strong enough
- incentives must be sustainable

### Monetization timing risk

The system may become technically impressive before it becomes clearly saleable.

---

## 29. What Metric Proves Success?

There should not be only one metric forever, but if one core metric is needed:

## Primary success metric

**Number of paying consumers regularly using premium MLAT-derived data outputs**

That is the best business proof.

Because it validates:

- output quality
- reliability
- packaging
- willingness to pay

### Supporting technical metrics

- number of real registered receivers on-chain
- percentage of valid receiver records discovered successfully
- number of successful live solves
- median uncertainty by region
- API usage growth
- premium conversion rate

### Current pre-revenue proof metric

Before paid adoption, the best proof metric is:

**successful discovery of real on-chain receivers and sustained delivery of usable aircraft outputs through the API/dashboard**

That metric is already partially achieved.

---

## 30. Strategic Recommendation

### What this project should become

This should be positioned as:

> a decentralized receiver registry and MLAT-derived aviation data platform, with off-chain processing and future low-cost billing via Fiber.

### What should be emphasized commercially

The product story should be led by:

- **quality**
  - confidence, uncertainty, and solve trustworthiness
- **latency / freshness**
  - how quickly customers receive usable positions
- **reliability**
  - whether the feed/API/dashboard stay available consistently
- **packaging**
  - how clearly the outputs are delivered, tiered, explained, and integrated

These four dimensions are more commercially important than the blockchain mechanism itself.

### What it should not become

It should not be positioned as:

> blockchain for raw flight tracking data transport

That is the wrong layer.

### Strongest next business step

The highest-value next commercial move is:

1. keep CKB as registry/identity
2. keep MLAT processing off-chain
3. use Fiber later for premium API/stream billing and receiver incentives
4. sell high-quality derived aviation outputs, not raw packet transport
5. benchmark and package the product explicitly around:
   - quality
   - freshness
   - reliability
   - premium data product packaging

---

## 31. Proposed Near-Term Roadmap

### Phase 1: Operational proof

- finish polishing hosted/local demo
- register more real receivers
- validate live discovery repeatedly
- improve real solve path confidence

### Phase 2: Product proof

- introduce premium API endpoint tiers
- define what is free vs paid
- package historical and live outputs clearly

### Phase 3: Fiber integration

- Fiber-backed billing for premium API usage
- Fiber-backed stream access
- later, receiver reward settlement

### Phase 4: Commercial proof

- onboard first external consumer
- measure repeated premium usage
- validate willingness to pay

---

## Final Judgment

This project is technically defensible **if** it remains disciplined about the role of each layer:

- **CKB** for receiver registry and shared identity/state
- **Fiber** for settlement and metered access
- **off-chain services** for telemetry transport, processing, storage, and delivery

That is the architecture that makes business and technical sense.

If the project tries to put too much of the raw tracking plane into blockchain/payment-channel infrastructure, it becomes harder to justify.

If it focuses on:

- decentralized discovery
- trustworthy receiver coordination
- valuable processed aviation outputs
- measurable quality
- low-latency / fresh delivery
- operational reliability
- strong commercial packaging
- premium access and incentives

then it has a coherent path.
