# DATA BRAIN — Backend (阶段0 + 阶段1)

AI/ML 交易大脑后端骨架。当前实现：

- **阶段0 — 桥接层**：统一的 `TradingBridge` 抽象，屏蔽底层执行层。
  - `mock`：确定性合成数据，**无需任何凭证即可运行**（默认）。
  - `metaapi`：通过 [MetaApi](https://metaapi.cloud) 接入真实 MT4/MT5 账号（骨架）。
- **阶段1 — 功能2 分析版**：
  - 市场环境分类引擎（ADX / +DI/-DI / ATR / 已实现波动率 / 交易时段）。
  - 交易历史抓取 → 按"平仓时刻环境标签"归因 → 每个 EA 的环境表现报告与洞察。

> 不做自动下单。EA 自动切换（阶段2）在此基础上扩展。

## 快速开始

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

打开 API 文档：http://localhost:8000/docs

## 主要接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| GET | `/api/accounts/{account_id}` | 账户信息（阶段0 验证桥接） |
| GET | `/api/candles` | 历史 K 线 |
| GET | `/api/regime` | 市场环境标签序列 |
| GET | `/api/analysis/{account_id}` | EA 环境表现分析（功能2 核心） |

示例：

```bash
curl "http://localhost:8000/api/analysis/acc-1?symbol=XAUUSD&days=40"
```

## 接入真实账号（MetaApi）

1. 在 `requirements.txt` 取消 `metaapi-cloud-sdk` 注释并安装。
2. 复制 `.env.example` 为 `.env`，设置：

```
BRIDGE_PROVIDER=metaapi
METAAPI_TOKEN=你的token
```

3. 在 MetaApi 添加你的 MT4/MT5 账号，拿到 account_id，调用接口时用它。

> EA 启停（`set_ea_enabled`）需配合自建桥接 EA 的指令协议，见仓库根 `docs/` 设计文档 §0/§4。

## 测试

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

## 目录结构

```
app/
  bridge/      桥接抽象 + mock + metaapi + factory
  regime/      市场环境分类引擎
  analysis/    EA 环境表现分析
  api/         FastAPI 路由
  schemas.py   统一数据模型
  config.py    配置
  main.py      应用入口
tests/         单元 + 接口测试
```
