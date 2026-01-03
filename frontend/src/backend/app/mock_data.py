"""Mock dataset + helpers for the TB3 demo UI.

This module is used when MOCK_DATA=1 to serve *read* APIs from deterministic
fake data (no chain required) and (optionally) to pre-fill the local sqlite DB.

Goals:
- Fast: no chain calls, no long-running seed.
- Pretty: non-trivial scores, HMM, and b/d/u distributions.
- Useful: tasks / proposals / audit logs look realistic and varied.

Important:
- Values like `score`, `hmm_*`, `b/d/u` follow the common on-chain convention of
  being scaled integers (e.g. score in [0..1] is stored as int(score*1_000_000)).
  The frontend often divides to show decimals, so we generate scaled ints.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any


# bech32 charset (same as cosmos / bech32 human-readable payload alphabet)
_BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _hash_hex(label: str, seed: int, nbytes: int = 32) -> str:
    h = hashlib.sha256(f"{seed}:{label}".encode()).digest()
    if nbytes <= len(h):
        return h[:nbytes].hex()
    # extend deterministically
    out = bytearray(h)
    while len(out) < nbytes:
        out.extend(hashlib.sha256(out).digest())
    return bytes(out[:nbytes]).hex()


def fake_cosmos_addr(label: str, seed: int, prefix: str = "cosmos") -> str:
    """Generate a deterministic, bech32-ish address string.

    This is NOT a valid bech32 checksum address, but it is stable and visually
    similar. The frontend only needs a string.
    """

    raw = bytes.fromhex(_hash_hex(f"addr:{label}", seed, nbytes=32))
    # map bytes to bech32 alphabet; 38 chars is close to typical cosmos addresses
    payload = "".join(_BECH32[b % len(_BECH32)] for b in raw)[:38]
    return f"{prefix}1{payload}"


def fake_tx_hash(label: str, seed: int) -> str:
    return _hash_hex(f"tx:{label}", seed, nbytes=32)


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def _mk_prob_triplet(rnd: random.Random, a: int, b: int, c: int, total: int = 1000) -> tuple[int, int, int]:
    """Return ints (x,y,z) that sum to `total` with some jitter."""

    base = [a, b, c]
    # jitter each bucket but keep non-negative
    jitter = [rnd.randint(-40, 40) for _ in range(3)]
    vals = [max(0, base[i] + jitter[i]) for i in range(3)]
    s = sum(vals) or 1
    scaled = [int(total * v / s) for v in vals]
    # fix rounding drift
    drift = total - sum(scaled)
    scaled[0] += drift
    return int(scaled[0]), int(scaled[1]), int(scaled[2])


def _mk_score(rnd: random.Random, base: float) -> int:
    # scaled by 1_000_000
    v = int(base * 1_000_000) + rnd.randint(-60_000, 60_000)
    return _clamp(v, 0, 1_000_000)


def _iso_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def build_mock_dataset(seed: int, addrs: dict[str, str]) -> dict[str, Any]:
    rnd = random.Random(seed)
    now = int(time.time())

    # Prefer provided addrs (so settings stay consistent), but fall back to
    # deterministic fake ones if missing.
    def A(key: str) -> str:
        v = (addrs or {}).get(key, "")
        if v:
            return v
        return fake_cosmos_addr(key, seed)

    admin = A("admin")
    cloud = A("cloud")
    vehicle = A("vehicle")
    edge1 = A("edge1")
    edge2 = A("edge2")
    edge3 = A("edge3")

    # --- edges ---
    # HMM + b/d/u are scaled by 1000 for 2-decimal display after division.
    # score is scaled by 1_000_000.
    edges_cfg = [
        (edge1, "A", "ACTIVE", 0.86, (820, 140, 40), (760, 170, 70)),  # strong
        (edge2, "A", "ACTIVE", 0.28, (220, 180, 600), (260, 240, 500)),  # malicious-ish
        (edge3, "B", "ACTIVE", 0.62, (610, 260, 130), (520, 310, 170)),  # mixed
    ]

    edges: list[dict[str, Any]] = []
    for i, (addr, region, status, base_score, hmm_base, bdu_base) in enumerate(edges_cfg, start=1):
        score = _mk_score(rnd, base_score)
        hmm_t, hmm_s, hmm_m = _mk_prob_triplet(rnd, *hmm_base)
        b, d, u = _mk_prob_triplet(rnd, *bdu_base)
        edges.append(
            {
                "edgeAddr": addr,
                "region": region,
                "status": status,
                "score": str(score),
                "hmmT": str(hmm_t),
                "hmmS": str(hmm_s),
                "hmmM": str(hmm_m),
                "b": str(b),
                "d": str(d),
                "u": str(u),
            }
        )

    # --- proposals ---
    # keep structure compatible with earlier mock: governanceProposal: [ { proposalId, ... } ]
    def _proposal(pid: int, status: str, title: str, desc: str, days_ago: int, days_to_end: int) -> dict[str, Any]:
        submit = now - days_ago * 86400
        end = submit + days_to_end * 86400
        yes = rnd.randint(50, 90)
        no = rnd.randint(0, 30)
        abstain = rnd.randint(0, 10)
        veto = rnd.randint(0, 10)
        return {
            "proposalId": str(pid),
            "title": title,
            "desc": desc,
            "proposerAddr": admin,
            "status": status,
            "type": "PARAM_CHANGE",
            "yes": str(yes),
            "no": str(no),
            "abstain": str(abstain),
            "veto": str(veto),
            "submitTs": str(submit),
            "endTs": str(end),
        }

    proposals = [
        _proposal(101, "PENDING", "提案#101: 降低恶意边缘节点权重", "对 edge2 的惩罚系数从 0.7 调整为 0.85", 1, 3),
        _proposal(102, "PENDING", "提案#102: 提升可信节点奖励", "对 Trusted 状态节点增加积分奖励", 2, 4),
        _proposal(99, "PASSED", "提案#99: 调整 HMM 先验", "更新 HMM 初始分布以适配新数据", 10, 2),
        _proposal(98, "REJECTED", "提案#98: 收紧任务超时阈值", "将任务超时由 60s 下调至 30s", 14, 2),
    ]

    # --- tasks ---
    tasks: list[dict[str, Any]] = []
    log_summaries: list[dict[str, Any]] = []
    log_details: list[dict[str, Any]] = []
    task_results: list[dict[str, Any]] = []

    regions = ["A", "B"]
    edges_by_region = {"A": [edge1, edge2], "B": [edge3]}

    def _choose_edge(region: str, i: int) -> str:
        # make edge2 appear sometimes to drive "low trust" warnings
        if region == "A" and i % 5 == 0:
            return edge2
        return edges_by_region[region][0]

    def _make_result(task_id: str, ok: bool) -> dict[str, Any]:
        v = rnd.random()
        return {"task_id": task_id, "ok": ok, "value": v, "note": "mock" if ok else "mismatch"}

    statuses = [
        ("CREATED", 0.15),
        ("EXECUTING", 0.20),
        ("DONE", 0.55),
        ("FAILED", 0.10),
    ]

    def _sample_status() -> str:
        r = rnd.random()
        acc = 0.0
        for s, p in statuses:
            acc += p
            if r <= acc:
                return s
        return "DONE"

    n_per_region = 12
    for region in regions:
        for i in range(1, n_per_region + 1):
            task_id = f"demo-{region}-{i:04d}"
            chosen_edge = _choose_edge(region, i)
            st = _sample_status()

            created = now - rnd.randint(1, 21) * 86400 - rnd.randint(0, 3600)
            updated = created + rnd.randint(10, 3600)

            payload = {"task_id": task_id, "region": region, "n": rnd.randint(1, 10), "p": rnd.random()}
            payload_hash = _hash_hex("payload:" + json.dumps(payload, sort_keys=True), seed)

            ok = st == "DONE"
            result_hash = ""
            result_json: dict[str, Any] | None = None
            if st in ("DONE", "FAILED"):
                result_json = _make_result(task_id, ok=ok)
                result_hash = _hash_hex("result:" + json.dumps(result_json, sort_keys=True), seed)

            profile = rnd.choice(["default", "latency", "throughput", "secure"])

            tasks.append(
                {
                    "taskId": task_id,
                    "vehicleAddr": vehicle,
                    "chosenEdgeAddr": chosen_edge,
                    "region": region,
                    "status": st,
                    "profile": profile,
                    "payloadHash": payload_hash,
                    "resultHash": result_hash,
                    "createdTs": str(created),
                    "updatedTs": str(updated),
                }
            )

            # --- logs per task ---
            stages: list[str]
            if st == "CREATED":
                stages = ["RECV"]
            elif st == "EXECUTING":
                stages = ["RECV", "EXEC"]
            else:
                stages = ["RECV", "EXEC", "RESULT"]

            base_latency = rnd.randint(60, 320)
            is_bad = chosen_edge == edge2
            for j, stage in enumerate(stages):
                ts = created + j * rnd.randint(60, 240)

                cpu = rnd.randint(8, 85)
                mem = rnd.randint(60, 260)
                net = rnd.randint(5, 80)
                latency = base_latency + j * rnd.randint(15, 60)

                # make edge2 look slower / heavier
                if is_bad and stage in ("EXEC", "RESULT"):
                    cpu = rnd.randint(180, 900)
                    mem = rnd.randint(600, 2400)
                    net = rnd.randint(120, 900)
                    latency = rnd.randint(2500, 8000)

                # on RESULT stage we attach result hash (if exists)
                res_hash = result_hash if (stage == "RESULT" and result_hash) else ""

                detail = {
                    "taskId": task_id,
                    "edgeAddr": chosen_edge,
                    "stage": stage,
                    "ts": ts,
                    "cpu_ms": cpu,
                    "mem_mb_peak": mem,
                    "net_kb": net,
                    "latency_ms": latency,
                    "resultHash": res_hash,
                    "profile": profile,
                }

                log_hash = _hash_hex("log:" + json.dumps(detail, sort_keys=True), seed)

                tx_hash = fake_tx_hash(f"{task_id}:{stage}", seed)
                height = 10_000 + (i * 10) + j

                log_summaries.append(
                    {
                        "stage": stage,
                        "taskId": task_id,
                        "logHash": log_hash,
                        "resultHash": res_hash,
                        "cpu": str(cpu),
                        "mem": str(mem),
                        "latency": str(latency),
                        "net": str(net),
                        "signer": chosen_edge,
                        "txHash": tx_hash,
                        "height": str(height),
                        "ts": str(ts),
                        "edgeAddr": chosen_edge,
                    }
                )

                # Log detail row (DB-like)
                log_details.append(
                    {
                        "task_id": task_id,
                        "edge_addr": chosen_edge,
                        "stage": stage,
                        "ts": ts,
                        "cpu_ms": cpu,
                        "mem_mb_peak": mem,
                        "net_kb": net,
                        "latency_ms": latency,
                        "result_hash": res_hash or None,
                        "log_hash": log_hash,
                        "detail_json": json.dumps(detail, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                        "tx_hash": tx_hash,
                        "height": height,
                        "signer": chosen_edge,
                        "msg_type": "submitLogSummary" if stage != "RESULT" else "submitLogSummary/RESULT",
                    }
                )

            # task result row (DB-like)
            if result_json and result_hash:
                # simple "sig" placeholders
                sig = _hash_hex("sig:" + result_hash, seed)[:96]
                task_results.append(
                    {
                        "task_id": task_id,
                        "chosen_edge_addr": chosen_edge,
                        "result_json": result_json,
                        "result_hash": result_hash,
                        "result_sig": sig,
                        "verified": "true" if ok else "false",
                        "tx_hash": fake_tx_hash(f"{task_id}:record-result", seed),
                        "height": 20_000 + i,
                        "signer": cloud,
                    }
                )

    return {
        "edges": edges,
        "tasks": tasks,
        "proposals": proposals,
        "log_summaries": log_summaries,
        "log_details": log_details,
        "task_results": task_results,
        "meta": {
            "seed": seed,
            "generated_at": _iso_ts(now),
        },
    }


# ---- API helpers used by main.py ----

def mock_list_edges(seed: int, addrs: dict[str, str]) -> dict[str, Any]:
    ds = build_mock_dataset(seed, addrs)
    return {"edges": ds["edges"]}


def mock_list_tasks(seed: int, addrs: dict[str, str]) -> dict[str, Any]:
    ds = build_mock_dataset(seed, addrs)
    return {"tasks": ds["tasks"]}


def mock_list_proposals(seed: int, addrs: dict[str, str]) -> dict[str, Any]:
    ds = build_mock_dataset(seed, addrs)
    return {"governanceProposal": ds["proposals"]}


def mock_list_log_summaries(seed: int, addrs: dict[str, str]) -> dict[str, Any]:
    ds = build_mock_dataset(seed, addrs)
    return {"log": ds["log_summaries"]}


def _by(items: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for it in items:
        out[str(it.get(key, ""))] = it
    return out


def mock_audit_task_logs(seed: int, addrs: dict[str, str], task_id: str) -> dict[str, Any]:
    """Return richer compare rows for the audit page.

    We simulate:
    - matches (chain log hash == db recomputed hash)
    - mismatches (db detail differs)
    - missing db rows
    - occasional db-only orphan rows
    """

    rnd = random.Random(seed ^ 0xA11D)
    ds = build_mock_dataset(seed, addrs)

    chain_logs = [l for l in ds["log_summaries"] if l["taskId"] == task_id]

    # Construct a db view based on details, then mutate a subset.
    details = [d for d in ds["log_details"] if d["task_id"] == task_id]
    db_by_log = _by([{**d, "logHash": d["log_hash"], "ts": str(d["ts"])} for d in details], "logHash")

    items: list[dict[str, Any]] = []
    mismatch = 0
    missing = 0
    ok = 0

    for ch in chain_logs:
        log_hash = ch["logHash"]
        db = db_by_log.get(log_hash)

        mode = rnd.random()
        if mode < 0.70:
            # match
            match = True
            ok += 1
        elif mode < 0.85:
            # mismatch: tweak db detail_json to change recomputed hash
            match = False
            mismatch += 1
            if db:
                try:
                    dj = json.loads(db.get("detail_json") or "{}")
                except Exception:
                    dj = {"_": "bad_json"}
                dj["audit_note"] = "db_mutated"
                new_json = json.dumps(dj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                new_hash = _hash_hex("log:" + json.dumps(dj, sort_keys=True), seed)
                db = {**db, "detail_json": new_json, "log_hash": new_hash, "logHash": new_hash}
        else:
            # missing db
            match = False
            missing += 1
            db = None

        items.append(
            {
                "stage": ch["stage"],
                "ts": ch["ts"],
                "chainLogHash": log_hash,
                "dbLogHash": (db.get("logHash") if db else ""),
                "match": match,
                "txHash": ch.get("txHash", ""),
                "height": ch.get("height", ""),
                "chain": ch,
                "db": db,
            }
        )

    # Add an orphan db row sometimes
    if rnd.random() < 0.35:
        orphan_hash = fake_tx_hash(f"{task_id}:orphan", seed)
        items.append(
            {
                "stage": "ORPHAN",
                "ts": str(int(time.time()) - 1234),
                "chainLogHash": "",
                "dbLogHash": orphan_hash,
                "match": False,
                "txHash": "",
                "height": "",
                "chain": None,
                "db": {
                    "task_id": task_id,
                    "stage": "ORPHAN",
                    "logHash": orphan_hash,
                    "detail_json": json.dumps({"orphan": True, "task_id": task_id}, ensure_ascii=False),
                },
            }
        )

    return {
        "task_id": task_id,
        "items": items,
        "summary": {
            "chain_rows": len(chain_logs),
            "matches": ok,
            "mismatches": mismatch,
            "missing_db": missing,
        },
        "meta": ds.get("meta"),
    }


# ---- optional: pre-fill local sqlite DB with some rows ----

def ensure_mock_db(SessionLocal, seed: int, addrs: dict[str, str]) -> None:
    """Populate the local sqlite DB with a subset of mock data.

    Safe to call multiple times; we only insert if the tables are empty.
    """

    # Import models lazily (avoids import cycles during app startup)
    from .models import LogDetail, TaskResultDetail

    ds = build_mock_dataset(seed, addrs)

    with SessionLocal() as db:
        if db.query(LogDetail).first() is None:
            db.add_all(
                [
                    LogDetail(
                        task_id=r["task_id"],
                        edge_addr=r["edge_addr"],
                        stage=r["stage"],
                        ts=r["ts"],
                        cpu_ms=r["cpu_ms"],
                        mem_mb_peak=r["mem_mb_peak"],
                        net_kb=r["net_kb"],
                        latency_ms=r["latency_ms"],
                        result_hash=r.get("result_hash"),
                        log_hash=r["log_hash"],
                        detail_json=r["detail_json"],
                        tx_hash=r.get("tx_hash", ""),
                        height=r.get("height", 0),
                        signer=r.get("signer", ""),
                        msg_type=r.get("msg_type", ""),
                    )
                    for r in ds["log_details"]
                ]
            )

        if db.query(TaskResultDetail).first() is None:
            db.add_all(
                [
                    TaskResultDetail(
                        task_id=r["task_id"],
                        chosen_edge_addr=r["chosen_edge_addr"],
                        result_json=json.dumps(r["result_json"], ensure_ascii=False, sort_keys=True),
                        result_hash=r["result_hash"],
                        result_sig=r["result_sig"],
                        verified=r["verified"],
                        tx_hash=r["tx_hash"],
                        height=r["height"],
                        signer=r["signer"],
                    )
                    for r in ds["task_results"]
                ]
            )

        db.commit()
