# TB3 可审计可信交互 Demo

本仓库包含三部分：

- **Chain**：Ignite/Cosmos 链（tbthree）
- **Backend**：FastAPI 后端（对接链 RPC）
- **Frontend**：前端 Dashboard

## 运行前准备

### 系统依赖（建议版本）
- Node.js >= 18（建议 18/20）
- npm >= 9
- Python >= 3.12（你本地用的是 3.12）
- Ignite CLI（用于启动链）

> 如果你的机器没装 Ignite：请先按官方文档安装 Ignite CLI。

---


## 终端 1：启动链

```bash
cd ./chain/tbthree
make up

确认 RPC 正常：

curl -s http://127.0.0.1:26657/status | head
## 终端 2：启动后端（FastAPI）

建议使用虚拟环境：

cd ./backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


检查后端是否启动成功：

curl -s http://127.0.0.1:8000/health
curl -I http://127.0.0.1:8000/docs
## 终端 3：启动前端
cd ./frontend
npm install
npm run serve
