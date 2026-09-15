# Draft Request To LocaRDS/OpenSky Maintainers

Status: draft only. Not sent.

## Suggested Subject

Request for a small receiver-level Mode-S extract for MLAT pipeline validation

## Message

Hello OpenSky/LocaRDS team,

I am developing an open-source receiver registry and a reference
multilateration (MLAT) application. I am looking for a small, legitimate
historical research extract that can test an existing production MLAT pipeline
without buying or operating a separate receiver network.

I have already evaluated the public LocaRDS v1.0 dataset. It has been very
useful for a separate solver-only diagnostic because it contains real,
pre-grouped multi-receiver observations, receiver coordinates, nanosecond-unit
timestamps, and ADS-B position truth. I am **not** treating that diagnostic as
validation of the production pipeline.

The public LocaRDS files do not contain the original Mode-S frames. They also do
not document the receiver clock source or provide a defensible numeric clock
uncertainty for each receiver. I have not treated the LocaRDS `good` flag as a
substitute for those fields.

Could OpenSky provide, or confirm whether it is possible to provide, a small
authorized extract with the following fields for each receiver reception?

- original Mode-S frame bytes or canonical hex;
- stable receiver/sensor identifier;
- receiver latitude, longitude, and altitude;
- receiver arrival timestamp;
- exact timestamp unit, epoch or counter semantics, and source resolution;
- documented receiver clock source;
- clock calibration method and applicable calibration interval;
- a defensible numeric timing uncertainty for each receiver, including whether
  it is a bound, percentile, standard deviation, or another measure;
- any identifier that groups receptions of the same original transmission, if
  available; and
- independent aircraft position truth suitable for scoring, together with its
  source and quality limitations.

For this pipeline, a production-eligible observation currently requires a
positive integer nanosecond timestamp, a documented synchronized clock source,
and per-receiver clock uncertainty no greater than 100 ns. I do not want the
dataset changed or a field inferred merely to pass this threshold. If the
archive cannot support this level of clock evidence, a clear confirmation of
that limitation would itself be useful.

For the benchmark, I would need a short fixed period in one area with:

- at least four distinct receivers observing each selected transmission;
- preferably a meaningful subset with six or more receivers, because our
  existing diagnostic found weak 3D geometry in many four-receiver cases;
- enough overlapping ADS-B-position transmissions to score horizontal,
  vertical, and 3D error; and
- a time split that allows clock calibration on one period and validation on a
  later held-out period without using validation truth for tuning.

I would first prefer only a schema description and a very small sample. I will
not build a production adapter or claim compatibility until the sample passes
the existing input validation unchanged.

The broader project links observations to CKB Receiver Registry identities.
Those on-chain records represent identity ownership and lifecycle state only;
they do not claim to prove physical receiver existence, location, clock
accuracy, or observation truth. I would preserve OpenSky sensor identifiers as
source identifiers. I would not present pseudonymous sensors as identities
owned by their physical operators without explicit authorization. Please let
me know whether a dataset-custodian identity mapping would be acceptable and
how you would want that relationship described.

Could you also clarify the permission terms for this specific use?

- non-profit research and public benchmark reporting;
- pilot and grant-demonstration use;
- any later commercial evaluation;
- local retention period;
- publication of aggregate error and receiver-count metrics;
- publication of pseudonymous contributing sensor IDs;
- handling and publication restrictions for receiver coordinates;
- sharing a minimal reproducibility fixture, if allowed; and
- required OpenSky/LocaRDS citations and attribution.

I will comply with OpenSky access controls, privacy requirements, data-use
terms, query limits, and redistribution restrictions. Collaborators will apply
separately if required. No data will be scraped or accessed without approval.

Project repository: https://github.com/Jeremicarose/AIRCRAFT-MALT

Relevant audit documents can be provided with the request:

- `docs/mlat/locards-suitability-audit.md`
- `docs/mlat/baseline-analysis.md`
- `docs/mlat/data-source-contract.md`

Thank you for considering the request. A confirmation that one or more required
fields are unavailable would also help us choose an appropriate live-operator
pilot rather than misuse an incomplete dataset.

Kind regards,

[Name]
[Affiliation, if applicable]
[OpenSky account, if applicable]
[Contact details]

## Before Sending

Fill in the identity and affiliation fields. State clearly whether the current
project is non-profit research, personal research, or connected to a commercial
entity. If pilot, grant, or later commercial use is possible, keep that wording
in the request so OpenSky can issue the correct permission instead of relying
on the default research licence.
