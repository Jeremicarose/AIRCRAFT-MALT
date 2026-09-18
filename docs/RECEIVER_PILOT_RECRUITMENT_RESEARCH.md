# CKB Receiver Registry Pilot Recruitment Research

**Research date:** 7 September 2026
**Recruitment target:** 8 written confirmations: 5 receiver operators and 3
coordinators/developers. Select 4 operators and 2 coordinators for the pilot and
retain one backup for each role.

## Current status

This document identifies public leads and legitimate ways to approach them. It
does not show that anyone is interested. No person or community was contacted
during this research, and there are currently zero confirmed participants.

A person becomes a confirmed participant only after all of these are true:

1. They explicitly say in writing that they want to participate.
2. Their relevant experience is verified.
3. They confirm the 45-minute test, 20-minute interview, and seven-day follow-up.
4. They confirm availability.
5. They acknowledge that the proposed $30 incentive depends on grant approval.

An emoji, poll response, general encouragement, or "sounds interesting" is not a
confirmation.

## Important findings before recruitment

### The ownership problem has public evidence, but it is not yet validated

A Wingbits user publicly described being both a station owner and a host. They
asked for separate owner and host accounts, invitations, per-station wallet
control, and a clearer view of each person's share. This is close to the
Registry's ownership and role hypothesis. It shows that the problem can occur in
a real receiver network. It does not prove that this user wants a separate CKB
registry or would tolerate its wallet workflow.

