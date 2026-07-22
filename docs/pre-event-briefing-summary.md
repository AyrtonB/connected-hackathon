# Pre-Event Briefing — Summary

Source: `docs/pdfs/Pre-event-briefing-Improving-the-Use-of-Weather-and-Climate-Data-for-Smarter-Decision-Making.pdf`

## Event Details

- **Title:** Improving the Use of Weather and Climate Data for Smarter Decisions
- **Date:** Wednesday 22 July 2026, 09:00–17:00
- **Venue:** Connected Places Catapult, 1 Sekforde Street, London, EC1R 0BE (nearest tube: Farringdon)
- **Partners:** Government Digital Service (GDS), Met Office, Snowflake, Connected Places Catapult — delivered in partnership with UKRI / Innovate UK
- **Event contacts:** Daniel Hesse (GDS), James Guscott (Met Office), Paddy Gardner (Snowflake), Ryan Goodman (Connected Places Catapult)
- **Questions:** events@cp.catapult.org.uk

## Aim of the Day

Bring together public sector practitioners, researchers, innovators, technologists and domain experts to explore how weather and climate data can create greater value across the UK. Concretely, the day aims to:

- Explore practical concepts and prototypes
- Understand user stories centred on a real decision or workflow
- Generate evidence of where weather/climate data could improve that decision
- Gather insight into what makes the data easier or harder to use
- Produce recommendations for what could be developed further

## Partner Roles

- **Government Digital Service (GDS)** — digital centre of government; sets/leads the digital strategy, measures digital performance, maintains guidance (e.g. Service Manual), drives efficiency. Priorities: joined-up public services, harnessing AI for public good, strengthening digital/data infrastructure, growing talent.
- **Met Office** — UK's national meteorological service. Positioned as **Trusted** (national weather/climate service with public purpose), **Useful** (turns complex science into actionable information), and **Decision-ready** (helps users interpret risk, uncertainty, and impact).
- **Snowflake** — Cloud Data & AI platform, trusted by 790 of the Forbes Global 2000; in UK public sector it eliminates silos and improves data sharing across NHS, education, and central/local government.

## The Core Framing

> **Weather data is decision intelligence** — useful when combined with context, uncertainty, geospatial data, and human judgement.

**Hackathon question:** *What extra value appears when AI can search, summarise, join and explain weather data in the context of real operational choices?*

**The simple story:** Trusted Met Office data → Data platform + AI → Decision-ready outputs. The hackathon is testing how trusted data becomes more useful when joined with AI, context, and a data platform — and what that reveals about how the Met Office could improve its own data to support better decisions.

## Four Challenge Areas

| Theme | Focus |
|---|---|
| **Resilience & emergency response** | Anticipate severe weather impacts and plan interventions |
| **Transport & infrastructure** | Reduce disruption, improve routing, protect assets |
| **Health, housing & wellbeing** | Target earlier action for vulnerable people and places |
| **Energy, events & local economy** | Match operations, safety and demand to weather risk |

### Example seed challenges (from GDS)

- **Event Safety Planning** — helping large-scale public events (festivals, sporting events) run safely with minimal disruption amid an increasingly volatile climate. Target participants: events management/risk sector.
- **Local Resilience Forums** — helping local authorities use weather/climate data to plan for and prepare local incidents and emergencies. Target participants: local authority users.
- **Research Integration** — enabling researchers to better integrate weather/climate data into their models. Target participants: academics with research/coding skills interested in weather-related issues (e.g. climate change).

## Data Available to Participants

A mix of live/operational-style feeds and controlled hackathon datasets, spanning location, time, risk and uncertainty. Think of it as ingredients: **forecasts + observations + warnings + history + local context.**

**Operational-style feeds:**
- UK site-specific forecasts
- Global site-specific forecasts
- Pseudo observations (based on T0)
- National Severe Weather Warning Service (NSWWS)
- Land observations
- Marine observations
- IMPROVER UK site-specific percentiles

**Controlled sharing:**
- NSWWS 2-year archive
- UKV gridded sample
- National Climate Messages
- LTA / long-term averages
- Flood Messages
- Climate Data (Climate Data Portal)

## Snowflake Platform (What You'll Build On)

- **Platform principles:** Easy, Connected, Trusted.
- **Architecture:** cross-cloud (AWS / Azure / GCP via Snowgrid); one integrated product spanning Data Engineering, Analytics, AI, and Applications & Collaboration; unified via the **Snowflake Horizon Catalog** (governance/context layer for AI over all data).
- **Compute:** elastic — SQL, Java/Scala, Python, Apache Spark, Containers, CPU/GPU.
- **Storage:** interoperable across Data Mesh, Data Lakehouse and Data Warehouse patterns; supports unstructured, semi-structured and structured data, Iceberg tables, Snowflake tables, hybrid tables, Snowflake Postgres.
- **Zero-ETL data sharing:** securely share/view/query/join data across organisations with built-in lineage, masking, access policies, classification, differential privacy.
- **Snowflake AI:**
  - **Cortex Analyst** — text-to-SQL over governed table semantics
  - **Cortex Search** — embed, hybrid search, rerank over unstructured data
  - **Cortex Agents** — orchestration, tool use, reflection, monitoring/iteration
  - **Cortex AI functions** — `AI_COMPLETE`, `AI_FILTER`, `AI_AGG`, `AI_CLASSIFY`, `AI_EMBED`, `AI_SIMILARITY`, `AI_EXTRACT` (reasoning, extraction, summarisation, generation) across models from OpenAI, Anthropic, Meta, Mistral, DeepSeek, Gemini, Snowflake's own.
  - **Cortex Code** — an agentic coding assistant, available as a Snowsight browser widget or as a **CLI** (works in the terminal or in VS Code/Cursor); understands Snowflake's data/compute/governance semantics; now extends to `dbt` and Apache Airflow for transformation/orchestration workflows.

## Worked Example (illustrates the methodology, not a real team's answer)

- **Theme:** Climate Resilience and Public Services
- **Challenge statement:** *"How might we use weather & climate data so that future housing can be resilient to extreme weather events?"*
- **Persona:** Sarah Flakes, Senior Urban Planning lead at Combined Authority X — needs climate scenario modelling (2030/2050/2080), flood/drainage risk data, and site suitability scoring to make evidence-based, climate-resilient housing decisions, currently hampered by inconsistent and fragmented data across authorities.
