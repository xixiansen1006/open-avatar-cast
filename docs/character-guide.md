# 角色包指南

## 目录约定

```
characters/
  <character_id>/
    character.yaml   # 必填
    avatar.svg       # 建议；也可 png，改 yaml 中 avatar 字段
```

`<character_id>` 只能用目录安全字符（建议小写 + 下划线）。

## character.yaml 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 展示名 |
| `description` | string | 简介 |
| `persona` | string | 人设（给可选 LLM 用） |
| `voice` | string | TTS 音色 ID（Edge 示例：`zh-CN-XiaoxiaoNeural`） |
| `rate` | string | 语速，如 `+0%`、`+8%` |
| `volume` | string | 音量，如 `+0%` |
| `avatar` | string | 相对角色目录的资源文件名 |
| `lip_sync` | object | 口型参数 |
| `tags` | string[] | 标签 |

### lip_sync

```yaml
lip_sync:
  min_scale: 0.15   # 闭嘴时最小开合
  max_scale: 1.0    # 最大开合
  smoothing: 0.35   # 0~1，越大越跟手、越小越平滑
```

## 头像与口型

前端会把 SVG 内联进页面，并查找 **`id="mouth"`** 元素做口型缩放。

建议：

- 用 `<ellipse id="mouth" ...>` 或 `<path id="mouth" ...>`（ellipse 效果最好）
- 画布约 `320×360`，背景可透明或深色；OBS 场景另有绿幕容器

示例见 `characters/demo_host/avatar.svg`。

## Edge-TTS 中文音色（常用）

| Voice | 风格 |
|-------|------|
| `zh-CN-XiaoxiaoNeural` | 女声，亲和 |
| `zh-CN-YunxiNeural` | 男声，沉稳 |
| `zh-CN-XiaoyiNeural` | 女声，活泼 |
| `zh-CN-YunyangNeural` | 男声，新闻感 |

完整列表可运行：`edge-tts --list-voices | grep zh-CN`。

## 新增角色步骤

1. 复制 `characters/demo_host` 为新目录
2. 改 `character.yaml` 与 `avatar.svg`
3. 重启服务（或至少刷新前端）；`GET /api/characters` 应能看到新角色

## 版权声明

角色包内的 Live2D / 商业立绘 / 第三方模型 **版权自负**。  
本仓库示例仅为原创简易 SVG，可自由修改。
