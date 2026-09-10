# Recruitment Pipeline

## Cohort

Recruit to complete six sessions:

| Category | Primary participants | Backup | Diversity rule |
|---|---:|---:|---|
| Receiver operators | 4 | 1 | Use at least three networks or communities |
| Coordinators or developers | 2 | 1 | Use two different organizations or projects |

Prioritize people with direct experience of replacement, transfer, retirement,
relocation, network migration, multi-network inventory, provenance, or feed
integration. Public activity makes someone a lead. It does not prove current
eligibility, interest, or participation.

The first screening slate is:

- Operators: `u/NeroB18`, Eliel Felipe Junior, Michael Russo, and Albert Zrim.
- Operator backup: `Dahugo`.
- Coordinators or developers: James Dunthorne and Katia (`@iakat`).
- Coordinator or developer backup: Chris Portscheller (`@cport1`).

This is an outreach order, not a participant list. No person above has agreed to
take part.

## Required states

Every person moves through only evidence-supported states:

```text
LEAD -> CONTACTED -> PERMISSION REQUESTED -> INVITED -> INTERESTED
     -> CONFIRMED -> SCHEDULED -> PILOT RUN -> INTERVIEWED -> FOLLOW-UP
     -> POTENTIAL CLIENT -> PARTNER / INTEGRATION

Any active state -> DECLINED
```

Direct outreach can skip `PERMISSION REQUESTED` when the public contact route
allows a personal message. Community posts cannot skip it. Record dates in ISO
format. A reaction, like, general compliment, or third-party referral is not
interest. `CONFIRMED` requires the person's own agreement to the time commitment
and testnet conditions.

## Tracker fields

The CSV records name or handle, organization or community, role, public
experience evidence, relevant problem, contact channel, permission, contact
date, response, interest, pilot status, schedule, follow-up, opportunity, and
notes. Do not add private credentials, private feed URLs, IP addresses, seed
phrases, keys, passwords, or an exact private receiver location.

## A. Initial permission request

> Hello. I am Jeremic, an independent developer building CKB Receiver Registry
> V2 with an MLAT reference application. It gives an ADS-B or Mode S receiver one
> persistent identity while its metadata, owner, network, or lifecycle changes.
>
> I am contacting you because your community has practical experience operating
> or coordinating receivers. I am testing whether cross-network identity and
> inspectable ownership history solve a real operational problem, and whether
> tracing an MLAT aircraft result back to its contributing receivers makes that
> value concrete.
>
> The study uses CKB testnet only. A session takes 30 to 45 minutes. It requires
> no private key, seed phrase, receiver credential, feed credential, or precise
> private location. May I share one pilot invitation in a channel you choose? I
> will use only the wording and channel you approve.

Personalize the first paragraph with the community name and one relevant public
fact. Do not mention an incentive in the opening message.

## B. Pilot invitation

> I am inviting a small group of ADS-B or Mode S receiver operators and network
> coordinators to test CKB Receiver Registry V2 with its MLAT reference app.
>
> During one 30 to 45 minute remote session, you will explore the application,
> create and manage a test receiver identity on CKB testnet, then trace an MLAT
> aircraft result back to the receivers that contributed to it. You need a
> current desktop browser and, for owner tasks, a supported CKB testnet wallet.
> Testnet funds will be provided through the normal faucet process. Never share
> a private key, seed phrase, password, feed credential, or exact private
> receiver location.
>
> I need candid feedback about what matches your real workflow, what is
> confusing, what has no value, what would block adoption, and what an API or
> integration would need. Are you willing to complete the short eligibility
> check and choose a session time?

## C. Scheduling follow-up

> Hello [name or handle]. You expressed interest in the receiver identity pilot
> on [date], but we have not selected a session time. Here is the scheduling
> link: [link]. The session takes 30 to 45 minutes and uses CKB testnet only. If
> the pilot is no longer relevant, tell me and I will close the invitation.

Send this once. Do not keep following up without a new response.

## D. Post-pilot follow-up

> Thank you for testing the Receiver Registry and MLAT workflow on [date]. I am
> checking what remained useful after the session.
>
> What was useful? What was confusing? What would you change? Would you use this
> in your current work? Would you consider integrating it? What would have to
> happen first? Would you join another test? Is there another receiver operator
> or coordinator you would be comfortable introducing?
>
> Please answer only from your own experience. A negative answer is useful and
> will not trigger more follow-up.

## Recruitment metrics

Record counts for leads, contacted, responses, interested, confirmed,
scheduled, completed, and declined. Calculate response rate as responses divided
by contacted leads. Never divide by all researched leads.
