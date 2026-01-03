# Chain (Ignite/Cosmos) — TB3

本目录用于放置 Ignite scaffolding 生成的链工程。

当前仓库采用 **脚本一键 scaffold**（确保与你本机的 Ignite v29.6.1-dev 与 Cosmos SDK v0.53.3 模板一致）。

首次运行：

```bash
make bootstrap
```

之后启动：

```bash
make up
```

注意：`make bootstrap` 会在 `chain/tb3/` 下生成链工程，并在生成后把 `chain/overrides/` 里的业务逻辑文件覆盖到生成目录中。
