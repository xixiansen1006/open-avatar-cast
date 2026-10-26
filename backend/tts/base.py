"""TTS 抽象接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TTSResult:
    """合成结果：音频字节 + MIME。"""

    audio: bytes
    mime_type: str = "audio/mpeg"
    voice: str = ""


class TTSProvider(ABC):
    """可插拔 TTS 提供商。"""

    name: str = "base"

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        rate: str | None = None,
        volume: str | None = None,
    ) -> TTSResult:
        """将文本合成为音频。"""

    async def close(self) -> None:
        """释放资源（可选）。"""
        return None
