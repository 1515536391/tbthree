README_FIXPACK_Q.txt

What:
- Change backend demo seed default tasks_per_region from 15 -> 6.

Why:
- Reduce number of on-chain txs during /demo/seed so it finishes faster and is less likely to exceed the frontend 30s timeout.

Files overwritten:
- backend/app/schemas.py

How to apply (from project root, e.g. ~/work/tb3-mvp-v2/tb3-mvp-v2):
  tar -xzf /mnt/d/edge/tb3_backend_default_tasks_per_region_6_fixpack_Q.tgz --touch

Then restart backend (uvicorn).
