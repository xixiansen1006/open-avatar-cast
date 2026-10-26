"""obs-websocket 轻量封装。

依赖可选：pip install obsws-python
连不上或不安装时，不阻塞主流程。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class OBSClient:
    """薄包装：仅提供连接探测与场景切换示例。"""

    def __init__(self, host: str, port: int, password: str = "") -> None:
        self.host = host
        self.port = port
        self.password = password
        self._ws: Any = None
        self.connected = False

    def connect(self) -> bool:
        try:
            import obsws_python as obs  # type: ignore
        except ImportError:
            logger.info("未安装 obsws-python，跳过 OBS 连接（可选依赖）")
            return False

        try:
            self._ws = obs.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password,
                timeout=3,
            )
            # 一次轻量请求验证连通
            self._ws.get_version()
            self.connected = True
            logger.info("已连接 OBS WebSocket %s:%s", self.host, self.port)
            return True
        except Exception as exc:  # noqa: BLE001 — 故意吞掉，避免阻塞
            logger.warning("OBS WebSocket 连接失败（可忽略）: %s", exc)
            self._ws = None
            self.connected = False
            return False

    def set_current_program_scene(self, scene_name: str) -> bool:
        if not self.connected or self._ws is None:
            return False
        try:
            self._ws.set_current_program_scene(scene_name)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("切换 OBS 场景失败: %s", exc)
            return False

    def disconnect(self) -> None:
        self._ws = None
        self.connected = False


def try_connect_obs(host: str, port: int, password: str = "") -> OBSClient:
    """尝试连接；失败也返回未连接的客户端实例。"""
    client = OBSClient(host=host, port=port, password=password)
    client.connect()
    return client
