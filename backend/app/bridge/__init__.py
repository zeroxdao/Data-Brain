"""MT4/MT5 桥接层。

通过统一的 TradingBridge 抽象接口，屏蔽底层是 MetaApi 云服务
还是自建 VPS 桥接，亦或是离线 mock 数据。
"""
from .base import TradingBridge
from .factory import get_bridge

__all__ = ["TradingBridge", "get_bridge"]
