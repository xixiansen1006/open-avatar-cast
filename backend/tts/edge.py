"""Edge-TTS 实现（默认，无需本地大模型）。"""

from __future__ import annotations

import edge_tts

from .base import TTSProvider, TTSResult


class EdgeTTSProvider(TTSProvider):
    name = "edge"

    def __init__(
        self,
        default_voice: str = "zh-CN-XiaoxiaoNeural",
        default_rate: str = "+0%",
        default_volume: str = "+0%",
    ) -> None:
        self.default_voice = default_voice
        self.default_rate = default_rate
        self.default_volume = default_volume

    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        rate: str | None = None,
        volume: str | None = None,
    ) -> TTSResult:
        text = (text or "").strip()
        if not text:
            raise ValueError("文本不能为空")

        use_voice = voice or self.default_voice
        use_rate = rate or self.default_rate
        use_volume = volume or self.default_volume

        communicate = edge_tts.Communicate(
            text,
            voice=use_voice,
            rate=use_rate,
            volume=use_volume,
        )
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])

        if not chunks:
            raise RuntimeError("Edge-TTS 未返回音频数据")

        return TTSResult(
            audio=b"".join(chunks),
            mime_type="audio/mpeg",
            voice=use_voice,
        )
