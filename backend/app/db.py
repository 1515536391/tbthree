from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Generator
from contextlib import contextmanager

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class LogDetail(Base):
    __tablename__ = "log_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(128), index=True, nullable=False)
    edge_addr = Column(String(128), index=True, nullable=True)
    stage = Column(String(32), index=True, nullable=False)
    ts = Column(Integer, nullable=False)

    cpu_ms = Column(Integer, nullable=False)
    mem_mb_peak = Column(Integer, nullable=False)
    net_kb = Column(Integer, nullable=False)
    latency_ms = Column(Integer, nullable=False)

    result_hash = Column(String(128), nullable=True)
    log_hash = Column(String(128), unique=True, index=True, nullable=False)
    detail_json = Column(Text, nullable=False)

    # chain audit
    tx_hash = Column(String(128), nullable=True)
    height = Column(Integer, nullable=True)
    msg_type = Column(String(128), nullable=True)
    signer = Column(String(128), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TaskResultDetail(Base):
    __tablename__ = "task_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(128), unique=True, index=True, nullable=False)
    chosen_edge_addr = Column(String(128), nullable=False)
    result_json = Column(Text, nullable=False)
    result_hash = Column(String(128), nullable=False)
    result_sig = Column(Text, nullable=True)
    verified = Column(Boolean, default=False, nullable=False)

    tx_hash = Column(String(128), nullable=True)
    height = Column(Integer, nullable=True)
    signer = Column(String(128), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def make_engine(db_url: str):
    return create_engine(db_url, future=True)


def init_db(db_url: str) -> sessionmaker[Session]:
    engine = make_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope(SessionLocal: sessionmaker[Session]) -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# helpers

def upsert_task_result(
    db: Session,
    *,
    task_id: str,
    chosen_edge_addr: str,
    result_json: dict[str, Any],
    result_hash: str,
    result_sig: str | None,
    verified: bool,
    tx_hash: str | None = None,
    height: int | None = None,
    signer: str | None = None,
) -> None:
    payload = json.dumps(result_json, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    existing = db.execute(select(TaskResultDetail).where(TaskResultDetail.task_id == task_id)).scalar_one_or_none()
    if existing is None:
        db.add(
            TaskResultDetail(
                task_id=task_id,
                chosen_edge_addr=chosen_edge_addr,
                result_json=payload,
                result_hash=result_hash,
                result_sig=result_sig,
                verified=verified,
                tx_hash=tx_hash,
                height=height,
                signer=signer,
            )
        )
    else:
        existing.chosen_edge_addr = chosen_edge_addr
        existing.result_json = payload
        existing.result_hash = result_hash
        existing.result_sig = result_sig
        existing.verified = verified
        existing.tx_hash = tx_hash
        existing.height = height
        existing.signer = signer
