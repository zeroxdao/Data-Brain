"""MetaApi 桥接实现（阶段0 真实接入）。

依赖可选包 metaapi-cloud-sdk。仅当 BRIDGE_PROVIDER=metaapi 且安装该包时启用。
代码保持精简，作为接入真实 MT4/MT5 账号的起点骨架。

文档参考: https://metaapi.cloud/docs/client/
"""
from __future__ import annotations

from datetime import datetime

from app.bridge.base import TradingBridge
from app.schemas import AccountInfo, Candle, Deal, DealType


class MetaApiBridge(TradingBridge):
    """通过 MetaApi 云服务连接 MT4/MT5 账号。"""

    def __init__(self, token: str, domain: str = "agiliumtrade.agiliumtrade.ai") -> None:
        try:
            from metaapi_cloud_sdk import MetaApi  # type: ignore
        except ImportError as exc:  # pragma: no cover - 仅在真实接入时触发
            raise RuntimeError(
                "未安装 metaapi-cloud-sdk。请先 `pip install metaapi-cloud-sdk` "
                "并在 requirements.txt 中取消对应注释。"
            ) from exc

        self._token = token
        self._api = MetaApi(token, {"domain": domain})
        self._connections: dict[str, object] = {}

    async def _get_connection(self, account_id: str):
        if account_id in self._connections:
            return self._connections[account_id]
        account = await self._api.metatrader_account_api.get_account(account_id)
        if account.state not in ("DEPLOYED",):
            await account.deploy()
        await account.wait_connected()
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        self._connections[account_id] = connection
        return connection

    async def get_account(self, account_id: str) -> AccountInfo:
        conn = await self._get_connection(account_id)
        info = await conn.get_account_information()  # type: ignore[attr-defined]
        return AccountInfo(
            account_id=account_id,
            broker=info.get("broker"),
            currency=info.get("currency", "USD"),
            balance=float(info.get("balance", 0)),
            equity=float(info.get("equity", 0)),
            leverage=int(info.get("leverage", 100)),
        )

    async def get_candles(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> list[Candle]:
        conn = await self._get_connection_for_history()
        raw = await conn.get_historical_candles(symbol, timeframe, start, 1000)  # type: ignore
        candles: list[Candle] = []
        for c in raw or []:
            t = c["time"]
            if t < start or t > end:
                continue
            candles.append(
                Candle(
                    time=t,
                    open=float(c["open"]),
                    high=float(c["high"]),
                    low=float(c["low"]),
                    close=float(c["close"]),
                    volume=float(c.get("tickVolume", 0)),
                )
            )
        return candles

    async def _get_connection_for_history(self):
        # 历史 K 线可用任一已连接账号；这里简化为复用首个连接
        if not self._connections:
            raise RuntimeError("尚无已连接账号，无法读取历史 K 线。")
        return next(iter(self._connections.values()))

    async def get_deals(
        self,
        account_id: str,
        start: datetime,
        end: datetime,
        symbol: str | None = None,
    ) -> list[Deal]:
        conn = await self._get_connection(account_id)
        history = await conn.get_deals_by_time_range(start, end)  # type: ignore[attr-defined]
        deals: list[Deal] = []
        for d in history.get("deals", []) if isinstance(history, dict) else history:
            if symbol and d.get("symbol") != symbol:
                continue
            if d.get("entryType") not in ("DEAL_ENTRY_OUT", None):
                continue
            deals.append(
                Deal(
                    deal_id=str(d.get("id")),
                    symbol=d.get("symbol", symbol or ""),
                    ea_name=d.get("comment") or None,
                    type=DealType.BUY if d.get("type") == "DEAL_TYPE_BUY" else DealType.SELL,
                    volume=float(d.get("volume", 0)),
                    open_time=d.get("time"),
                    close_time=d.get("time"),
                    open_price=float(d.get("price", 0)),
                    close_price=float(d.get("price", 0)),
                    profit=float(d.get("profit", 0)),
                    commission=float(d.get("commission", 0)),
                    swap=float(d.get("swap", 0)),
                )
            )
        return deals

    async def set_ea_enabled(self, account_id: str, ea_name: str, enabled: bool) -> bool:
        # 真实实现：通过桥接 EA 的指令通道下发启停/权重指令。
        # MetaApi 本身不直接控制终端里的 EA，需配合自建桥接 EA 或全局变量协议。
        raise NotImplementedError(
            "EA 启停需配合自建桥接 EA 的指令协议实现（见设计文档 §0/§4）。"
        )
