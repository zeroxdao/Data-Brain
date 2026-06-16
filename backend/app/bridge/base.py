"""桥接层抽象接口。

任何执行层实现（MetaApi / 自建 VPS / mock）都实现这个接口，
上层业务（环境引擎、分析、调度）只依赖它，不关心底层细节。
"""
from __future__ import annotations

import abc
from datetime import datetime

from app.schemas import AccountInfo, Candle, Deal


class TradingBridge(abc.ABC):
    """统一的交易桥接接口。"""

    @abc.abstractmethod
    async def get_account(self, account_id: str) -> AccountInfo:
        """读取账户信息（余额、净值、杠杆等）。"""

    @abc.abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        """读取历史 K 线，用于计算市场环境特征。"""

    @abc.abstractmethod
    async def get_deals(
        self,
        account_id: str,
        start: datetime,
        end: datetime,
        symbol: str | None = None,
    ) -> list[Deal]:
        """读取历史成交记录（已平仓交易）。"""

    @abc.abstractmethod
    async def set_ea_enabled(self, account_id: str, ea_name: str, enabled: bool) -> bool:
        """启用 / 暂停指定 EA（功能2 自动调度的执行动作）。

        真实实现中，这通常通过桥接 EA 的指令通道或修改其权重实现。
        """

    async def close(self) -> None:  # 可选，资源清理
        return None
