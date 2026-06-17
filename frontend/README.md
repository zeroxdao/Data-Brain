# DATA BRAIN — Frontend Dashboard

Next.js 16 + Tailwind CSS + SWR + lightweight-charts 前端仪表盘。

## 页面

| 路由 | 内容 |
|---|---|
| `/` | 总览（账户、K 线图、调度状态、EA 决策卡片、环境历史） |
| `/orchestrator` | 调度大脑控制（启动/停止/熔断重置 + 决策日志） |
| `/analysis` | EA 历史表现分析报告（按市场环境拆分） |
| `/regime` | 市场环境面板（ADX/ATR/波动率 + K 线图） |
| `/log` | 完整决策日志表格 |
| `/settings` | 配置说明 |

## 快速开始

```bash
cd frontend
cp .env.local.example .env.local   # 按需修改 API 地址
npm install
npm run dev      # 开发模式 http://localhost:3000
npm run build    # 生产构建
```

> 后端 FastAPI 需先在 http://localhost:8000 运行，见 `backend/README.md`。

## 接入真实账号

在 `.env.local` 中设置：

```
NEXT_PUBLIC_API_URL=https://你的后端域名
```

然后在各页面的 `ACCOUNT_ID` / `SYMBOL` 常量替换为真实账号 ID 和交易品种。
（后续版本会改为用户登录态动态管理。）
