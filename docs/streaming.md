# 推流指南

## 方式一：OBS 浏览器源（推荐）

本前端页面即为「可捕获的虚拟主播画面」。

### 步骤

1. 启动本服务：`bash scripts/run.sh`
2. 打开 OBS → **来源** → **浏览器**
3. 设置：
   - **URL**：`http://127.0.0.1:8765/?obs=1`
   - **宽度 / 高度**：例如 `1280` × `720`（或与画布一致）
   - 勾选「控制音频时关闭源时关闭」「刷新浏览器当场景变为活动」按需
4. 抠像：
   - 默认舞台背景为纯绿 `#00ff00`，可用 **色度键** 滤镜抠掉；
   - 或使用 `?obs=1`（透明背景）+ OBS 合成其他图层。
5. 控制播报：
   - 另开普通浏览器访问 `http://127.0.0.1:8765/`（不带 `obs=1`）操作面板；或
   - 用 CLI：`python scripts/speak_cli.py "大家好"` 触发服务端合成（需自行接到前端时可扩展 WebSocket；MVP 以页面操作为主）。

### URL 参数

| 参数 | 含义 |
|------|------|
| `obs=1` | 隐藏控制面板，便于推流画面干净 |
| `character=cool_guide` | 预选角色 |
| `text=...` | 预填文本 |

示例：

```
http://127.0.0.1:8765/?obs=1&character=demo_host
```

## 方式二：ffmpeg 可选 RTMP

若你已有「合成画面」（例如用 ffmpeg 抓取虚拟摄像头 / 窗口），可推到直播平台：

```bash
# 示例：将桌面区域或虚拟摄像头推到 RTMP（请按实际输入设备修改）
ffmpeg -f x11grab -video_size 1280x720 -framerate 30 -i :0.0+0,0 \
  -f pulse -i default \
  -c:v libx264 -preset veryfast -b:v 2500k -pix_fmt yuv420p \
  -c:a aac -b:a 128k \
  -f flv "rtmp://live.example.com/live/YOUR_STREAM_KEY"
```

Windows 可用 `gdigrab` / `dshow`；macOS 可用 `avfoundation`。  
**注意**：本仓库不捆绑 ffmpeg 与平台推流密钥；请遵守各平台直播规范。

## 方式三：可选 OBS WebSocket

在 `config.yaml` / `.env` 中开启：

```yaml
obs:
  enabled: true
  host: "127.0.0.1"
  port: 4455
  password: "your-password"
```

并安装可选依赖：

```bash
pip install obsws-python
```

启动时会尝试连接；**失败只记日志，不阻塞 TTS 与页面**。  
当前封装仅含连通探测与场景切换示例（`backend/stream/obs_client.py`），可按需扩展。
