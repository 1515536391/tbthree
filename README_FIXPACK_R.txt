Fixpack R: Auto demo seed on backend startup + default tasks_per_region=6 + audit detached fix

What it does:
1) On backend startup, run demo seed in a background thread (so frontend不会再因 /demo/seed 等待而 30s 超时).
2) DemoSeedRequest 的默认 tasks_per_region 从 15 改为 6（更快）.
3) 修复 /audit/tasks/<id>/logs 的 SQLAlchemy DetachedInstanceError.

Env switches (optional):
- AUTO_DEMO_SEED=true/false (default: true)
- AUTO_DEMO_SEED_FORCE=true/false (default: false)
- AUTO_DEMO_SEED_TASKS_PER_REGION=6 (default follows DemoSeedRequest default)
- AUTO_DEMO_SEED_DAYS_SPAN=7
- AUTO_DEMO_SEED_BAD_EDGE_MODE=true
- AUTO_DEMO_SEED_SEED=42
- AUTO_DEMO_SEED_MAX_WAIT_SEC=120
- AUTO_DEMO_SEED_DELAY_SEC=2

If you want to re-seed from scratch:
- delete marker file: backend/data/.demo_seed_done
  or set AUTO_DEMO_SEED_FORCE=true
