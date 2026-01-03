from __future__ import annotations

import os
import tempfile
import threading
import time
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .chain_cli import ChainCLI
from .config import Settings, get_settings
from .db import LogDetail, init_db, session_scope, upsert_task_result
from .hashing import sha256_hex_of_json
from .schemas import (
    CreateTaskRequest,
    DemoSeedRequest,
    RecordResultRequest,
    SubmitLogRequest,
    TaskFeedbackRequest,
)

from .mock_data import (
    ensure_mock_db,
    mock_audit_task_logs,
    mock_list_edges,
    mock_list_log_summaries,
    mock_list_proposals,
    mock_list_tasks,
    mock_logs_by_task,
    mock_show_edge,
    mock_show_task,
    fake_cosmos_addr,
)

app = FastAPI(title="TB3 MVP Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def settings() -> Settings:
    return get_settings()


def chain_cli(s: Settings = Depends(settings)) -> ChainCLI:
    return ChainCLI(
        tbthreed=s.tbthreed,
        chain_id=s.chain_id,
        node=s.chain_rpc,
        home=s.chain_home,
        module=s.module_name,
        keyring_backend=s.keyring_backend,
    )


SessionLocal = None  # set in startup


# ------------------------- auto demo seed (startup) -------------------------

_AUTO_SEED_STARTED = False


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _mock_enabled() -> bool:
    # Set MOCK_DATA=1 in backend/.env to enable fast fake data.
    return _env_bool("MOCK_DATA", False) or _env_bool("TB3_MOCK_DATA", False)


def _mock_seed() -> int:
    try:
        return int(os.getenv("MOCK_DATA_SEED", "42"))
    except Exception:
        return 42


def _mock_addrs(s: Settings) -> dict[str, str]:
    """Return deterministic demo addresses for MOCK_DATA mode.

    We prefer values from Settings, but those are often unset or accidentally
    duplicated (e.g. using the same admin addr everywhere), which makes the UI
    look "fake". When duplicates/missing are detected, we synthesize stable
    cosmos-like bech32 strings derived from the mock seed.
    """

    seed = int(os.getenv("MOCK_SEED", "4242"))

    addrs = {
        "admin": s.admin_addr,
        "cloud": s.cloud_addr,
        "vehicle1": s.vehicle1_addr,
        "edge1": s.edge1_addr,
        "edge2": s.edge2_addr,
        "edge3": s.edge3_addr,
    }

    # Normalize blanks
    for k, v in list(addrs.items()):
        if not v or not str(v).strip():
            addrs[k] = ""

    # If missing or duplicated, generate deterministic unique addrs.
    seen: dict[str, str] = {}
    for k in list(addrs.keys()):
        v = addrs[k]
        if (not v) or (v in seen):
            addrs[k] = fake_cosmos_addr(f"{k}", seed=seed, prefix="cosmos")
        else:
            seen[v] = k

    return addrs




def _auto_seed_marker_path() -> Path:
    # backend/app -> backend
    base = Path(__file__).resolve().parents[1]
    return base / 'data' / '.auto_demo_seed_done.json'


def _start_auto_demo_seed() -> None:
    """Kick off demo seed in a background thread on startup.

    Controlled by env:
      - AUTO_DEMO_SEED (default: true)
      - AUTO_DEMO_SEED_FORCE (default: false)
      - AUTO_DEMO_SEED_MAX_WAIT_SEC (default: 120)
      - AUTO_DEMO_SEED_DELAY_SEC (default: 2)
      - AUTO_DEMO_SEED_TASKS_PER_REGION / DAYS_SPAN / BAD_EDGE_MODE / SEED
    """
    global _AUTO_SEED_STARTED
    if _AUTO_SEED_STARTED:
        return

    enabled = _env_bool('AUTO_DEMO_SEED', True)
    if not enabled:
        return

    _AUTO_SEED_STARTED = True

    def _worker() -> None:
        try:
            s = get_settings()
            marker_path = _auto_seed_marker_path()
            force = _env_bool('AUTO_DEMO_SEED_FORCE', False)
            if marker_path.exists() and not force:
                print(f'[auto-seed] skip: marker exists at {marker_path}')
                return

            # Wait for chain to be ready (non-blocking for server startup).
            max_wait = int(os.getenv('AUTO_DEMO_SEED_MAX_WAIT_SEC', '120'))
            delay = float(os.getenv('AUTO_DEMO_SEED_DELAY_SEC', '2'))
            deadline = time.time() + max_wait

            chain = ChainCLI(
                tbthreed=s.tbthreed,
                chain_id=s.chain_id,
                node=s.chain_rpc,
                home=s.chain_home,
                module=s.module_name,
                keyring_backend=s.keyring_backend,
            )

            while True:
                try:
                    # a light query to check connectivity
                    chain.query(s.module_name, 'list-edge', [])
                    break
                except Exception as e:
                    if time.time() >= deadline:
                        print(f'[auto-seed] abort: chain not ready after {max_wait}s: {e}')
                        return
                    time.sleep(delay)

            req = DemoSeedRequest(
                seed=int(os.getenv('AUTO_DEMO_SEED_SEED', str(DemoSeedRequest().seed))),
                tasks_per_region=int(os.getenv('AUTO_DEMO_SEED_TASKS_PER_REGION', str(DemoSeedRequest().tasks_per_region))),
                days_span=int(os.getenv('AUTO_DEMO_SEED_DAYS_SPAN', str(DemoSeedRequest().days_span))),
                bad_edge_mode=_env_bool('AUTO_DEMO_SEED_BAD_EDGE_MODE', DemoSeedRequest().bad_edge_mode),
            )

            print(f'[auto-seed] start: seed={req.seed} tasks_per_region={req.tasks_per_region} days_span={req.days_span} bad_edge_mode={req.bad_edge_mode}')

            # Call the same implementation as the HTTP endpoint (no network request).
            res = demo_seed(req=req, s=s, chain=chain)

            marker_path.parent.mkdir(parents=True, exist_ok=True)
            import json as _json

            marker_path.write_text(
                _json.dumps({'done': True, 'ts': datetime.utcnow().isoformat(), 'result': res}, ensure_ascii=False),
                encoding='utf-8',
            )
            print(f'[auto-seed] done; marker written to {marker_path}')
        except Exception:
            print('[auto-seed] failed with exception:')
            print(traceback.format_exc())

    threading.Thread(target=_worker, daemon=True).start()


@app.on_event("startup")
def _startup() -> None:
    global SessionLocal
    s = get_settings()
    SessionLocal = init_db(s.db_url)

    # In MOCK_DATA mode we do NOT talk to the chain; we only create sqlite + preload mock rows.
    if _mock_enabled():
        seed = _mock_seed()
        ensure_mock_db(SessionLocal, seed=seed, addrs=_mock_addrs(s))
        print(f"[mock-data] enabled (seed={seed})")
        return

    _start_auto_demo_seed()


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "ts": datetime.utcnow().isoformat()}

