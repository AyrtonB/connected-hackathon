# Ideation

Candidate concepts, one per challenge theme, sketched using the Guide for Participants
methodology (challenge statement → persona → data → prototype shape). Scored against the
judging criteria — Technology & Innovation (50%), Impact & Value (30%), Feasibility (20%) —
to help narrow down before committing build time.

The seed challenges GDS flagged (Event Safety Planning, Local Resilience Forums, Research
Integration) map onto the themes below, but these concepts push toward things that showcase
**Snowflake Cortex AI specifically** (search, summarise, join, explain), since that's the
"extra value" question the hackathon is actually asking, not just a weather dashboard.

---

## 1. Resilience & Emergency Response — "Incident Briefing Copilot"

**Challenge statement:** How might we use weather & climate data so that Local Resilience
Forum duty officers can get a decision-ready briefing in minutes instead of hours?

**Persona:** LRF/Category 1 responder duty officer, needs to fuse NSWWS warnings, land/marine
observations and site-specific forecasts for their patch into a single actionable brief before
a multi-agency call.

**What it does:** Natural-language query ("what's the risk to X over the next 48h") over
joined NSWWS + forecast + historical NSWWS archive data. Cortex Analyst turns the question into
SQL over governed tables; Cortex Search/AI_SUMMARIZE turns the warning text + numeric data into
a plain-English briefing note with recommended actions, citing the underlying data.

**Data:** NSWWS (live + 2-year archive), UK site-specific forecasts, land/marine observations,
Flood Messages.

**Judging fit:** Technology 4/5 (genuine text-to-SQL + summarisation over joined structured/
unstructured data), Impact 5/5 (direct fit to GDS's named "Local Resilience Forums" seed
challenge, life-safety relevant), Feasibility 4/5 (all data listed as available, narrow scope).

---

## 2. Transport & Infrastructure — "Route Risk Explainer"

**Challenge statement:** How might we use weather & climate data so that highways/rail
operations planners can see which routes/assets are at risk today, in plain language, not just
a map of numbers?

**Persona:** Network operations planner deciding on speed restrictions, gritting, or asset
inspections.

**What it does:** Join site-specific forecasts + IMPROVER percentiles (uncertainty!) against a
sample asset/route list; AI_FILTER / AI_AGG to flag at-risk segments; Cortex Agent explains
*why* (e.g. "70th percentile gust forecast exceeds asset threshold for 6h from 14:00") rather
than just a red/amber/green tile.

**Data:** UK site-specific forecasts, IMPROVER UK site-specific percentiles, LTA/long-term
averages (to contextualise "is this unusual for the time of year").

