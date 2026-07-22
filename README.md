# wxdecide

Team project for the Connected Places Catapult / Met Office / Snowflake hackathon —
*"Improving the Use of Weather and Climate Data for Smarter Decision Making"* (22 July 2026).

See [`docs/`](docs/) for the event briefing summaries, source PDFs, and ideation notes.

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync              # create .venv and install dependencies
uv run pytest        # run tests
uv run ruff check .  # lint
```

Add packages as the solution takes shape, e.g.:

```bash
uv add snowflake-connector-python pandas
```

## Layout

```
src/wxdecide/   package source
tests/          tests
docs/           hackathon briefing docs, PDFs, ideation notes
```
