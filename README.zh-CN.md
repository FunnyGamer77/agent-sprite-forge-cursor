# Agent Sprite Forge — Cursor 适配版

> 基于 [@0x0funky](https://github.com/0x0funky) 的 [agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge) 改造。
> 保留原项目「Agent 决策 + Python 确定性后处理」的设计哲学，把它接到 Cursor 的 `GenerateImage` 工具与 skills 体系上。
>
> English: [README.md](README.md)

在 Cursor 里用一句中文（或英文）prompt，生成游戏可用的 2D 精灵图、动画 GIF、分层 RPG 地图、道具包、碰撞 / 触发区域元数据。
**Agent 负责创意决策（资源类型、Sheet 布局、帧数、风格）**；**Python 脚本只做确定性的像素操作**（去 magenta 背景、切帧、对齐、透明 GIF / PNG 导出）。

## 与原项目的区别

| 维度 | 原版（Codex） | 本适配版（Cursor） |
| --- | --- | --- |
| 图像生成工具 | `image_gen` | `GenerateImage` |
| 引入参考图 | 先 `view_image` 让本地图可见 | 直接传 `reference_image_paths`；只有 agent 还没读过的本地图才需要先 `Read` |
| Skills 目录 | `~/.codex/skills/` | `~/.cursor/skills/`（或项目级 `.cursor/skills/`） |
| 触发方式 | `$generate2dsprite` 斜杠命令 | description 自动发现，自然语言：「用 generate2dsprite 帮我做……」 |
| Chroma-key 工具 | `$CODEX_HOME/skills/.system/imagegen/scripts/remove_chroma_key.py` | 自带 `skills/generate2dmap/scripts/remove_chroma_key.py`（soft-matte + despill） |
| Python 后处理脚本 | `generate2dsprite.py`、`extract_prop_pack.py`、`compose_layered_preview.py` | **保持不变** |

Agent 决策规则、prompt 契约、Sheet 形状、像素流水线全部保留，只重写了与 Cursor 工具 / skill loader 接合的胶水层。

## 提供两个 Skill

- **`generate2dsprite`** — 精灵图、动画 sheet、道具、特效、透明 GIF。
- **`generate2dmap`** — 烤好的 / 分层栅格地图、tilemap、视差场景、道具包、碰撞与触发区域元数据，以及面向引擎（Phaser / Tiled / LDtk / Godot / Unity / 项目原生）的接线。

`generate2dmap` 在做分层地图、需要可复用透明道具时会复用 `generate2dsprite` 的工作流。

## 安装

### 方式 A：装到当前用户（推荐）

```bash
cd agent-sprite-forge-cursor
./install.sh
```

会把 `skills/generate2dsprite/` 和 `skills/generate2dmap/` 复制到 `~/.cursor/skills/`，并执行 `pip install --user -r requirements.txt` 装好 `Pillow` / `numpy`。

### 方式 B：装到当前项目

```bash
./install.sh --project
```

复制到 `./.cursor/skills/`，跟仓库一起被 commit，团队成员 clone 后即可用。

### 方式 C：手动安装

```bash
mkdir -p ~/.cursor/skills
cp -R skills/* ~/.cursor/skills/
python3 -m pip install --user -r requirements.txt
```

装完后重启 Cursor（或者新开一个对话），skill 就会被识别。

## 试一下

精灵图：

```text
用 generate2dsprite 帮我做一个终极土系泰坦的 2x2 idle 动画。
```

```text
用 generate2dsprite 做一个侧视角火法师的法术 bundle：
吟唱 sheet、抛射物循环、命中爆炸。
```

```text
Use generate2dsprite to create a top-down 4x4 player_sheet for a wandering young samurai
with a red scarf and short katana. Row order: down, left, right, up. Solid #FF00FF background.
```

参考图转精灵（先把图丢到对话里，再说）：

```text
用 generate2dsprite 帮我让这个角色做一个施法动作，
保留脸部、配色和服装。用 2x3 的 cast sheet。
```

地图：

```text
用 generate2dmap 做一个俯视角 RPG 神社地图。
分层栅格流水线，3x3 道具包放小型环境物，精确碰撞，遇敌草丛区域，
一个休息点，y-sort 排序。
```

```text
用 generate2dmap 做一个固定视角的像素风战斗竞技场，简单碰撞即可。
```

## 输出物

典型的精灵 sheet：

```
output/<name>/
  raw-sheet.png
  raw-sheet-clean.png
  sheet-transparent.png
  frames/*.png
  animation.gif
  prompt-used.txt
  pipeline-meta.json
```

典型的分层地图：

```
assets/map/<name>-base.png                     # 仅地面的底图
assets/map/<name>-base.prompt.txt
assets/map/<name>-dressed-reference.png        # 规划用的装饰参考图
assets/props/<prop>/prop.png                   # 每个道具一个文件夹
assets/props/<name>-prop-pack.json             # 道具包提取清单
data/<name>-props.json                         # 道具放置
data/<name>-collision.json                     # 碰撞 / 行走区域
data/<name>-zones.json                         # 遇怪 / 休息 / 出口触发
assets/map/<name>-layered-preview.png          # 合成预览（仅供 QA）
```

## 仓库结构

```
agent-sprite-forge-cursor/
├── README.md
├── README.zh-CN.md
├── LICENSE
├── requirements.txt
├── install.sh
└── skills/
    ├── generate2dsprite/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── modes.md
    │   │   └── prompt-rules.md
    │   └── scripts/
    │       └── generate2dsprite.py
    └── generate2dmap/
        ├── SKILL.md
        ├── references/
        │   ├── layered-map-contract.md
        │   ├── map-strategies.md
        │   └── prop-pack-contract.md
        └── scripts/
            ├── compose_layered_preview.py
            ├── extract_prop_pack.py
            └── remove_chroma_key.py
```

## 注意事项

- Python 脚本是低层处理器：`--rows`、`--cols`、`--fit-scale`、`--align`、`--shared-scale`、`--component-mode` 这些参数是 agent 按资源类型动态决定的，不是给用户记的预设。
- `#FF00FF` 洋红背景约定贯穿整条流水线，除非你同时改后处理阈值，否则别换底色。
- 商用项目优先用你自己拥有 IP 的角色。

## 致谢与许可

原项目：[0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge)，MIT License。
本 Cursor 适配版沿用 MIT 许可，详见 `LICENSE`。

确定性的 Python 脚本（`generate2dsprite.py`、`extract_prop_pack.py`、`compose_layered_preview.py`）以及 prompt / mode / contract 文档完整自上游引入，仅做了 Cursor 路径与工具名的最小化调整。捆绑的 `remove_chroma_key.py` 是为本仓库重写的，对外接口与它替代的 Codex 内置脚本保持一致。
