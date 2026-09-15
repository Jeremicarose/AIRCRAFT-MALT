# MLAT Data-Source Evaluation

Evaluation date: 2026-09-14

## Executive Finding

No currently documented public dataset or network API is a **GO** for the
unchanged production pipeline.

The best first path is a small, authorized, source-complete historical extract
from the LocaRDS/OpenSky maintainers. This is a **CONDITIONAL GO**, not a claim
that the data is already available. OpenSky documents that its internal archive
contains raw messages, reception timestamps, and receiver positions. The
maintainers must still confirm and supply the original frames, stable receiver
IDs, comparable clock calibration, a defensible per-receiver uncertainty at or
below 100 ns, usage permission, and a legitimate Registry identity plan.

The strongest live fallback is four or more cooperating operators with
GPS-qualified receivers and explicit permission to use their local raw Beast
feeds. This can use the repository's existing multi-receiver Beast bridge, but
ordinary PiAware/dump1090 Beast output does not by itself establish a common
clock or a 100 ns uncertainty.

No adapter should be built until an actual sample and its clock evidence pass
the contract in [data-source-contract.md](data-source-contract.md).

## Data Classes

- **A: raw receiver observation** means one receiver's original Mode-S frame
  plus its receiver arrival timestamp and stable receiver identity. This is the
  required message-level input.
- **B: decoded receiver observation** retains one receiver's observation but
  replaces or removes the original frame. It is usable only if the existing
  correlator is not being validated, so it is not a production substitute.
- **C: already-solved position** is an MLAT or fused aircraft position. It is
  output, not MLAT input.
- **D: aircraft-reported ADS-B position** is a position broadcast by the
  aircraft. It can provide benchmark truth when kept separate from solving,
  but it does not replace receiver arrivals.

## Source Comparison

`Available` below means the field is in the documented product or inspected
dataset. It does not mean the provider may possess it internally.

