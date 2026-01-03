FIXPACK T — Rich mock data (tasks / proposals / audit compare)

What this does
- Builds on FIXPACK S mock mode (MOCK_DATA=1).
- Makes the fake data look much more "real":
  - Edge scores become meaningful (scaled by 1e6 -> UI shows ~0.15–0.90)
  - HMM (T/S/M) and b/d/u show non-zero distributions
  - Tasks list is larger and more varied (statuses, regions, edges)
  - Pending governance proposals: multiple, mixed statuses
  - Audit page compare: richer mix of match/mismatch/missing + per-row tx info
- Also de-duplicates addresses in mock mode (if your Settings has duplicates),
  so the UI won't show the same edgeAddr repeated.

Files changed
- backend/app/mock_data.py
- backend/app/main.py

How to apply
1) Extract from the repo root:
   tar -xzf tb3_backend_rich_mock_data_fixpack_T.tgz --touch

2) Ensure backend/.env has:
   MOCK_DATA=1

3) Restart backend:
   uvicorn app.main:app --host 0.0.0.0 --port 8000

Notes
- In MOCK_DATA=1, the backend read APIs (/edges, /tasks, /governance/proposals,
  /logs, /audit/tasks/*/logs) are served from mock data and will NOT reflect
  on-chain changes.
- Any tx endpoints you call manually (or demo/seed if you run it) may still
  hit the chain, but the dashboard will keep showing mock read data.
