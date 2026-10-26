"""TTS 提供商工厂。"""

from __future__ import annotations

from ..config import AppConfig, TTSConfig
from .base import TTSProvider
from .edge import EdgeTTSProvider
from .openai_compat import OpenAICompatTTSProvider


def create_tts_provider(cfg: AppConfig | TTSConfig) -> TTSProvider:
    tts = cfg.tts if isinstance(cfg, AppConfig) else cfg
    if tts.provider == "openai_compat":
        return OpenAICompatTTSProvider(
            base_url=tts.openai_base_url,
            api_key=tts.openai_api_key,
            model=tts.openai_model,
            default_voice=tts.openai_voice,
        )
    return EdgeTTSProvider(
        default_voice=tts.edge_voice,
        default_rate=tts.edge_rate,
        default_volume=tts.edge_volume,
    )


__all__ = [
    "TTSProvider",
    "EdgeTTSProvider",
    "OpenAICompatTTSProvider",
    "create_tts_provider",
]