Evidence: [Wingbits owner/host feature request](https://feedback.wingbits.com/p/dashboard-gui-ideas-about-hosts-and-owners).

### An adjacent product already has a directory and provenance model

4DSKY describes a directory with registration, device management,
synchronisation, and a visual explorer. It also describes verifiable provenance
and sensor discovery as part of its edge network. This matters because it is
evidence that receiver discovery and coordination are real infrastructure jobs.
It also means CKB Receiver Registry is not entering an empty field. The pilot
must discover why a separate, cross-network identity is useful compared with a
network's own directory.

Evidence: [4DSKY implementation](https://docs.4dsky.com/implementation),
[ADEX overview](https://docs.4dsky.com/adex-framework/overview), and
[4DSKY network description](https://4dsky.com/).

### The incentive should not lead the message

The 2024/2025 OpenSky community survey received at least partial responses from
596 people, including 317 sensor owners. Interest in aviation and contributing
to independent, open-access data were the strongest stated motivations.
Financial gain was the weakest. Lead with the chance to improve receiver
infrastructure and influence a real product. Disclose the conditional incentive
clearly, but do not use it as the headline.

Evidence: [OpenSky community survey paper](https://journals.open.tudelft.nl/joas/article/download/8474/6520).

# A. Recruitment Strategy

## Recommended cohort

Use a two-track cohort because the two roles answer different questions:

| Role | Confirm | Pilot | Backup | What this role tests |
|---|---:|---:|---:|---|
| Current/recent receiver operator | 5 | 4 | 1 | Registration, updates, ownership, retirement, wallet burden |
| Coordinator/developer | 3 | 2 | 1 | Inventory, discovery, audit history, integration, adoption authority |

The final six should represent at least two independent ecosystems. A stronger
mix would include one reward-based network, one volunteer/open network, and one
open-source or network-infrastructure perspective.

## Priority order

1. **Warm coordinator introductions:** Ask 4DSKY, OpenSky, ADSB.lol, ADSB.im,
   and SDR Enthusiasts administrators to introduce one relevant person. A warm
   introduction is more likely to produce candid infrastructure feedback than a
   broad post.
2. **One approved post in each of two operator communities:** Start with
   Wingbits and either OpenSky or FlightAware. Do not post the same message in
   multiple channels inside one community.
3. **Personalised public-lead outreach:** Contact only people whose public work
   directly shows relevant experience. Mention the exact work that made them a
   fit. Send one follow-up at most.
4. **Referral question after screening:** Ask an eligible person whether one
   other operator or coordinator would offer a meaningfully different view.
   Do not ask for a member list or private contact data.
5. **Second wave only if needed:** Airplanes.live and r/ADSB can broaden the
   operator pool. ADS-B Exchange should be used only if its administrators give
   an explicit exception to its no-advertising rule.

## Selection rules

- Do not select more than two people whose main experience comes from the same
  network unless there are no better qualified alternatives.
- Prefer people who can describe a recent receiver change, failure, transfer,
  replacement, or retirement.
- At least one coordinator should have changed production receiver inventory or
  integration code, not only discussed it.
- Do not count the applicant, close contributors, or CKB-only developers.
- Do not treat a public candidate as interested. Public evidence establishes
  relevance only.
- Keep the proposed $30 incentive conditional on grant approval in every message
  and form.

## Recruitment funnel

```text
permission requested
  -> permission granted
  -> individual or community outreach
  -> reply
  -> eligibility verified
  -> explicit written interest
  -> availability confirmed
  -> session scheduled
  -> session completed
  -> seven-day follow-up completed
```

# B. Community List

| Priority | Community | Website and public channel | Type | Why it is relevant / likely participants | Recruitment status | Recommended public contact |
|---|---|---|---|---|---|---|
| 1 | Wingbits | [Website](https://wingbits.com/) · [official channels](https://docs.wingbits.com/introduction/official-wingbits-channels) · [Discord](https://discord.gg/zAt9m3aSm6) · [Reddit](https://www.reddit.com/r/wingbits_official/) | Reward-based ADS-B DePIN | Active station owners, hosts, wallet users, and network staff. Particularly useful for ownership and wallet questions. | Plausible only with written permission. Its security guide warns members about unsolicited DMs. | Human support through the chat on wingbits.com or `help@wingbits.com` |
| 1 | OpenSky Network | [Website](https://opensky-network.org/) · [feeders](https://opensky-network.org/feed) · [Discord](https://discord.gg/RPh89jpVVz) · [GitHub](https://github.com/openskynetwork) | Non-profit research receiver network | Volunteer sensor owners, research users, feeder maintainers, and network staff. OpenSky explicitly operates a volunteer sensor network. | Research participation appears compatible with the community, but permission for this external pilot is not published. Ask first. | `contact@opensky-network.org` or a Discord administrator |
| 1 | ADSB.im / ADS-B & SDR Feeder Image | [Website](https://adsb.im/) · [GitHub](https://github.com/dirkhh/adsb-feeder-image) · [Discord](https://discord.gg/HjaEg53VvN) | Open-source multi-feeder distribution | Operators who configure several aggregators and developers who maintain receiver identities, feed keys, and multiple local nodes. | No public recruitment rule found. Ask a Discord administrator before one post. | Discord administrator or Dirk Hohndel's public profile contact |
| 1 | SDR Enthusiasts | [GitHub](https://github.com/sdr-enthusiasts) · [guide](https://sdr-enthusiasts.gitbook.io/ads-b/) · [Discord](https://discord.gg/sTf9uYF) | Open-source receiver software community | Maintainers and technically experienced operators using Ultrafeeder, readsb, tar1090, MLAT, monitoring, and many feed clients. | No public recruitment permission found. GitHub issues are for software work, not recruitment. Ask a Discord administrator. | Discord administrator |
| 1 | ADSB.lol | [Website](https://www.adsb.lol/) · [Zulip](https://adsblol.zulipchat.com/) · [GitHub](https://github.com/adsblol) · [IRC](https://web.libera.chat/#adsblol) | Open-data ADS-B/MLAT network | Network operator, infrastructure contributors, feeder developers, and technically strong operators. The public infrastructure includes Kubernetes, readsb, and MLAT server components. | Public community, but external recruitment permission is not stated. Ask before opening one topic. | `info@adsb.lol` or a Zulip administrator |
| 1 | 4DSKY | [Website](https://4dsky.com/) · [docs](https://docs.4dsky.com/) · [Discord](https://discord.gg/X6EVsv6gDR) | Edge-native ADS-B/Mode S/MLAT network and DePIN | Sensor hosts, network coordinators, and developers already working with registration, discovery, device credentials, provenance, and integrations. | Do not begin with a broad post. Request a direct staff conversation or an introduction to one host and one infrastructure person. | `contact@neuron.world`, the [support route](https://4dsky.com/onboarding), or a Discord administrator |
| 1 | FlightAware Discussions | [ADS-B category](https://discussions.flightaware.com/c/flightaware/ads-b-flight-tracking/9) · [guidelines](https://discussions.flightaware.com/guidelines) | Commercial network's public feeder forum | Large pool of PiAware and FlightFeeder operators, including people running several sites. | Guidelines ban spam, cross-posting, and wrong-category topics. They do not explicitly approve research recruitment. Staff permission is required. | [Staff/contact route](https://www.flightaware.com/about/contact/) or `support@flightaware.com` |
| 2 | Airplanes.live | [Website](https://airplanes.live/) · [about](https://airplanes.live/about/) · [Discord](https://discord.gg/adsb) · [GitHub](https://github.com/airplanes-live) | Community-run ADS-B/MLAT aggregator | Volunteer feeders and developers maintaining feed scripts, receiver images, MLAT, and network services. | No public recruitment rule found. Ask an administrator before one post. | `contact@airplanes.live` or Discord administrator |
| 2 | r/ADSB | [Community](https://www.reddit.com/r/ADSB/) · [July 2026 rule update](https://www.reddit.com/r/ADSB/comments/1uuowzp/upcoming_changes_to_the_subreddit_rules_regarding/) | Public cross-network ADS-B discussion | Operators from many networks and independent software developers. Useful for diversity and backups. | Non-commercial personal projects are allowed, but software posts require the correct flair and AI disclosure. Paid research recruitment is not clearly covered. Use Modmail first. | [r/ADSB Modmail](https://www.reddit.com/message/compose?to=/r/ADSB) |
| 3 | ADS-B Exchange | [Community](https://www.adsbexchange.com/community/) · [Discord](https://discord.com/invite/ad8SSMpWvH) · [forum rules](https://adsbx.discourse.group/t/adsb-exchange-forum-rules/25) | Commercial ADS-B/MLAT network and feeder community | Experienced feeder operators and network staff. | The public forum rules explicitly prohibit advertisements. Do not post recruitment without a written administrator exception. | [Support centre](https://support.adsbexchange.com/hc/en-us) |

# C. Permission Requirements

## What is confirmed

- **ADSB Exchange:** its public forum says no advertisements. Treat recruitment
  as prohibited unless an administrator grants a written exception.
- **FlightAware:** its guidelines prohibit spam and cross-posting and require the
  correct category. They do not provide a research-recruitment exception.
- **r/ADSB:** non-commercial personal projects may be posted, but software posts
  have flair, history, and AI-disclosure requirements. Recruitment with an
  incentive is ambiguous, so Modmail approval is necessary.
- **Wingbits:** its security guide tells users to distrust unsolicited DMs and
  says official support will not DM first. Do not contact a list of Discord
  members. Ask the team to approve one post or make introductions.

## What is not confirmed

No public rule was found that expressly permits external participant recruitment
in Wingbits Discord, OpenSky Discord, ADSB.im Discord, SDR Enthusiasts Discord,
ADSB.lol Zulip, 4DSKY Discord, or Airplanes.live Discord. Being able to join a
public server is not permission to recruit there.

For each of these communities, save the moderator's written answer in the
tracker. Record the approved channel and any required wording. One approval is
valid only for the channel and message the moderator approved.

# D. Candidate Shortlist

These are leads, not volunteers and not confirmed participants. No exact
receiver locations or private contact details are included.

| Candidate | Role | Community | Public evidence of experience | Public profile | Recommended contact method | Priority |
|---|---|---|---|---|---|---|
| James Dunthorne | Coordinator / potential partner | 4DSKY / Neuron | Publicly identifies as Neuron co-founder and describes a multi-sensor ADS-B, Mode S, FLARM, UAT, and MLAT network. 4DSKY documents device registration, discovery, and provenance. | [LinkedIn](https://uk.linkedin.com/in/jamesdunthorne) · [4DSKY](https://4dsky.com/) | One tailored LinkedIn message or the organisation contact address. Ask for a coordinator interview, not endorsement. | P1 |
| Katia (`@iakat`) | Network developer / coordinator | ADSB.lol | ADSB.lol identifies the service as operated by `@iakat`; public repositories cover its GitOps infrastructure, feed client, API, readsb, and MLAT server. | [GitHub](https://github.com/iakat) · [ADSB.lol GitHub](https://github.com/adsblol) | Zulip private message or `info@adsb.lol`. Do not open a GitHub issue for recruitment. | P1 |
| Dirk Hohndel (`@dirkhh`) | Open-source developer and operator | ADSB.im / SDR Enthusiasts | Maintains the ADS-B/SDR Feeder Image for many single-board computers and aggregators; public 2026 support posts also show hands-on operation and testing. | [GitHub](https://github.com/dirkhh) · [project](https://github.com/dirkhh/adsb-feeder-image) | Public Mastodon address on GitHub or an administrator-approved Discord message. | P1 |
| Ramon F. Kolb (`@kx1t`) | Open-source infrastructure developer | SDR Enthusiasts | Principal author of ADSB-Ultrafeeder, which combines readsb, tar1090, monitoring, multi-feeder support, and an MLAT hub; also maintains Planefence. | [GitHub](https://github.com/kx1t) · [Ultrafeeder](https://github.com/sdr-enthusiasts/docker-adsb-ultrafeeder) | Contact route on the public profile or Planefence README. Do not use an unrelated issue. | P1 |
| Chris Portscheller (`@cport1`) | Receiver-network product developer | SkyTracker / r/RTLSDR | Publicly demonstrated an early receiver network with station profiles, uptime, histories, leaderboards, and a shared station map. This is directly adjacent to receiver inventory and discovery. | [GitHub](https://github.com/cport1) · [public discussion](https://www.reddit.com/r/RTLSDR/comments/1rydz4u/i_started_building_out_an_adsb_network_with/) | One Reddit or GitHub-profile contact referencing the station-profile work. | P1 |
| Michael Russo (`@mrusso`) | Multi-site operator and app developer | FlightAware | Publicly states that he is a long-time PiAware feeder with three sites and built an app that handles multiple receivers. Posted 5 September 2026. | [FlightAware discussion](https://discussions.flightaware.com/t/overhead-1090-a-native-iphone-ipad-apple-tv-viewer-for-your-piaware-receiver/100718) | FlightAware forum private message after staff permission, or the app's public contact route. | P1 |
| Eliel Felipe Junior | OpenSky operator and developer | OpenSky Network | The 2026 OpenSky Symposium lists his work on operating a volunteer OpenSky node in Brazil. His public site describes a Raspberry Pi homelab with ADS-B feeds and an app consuming its data. | [Website](https://elielfelipe.com.br/) · [OpenSky programme](https://symposium.dev.opensky-network.org/) | LinkedIn, which his public site names as the preferred first contact. | P1 |
| `u/NeroB18` | Current receiver operator | Wingbits / GEODNET | Publicly stated in May 2026 that they had operated a dual Wingbits/GEODNET station since June 2025 and described setup changes and observed rewards. | [Evidence thread](https://www.reddit.com/r/Nordic_Crypto/comments/1t7z5ba/wingbits_review_earn_wings_by_tracking_flights/) · [profile](https://www.reddit.com/user/NeroB18/) | One personalised Reddit message. Do not infer any other identity or contact address. | P1 |
| Mike Nye (`@mikenye`) | Open-source receiver infrastructure developer | SDR Enthusiasts / Plane.watch | Public SDR Enthusiasts credits identify him as a base-image and guide maintainer; his public work includes a BEAST/MLAT authentication proxy for Plane.watch. | [GitHub](https://github.com/mikenye) · [SDR Enthusiasts](https://github.com/sdr-enthusiasts) | Public Discord listed on the GitHub profile, after checking the server's recruitment rule. | P2 |
| `@wiedehopf` | ADS-B/MLAT software maintainer | Open-source / FlightAware | Maintains readsb, tar1090, graphs1090, installation tooling, and receiver guides used by several global networks. | [GitHub](https://github.com/wiedehopf) · [readsb](https://github.com/wiedehopf/readsb) | FlightAware forum private message or a community-approved Discord introduction. Never use a bug issue as a recruitment route. | P2 |
| Fredrik Hedgren (`fredrik.hedgren`) | Multi-station owner/host | Wingbits | Public Wingbits feedback says they are both a host and owner of stations and describes owner/host invitations and per-station wallet needs. The post is about two years old, so current operation must be screened. | [Wingbits feedback](https://feedback.wingbits.com/p/dashboard-gui-ideas-about-hosts-and-owners) | Ask Wingbits staff for an introduction. Do not guess an email address from the username. | P2 |
| Albert Zrim (`OE6VAG`) | Current receiver operator | Independent / ADS-B Exchange | Public station documentation describes a current 24/7 Raspberry Pi ADS-B receiver using dump1090, tar1090, graphs1090, and an ADS-B Exchange feed. | [Station documentation](https://oe6vag.net/radio-monitoring/) · [contact page](https://oe6vag.net/navigation/) | One message through the website contact form. | P2 |
| `Dahugo` | Current dual-band operator | FlightAware | In June 2026, publicly described building a 978 UAT receiver and preparing to operate a separate 1090 receiver. | [FlightAware discussion](https://discussions.flightaware.com/t/problems-claiming-piaware-station/100525) | FlightAware forum private message after staff permission. Do not use contact details quoted inside old posts. | P2 |

## Candidate scores

Scores measure fit for this pilot, not personal worth. They are based only on
public evidence. `R` is relevance, `E` is hands-on experience, `V` is likely
product-validation value, `D` is contribution to community diversity, and `A`
is accessibility through a legitimate public route.

| Candidate | R | E | V | D | A | Total / 25 |
|---|---:|---:|---:|---:|---:|---:|
| James Dunthorne | 5 | 5 | 5 | 5 | 4 | 24 |
| Katia (`@iakat`) | 5 | 5 | 5 | 4 | 5 | 24 |
| Dirk Hohndel | 5 | 5 | 5 | 4 | 5 | 24 |
| Ramon F. Kolb | 5 | 5 | 5 | 4 | 5 | 24 |
| Eliel Felipe Junior | 5 | 4 | 5 | 5 | 5 | 24 |
| Michael Russo | 5 | 5 | 5 | 4 | 4 | 23 |
| Mike Nye | 5 | 5 | 5 | 4 | 4 | 23 |
| Albert Zrim | 5 | 4 | 4 | 5 | 5 | 23 |
| Chris Portscheller | 5 | 4 | 5 | 4 | 4 | 22 |
| `u/NeroB18` | 5 | 4 | 4 | 5 | 4 | 22 |
| `@wiedehopf` | 5 | 5 | 5 | 4 | 3 | 22 |
| Fredrik Hedgren | 5 | 4 | 5 | 5 | 2 | 21 |
| `Dahugo` | 5 | 3 | 4 | 4 | 4 | 20 |

## First-choice balanced slate to screen

This is a screening order, not a claim that these people will participate:

- Wingbits operators: `u/NeroB18`, then Fredrik Hedgren if Wingbits can make an
  introduction and current operation is verified.
- Independent/volunteer operators: Michael Russo, Eliel Felipe Junior, Albert
  Zrim, and `Dahugo`.
- Coordinators/developers: one of James Dunthorne or Chris Portscheller for the
  adjacent-product view; one of Katia, Dirk Hohndel, Ramon F. Kolb, Mike Nye, or
  `@wiedehopf` for open-source infrastructure.

# E. Outreach Plan

## Step 1: Prepare the intake before posting

Create one form and one public project-information page. The page should state
the independent status of the project, testnet-only use, privacy limits,
conditional incentive, time commitment, researcher contact, and how notes will
be used in a grant proposal. Do not collect exact receiver locations or any
credentials.

## Step 2: Ask for permission in parallel

Send permission requests to Wingbits, OpenSky, ADSB.im/SDR Enthusiasts,
ADSB.lol, 4DSKY, FlightAware, Airplanes.live, and r/ADSB. Do not publish while
waiting. Record the answer, approver, channel, and date.

## Step 3: Use each community differently

- **Wingbits:** ask staff to place or approve one post in an operator channel.
  Ask whether staff can privately forward the invitation to the public
  owner/host feature-request author. Do not browse the server member list or DM
  members.
- **OpenSky:** ask for one post in the feeder/community channel and one
  introduction to someone who understands sensor inventory. Mention that this
  is product validation, not OpenSky-sponsored research.
- **ADSB.im / SDR Enthusiasts:** ask for one post in the ADSB.im or general
  feeder channel. Separately invite no more than two maintainers whose public
  work matches the pilot.
- **ADSB.lol:** ask the administrator whether a single Zulip topic is suitable.
  Invite one infrastructure maintainer, not every contributor.
- **4DSKY:** begin with a direct organisation email. Ask for one coordinator
  session and, if appropriate, an introduction to one sensor host. A broad
  community post is unnecessary unless the team recommends it.
- **FlightAware:** request staff approval for one topic in ADS-B Flight
  Tracking. Do not reply to unrelated help threads. After approval, privately
  contact only the two or three shortlisted forum users.
- **Airplanes.live:** ask a Discord administrator whether one feeder-focused
  post is acceptable. Use it only if the first wave lacks independent-network
  operators.
- **r/ADSB:** use Modmail. If approved, follow the exact flair and disclosure
  instructions. Do not cross-post to r/RTLSDR and other subreddits.
- **ADS-B Exchange:** do not post under the current forum rule. Only proceed if
  support gives a written exception and specifies where the post belongs.

## Step 4: Pace individual outreach

- Send no more than six personalised invitations in one day.
- Refer to one specific public project, receiver, or discussion.
- Do not mention a person's location, even when a public receiver map exposes it.
- Wait five business days before one short follow-up.
- Stop after a decline, no response to the follow-up, or any request not to
  contact them.
- Never ask an administrator for a member export or private email list.

## Step 5: Screen before scheduling

Apply the same eligibility test to every lead. Record evidence using a
pseudonymous participant ID. A public profile URL is enough for recruitment
tracking; do not copy public pages into a private dossier.

## Step 6: Protect cohort quality

Review the slate after every three confirmations. If one ecosystem is beginning
to dominate, pause that source and recruit from a different network. Select the
pilot six only after all eight confirmations are available.

# F. Messages

## Permission request: Wingbits

> Hello. I am Jeremic, an independent developer preparing a small
> product-validation pilot for CKB Receiver Registry. It is a browser-based tool
> for receiver identity, metadata updates, ownership changes, discovery, and
> retirement on CKB testnet.
>
> I would like to invite a small number of current Wingbits station operators to
> one 45-minute test, one 20-minute interview, and a short follow-up. The project
> is independent and is not affiliated with or sponsored by Wingbits. No station
> credentials, exact locations, private feeds, private keys, or seed phrases will
> be requested. The proposed $30 completion incentive is conditional on grant
> approval.
>
> Would one recruitment post be permitted? If so, which single channel and wording
> would you prefer? I will not DM server members or post in multiple channels.

## Permission request: OpenSky Network

> Hello. I am an independent developer validating a browser-based registry for
> ADS-B/Mode S receiver identity and lifecycle on CKB testnet. I am looking for a
> few current or recent receiver operators and one person familiar with
> multi-receiver inventory or feeder infrastructure.
>
> This is independent research and is not affiliated with OpenSky. Participation
> is one 45-minute product test, one 20-minute interview, and a short follow-up.
> I will not request credentials, feeds, exact locations, private keys, or seed
> phrases. The proposed $30 incentive is conditional on grant approval.
>
> May I share one participant call in the community? If yes, which channel is
> appropriate, and would an administrator prefer to post it?

## Permission request: ADSB.im / SDR Enthusiasts

> Hello. I maintain an independent testnet prototype for persistent ADS-B
> receiver identity, metadata changes, ownership transfer, discovery, and
> retirement. I am seeking a few hands-on feeder operators and one maintainer for
> a small product-validation pilot.
>
> The work is not affiliated with ADSB.im or SDR Enthusiasts. It requires a
> 45-minute browser test, a 20-minute interview, and one short follow-up. No feed
> keys, receiver credentials, exact locations, private feeds, private keys, or
> seed phrases will be requested. A proposed $30 completion incentive depends on
> grant approval.
>
> Would one post be acceptable here? Please tell me the single correct channel and
> any wording or disclosure you require. I will not use GitHub issues or DM the
> member list.

## Permission request: ADSB.lol

> Hello. I am an independent developer preparing a small validation pilot for a
> browser-based ADS-B receiver registry on CKB testnet. I am looking for current
> receiver operators and a maintainer who understands multi-receiver discovery,
> inventory, or MLAT infrastructure.
>
> This project is not affiliated with ADSB.lol. Participation is a 45-minute
> product test, a 20-minute interview, and a short follow-up. No credentials,
> exact receiver locations, private feeds, private keys, or seed phrases will be
> requested. The proposed $30 incentive is conditional on grant approval.
>
> May I open one recruitment topic in this Zulip organisation? If so, which stream
> should I use?

## Permission request: 4DSKY

> Hello. I am Jeremic, an independent developer validating CKB Receiver Registry,
> a testnet prototype for persistent receiver identity, owner-authorised updates,
> discovery, transfer, and retirement.
>
> 4DSKY's public work on ADEX discovery, registration, device management, and
> provenance is directly relevant. I would value one candid session with a person
> responsible for sensor or network coordination and, if appropriate, one sensor
> host. The purpose is to test whether a separate cross-network registry solves a
> real problem, not to request endorsement or claim a partnership.
>
> Participation is a 45-minute product test, 20-minute interview, and short
> follow-up. No credentials, exact locations, feeds, private keys, or seed phrases
> are requested. The proposed $30 incentive is conditional on grant approval.
> Would the team be open to this, or willing to suggest the correct contact?

## Permission request: FlightAware

> Hello. I am an independent developer preparing a small product-validation pilot
> for an ADS-B/Mode S receiver identity and lifecycle tool on CKB testnet. I would
> like to make one participant call for current or recent receiver operators in
> the ADS-B Flight Tracking category.
>
> The project is not affiliated with FlightAware. Participation includes a
> 45-minute test, a 20-minute interview, and a short follow-up. No FlightAware or
> receiver credentials, private feeds, exact locations, private keys, or seed
> phrases will be requested. The proposed $30 incentive is conditional on grant
> approval.
>
> Would staff permit one topic? If so, please confirm the category and any wording
> or link restrictions. I will not cross-post or recruit inside unrelated support
> threads.

## Permission request: Airplanes.live

> Hello. I am an independent developer validating a browser-based registry for
> persistent ADS-B receiver identity, metadata changes, ownership, discovery, and
> retirement using CKB testnet.
>
> I am looking for a small number of active feeder operators and one open-source
> infrastructure maintainer. This project is not affiliated with Airplanes.live.
> It involves a 45-minute test, a 20-minute interview, and a short follow-up. No
> credentials, exact receiver locations, private feeds, private keys, or seed
> phrases will be requested. The proposed $30 incentive is conditional on grant
> approval.
>
> May I share one recruitment post? If so, which single Discord channel is
> appropriate?

## Permission request: r/ADSB

> Hello moderators. I am an independent developer preparing a small
> product-validation pilot for CKB Receiver Registry, a browser-based ADS-B/Mode S
> receiver identity and lifecycle prototype on testnet.
>
> I would like to make one post seeking current/recent receiver operators and
> receiver-network developers. Participation is a 45-minute test, a 20-minute
> interview, and a short follow-up. No credentials, exact locations, feeds,
> private keys, or seed phrases will be requested. The proposed $30 incentive is
> conditional on grant approval. The project is not affiliated with Reddit or any
> receiver network.
>
> Does this fit the community's rules? If approved, please tell me the required
> flair, AI-assistance disclosure, and whether an external screening-form link is
> allowed. I will not cross-post it to other subreddits.

## Permission request: ADS-B Exchange

> Hello. I saw that the public forum rules prohibit advertisements, so I will not
> post a recruitment call without a written exception. I am an independent
> developer running a small product-validation pilot for an ADS-B receiver
> identity and lifecycle prototype on CKB testnet.
>
> Would the team consider allowing one clearly labelled research-participant call
> in a channel you choose? It would request no credentials, private feeds, exact
> locations, private keys, or seed phrases. The proposed $30 incentive is
> conditional on grant approval. If this is not allowed, no response or exception
> is expected and I will not post.

## Recruitment message after permission

> **ADS-B / Mode S receiver operators and network maintainers wanted for a small
> product test**
>
> I am Jeremic, an independent developer building CKB Receiver Registry. It is a
> browser-based prototype for giving a receiver a persistent identity while its
> metadata, owner, or operating status changes.
>
> I am looking for people who currently operate an ADS-B/Mode S receiver, operated
> one within the last 12 months, or maintain software/inventory for multiple
> receivers. I want candid feedback on whether this solves a real coordination
> problem and which parts are unnecessary.
>
> Participation is voluntary and includes one remote product-testing session of
> up to 45 minutes, one interview of up to 20 minutes, and one short follow-up
> within seven days. Testing uses CKB testnet; no real funds are needed.
>
> I will not request receiver-network credentials, feed keys, private feeds,
> exact receiver locations, private keys, seed phrases, or exchange credentials.
> The project is independent and is not sponsored by this community or any
> receiver network.
>
> A proposed $30 incentive after completing all three parts is conditional on
> grant approval, so payment is not guaranteed at this stage.
>
> To express interest, please complete [screening form link] or contact me at
> [public project email]. Completing the form expresses interest; it does not
> commit you to participate.

## Personalised candidate invitation

> Hello [name/handle]. I found your public work on [specific receiver, project, or
> infrastructure contribution]. That experience is why I am contacting you.
>
> I am an independent developer validating CKB Receiver Registry, a browser-based
> testnet prototype for persistent receiver identity, owner-authorised updates,
> discovery, transfer, and retirement. I am looking for candid feedback from
> people who have actually operated or coordinated receiver infrastructure.
>
> The commitment is one remote test of up to 45 minutes, a 20-minute interview,
> and one short follow-up within seven days. No credentials, exact locations,
> private feeds, private keys, or seed phrases are requested. A proposed $30
> completion incentive is conditional on grant approval.
>
> Would you be open to the short screening form? A "no" is completely fine, and I
> will not follow up if this is not relevant.

## One permitted follow-up

> Hello [name/handle]. I am following up once on the receiver-registry pilot
> invitation I sent on [date]. I am closing recruitment on 30 September. If it is
> not relevant, no reply is needed and I will not contact you again.

# G. Screening Form

Use branching so coordinator-only questions do not burden single-receiver
operators.

1. Do you currently operate an ADS-B/Mode S receiver, or have you operated one
   within the last 12 months? If yes, when was it last active?
2. What receiver hardware and software do you use or maintain?
3. Do you manage one receiver or multiple receivers? Please give only the count;
   do not provide exact locations.
4. Which receiver networks or communities are you involved with?
5. How do you currently track receiver identity, ownership, host, and operating
   status?
6. Have you ever had to update, transfer, replace, or retire a receiver? Briefly
   describe the most recent example without sharing credentials or a precise
   location.
7. Are you willing to participate in one remote product-testing session of up to
   45 minutes?
8. Are you willing to participate in one interview of up to 20 minutes?
9. Are you willing to complete one short follow-up within seven days?
10. Are you comfortable using CKB testnet? No real funds are required, and you
    will not be asked to share a private key or seed phrase.
11. Do you understand that the proposed $30 completion incentive is conditional
    on grant approval and is not currently guaranteed?
12. **For coordinators/developers:** What work have you done with multiple
    receivers, MLAT, feeder management, inventory, monitoring, or receiver-network
    software?
13. Which non-sensitive evidence may be used to verify your experience: a public
    profile/project link, a redacted status screenshot, or a redacted receiver
    photograph? Evidence will not be published without separate consent.
14. What time zone and general time windows work for a remote session? Do not
    provide a home address or receiver location.
15. May the researcher contact you about this pilot using the contact method you
    provide? Participation is voluntary and you may stop at any time.

The form must not ask for a private key, seed phrase, exchange login, receiver
network login, feed key, private feed URL, IP address, or exact receiver location.

# H. Recruitment Tracker

The maintainer-local working CSV is `artifacts/receiver-pilot-tracker.csv`.
It is intentionally excluded from source control because it may contain contact
and recruitment status data. It contains the requested funnel fields plus
source, evidence, follow-up, and next-action fields. Every public lead starts as
not contacted, with eligibility and interest left blank until those statuses are
established directly.

## Status rules

- Use an ISO date such as `2026-09-10` in `Contacted`, `Replied`, and scheduling
  fields. Leave the field blank when the event has not happened.
- `Permission` is `Pending`, `Granted`, `Denied`, or `N/A-direct`.
- `Eligible` becomes `Yes` only after the role and recent experience are checked.
- `Written Interest` becomes `Yes` only after an explicit written opt-in that
  names or clearly acknowledges the commitments.
- `Evidence Strength` is `Strong`, `Weak`, or `None`.
- `Backup` is assigned only after all eight confirmations are reviewed.

## Strong evidence

- Explicit written interest in this pilot
- Confirmed availability
- Verified current/recent operator or infrastructure experience
- Acknowledgement of the full commitment and conditional incentive

## Weak evidence

- Reaction, upvote, poll answer, or emoji
- General praise for the idea
- "Sounds interesting" without accepting the commitment
- A referral made by someone else without the person's own response

# I. Validation Questions

Ask about real past behaviour before showing the prototype. Hypothetical answers
are weaker than a detailed example of what the person actually did.

## Problem and current workflow

1. Tell me about the last time you added, replaced, transferred, or retired a
   receiver. What happened from start to finish?
2. Who decided the receiver's identifier? Where was that identifier stored?
3. Which records, configuration files, dashboards, spreadsheets, or databases
   had to change?
4. Who was allowed to make those changes? How did other people know the change
   was authorised?
5. In your setup, can the hardware owner, physical host, feed-account owner, and
   technical maintainer be different people? When has that happened?
6. What breaks when a receiver is replaced or its owner, host, feed key, label,
   or metadata changes?
7. Tell me about a stale, duplicate, missing, or wrongly attributed receiver
   record you have encountered. What was the practical consequence?
8. How much time does receiver inventory work take in a normal month and during a
   migration or incident?
9. Which parts of the current process work well and should not be replaced?
10. Who consumes receiver inventory, and what fields do their tools actually
    need?

## Product test

11. Without my help, register the test receiver and explain what identity you
    think the application created.
12. Find the receiver again without using its transaction or cell outpoint.
13. Update one allowed field. Which parts of the identity remained stable?
14. Review the ownership and history. What does this prove to you, and what does
    it not prove?
15. Compare the active receiver with the revoked one. What would you expect your
    network software to do with each?
16. Which step was unclear, risky, or slower than your current process?
17. At any point, did the interface appear to prove physical location, clock
    quality, or feed honesty? It must not imply those things.

## Value and scope

18. Rank these jobs from most to least useful: stable identity, owner-controlled
    updates, ownership transfer, public discovery, change history, and permanent
    retirement. Why?
19. Which feature would you remove first?
20. What information is missing for a real receiver record? Which information
    must remain private?
21. Does an identity need to work across receiver networks, or is each network's
    own identifier enough? Describe the last situation that supports your answer.
22. What value, if any, does CKB add over a signed database, Git repository, or
    coordinator-managed API?
23. What is the maximum acceptable wallet or transaction burden for an operator?
24. What would make this unsafe, untrustworthy, or operationally unacceptable?

## Adoption and partnership

25. If your network evaluated this, who would make the decision and who could
    block it?
26. Which API, export format, event, authentication method, or service-level
    behaviour would an integration require?
27. What would it cost your team to test an integration? Which part is the main
    cost?
28. What evidence would you need before relying on a Registry record?
29. What competing tool or internal process would this have to replace or work
    beside?
30. What concrete next step would you be willing to complete in the next seven
    days: import a sample export, review the schema, write an integration note,
    or none of these?
31. If the product disappeared tomorrow, what would you return to using?
32. Who else has this problem for a different reason? May I mention your name
    when asking them for an introduction? Do not request their private contact
    details without consent.

## Evidence to capture for the grant

- A concrete past problem and its current workaround
- Time, risk, or coordination cost attached to that problem
- Observed task completion and assistance needed
- Feature value and feature rejection, not only positive comments
- Explanation of what CKB proves and does not prove
- A stated adoption blocker
- A concrete seven-day follow-up action
- Permission to quote a redacted statement, recorded separately from consent to
  participate

# J. Weekly Recruitment Targets

The month-end target is 30 September 2026. Front-load permission requests and
high-quality direct outreach; community approvals can take several days.

| Dates | Work | Cumulative attempt target | Confirmation target |
|---|---|---:|---:|
| 7-13 September | Send 8 permission requests. Send 6 personalised operator invitations and 3 coordinator invitations through legitimate public routes. Publish only where approval arrives. | 6 operators + 3 coordinators | 2 total |
| 14-20 September | Make one approved post in no more than three independent communities. Send 7-9 more operator invitations and 3-4 coordinator invitations. Follow up once with first-wave non-responders after five business days. | 13-15 operators + 6-7 coordinators | 4-5 total |
| 21-27 September | Fill community gaps with 7-9 operator invitations and 2-3 coordinator invitations. Ask eligible respondents for one consent-based referral. Begin scheduling while continuing screening. | 20-24 operators + 8-10 coordinators | 7 total |
| 28-30 September | Use only targeted gap-filling outreach. Verify evidence, commitments, and availability. Select 4 operators and 2 coordinators; designate one backup of each role. | 20-30 operators + 8-12 coordinators | 8 total: 5 operators + 3 coordinators |

## Decision points

- **13 September:** If fewer than three communities have answered, follow up with
  moderators and expand to Airplanes.live. Do not post without permission.
- **20 September:** If fewer than four people are confirmed, stop broadening the
  same ecosystem. Use warm coordinator referrals and the public shortlist.
- **27 September:** If one role is short, recruit only that role. Do not lower the
  experience requirement to reach eight.
- **30 September:** If fewer than eight qualified people have explicitly opted
  in, report the actual funnel. Do not turn weak evidence into confirmations.

## Success at the recruitment stage

Recruitment succeeds when eight qualified people explicitly accept the full
commitment and the cohort is diverse enough to challenge the product. It does
not succeed merely because 38 messages were sent. A smaller, honest funnel is
stronger grant evidence than an inflated confirmation count.
