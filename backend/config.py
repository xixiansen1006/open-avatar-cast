"""应用配置：YAML + 环境变量。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（backend/ 的上一级）
ROOT_DIR = Path(__file__).resolve().parent.parent
CHARACTERS_DIR = ROOT_DIR / "characters"
FRONTEND_DIR = ROOT_DIR / "frontend"
DEFAULT_CONFIG_PATH = ROOT_DIR / "config.yaml"
EXAMPLE_CONFIG_PATH = ROOT_DIR / "config.example.yaml"


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8765
    reload: bool = False


class TTSConfig(BaseModel):
    provider: Literal["edge", "openai_compat"] = "edge"
    edge_voice: str = "zh-CN-XiaoxiaoNeural"
    edge_rate: str = "+0%"
    edge_volume: str = "+0%"
    openai_base_url: str = "http://127.0.0.1:9880/v1"
    openai_api_key: str = ""
    openai_model: str = "tts-1"
    openai_voice: str = "alloy"


class LLMConfig(BaseModel):
    enabled: bool = False
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    system_prompt: str = "你是一位友好的虚拟主播，回答简洁自然，适合口播。"


class OBSConfig(BaseModel):
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 4455
    password: str = ""


class AppConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    default_character: str = "demo_host"
    tts: TTSConfig = Field(default_factory=TTSConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    obs: OBSConfig = Field(default_factory=OBSConfig)


class EnvOverrides(BaseSettings):
    """从环境变量覆盖关键配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    oac_host: str | None = None
    oac_port: int | None = None
    oac_tts_provider: Literal["edge", "openai_compat"] | None = None
    oac_edge_voice: str | None = None
    oac_openai_tts_base_url: str | None = None
    oac_openai_tts_api_key: str | None = None
    oac_openai_tts_model: str | None = None
    oac_openai_tts_voice: str | None = None
    oac_llm_enabled: bool | None = None
    oac_llm_base_url: str | None = None
    oac_llm_api_key: str | None = None
    oac_llm_model: str | None = None
    oac_obs_enabled: bool | None = None
    oac_obs_host: str | None = None
    oac_obs_port: int | None = None
    oac_obs_password: str | None = None


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"配置文件格式错误: {path}")
    return data


def _apply_env(cfg: AppConfig, env: EnvOverrides) -> AppConfig:
    if env.oac_host is not None:
        cfg.server.host = env.oac_host
    if env.oac_port is not None:
        cfg.server.port = env.oac_port
    if env.oac_tts_provider is not None:
        cfg.tts.provider = env.oac_tts_provider
    if env.oac_edge_voice is not None:
        cfg.tts.edge_voice = env.oac_edge_voice
    if env.oac_openai_tts_base_url is not None:
        cfg.tts.openai_base_url = env.oac_openai_tts_base_url
    if env.oac_openai_tts_api_key is not None:
        cfg.tts.openai_api_key = env.oac_openai_tts_api_key
    if env.oac_openai_tts_model is not None:
        cfg.tts.openai_model = env.oac_openai_tts_model
    if env.oac_openai_tts_voice is not None:
        cfg.tts.openai_voice = env.oac_openai_tts_voice
    if env.oac_llm_enabled is not None:
        cfg.llm.enabled = env.oac_llm_enabled
    if env.oac_llm_base_url is not None:
        cfg.llm.base_url = env.oac_llm_base_url
    if env.oac_llm_api_key is not None:
        cfg.llm.api_key = env.oac_llm_api_key
    if env.oac_llm_model is not None:
        cfg.llm.model = env.oac_llm_model
    if env.oac_obs_enabled is not None:
        cfg.obs.enabled = env.oac_obs_enabled
    if env.oac_obs_host is not None:
        cfg.obs.host = env.oac_obs_host
    if env.oac_obs_port is not None:
        cfg.obs.port = env.oac_obs_port
    if env.oac_obs_password is not None:
        cfg.obs.password = env.oac_obs_password
    return cfg


@lru_cache
def get_config() -> AppConfig:
    """加载 config.yaml（不存在则用 example）并合并环境变量。"""
    # 支持从项目根目录加载 .env
    env_path = ROOT_DIR / ".env"
    if env_path.is_file():
        from dotenv import load_dotenv

        load_dotenv(env_path)

    path = DEFAULT_CONFIG_PATH if DEFAULT_CONFIG_PATH.is_file() else EXAMPLE_CONFIG_PATH
    raw = _load_yaml(path)
    cfg = AppConfig.model_validate(raw)
    env = EnvOverrides()
    return _apply_env(cfg, env)


def reload_config() -> AppConfig:
    get_config.cache_clear()
    return get_config()
