TB3 Backend Fixpack M (seed broadcast-mode)

Changes:
- backend/app/chain_cli.py: set tx '--broadcast-mode' from 'block' to 'sync'.
  Reason: current tbthreed (create-task --help) supports only (sync|async) and errors on 'block'.

How to apply (from project root ~/work/tb3-mvp-v2/tb3-mvp-v2):
  tar -xzf /mnt/d/edge/tb3_backend_seed_broadcast_fixpack_M.tgz --touch

Then restart backend and retry /demo/seed.
