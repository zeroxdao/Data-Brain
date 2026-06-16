"""根据配置返回合适的桥接实现。"""
from __future__ import annotations

from functools import lru_cache

from app.bridge.base import TradingBridge
from app.bridge.mock import MockBridge
from app.config import get_settings


@lru_cache
def get_bridge() -> TradingBridge:
    settings = get_settings()
    if settings.bridge_provider == "metaapi":
        if not settings.metaapi_token:
            raise RuntimeError(
                "BRIDGE_PROVIDER=metaapi 但未配置 METAAPI_TOKEN。"
            )
        from app.bridge.metaapi import MetaApiBridge

        return MetaApiBridge(settings.metaapi_token, settings.metaapi_domain)
    return MockBridge()
