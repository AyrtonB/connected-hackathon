"""Database engine and session helpers.

Defaults to the local Postgres started via `docker-compose.yml` at the repo root; override with
the `DATABASE_URL` env var to point elsewhere. Schema is managed by Alembic (see `alembic/` at
the repo root) — run `uv run alembic upgrade head` before using these, rather than calling
`SQLModel.metadata.create_all()` directly, so the DB schema and migration history stay in sync.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session, create_engine

DEFAULT_DATABASE_URL = "postgresql+psycopg://wxdecide:wxdecide@localhost:5432/wxdecide"


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_engine():
    return create_engine(get_database_url())


@contextmanager
def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