@app.get("/")
def root() -> dict[str, Any]:
    # Helpful for users who open http://localhost:8000 in the browser.
    return {"ok": True, "docs": "/docs", "health": "/health", "mock_data": _mock_enabled()}



@app.get("/accounts")
def accounts(s: Settings = Depends(settings)) -> dict[str, Any]:
    return {
        "admin": {"name": s.admin_name, "addr": s.admin_addr},
        "cloud": {"name": s.cloud_name, "addr": s.cloud_addr},
        "vehicle1": {"name": s.vehicle1_name, "addr": s.vehicle1_addr},
        "edges": [
            {"name": s.edge1_name, "addr": s.edge1_addr},
            {"name": s.edge2_name, "addr": s.edge2_addr},
            {"name": s.edge3_name, "addr": s.edge3_addr},
        ],
    }


# ------------------------- chain queries (thin wrappers) -------------------------

def _safe_query(chain: ChainCLI, module: str, cmd: str, args: list[str]) -> dict[str, Any]:
    try:
        return chain.query(module, cmd, args)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/edges")
def list_edges(chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if _mock_enabled():
        s = get_settings()
        return mock_list_edges(seed=_mock_seed(), addrs=_mock_addrs(s))
    return _safe_query(chain, chain.module, "list-edge", [])


@app.get("/edges/{edge_addr}")
def show_edge(edge_addr: str, chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if _mock_enabled():
        s = get_settings()
        return mock_show_edge(edge_addr, seed=_mock_seed(), addrs=_mock_addrs(s))
    return _safe_query(chain, chain.module, "show-edge", [edge_addr])


@app.get("/tasks")
def list_tasks(chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if _mock_enabled():
        s = get_settings()
        return mock_list_tasks(seed=_mock_seed(), addrs=_mock_addrs(s))
    return _safe_query(chain, chain.module, "list-task", [])


@app.get("/tasks/{task_id}")
def show_task(task_id: str, chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if _mock_enabled():
        s = get_settings()
        return mock_show_task(task_id, seed=_mock_seed(), addrs=_mock_addrs(s))
    return _safe_query(chain, chain.module, "show-task", [task_id])


@app.get("/logs")
def list_log_summaries(chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if _mock_enabled():
        s = get_settings()
        return mock_list_log_summaries(seed=_mock_seed(), addrs=_mock_addrs(s))
    return _safe_query(chain, chain.module, "list-log-summary", [])


@app.get("/tasks/{task_id}/logs")
def list_logs_by_task(task_id: str, chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if _mock_enabled():
        s = get_settings()
        return mock_logs_by_task(task_id, seed=_mock_seed(), addrs=_mock_addrs(s))
    # Chain only supports list-all; we filter in backend.
    all_logs = _safe_query(chain, chain.module, "list-log-summary", [])
    logs = all_logs.get("logSummary") or all_logs.get("logSummaries") or []
    filtered = [l for l in logs if l.get("taskId") == task_id]
    return {"items": filtered, "total": len(filtered)}


@app.get("/audit/tasks/{task_id}/logs")
def audit_task_logs(task_id: str, chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if _mock_enabled():
        s = get_settings()
        return mock_audit_task_logs(task_id, seed=_mock_seed(), addrs=_mock_addrs(s))

    """Audit view: compare chain log hashes vs DB detail -> recompute hash and match."""
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="DB not ready")

    chain_logs = list_logs_by_task(task_id, chain)
    chain_items = chain_logs.get("items", [])

    with session_scope(SessionLocal) as db:
        rows = db.query(LogDetail).filter(LogDetail.task_id == task_id).all()

        db_map = {r.log_hash: r for r in rows}

        audited = []
        for item in chain_items:
            log_hash = item.get("logHash") or item.get("log_hash")
            db_row = db_map.get(log_hash)
            if not db_row:
                audited.append({"logHash": log_hash, "match": False, "reason": "missing_in_db", "chain": item})
                continue
            try:
                detail = db_row.detail_json
                recomputed = sha256_hex_of_json(json.loads(detail))  # type: ignore
            except Exception:
                recomputed = ""
            audited.append(
                {
                    "logHash": log_hash,
                    "match": recomputed == log_hash,
                    "chain": item,
                    "db": {
                        "stage": db_row.stage,
                        "ts": db_row.ts,
                        "cpu_ms": db_row.cpu_ms,
                        "mem_mb_peak": db_row.mem_mb_peak,
                        "net_kb": db_row.net_kb,
                        "latency_ms": db_row.latency_ms,
                        "tx_hash": db_row.tx_hash,
                        "height": db_row.height,
                        "signer": db_row.signer,
                    },
                }
            )

    return {"taskId": task_id, "items": audited}


@app.get("/governance/proposals")
def list_proposals(chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if _mock_enabled():
        s = get_settings()
        return mock_list_proposals(seed=_mock_seed(), addrs=_mock_addrs(s))
    return _safe_query(chain, chain.module, "list-governance-proposal", [])


@app.get("/reputation/propagations")
def list_propagations(chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    return _safe_query(chain, chain.module, "list-reputation-propagation", [])


# ------------------------- chain tx wrappers -------------------------

@app.post("/admin/edges/register")
def admin_register_edge(edge_addr: str, region: str, s: Settings = Depends(settings), chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    try:
        res = chain.tx(chain.module, "register-edge", [edge_addr, region], from_name=s.admin_name)
        return {"txHash": res.txhash, "height": res.height, "raw": res.raw}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks")
def create_task(req: CreateTaskRequest, s: Settings = Depends(settings), chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    """Create task and choose edge by reputation (simple sort by score)."""
    try:
        edges_raw = chain.query(chain.module, "list-edge", [])
        edges = edges_raw.get("edge") or edges_raw.get("edges") or []
        region_edges = [e for e in edges if (e.get("region") == req.region) and (e.get("status") != "TASK_FROZEN")]
        # sort by score desc
        def score_of(e: dict) -> int:
            try:
                return int(e.get("score", 0))
            except Exception:
                return 0

        region_edges.sort(key=score_of, reverse=True)
        chosen = region_edges[0] if region_edges else (edges[0] if edges else None)
        if not chosen:
            raise RuntimeError("No edge available")
        chosen_edge_addr = chosen.get("edgeAddr") or chosen.get("edge_addr")
        if not chosen_edge_addr:
            raise RuntimeError("Bad edge object")

        task_id = f"manual-{req.region}-{int(datetime.utcnow().timestamp())}"
        payload_hash = sha256_hex_of_json(req.payload)
        now_ts = str(int(datetime.now(timezone.utc).timestamp()))
        res = chain.tx(
            chain.module,
            "create-task",
            [
                task_id,
                s.vehicle1_addr,
                chosen_edge_addr,
                req.region,
                "CREATED",
                req.task_type,
                payload_hash,
                "",  # log_hashes
                "",  # result_hash
                "",  # result_sig
                "false",
                now_ts,
                now_ts,
            ],
            from_name=s.vehicle1_name,
        )
        return {"taskId": task_id, "chosenEdgeAddr": chosen_edge_addr, "txHash": res.txhash, "height": res.height}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/edges/{edge_addr}/logs")
def submit_log(edge_addr: str, req: SubmitLogRequest, s: Settings = Depends(settings), chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="DB not ready")

    # Compute logHash from detail
    log_hash = sha256_hex_of_json(req.log_detail)

    # Persist detail
    with session_scope(SessionLocal) as db:
        db.add(
            LogDetail(
                task_id=req.task_id,
                edge_addr=edge_addr,
                stage=req.stage,
                ts=req.ts,
                cpu_ms=req.cpu_ms,
                mem_mb_peak=req.mem_mb_peak,
                net_kb=req.net_kb,
                latency_ms=req.latency_ms,
                result_hash=req.result_hash,
                log_hash=log_hash,
                detail_json=json.dumps(req.log_detail, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            )
        )

    # Broadcast tx (edge signs)
    try:
        # map creator by edge_addr -> edge name
        edge_name = {
            s.edge1_addr: s.edge1_name,
            s.edge2_addr: s.edge2_name,
            s.edge3_addr: s.edge3_name,
        }.get(edge_addr)
        if not edge_name:
            raise RuntimeError("Unknown edge addr")

        res = chain.tx(
            chain.module,
            "submit-log-summary",
            [
                req.stage,
                task_id,
                log_hash,
                req.result_hash or "",
                str(req.cpu_ms),
                str(req.mem_mb_peak),
                str(req.latency_ms),
                str(req.net_kb),
                str(req.ts),
            ],
            from_name=edge_name,
        )

        # update audit info in DB (best-effort)
        with session_scope(SessionLocal) as db:
            row = db.query(LogDetail).filter(LogDetail.log_hash == log_hash).one_or_none()
            if row:
                row.tx_hash = res.txhash
                row.height = res.height
                row.msg_type = "submitLogSummary"
                row.signer = edge_addr

        return {"logHash": log_hash, "txHash": res.txhash, "height": res.height}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/edges/{edge_addr}/tasks/{task_id}/result")
def record_result(edge_addr: str, task_id: str, req: RecordResultRequest, s: Settings = Depends(settings), chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="DB not ready")

    result_hash = sha256_hex_of_json(req.result_json)

    # sign result_hash via tbthreed keys sign
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(result_hash)
        sign_file = f.name

    edge_name = {
        s.edge1_addr: s.edge1_name,
        s.edge2_addr: s.edge2_name,
        s.edge3_addr: s.edge3_name,
    }.get(edge_addr)
    if not edge_name:
        raise HTTPException(status_code=400, detail="Unknown edge")

    try:
        sig = chain.keys_sign(edge_name, sign_file)
        verified = chain.keys_verify(edge_addr, sig, sign_file)

        # broadcast recordResult (cloud as tx signer)
        res = chain.tx(chain.module, "record-result", [task_id, result_hash, sig, str(verified).lower()], from_name=s.cloud_name)

        # store in DB
        with session_scope(SessionLocal) as db:
            upsert_task_result(
                db,
                task_id=task_id,
                chosen_edge_addr=edge_addr,
                result_json=req.result_json,
                result_hash=result_hash,
                result_sig=sig,
                verified=verified,
                tx_hash=res.txhash,
                height=res.height,
                signer=s.cloud_addr,
            )

        return {"taskId": task_id, "resultHash": result_hash, "signature": sig, "verified": verified, "txHash": res.txhash, "height": res.height}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.unlink(sign_file)
        except Exception:
            pass


@app.post("/vehicles/{vehicle_addr}/tasks/{task_id}/complaint")
def submit_feedback(vehicle_addr: str, task_id: str, req: TaskFeedbackRequest, s: Settings = Depends(settings), chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    try:
        # for now only vehicle1
        if vehicle_addr != s.vehicle1_addr:
            raise HTTPException(status_code=403, detail="Only vehicle1 supported in MVP")
        res = chain.tx(
            chain.module,
            "submit-task-feedback",
            [task_id, str(req.accepted).lower()],
            from_name=s.vehicle1_name,
        )
        return {"txHash": res.txhash, "height": res.height}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/governance/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: str, s: Settings = Depends(settings), chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    try:
        res = chain.tx(chain.module, "approve-proposal", [proposal_id], from_name=s.admin_name)
        return {"txHash": res.txhash, "height": res.height}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/governance/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: str, reason: str = "", s: Settings = Depends(settings), chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    try:
        res = chain.tx(chain.module, "reject-proposal", [proposal_id, reason], from_name=s.admin_name)
        return {"txHash": res.txhash, "height": res.height}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------- demo seed -------------------------

import json
import random


@app.get("/demo/status")
def demo_status(chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    # best effort: list counts
    edges = _safe_query(chain, chain.module, "list-edge", [])
    tasks = _safe_query(chain, chain.module, "list-task", [])
    props = _safe_query(chain, chain.module, "list-governance-proposal", [])
    return {
        "edges": len(edges.get("edge") or edges.get("edges") or []),
        "tasks": len(tasks.get("task") or tasks.get("tasks") or []),
        "proposals": len(props.get("governanceProposal") or props.get("governanceProposals") or []),
    }


@app.post("/demo/seed")
def demo_seed(req: DemoSeedRequest, s: Settings = Depends(settings), chain: ChainCLI = Depends(chain_cli)) -> dict[str, Any]:
    if _mock_enabled():
        return {"ok": True, "mock": True, "note": "MOCK_DATA=1: demo/seed is skipped; mock dataset is served via GET /edges,/tasks,/governance/proposals,/audit/..."}

    """Seed demo data by sending REAL txs."""
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="DB not ready")

    rnd = random.Random(req.seed)

        # Resolve which local keys actually exist. If some expected demo keys (vehicle1/edge*/cloud1)
    # are missing from the local keyring, fall back to the admin key so demo seed can still run.
    def _key_addr(name: str) -> str:
        try:
            return chain.keys_show_addr(name).strip()
        except Exception:
            return ""

    admin_name = s.admin_name
    admin_addr = _key_addr(admin_name) or s.admin_addr

    def pick_actor(preferred_name: str, preferred_addr: str) -> tuple[str, str]:
        addr = _key_addr(preferred_name)
        if addr:
            return preferred_name, addr
        # fall back to admin
        return admin_name, admin_addr

    cloud_name, cloud_addr = pick_actor(s.cloud_name, s.cloud_addr)
    vehicle_name, vehicle_addr = pick_actor(s.vehicle1_name, s.vehicle1_addr)

    edge1_name, edge1_addr = pick_actor(s.edge1_name, s.edge1_addr)
    edge2_name, edge2_addr = pick_actor(s.edge2_name, s.edge2_addr)
    edge3_name, edge3_addr = pick_actor(s.edge3_name, s.edge3_addr)

    # Best-effort register edges (idempotent). Ignore errors (already exists, etc.).
    for addr, region in [(edge1_addr, "A"), (edge2_addr, "A"), (edge3_addr, "B")]:
        try:
            chain.tx(chain.module, "register-edge", [addr, region], from_name=admin_name)
        except Exception:
            pass

    # helper to choose which edge to assign
    def pick_edge(region: str, i: int) -> str:
        if region == "A":
            if req.bad_edge_mode and i % 2 == 1:
                return edge2_addr
            return edge1_addr
        return edge3_addr

    def edge_name_by_addr(addr: str) -> str:
        return {edge1_addr: edge1_name, edge2_addr: edge2_name, edge3_addr: edge3_name}.get(addr, admin_name)

    created_tasks: list[str] = []
    created_logs = 0
    created_props_before = _safe_query(chain, chain.module, "list-governance-proposal", [])
    props_before = len(created_props_before.get("governanceProposal") or created_props_before.get("governanceProposals") or [])

    now_ts = int(datetime.utcnow().timestamp())

    for region in ["A", "B"]:
        for i in range(req.tasks_per_region):
            task_id = f"demo-{region}-{i+1:04d}"
            chosen_edge = pick_edge(region, i)
            payload = {"task_id": task_id, "region": region, "n": rnd.randint(1, 10)}
            payload_hash = sha256_hex_of_json(payload)
            created_ts = str(int(datetime.now(timezone.utc).timestamp()))

            # createTask
            chain.tx(
                chain.module,
                "create-task",
                [
                    task_id,
                    vehicle_addr,
                    chosen_edge,
                    region,
                    "CREATED",
                    "default",
                    payload_hash,
                    "",
                    "",
                    "",
                    "false",
                    created_ts,
                    created_ts,
                ],
                from_name=vehicle_name,
            )
            created_tasks.append(task_id)

            # logs
            edge_addr = chosen_edge
            edge_name = edge_name_by_addr(edge_addr)

            base_latency = rnd.randint(50, 300)
            bad = req.bad_edge_mode and (edge_addr == edge2_addr)

            stages = ["RECV", "EXEC", "RESULT"]
            stage_offsets = [0, rnd.randint(1, 3), rnd.randint(4, 6)]
            for st, off in zip(stages, stage_offsets):
                latency = base_latency + off * 20
                cpu = rnd.randint(10, 80)
                mem = rnd.randint(50, 200)
                net = rnd.randint(5, 50)

                if bad and st in ["EXEC", "RESULT"]:
                    latency = rnd.randint(2500, 6000)
                    cpu = rnd.randint(200, 800)
                    mem = rnd.randint(800, 2000)
                    net = rnd.randint(200, 800)

                ts = now_ts - rnd.randint(0, req.days_span * 24 * 3600)

                result_hash = ""
                if st == "RESULT":
                    result_json = {"task_id": task_id, "ok": not bad, "value": rnd.random()}
                    result_hash = sha256_hex_of_json(result_json)

                detail = {
                    "taskId": task_id,
                    "edgeAddr": edge_addr,
                    "stage": st,
                    "ts": ts,
                    "cpu_ms": cpu,
                    "mem_mb_peak": mem,
                    "net_kb": net,
                    "latency_ms": latency,
                    "resultHash": result_hash,
                }
                log_hash = sha256_hex_of_json(detail)

                # store DB
                with session_scope(SessionLocal) as db:
                    db.add(
                        LogDetail(
                            task_id=task_id,
                            edge_addr=edge_addr,
                            stage=st,
                            ts=ts,
                            cpu_ms=cpu,
                            mem_mb_peak=mem,
                            net_kb=net,
                            latency_ms=latency,
                            result_hash=result_hash or None,
                            log_hash=log_hash,
                            detail_json=json.dumps(detail, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                        )
                    )

                # submitLogSummary tx (edge signs)
                txr = chain.tx(
                    chain.module,
                    "submit-log-summary",
                    [st, task_id, log_hash, result_hash or "", str(cpu), str(mem), str(latency), str(net), str(ts)],
                    from_name=edge_name,
                )

                with session_scope(SessionLocal) as db:
                    row = db.query(LogDetail).filter(LogDetail.log_hash == log_hash).one_or_none()
                    if row:
                        row.tx_hash = txr.txhash
                        row.height = txr.height
                        row.signer = edge_addr
                        row.msg_type = "submitLogSummary"

                created_logs += 1

                if st == "RESULT":
                    # recordResult (cloud signs tx)
                    # sign resultHash with edge key
                    with tempfile.NamedTemporaryFile("w", delete=False) as f:
                        f.write(result_hash)
                        sign_file = f.name
                    try:
                        sig = chain.keys_sign(edge_name, sign_file)
                        verified = chain.keys_verify(edge_addr, sig, sign_file)
                        txres = chain.tx(chain.module, "record-result", [task_id, result_hash, sig, str(verified).lower()], from_name=cloud_name)

                        with session_scope(SessionLocal) as db:
                            upsert_task_result(
                                db,
                                task_id=task_id,
                                chosen_edge_addr=edge_addr,
                                result_json=result_json,
                                result_hash=result_hash,
                                result_sig=sig,
                                verified=verified,
                                tx_hash=txres.txhash,
                                height=txres.height,
                                signer=s.cloud_addr,
                            )
                    finally:
                        try:
                            os.unlink(sign_file)
                        except Exception:
                            pass

            # feedback
            # NOTE: newer tbthreed CLI expects exactly 2 positional args:
            #   submit-task-feedback <task_id> <accepted>
            # Keep demo seed compatible by only sending these two.
            if bad:
                chain.tx(
                    chain.module,
                    "submit-task-feedback",
                    [task_id, "false"],
                    from_name=vehicle_name,
                )
            else:
                chain.tx(
                    chain.module,
                    "submit-task-feedback",
                    [task_id, "true"],
                    from_name=vehicle_name,
                )

            # a few consensus events
            if i % 5 == 0:
                missed = 0 if not bad else rnd.randint(5, 20)
                doubles = 0 if not bad else rnd.randint(0, 1)
                part = 950 if not bad else rnd.randint(200, 700)
                chain.tx(
                    chain.module,
                    "report-consensus-event",
                    [edge_addr, str(missed), str(doubles), str(part)],
                    from_name=cloud_name,
                )

    created_props_after = _safe_query(chain, chain.module, "list-governance-proposal", [])
    props_after = len(created_props_after.get("governanceProposal") or created_props_after.get("governanceProposals") or [])

    return {
        "ok": True,
        "seed": req.seed,
        "tasks": len(created_tasks),
        "logs": created_logs,
        "proposals_before": props_before,
        "proposals_after": props_after,
    }
