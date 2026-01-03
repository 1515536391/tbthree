# TB3 可信交互引擎链 (TB3) — 单链模拟跨域 MVP

> 交付目标：**本地可跑通 + 前端酷炫统一深色风 + TB31~TB34 完整闭环 + Demo 假数据不影响真实功能**。

本仓库包含三部分：

- `chain/`：Cosmos SDK 链（Ignite v29.6.1-dev / Cosmos SDK v0.53.3）
- `backend/`：FastAPI（托管 demo mnemonics/keys，代签发交易，验签，SQLite 日志明细库）
- `frontend/`：Vue2 + Element-UI + ECharts（深色统一炫酷 dashboard）

---

## 你最终会得到什么？

- **TB31**：链上信誉值（主观逻辑 b/d/u + score）+ 3 态 HMM 概率（T/S/M）
- **TB32**：日志摘要上链（logHash + 元数据），后端 DB 存明细，前端可一键对账（match/mismatch）
- **TB33**：`score<0.3` 自动生成治理提案（PENDING），管理员一键审批（降权/冻结任务/冻结共识）
- **TB34**：Edge 签名 resultHash，后端验签 + 上链存证（resultHash+sig+verified）
- **Demo**：一键灌数据 `/demo/seed`（真实 tx 产生，不 hardcode），edge2 走坏路径可触发治理

---

## 0. 前置环境

你本机需要：

- Go `1.24.1`
- Ignite CLI `v29.6.1-dev`
- Node.js `>=18`
- Python `>=3.10`

---

## 1. 一键启动（推荐流程）

```bash
make up
```

第一次运行会自动执行 `make bootstrap`：

- scaffold 链到 `chain/tb3/`
- scaffold tb3 模块 + 对象 + 消息
- 应用 `chain/overrides/` 中的业务逻辑（TB31~TB34）

> 启动后：
> - 前端：`http://127.0.0.1:8080`
> - 后端：`http://127.0.0.1:8000/health`

---

## 2. 初始化角色账号 + 注册边缘节点

```bash
make init
```

它会：

- 在链的 keyring(test) 中创建：cloud1、vehicle1、edge1~edge3
- 给这些账号从 alice 转账（faucet）
- 将地址写入 `backend/.env`
- 用 `alice`(admin) 注册 edge：
  - edge1 region=A
  - edge2 region=A
  - edge3 region=B

---

## 3. 灌入演示数据（真实 tx）

方式 A：前端按钮

- Dashboard 顶部点 **“一键填充演示数据”**

方式 B：命令行

```bash
make seed
```

---

## 4. 一键跑完整演示（init + seed）

```bash
make demo
```

---

## 5. 常用命令

- 看日志：

```bash
make logs
```

- 停止全部：

```bash
make down
```

- 重置（清链数据目录 + 清后端 DB）：

```bash
make reset
```

---

## 说明

- 本项目为了“操作简单”，后端通过调用链 CLI（`tb3d`）来发交易与签名/验签。
- Demo 假数据遵循“真实闭环”：所有数据都通过 **真实 tx** 与 **真实验签/写库** 产生，前端不会 hardcode 假列表。
