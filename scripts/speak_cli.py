#!/usr/bin/env python3
"""命令行触发 TTS，将音频写到文件（默认 /tmp/oac-speak.mp3）。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="open-avatar-cast speak CLI")
    parser.add_argument("text", help="要合成的文本")
    parser.add_argument(
        "-c",
        "--character",
        default=None,
        help="角色 ID，如 demo_host",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="/tmp/oac-speak.mp3",
        help="输出 mp3 路径",
    )
    parser.add_argument(
        "--base",
        default="http://127.0.0.1:8765",
        help="服务根 URL",
    )
    parser.add_argument("--llm", action="store_true", help="经 LLM")
    args = parser.parse_args()

    url = args.base.rstrip("/") + "/api/speak"
    payload = {
        "text": args.text,
        "character_id": args.character,
        "use_llm": args.llm,
    }
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload)
        if resp.status_code != 200:
            print(f"失败 [{resp.status_code}]: {resp.text}", file=sys.stderr)
            return 1
        out = Path(args.output)
        out.write_bytes(resp.content)
        voice = resp.headers.get("X-OAC-Voice", "?")
        print(f"已写入 {out} ({len(resp.content)} bytes, voice={voice})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
