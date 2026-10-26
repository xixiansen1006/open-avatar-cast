"""角色包加载：characters/<id>/character.yaml + 资源文件。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from .config import CHARACTERS_DIR


class CharacterMeta(BaseModel):
    id: str
    name: str
    description: str = ""
    persona: str = ""
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"
    volume: str = "+0%"
    avatar: str = "avatar.svg"
    # 口型动画参数（前端可用）
    lip_sync: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    @property
    def dir_path(self) -> Path:
        return CHARACTERS_DIR / self.id

    @property
    def avatar_path(self) -> Path:
        return self.dir_path / self.avatar

    def public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "persona": self.persona,
            "voice": self.voice,
            "rate": self.rate,
            "volume": self.volume,
            "avatar_url": f"/characters/{self.id}/{self.avatar}",
            "lip_sync": self.lip_sync,
            "tags": self.tags,
        }


def _parse_character(char_id: str, path: Path) -> CharacterMeta | None:
    yaml_path = path / "character.yaml"
    if not yaml_path.is_file():
        return None
    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        return None
    data.setdefault("id", char_id)
    data["id"] = char_id  # 目录名为准
    return CharacterMeta.model_validate(data)


def list_characters() -> list[CharacterMeta]:
    if not CHARACTERS_DIR.is_dir():
        return []
    result: list[CharacterMeta] = []
    for child in sorted(CHARACTERS_DIR.iterdir()):
        if not child.is_dir():
            continue
        meta = _parse_character(child.name, child)
        if meta is not None:
            result.append(meta)
    return result


def get_character(char_id: str) -> CharacterMeta | None:
    path = CHARACTERS_DIR / char_id
    if not path.is_dir():
        return None
    return _parse_character(char_id, path)
