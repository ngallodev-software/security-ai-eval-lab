"""
Database session for security-ai-eval-lab.

Shares the same DATABASE_URL env var as ai-reliability-fw
so both projects point at the same Postgres instance.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@event.listens_for(engine.sync_engine, "connect")
def set_search_path(dbapi_conn, connection_record):
    dbapi_conn.execute("SET search_path TO security_eval, public")


async def get_db():
    async with async_session() as session:
        yield session
