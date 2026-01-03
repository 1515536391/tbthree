from __future__ import annotations

from pydantic import BaseModel, Field


class DemoSeedRequest(BaseModel):
    seed: int = 42
    tasks_per_region: int = 15
    days_span: int = 7
    bad_edge_mode: bool = True


class CreateTaskRequest(BaseModel):
    region: str = Field(..., pattern=r"^[AB]$")
    task_type: str = "default"
    payload: dict = {}


class SubmitLogRequest(BaseModel):
    task_id: str
    stage: str
    ts: int
    cpu_ms: int
    mem_mb_peak: int
    net_kb: int
    latency_ms: int
    result_hash: str | None = None
    log_detail: dict


class RecordResultRequest(BaseModel):
    task_id: str
    result_json: dict


class TaskFeedbackRequest(BaseModel):
    task_id: str
    accepted: bool
    reason: str = ""
    severity: int = 1
