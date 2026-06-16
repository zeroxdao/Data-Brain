"""应用配置。

通过环境变量或 .env 文件覆盖默认值。接入真实 MT4/MT5 账号时，
设置 BRIDGE_PROVIDER=metaapi 并提供 METAAPI_TOKEN。
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DATA BRAIN"
    app_version: str = "0.1.0"

    # 桥接层: "mock" 用合成数据可离线运行; "metaapi" 接入真实账号
    bridge_provider: Literal["mock", "metaapi"] = "mock"

    # MetaApi 凭证（仅当 bridge_provider=metaapi 时需要）
    metaapi_token: str | None = None
    metaapi_domain: str = "agiliumtrade.agiliumtrade.ai"

    # 环境分类参数
    adx_period: int = 14
    atr_period: int = 14
    adx_trend_threshold: float = 25.0  # ADX > 阈值 视为趋势市
    # 已实现波动率分位阈值，用于划分高/低波动
    high_vol_quantile: float = 0.7
    low_vol_quantile: float = 0.3


@lru_cache
def get_settings() -> Settings:
    return Settings()