| Source/path | Class | Original frame | Receiver timestamp | Receiver ID | Receiver coordinates | Clock evidence | Same transmission at 4+ receivers | Historical/live access | License/access | CKB identity association | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LocaRDS v1.0 public archive | B + D | **Not available** | Available in ns units, but offsets/resolution differ | Dataset-local pseudonymous serial | Available | No source or numeric uncertainty; `good` is not clock qualification | Pre-grouped observations available | Historical download | CC BY-SA 4.0 | Cannot turn pseudonymous serials into operator-owned CKB identities | **NO-GO** |
| OpenSky public raw sample | A, incomplete | Available | `timeAtSensor`/`timestamp` stored as nullable doubles | Sensor serial | **Removed from current public sample distribution** | No documented source, calibration, or <=100 ns uncertainty | Potentially present, but no contract-complete group proven | Historical five-minute sample | OpenSky terms apply | Sensor serial is not a CKB identity | **NO-GO** |
| OpenSky Trino documented tables | C/D and decoded aggregates | Raw frame is not in the documented table list/schema | Table time is seconds; decoded tables expose min/max summaries, not per-receiver TDOA arrivals | State vectors can list contributing serials | Not provided as observation geometry | Not provided | No receiver-level arrival set | Historical, approved accounts | Research access reviewed; private/commercial use requires a licence | No operator-controlled CKB binding | **NO-GO** |
| OpenSky REST API / `readsb_mlat_sv` | C/D | Not available | State-vector time, not receiver arrival time | At most contributing sensor serials in state vectors | Not supplied per observation | Not supplied | No | Live/recent REST and historical solved state vectors | Operational use or commercial use requires written agreement | No | **NO-GO** |
| Authorized OpenSky maintainer extract | Potential A + D | OpenSky says its archive stores it; must be supplied | OpenSky says reception times are stored; comparability must be proven | Potentially available, subject to privacy | Potentially available, subject to privacy | **Unknown and decisive** | Must be demonstrated in a sample | Historical extract only if approved | Written approval, access review, privacy limits, and any commercial/pilot licence required | Requires maintainer/operator-approved, accurately scoped binding | **CONDITIONAL GO** |
| ADS-B Exchange API, stream, and historical products | C/D | Not documented as a product field | Position update times, not per-receiver arrivals | No receiving station per frame | No | No | No | Subscription API/stream/history | Commercial contract; reuse/redistribution only as licensed | No | **NO-GO** |
| FlightAware Firehose/AeroAPI | C/D | Not supplied | Flight/position event time, not per-receiver arrival | No receiving station per frame | No | No | No | Paid live/historical licensed products | Order and product licence control use and redistribution | No | **NO-GO** |
| Operator-authorized local PiAware/dump1090 Beast feed | A | Available on local Beast port | 48-bit Beast counter available; absolute/common timing depends on hardware and calibration | Must be bound by operator configuration | Supplied by the operator through Registry | Required separately; ordinary Beast output does not prove it | Only if 4+ overlapping operators participate | Live | Operator permission required; provider-owned FlightFeeder access may need FlightAware permission | Operator can register and control its own CKB identity | **CONDITIONAL GO** |
| Airplanes.live public map/API | C/D | Not exposed | Position time, not per-receiver arrival | No receiver ID per frame | Precise feeder locations are private | No | No | Live map/API | Raw-data reuse terms were not found; mark **UNKNOWN** | No | **NO-GO** |
| Authorized Airplanes.live research extract | Potential A | Network receives timestamped Mode-S data, but no extract schema is published | Potentially available | Potentially available | Held privately | Source/calibration/uncertainty not documented | Network performs MLAT, but extract coverage must be proven | Only by maintainer agreement | Permission, data licence, and feeder privacy consent required | Must be agreed with maintainers/operators | **CONDITIONAL GO** |
| ADSB.lol public API and historical files | C/D | Not supplied in the aircraft JSON products | Aircraft-state time, not receiver arrival | No receiver ID per frame | No | No | No | Public live/historical | API/history marked ODbL 1.0 | No | **NO-GO** |
| ADSB.lol feeder-only aggregate Beast output | A, but receiver relationship lost | Available | Beast records contain a timestamp counter, but provenance/comparability is not documented | Aggregate output does not carry original receiver ID per Beast frame | Not carried with each frame | No per-receiver source/calibration/uncertainty | Cannot reconstruct receiver-specific observations from the aggregate stream | Live, limited to feeder IPs, experimental | Output page marks ODbL 1.0; feeder access rules apply | No defensible per-frame mapping | **NO-GO** |
| Authorized ADSB.lol maintainer extract | Potential A | Internal feeder inputs may contain it; not a published extract | Unknown | Unknown | Unknown/private | Unknown | Must be demonstrated | Only by maintainer agreement | Written scope and licence needed | Must be agreed with operators/maintainer | **CONDITIONAL GO** |
| 4DSKY authorized P2P raw stream | Potential A | Documented challenge stream includes raw Mode-S bytes | Seconds since midnight plus nanoseconds | Documented integer sensor ID | Documented lat/lon/alt | Site claims 30 ns GPS synchronization for current Jetvision hardware, but per-sensor source, calibration, validity, and uncertainty evidence are not in the stream contract | Must be demonstrated with 4+ current sellers | Live access requires credentials and current sellers; no public historical archive found | Current data licence/pilot terms **UNKNOWN**; written confirmation required | Seller ID is not automatically a CKB identity; seller consent/registration required | **CONDITIONAL GO** |
| Other public academic ADS-B trajectory/state-vector datasets reviewed | C/D | Not supplied | Aircraft-state timestamps | No receiver-level identity | No per-observation receiver geometry | No | No | Historical downloads | Dataset-specific | No | **NO-GO** |
| Direct GPS-qualified receiver operators | A | Available through local Beast or explicit JSONL | Hardware counter or timestamp must be calibrated to a comparable nanosecond timebase | Operator-controlled stable mapping | Operator registers coordinates | Operator must supply source, <=100 ns uncertainty, current calibration window, and evidence | Requires at least 4 with overlapping reception and sound geometry | Live; a short raw capture could become a reproducible historical fixture with permission | Written participant/data-use permission required | Strongest legitimate mapping: each operator controls its Registry identity | **CONDITIONAL GO** |

## LocaRDS Confirmation