**Judging fit:** Technology 4/5 (uncertainty-aware reasoning is a nice differentiator),
Impact 3/5 (valuable but needs a synthetic asset dataset since we don't have real ones),
Feasibility 3/5 (asset data is the gap — would need to fabricate a small sample).

---

## 3. Health, Housing & Wellbeing — "Resilient Sites Advisor" (closest to the worked example)

**Challenge statement:** How might we use weather & climate data so that housing/planning
teams can identify which future development sites are resilient to extreme weather?

**Persona:** Sarah Flakes (from the Guide) — Senior Urban Planner needing climate scenario +
flood risk + site suitability in one place instead of fragmented sources.

**What it does:** Cortex Analyst over Climate Data Portal + LTA + UKV gridded sample lets a
planner ask "how has extreme rainfall changed at site X since the 1990s baseline?" and get a
scored, cited answer plus a resilience score per candidate site.

**Data:** Climate Data (Climate Data Portal), LTA/long-term averages, UKV gridded sample,
National Climate Messages.

**Judging fit:** Technology 3.5/5 (mostly retrieval + aggregation, less novel AI reasoning),
Impact 4/5 (matches the guide's own worked persona, easy to explain to judges),
Feasibility 4/5 (data is squarely in the "controlled sharing" list, no fabrication needed).

---

## 4. Energy, Events & Local Economy — "Event Safety & Ops Assistant"

**Challenge statement:** How might we use weather & climate data so that large public event
organisers can match staffing, safety and contingency plans to real-time weather risk?

**Persona:** Event safety/operations lead for a festival or sporting event (GDS's named
"Event Safety Planning" seed challenge, and mirrors the Glastonbury mud photo used in the deck).

**What it does:** Ask Cortex Agent "what's our crowd-safety risk profile for tomorrow 12–22:00"
— it joins site-specific forecast + NSWWS + marine (if coastal) + historic NSWWS archive for
comparable past events, and generates a plain-English contingency recommendation (e.g. extra
drainage, medical staffing uplift, structural wind checks) with the supporting data attached.

**Data:** UK site-specific forecasts, NSWWS (live + archive), National Severe Weather Warning
Service, land observations.

**Judging fit:** Technology 4/5, Impact 4/5 (directly named as a GDS seed challenge and easy to
demo memorably), Feasibility 4/5.

---

## 5. Energy — "Power Outage Forecast" (UK Power Networks Live Faults) — **leading candidate**

Seeded from a real dataset already dropped in [`data/Data Triage - Live Fault Data.xlsx`](../data/Data%20Triage%20-%20Live%20Fault%20Data.xlsx)
and <https://ukpowernetworks.opendatasoft.com/explore/assets/ukpn-live-faults/view/>.

**Challenge statement:** How might we join weather forecast/warning data with power network
fault data so that a DNO control room (or a Local Resilience Forum planning for vulnerable/
Priority-Services-Register customers) can anticipate weather-driven power outages before they
escalate, instead of reacting to them?

**Persona:** UKPN control room duty manager / LRF planning officer — currently reacts to faults
as customers call in; wants an early-warning view of where the network is at heightened risk
over the next 12–48h so crews and communications can be pre-positioned.

**Two real UKPN open datasets, two different jobs:**

| Dataset | ID | What it gives us | Update cadence |
|---|---|---|---|
| **Live Faults** | `ukpn-live-faults` | Current/recent incidents: type, category, priority, postcodes affected, customers affected, restored/estimated-restoration times, geopoint (aggregated from postcode) | Continuous, real-time |
| **Interruptions Incentive Scheme (IIS)** | `ukpn-iis` | *Historical* fault-level records: start/end datetime, cause code, "Exceptional Event" flag (i.e. explicitly tagged severe-weather exclusions), damage, licence area, spatial coordinates | Annual, CC BY 4.0 |

The IIS dataset is the key unlock: it has a **cause code + exceptional-weather-event flag per
incident**, going back multiple regulatory years, which is exactly the ground truth needed to
correlate historical outages against historical Met Office conditions (LTA / NSWWS archive) at
the same time and place — i.e. actual training/validation data for a forecast, not just a live
snapshot to eyeball.

**Data triage note:** the accompanying triage form confirms Live Faults is approved as fully
**open** data (openness rating 1, no PII, real-time), and — notably — the DNO's own stated
justification for publishing it was enabling "EV charge point operators to notify customers of
potential interruptions to their service," i.e. UKPN already anticipates third parties building
exactly this kind of downstream product on top of it.

**Prototype shape:**
1. Join `ukpn-iis` (historical, weather-flagged outages) against Met Office historical/LTA data
   by location + time → identify which weather variables (wind gust, rainfall intensity, lightning)
   most predict a cause-coded weather outage, by region.
2. Score current NSWWS warnings + forecasts against that pattern → produce a per-area outage
   risk rating for the next 12–48h.
3. Use `ukpn-live-faults` as the real-time validation/demo layer — during the event itself, show
   whether areas flagged as "elevated risk" do see live faults appear, and let Cortex
   Analyst/Agent explain *why* ("wind gusts forecast at 85th percentile, historically correlated
   with a 3x rise in cable faults in this licence area").

**Judging fit:** Technology & Innovation 4.5/5 — genuinely joins an external live operational
feed + a historical ground-truth dataset + Met Office forecasts, which is a stronger "join and
explain" story than any single-source concept above. Impact & Value 4.5/5 — directly protects
vulnerable customers and gives DNOs/LRFs lead time, a clear public-good narrative. **Feasibility
is the open risk (3/5):** one day isn't enough to build and validate a real trained forecast
model end-to-end; the honest, defensible framing for the demo is an **explainable early-warning
risk score**, calibrated against the historical IIS correlation, rather than claiming a
production-grade forecasting model. Worth being upfront about that distinction with judges —
it's exactly what the Feasibility criterion is scoring.

---

## Recommendation

**#5 (Power Outage Forecast)** is now the strongest candidate: it's the only concept built on a
real, already-sourced dataset pairing (a live operational feed *and* a historical
weather-flagged ground truth), which directly answers the hackathon's "search, summarise, join
and explain" framing rather than illustrating it hypothetically. Its main risk is Feasibility —
mitigate by explicitly scoping the demo to an "explainable risk score" rather than a claimed
production forecasting model.

Runner-up: **#1 (Incident Briefing Copilot) or #4 (Event Safety & Ops Assistant)** — both map
directly onto a GDS-named seed challenge (higher Impact & Value credibility with judges), both
lean on Cortex Analyst + summarisation/agent reasoning over joined structured + unstructured
data, and both are feasible with the listed datasets alone — no external dataset sourcing
required.

#3 is the safest/easiest to build (closest to the guide's own worked example) but is more of a
retrieval dashboard than a demonstration of agentic reasoning, which likely caps the Technology
& Innovation score (50% of the total).

Next step per the methodology: pick one, then run Stakeholder Mapping → Persona → User Journey
(current vs. future state) before touching the prototype.
