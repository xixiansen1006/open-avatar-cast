"""FastAPI 入口：静态前端 + TTS / 角色 / 健康检查 API。"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .characters import get_character, list_characters
from .config import CHARACTERS_DIR, FRONTEND_DIR, get_config
from .stream.obs_client import OBSClient, try_connect_obs
from .tts import create_tts_provider
from .tts.base import TTSProvider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("open-avatar-cast")

tts_provider: TTSProvider | None = None
obs_client: OBSClient | None = None


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="要播报的文本")
    character_id: str | None = Field(None, description="角色 ID，缺省用默认角色")
    use_llm: bool = Field(False, description="是否先经 LLM 改写/回复（需启用 llm）")
    voice: str | None = Field(None, description="临时覆盖音色")


class SpeakMeta(BaseModel):
    character_id: str
    voice: str
    text: str
    llm_used: bool = False
    provider: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    global tts_provider, obs_client
    cfg = get_config()
    tts_provider = create_tts_provider(cfg)
    logger.info("TTS provider: %s", tts_provider.name)

    if cfg.obs.enabled:
        obs_client = try_connect_obs(cfg.obs.host, cfg.obs.port, cfg.obs.password)
    else:
        obs_client = None

    yield

    if tts_provider is not None:
        await tts_provider.close()
    if obs_client is not None:
        obs_client.disconnect()


app = FastAPI(
    title="open-avatar-cast",
    description="轻量可换包虚拟主播数字人 MVP",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _maybe_llm_reply(user_text: str, persona: str) -> tuple[str, bool]:
    """可选 OpenAI-compatible chat；失败或未启用则原样返回。"""
    cfg = get_config()
    if not cfg.llm.enabled or not cfg.llm.api_key:
        return user_text, False

    system = cfg.llm.system_prompt
    if persona:
        system = f"{system}\n\n角色人设：{persona}"

    url = cfg.llm.base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.llm.api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": cfg.llm.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.7,
        "max_tokens": 512,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return str(content).strip() or user_text, True
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM 调用失败，回退原文: %s", exc)
        return user_text, False


@app.get("/api/health")
async def health() -> dict[str, Any]:
    cfg = get_config()
    return {
        "status": "ok",
        "version": "0.1.0",
        "tts_provider": tts_provider.name if tts_provider else None,
        "llm_enabled": cfg.llm.enabled,
        "obs_connected": bool(obs_client and obs_client.connected),
        "default_character": cfg.default_character,
        "characters_count": len(list_characters()),
    }


@app.get("/api/characters")
async def api_list_characters() -> dict[str, Any]:
    chars = [c.public_dict() for c in list_characters()]
    return {
        "default": get_config().default_character,
        "characters": chars,
    }


@app.get("/api/characters/{char_id}")
async def api_get_character(char_id: str) -> dict[str, Any]:
    char = get_character(char_id)
    if char is None:
        raise HTTPException(status_code=404, detail=f"角色不存在: {char_id}")
    return char.public_dict()


@app.post("/api/speak")
async def api_speak(body: SpeakRequest) -> Response:
    """合成语音，返回 audio/mpeg；元数据放在响应头。"""
    if tts_provider is None:
        raise HTTPException(status_code=503, detail="TTS 未就绪")

    cfg = get_config()
    char_id = body.character_id or cfg.default_character
    char = get_character(char_id)
    if char is None:
        raise HTTPException(status_code=404, detail=f"角色不存在: {char_id}")

    text = body.text.strip()
    llm_used = False
    if body.use_llm:
        text, llm_used = await _maybe_llm_reply(text, char.persona)

    voice = body.voice or char.voice or cfg.tts.edge_voice
    try:
        result = await tts_provider.synthesize(
            text,
            voice=voice,
            rate=char.rate,
            volume=char.volume,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("TTS 合成失败")
        raise HTTPException(status_code=502, detail=f"TTS 合成失败: {exc}") from exc

    # 注意：HTTP 头避免非 ASCII（中文文本不放进 header）
    headers = {
        "X-OAC-Character": char_id,
        "X-OAC-Voice": result.voice,
        "X-OAC-Provider": tts_provider.name,
        "X-OAC-LLM-Used": "1" if llm_used else "0",
        "X-OAC-Text-Length": str(len(text)),
        "Access-Control-Expose-Headers": (
            "X-OAC-Character, X-OAC-Voice, X-OAC-Provider, "
            "X-OAC-LLM-Used, X-OAC-Text-Length"
        ),
    }
    return Response(content=result.audio, media_type=result.mime_type, headers=headers)


@app.get("/api/speak")
async def api_speak_get(
    text: str = Query(..., min_length=1, max_length=2000),
    character_id: str | None = None,
    use_llm: bool = False,
) -> Response:
    """GET 便捷接口，便于 CLI / 快速测试。"""
    return await api_speak(
        SpeakRequest(text=text, character_id=character_id, use_llm=use_llm)
    )


# 角色静态资源（头像 SVG 等）
if CHARACTERS_DIR.is_dir():
    app.mount(
        "/characters",
        StaticFiles(directory=str(CHARACTERS_DIR)),
        name="characters",
    )

# 前端静态文件
if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="assets")


@app.get("/")
async def index() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="前端未找到")
    return FileResponse(index_path)


@app.get("/app.js")
async def app_js() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")


@app.get("/styles.css")
async def styles_css() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "styles.css", media_type="text/css")