The inspected local archive is `/private/tmp/locards-subset_1.zip`. Its MD5 is
`ca2e163f437ff8b9dfaef64bed871ff3`, matching the official
[Zenodo record](https://zenodo.org/records/4739276). It contains:

| File | Inspected schema |
|---|---|
| `subset_1/set_1.csv` | `id,timeAtServer,aircraft,latitude,longitude,baroAltitude,geoAltitude,numMeasurements,measurements` |
| `subset_1/set_1_sensors.csv` | `serial,latitude,longitude,height,type,good` |
| `subset_1/set_1_aircraft.csv` | `aircraft,trusted` |
| `subset_1/LICENSE.txt` | Creative Commons Attribution-ShareAlike 4.0 legal text |

An actual measurement value has the form:

```text
[sensor serial, receiver timestamp, RSSI]
[208,962354640,98]
```

The main row supplies a precomputed transmission group and an aircraft-reported
position. It does not supply the Mode-S payload used by the authors when they
formed that group. The [LocaRDS paper](https://www.mdpi.com/1424-8220/21/16/5516)
explains the grouping and timing preparation. Its nanosecond unit does not mean
that every receiver has one-nanosecond accuracy.

The archive has no `clock_source` or numeric `clock_uncertainty_ns`. Sensor
`type` names hardware, not its clock source. `good` identifies receivers whose
timing did not show drift during the one-hour recording and whose locations
could be jointly verified; it does not establish zero offset or the production
100 ns bound. The Phase 1 diagnostic's calibrated held-out residual statistics
also cannot be converted into a per-receiver hardware uncertainty declaration.

Result: public LocaRDS remains **NO-GO** for the unchanged production pipeline.
It remains useful only for the separately labelled solver diagnostic already
documented in [locards-suitability-audit.md](locards-suitability-audit.md).

## OpenSky Findings

OpenSky is the most promising historical source because the official
[FAQ](https://opensky-network.org/about/faq) says its internal archive stores
receiver positions, reception timestamps, and raw ADS-B messages and can
provide data down to individual transmissions. That statement establishes
internal availability, not access approval or clock suitability.

The currently documented interfaces do not provide a complete observation:

- The [Trino documentation](https://openskynetwork.github.io/opensky-api/trino.html)
  lists the current tables. State vectors are derived from raw Mode-S messages,
  use seconds for time, and may list sensor serials. The decoded message tables
  summarize duplicates through first/last time and count. The documented
  `readsb_mlat_sv` table contains already-solved MLAT latitude/longitude.
- The [REST API](https://openskynetwork.github.io/opensky-api/rest.html) exposes
  state vectors rather than per-receiver raw arrivals.
- The public [scientific data page](https://opensky-network.org/data/scientific)
  says the raw sample has receiver locations removed.
- The official [raw sample repository](https://github.com/openskynetwork/osky-sample)
  shows useful fields such as `rawMessage`, `sensorSerialNumber`,
  `timeAtSensor`, and nullable receiver coordinates. Those times are doubles,
  and the sample supplies no current clock-source, calibration-validity, or
  uncertainty contract.

OpenSky therefore has two different classifications:

- Existing public interfaces and samples: **NO-GO**.
- A purpose-made, authorized extract with all missing timing evidence:
  **CONDITIONAL GO**.

### OpenSky Requirement Availability

These labels distinguish what OpenSky says it stores from what the currently
documented public products expose:

| Requirement | Internal archive | Current public/Trino/REST access | Meaning for this project |
|---|---|---|---|
| Original Mode-S/ADS-B frame | **AVAILABLE**, according to the official FAQ | **PARTIALLY AVAILABLE** only in the anonymized raw sample; **NOT AVAILABLE** in the documented REST/state-vector interfaces | Must be included in an approved extract. |
| Per-receiver reception timestamp | **AVAILABLE**, according to the official FAQ | **PARTIALLY AVAILABLE** in the raw sample as nullable doubles; **NOT AVAILABLE** as receiver TDOA arrivals in current documented Trino state-vector/decoded aggregates | Exact representation, resolution, and comparability require confirmation. |
| Stable receiver identifier | **AVAILABLE** as a sensor serial in the raw schema | **PARTIALLY AVAILABLE**; state vectors can list serials and the raw sample has `sensorSerialNumber` | A serial is source identity, not a CKB identity. |
| Receiver latitude/longitude/altitude | **AVAILABLE**, according to the FAQ/raw schema | **NOT AVAILABLE** in the current anonymized raw sample; not attached to per-receiver arrivals in the documented APIs | Release depends on privacy approval. |
| Multiple receivers for one original frame | **AVAILABLE** in principle because OpenSky performs MLAT and archives individual receptions | **NOT AVAILABLE** as a contract-complete public event set | A sample must prove the grouping and receiver count. |
| Clock source | **UNKNOWN** | **NOT AVAILABLE** in the documented public schemas | Must be supplied or the source remains no-go. |
| Clock calibration and validity interval | **UNKNOWN** | **NOT AVAILABLE** | Must be supplied and explained without using validation truth for tuning. |
| Per-receiver clock uncertainty <=100 ns | **UNKNOWN** | **NOT AVAILABLE** | This is the decisive production gate. Precision units or a quality flag are not substitutes. |
| ADS-B ground truth | **AVAILABLE** for suitable position-bearing frames | **AVAILABLE** in state vectors and LocaRDS, with normal ADS-B truth limitations | Must be kept out of held-out solving and used only for scoring. |
| Historical access authorization | **PARTIALLY AVAILABLE** after reviewed application | **PARTIALLY AVAILABLE** to eligible university/government/aviation research users; private/commercial users must request a licence | Access has not been granted to this project. |
| Live operational use authorization | **UNKNOWN** for this proposed receiver-level feed | **NOT AVAILABLE** under default terms; a written agreement is required | Do not build against or operate an OpenSky service without approval. |

## Other Source Findings

### ADS-B Exchange

The official [data-products page](https://www.adsbexchange.com/data-products/)
describes live and historical **aircraft positions**, delivered by API,
streaming, JSON, or CSV. It explicitly describes ongoing subscriptions and
says one-time project extracts are not offered. No documented product carries
the underlying receiver/frame/arrival tuples. Result: **NO-GO**.

### FlightAware

[Firehose](https://www.flightaware.com/firehose/documentation) streams flight
positions, including ADS-B and positions already calculated by FlightAware's
MLAT system. It is not a receiver-observation feed. AeroAPI and Firehose are
licensed commercial products, and FlightAware's
[terms](https://www.flightaware.com/about/termsandconditions) restrict use and
redistribution according to the order. Result for network products: **NO-GO**.

FlightAware's official
[PiAware configuration documentation](https://www.flightaware.com/adsb/piaware/advanced_configuration)
and [local streaming guide](https://support.flightaware.com/hc/en-us/articles/37944925213975-Streaming-Data-from-your-ADS-B-Receiver)
confirm that a receiver operator can access its own local raw Beast output,
normally on port 30005. That solves frame transport, not clock qualification.
An operator-owned, GPS-qualified installation is a **CONDITIONAL GO** after
permission and evidence. Access to a provider-owned FlightFeeder must not be
assumed to be authorized.

### Airplanes.live

The public service exposes aircraft and solved MLAT positions. Its
[privacy policy](https://airplanes.live/privacy/) confirms that it receives a
unique feeder ID, precise receiver location, and received flight data, while
keeping precise locations private. Its own
[MLAT explanation](https://airplanes.live/what-is-ads-b/) says timestamped
Mode-S input is used internally. There is no published raw multi-receiver
extract, no per-receiver clock uncertainty contract, and no clear licence for
this proposed raw-data reuse. Public access is **NO-GO**; a specifically
authorized extract is **CONDITIONAL GO**.

### ADSB.lol

The public [API](https://www.adsb.lol/docs/open-data/api/) and
[historical files](https://www.adsb.lol/docs/open-data/historical/) are
aircraft-state products licensed under ODbL 1.0. The experimental
[feeder-only Beast output](https://www.adsb.lol/docs/feeders-only/beast-mlat-out/)
contains aggregated raw frames, but a standard Beast frame does not identify
which original receiver supplied it. Receiver geometry and clock evidence are
not attached. Result for all currently published outputs: **NO-GO**.

### 4DSKY

The official
[4DSKY MLAT challenge](https://github.com/NeuronInnovations/4dsky-mlat-challenge)
documents a structured P2P record containing sensor ID, sensor latitude,
longitude and altitude, time as seconds-since-midnight plus nanoseconds, and
the raw Mode-S bytes. This is the closest published live schema to the current
application contract. The [4DSKY site](https://www.4dsky.com/) advertises 30 ns
GPS-time synchronization for current Jetvision sensors.

Important gaps remain. The challenge says buyer credentials and exact seller
locations were made available for a hackathon; it does not establish current
access. The record does not carry a documented per-sensor clock source,
calibration validity window, evidence artifact, or uncertainty value. The site
claim cannot silently become `clock_uncertainty_ns=30`. No current data licence
or pilot-use terms were found. Result: **CONDITIONAL GO**, pending a written
agreement and a sample that proves every missing field.

### Other Academic Datasets

The OpenSky scientific catalog and targeted searches of public research
repositories were reviewed. Other discoverable datasets were flight
trajectories, aircraft state vectors, aggregated kinematic measurements, or
single-receiver collections. They do not retain four receiver-level arrivals
for one original frame with qualified clocks and coordinates. No additional
production-compatible public historical dataset was found. This is a bounded
search result, not proof that no private or unindexed dataset exists.

## Licensing And Access Constraints

| Source | Confirmed constraint |
|---|---|
| LocaRDS | CC BY-SA 4.0 permits use and adaptation, including commercial use, with attribution and ShareAlike obligations when adapted material is shared. This licence does not create missing technical fields. |
| OpenSky | The current [Terms of Use](https://opensky-network.org/about/terms-of-use) permit approved non-profit research/education under conditions. Private or commercial entities require written permission and a licence. Operational REST use requires a written agreement even for non-profits. Non-anonymized publication must protect sensor locations, data cannot be redistributed outside the authorized institute, collaborators generally apply separately, and citation is required. |
| ADS-B Exchange | Data products are commercial subscriptions. Use, retention, publication, and redistribution are limited by the purchased agreement. No raw receiver-observation product was found. |
| FlightAware | API/Firehose use and redistribution are controlled by the product order and licence. Local access does not automatically authorize use of provider-owned hardware or network-returned data. |
| Airplanes.live | Precise feeder locations are explicitly private. Terms for supplying a raw research extract were not located, so permission is **UNKNOWN** and must be written before access. |
| ADSB.lol | Public API, history, and feeder-only aggregate output pages identify ODbL 1.0. Feeder access controls must be respected. The network's separate CC0 feeder contribution language does not repair missing per-frame provenance. |
| 4DSKY | Access is credentialed. A code-repository licence is not a data licence. Current data use, retention, publication, commercial/pilot use, and seller-location permission are **UNKNOWN**. |
| Direct operators | Obtain explicit permission covering capture, processing, retention, publication of metrics, any redistribution, receiver-coordinate handling, and CKB identity registration. A network's terms do not replace the physical operator's authority, and operator consent does not grant access to provider-owned equipment. |

## Ranked Paths

| Rank | Path | Why it ranks here | Current status |
|---:|---|---|---|
| 1 | LocaRDS/OpenSky maintainer-provided historical extract | Best reproducibility, known overlapping network and ADS-B truth, and OpenSky confirms the underlying archive has frames/times/receiver positions. It avoids buying hardware. Clock evidence, access, privacy, and CKB scope remain unresolved. | **CONDITIONAL GO** |
| 2 | Four or more direct GPS-qualified receiver operators | Strongest complete product demonstration because real operators can consent, control their CKB identities, and provide local raw frames. Existing Beast tooling reduces implementation work. Recruitment, overlapping geometry, ground truth, and clock evidence make it less reproducible and slower than a historical extract. | **CONDITIONAL GO** |
| 3 | Authorized 4DSKY raw P2P feed | Published record is technically close and hardware is advertised as GPS synchronized. Current access, simultaneous seller count, exact timing evidence, data licence, and CKB binding are unresolved. | **CONDITIONAL GO** |
| 4 | Authorized Airplanes.live or ADSB.lol maintainer extract | Their MLAT infrastructure implies internal receiver observations, but no suitable export contract or clock evidence is published. | **CONDITIONAL GO** |
| 5 | Existing position/state-vector APIs and historical products | Easy to access, but they have already removed the observation information needed to perform genuine MLAT. | **NO-GO** |

No rank is a claim that access has been granted.

## Recommended Source

Request a small, fixed OpenSky historical extract first. The request should be
narrow enough for review: one geographic area, a short time range, and only
events with at least four receivers. Ask for a schema and a tiny sample before
requesting the full benchmark window.

This path becomes **GO** only after all of these are received and verified:

1. Original Mode-S frame bytes for each receiver reception.
2. A stable receiver identifier preserved for each reception.
3. Receiver latitude, longitude, and altitude under an approved privacy plan.
4. Receiver arrival timestamps whose units, epoch/counter semantics, and
   resolution are documented.
5. Clock source and calibration method for every included receiver.
6. A defensible per-receiver uncertainty at or below 100 ns, with its meaning,
   confidence/bound convention, validity interval, and evidence.
7. At least four distinct eligible receivers observing the same original frame,
   with enough six-plus-receiver events to study the geometry issue found in
   Phase 1.
8. Independent aircraft position truth that was not used to generate the
   observations or tune validation-period calibration.
9. Written permission covering this research/pilot use, retention, derived
   metrics, publication, and any commercial or grant demonstration context.
10. A legitimate identity mapping. Historical pseudonyms may be preserved as
    source IDs, but they cannot be represented as receiver-operator-owned CKB
    identities without authorization. Any custodian-controlled dataset identity
    must be clearly labelled and must not be presented as physical ownership.

If OpenSky cannot provide items 4-6, the historical path remains a solver-only
diagnostic and must stop. The next technical source should then be direct
operators with GPS-qualified receivers, not an aircraft-position API.

## Decision

**CONDITIONAL GO**

There is a legitimate path worth pursuing, but no evaluated source is a GO
today. The condition is receipt and verification of a source-complete sample,
clock evidence, permission, and a truthful CKB identity plan. Production code
and adapters must remain unchanged until those conditions are met.
