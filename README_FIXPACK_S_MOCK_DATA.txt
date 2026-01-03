Fixpack S (MOCK_DATA 伪造假数据)

作用
- 不依赖 tbthreed / 链节点 / demo/seed 交易
- 后端直接返回“假数据”，让前端页面能正常展示 Edges/Tasks/Governance/Audit
- 同时会初始化 sqlite 并预插入审计页需要的 LogDetail/TaskResultDetail 行（只用于 UI 展示）

如何启用（推荐）
1) 停掉后端（CTRL+C）

2) 重建数据库（可选，但你刚刚说想重建）
   进入 backend/data 目录，把旧库删除/移走：

   cd ~/work/tb3-mvp-v2/tb3-mvp-v2/backend
   rm -f data/tbthree.db data/tb3.db
   rm -f data/.auto_demo_seed_done.json   # 如果存在

3) 修改 backend/.env（没有就新建），加入：

   MOCK_DATA=1
   AUTO_DEMO_SEED=0

   # 可选：更换假数据随机种子（不同 seed 会生成不同数据，但仍然稳定）
   # MOCK_DATA_SEED=42

4) 启动后端：

   cd ~/work/tb3-mvp-v2/tb3-mvp-v2/backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000

5) 打开前端页面，应该会立即看到假数据。
   - http://localhost:8000/ 现在不会 404，会返回 docs/health 信息
   - /demo/seed 在 MOCK_DATA=1 时会被跳过（直接返回 ok）

关闭 MOCK_DATA
- 把 .env 里的 MOCK_DATA=1 改成 0 或删掉，然后重启后端
