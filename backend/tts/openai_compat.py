"""OpenAI-compatible TTS 空壳 / 最小实现。

可用于 CosyVoice、本地 OpenAI-compatible TTS 网关等。
未配置或服务不可达时，调用会抛出明确错误，不影响默认 Edge-TTS 主流程。
"""

from __future__ import annotations

import httpx

from .base import TTSProvider, TTSResult


class OpenAICompatTTSProvider(TTSProvider):
    """兼容 OpenAI /v1/audio/speech 的 TTS 客户端。

    预留说明（CosyVoice / 自建网关）：
    - 将 base_url 指向兼容端点，例如 http://127.0.0.1:9880/v1
    - model / voice 按服务端要求填写
    - 若服务端返回 wav，可调整 mime_type
    """

    name = "openai_compat"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:9880/v1",
        api_key: str = "",
        model: str = "tts-1",
        default_voice: str = "alloy",
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.default_voice = default_voice
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        rate: str | None = None,
        volume: str | None = None,
    ) -> TTSResult:
        # rate / volume：多数 OpenAI 兼容端不支持，此处保留参数以统一接口签名
        _ = rate, volume
        text = (text or "").strip()
        if not text:
            raise ValueError("文本不能为空")

        use_voice = voice or self.default_voice
        client = self._get_client()
        payload = {
            "model": self.model,
            "input": text,
            "voice": use_voice,
            "response_format": "mp3",
        }
        try:
            resp = await client.post("/audio/speech", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"OpenAI-compatible TTS 请求失败（请确认服务已启动且 "
                f"base_url={self.base_url}）：{exc}"
            ) from exc

        return TTSResult(
            audio=resp.content,
            mime_type="audio/mpeg",
            voice=use_voice,
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
