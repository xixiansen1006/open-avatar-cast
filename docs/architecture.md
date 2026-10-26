# 架构说明

## 总览

```
浏览器 / OBS 浏览器源
        │  HTTP
        ▼
   FastAPI (backend/main.py)
        │
        ├── 静态：frontend/ + characters/*/
        ├── /api/characters  → 扫描 characters/
        ├── /api/speak       → TTSProvider → audio/mpeg
        ├── /api/health
        └── （可选）LLM / OBS WebSocket
```

本项目刻意保持「可换包 + 推流友好」的薄内核：

| 层 | 职责 | 默认实现 |
|----|------|----------|
| 角色包 | 人设、音色、头像 SVG | `characters/<id>/` |
| TTS | 文本 → 音频 | Edge-TTS |
| 前端 | 播放 + 音量口型 | vanilla JS |
| 推流 | OBS 捕获页面 | 文档 + 可选 websocket |

## 请求路径：`/api/speak`

1. 解析 `character_id`（缺省用配置默认角色）
2. 若 `use_llm=true` 且已启用 LLM → OpenAI-compatible chat 改写文本
3. 用角色 `voice/rate/volume` 调用当前 `TTSProvider`
4. 返回 `audio/mpeg`；元数据放在 `X-OAC-*` 响应头

前端拿到音频后：

1. `Audio` 播放
2. `AudioContext` + `AnalyserNode` 取频域能量
3. 平滑后驱动 SVG `#mouth` 的 `ry` / `rx`

## TTS 可插拔

```
TTSProvider (抽象)
 ├── EdgeTTSProvider      # 默认，免大模型
 └── OpenAICompatTTSProvider  # CosyVoice / 自建网关等
```

工厂：`backend/tts/__init__.py` → `create_tts_provider(cfg)`。

## 与更重方案的边界

本仓库 **不做**：

- Live2D / VRM 运行时与收费 SDK 绑定
- 本地大模型下载与推理编排
- 完整弹幕互动 / 多模态 Agent 工作流

这些能力可在本 MVP 之上按需扩展；角色包与 TTS 接口已预留扩展点。

## 目录职责

| 路径 | 说明 |
|------|------|
| `backend/` | FastAPI、配置、TTS、可选 OBS |
| `frontend/` | 无构建静态页 |
| `characters/` | 可热增角色包（重启或刷新列表） |
| `docs/` | 架构 / 推流 / 角色指南 |
| `scripts/` | 启动与 CLI 冒烟 |
