# open-avatar-cast

轻量、可换包、推流友好的开源「虚拟主播数字人」MVP。

用 **FastAPI + Edge-TTS + 纯静态前端** 跑通：选角色 → 输入中文 → 听语音 → 口型动画 → 用 OBS 浏览器源推流。  
不强制 Live2D SDK、不下载巨型模型、关掉 LLM 也能纯 TTS 播报。

---

## 是什么 / 不是什么

| 本项目是 | 本项目不是 |
|----------|------------|
| 可换角色包（YAML + SVG 脸） | 完整 Live2D / VRM 商业管线 |
| TTS 可插拔（默认 Edge-TTS） | 本地大模型推理框架 |
| OBS 浏览器源友好 | 弹幕互动 / 多 Agent 运营台 |
| 可选 OpenAI-compatible LLM 钩子 | Open-LLM-VTuber 的平替复刻 |

**与 Open-LLM-VTuber 等项目的定位差异**：那些项目通常更完整（Live2D、对话 Agent、更多集成），也更重。  
`open-avatar-cast` 刻意做薄：**可换包、推流友好、依赖少、能在几分钟内本地跑起来**，适合二次开发起点与直播浏览器源场景。能力边界可参考同类项目「能做什么」，但实现均为原创，不复制其代码。

---

## 功能（MVP）

1. **可换形象**：`characters/` 下多角色包；至少 2 个示例（Canvas/SVG 脸，无收费 Live2D SDK）
2. **TTS 可插拔**：`TTSProvider` 抽象；默认 Edge-TTS；预留 OpenAI-compatible / CosyVoice 空壳
3. **说话驱动口型**：文本 → 后端合成 → 前端播放，用音量/频谱驱动 `#mouth`
4. **推流**：页面可作 OBS 浏览器源；`docs/streaming.md` 含 OBS + 可选 ffmpeg RTMP；可选 obs-websocket（连不上不阻塞）
5. **可选 LLM**：OpenAI-compatible chat；环境变量开关，关掉即纯播报

---

## 快速开始

### 要求

- Python 3.11+
- 能访问 Edge-TTS 所需网络（微软在线语音）

### 安装与启动

```bash
cd open-avatar-cast
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 可选：复制配置
cp config.example.yaml config.yaml
cp .env.example .env

bash scripts/run.sh
# 等价：
# PYTHONPATH=. python -m uvicorn backend.main:app --host 0.0.0.0 --port 8765
```

浏览器打开：<http://127.0.0.1:8765/>

1. 选择角色（`小晓 · 演示主播` / `阿哲 · 酷感向导`）
2. 输入中文 → **播报**
3. 应能听到语音，并看到嘴巴随音量开合

OBS 浏览器源 URL 示例：

```
http://127.0.0.1:8765/?obs=1&character=demo_host
```

更多见 [docs/streaming.md](docs/streaming.md)。

### CLI 合成试听

```bash
# 服务已启动时
python scripts/speak_cli.py "大家好，欢迎来到直播间" -c demo_host -o /tmp/oac.mp3
```

---

## 配置

- `config.example.yaml` → 复制为 `config.yaml`
- `.env.example` → 复制为 `.env`（`OAC_*` 环境变量可覆盖 YAML）

关键项：

| 项 | 说明 |
|----|------|
| `tts.provider` | `edge`（默认）或 `openai_compat` |
| `llm.enabled` | 是否启用对话改写 |
| `obs.enabled` | 是否尝试连接 OBS WebSocket |

可选依赖：

```bash
pip install obsws-python   # 仅当需要 OBS 控制时
```

---

## 目录结构

```
open-avatar-cast/
  README.md
  LICENSE                 # MIT
  requirements.txt
  config.example.yaml
  .env.example
  characters/
    demo_host/
    cool_guide/
  backend/                # FastAPI + TTS + 可选 OBS
  frontend/               # 无构建 HTML/CSS/JS
  docs/
  scripts/
```

架构细节：[docs/architecture.md](docs/architecture.md)  
角色包编写：[docs/character-guide.md](docs/character-guide.md)

---

## API 摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/characters` | 角色列表 |
| GET | `/api/characters/{id}` | 单个角色 |
| POST | `/api/speak` | JSON `{text, character_id?, use_llm?}` → `audio/mpeg` |
| GET | `/api/speak?text=...` | 便捷 GET |

响应头：`X-OAC-Character` / `X-OAC-Voice` / `X-OAC-Provider` / `X-OAC-LLM-Used`

---

## 免责声明

- **Live2D / 商业模型 / 第三方立绘**：版权与授权请自行负责；本仓库示例仅为原创简易 SVG。
- **TTS / LLM / 直播平台**：请遵守各服务商与平台条款；本项目不提供推流密钥或账号。
- **网络**：默认 Edge-TTS 依赖在线服务，离线环境请改用 `openai_compat` 对接本地 TTS。

---

## 路线图（非承诺）

- [ ] WebSocket 推送「开始/结束说话」便于多端控制
- [ ] 更稳的 viseme / 音素级口型（仍保持无 Live2D 依赖）
- [ ] 角色包热重载
- [ ] 浏览器源一键「透明背景 + 固定分辨率」预设
- [ ] 更多开源 TTS 适配示例（CosyVoice 实机文档）

---

## 许可证

[MIT](LICENSE)

---

## GitHub 描述建议

- **中文**：轻量可换包虚拟主播：Edge-TTS + SVG 口型 + OBS 浏览器源，开箱可推流。
- **English**: Lightweight swappable-avatar VTuber cast: Edge-TTS, SVG lip-sync, OBS Browser Source ready.
