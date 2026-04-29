# Agent Sprite Forge — Cursor Edition

> A Cursor-adapted port of [agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge) by [@0x0funky](https://github.com/0x0funky).
> Same agent-first philosophy, retargeted at Cursor's `GenerateImage` and skill conventions.
>
> 中文版：[README.zh-CN.md](README.zh-CN.md)

Turn natural-language prompts into game-ready 2D sprites and layered 2D maps from inside Cursor.
Plan with the agent. Render with Cursor's built-in image generation. Export clean transparent sheets, GIFs, maps, props, and collision-ready scene data.

## What's Different from the Original

| Concern | Original (Codex) | This port (Cursor) |
| --- | --- | --- |
| Image generation | `image_gen` tool | `GenerateImage` tool |
| Reference images | `view_image` to make local files visible | Pass paths via `GenerateImage`'s `reference_image_paths`; use `Read` only when the agent has not yet seen the file |
| Skills directory | `~/.codex/skills/` | `~/.cursor/skills/` (or `.cursor/skills/` per project) |
| Trigger | `$generate2dsprite` slash command | Description-driven auto-discovery; users can write `use generate2dsprite to ...` naturally |
| External chroma-key helper | `$CODEX_HOME/skills/.system/imagegen/scripts/remove_chroma_key.py` | Bundled `skills/generate2dmap/scripts/remove_chroma_key.py` (soft-matte + despill) |
| Deterministic processing scripts | `generate2dsprite.py`, `extract_prop_pack.py`, `compose_layered_preview.py` | **Unchanged** — same Python primitives |

The agent-decision rules, prompt contracts, sheet shapes, and pixel pipelines are preserved. Only the I/O glue around Cursor's tools and skill loader has been rewritten.

## What You Get

Two skills auto-discovered by Cursor:

- `generate2dsprite` — sprites, animation sheets, props, FX, transparent GIFs.
- `generate2dmap` — baked / layered raster maps, tilemaps, parallax stages, prop packs, collision and zone metadata, and engine-target wiring (Phaser / Tiled / LDtk / Godot / Unity / project-native).

`generate2dmap` will reach into `generate2dsprite`'s prop workflow when a layered map needs reusable transparent props.

## Install

All install options assume you are inside the `agent-sprite-forge-cursor/` directory (the same folder this `README.md` lives in). If you have not yet, get the repo first:

```bash
git clone https://github.com/FunnyGamer77/agent-sprite-forge-cursor.git
cd agent-sprite-forge-cursor
```

> Or download a zip and `cd` into the unpacked folder.

### Option A — install for your user (recommended)

```bash
./install.sh
```

This copies `skills/generate2dsprite/` and `skills/generate2dmap/` into `~/.cursor/skills/`, then runs `pip install --user -r requirements.txt` to make sure `Pillow` and `numpy` are available.

Useful flags:

- `--force` — overwrite existing skill folders in the target directory.
- `--no-deps` — skip `pip install` (use this if you manage Python deps elsewhere).

### Option B — install per-project

```bash
./install.sh --project
```

Copies the skills into `./.cursor/skills/` of your current working directory so they ship with that project's git repository.

### Option C — install to a custom directory

```bash
./install.sh --target /path/to/skills
```

### Option D — manual install (no install.sh)

```bash
mkdir -p ~/.cursor/skills
cp -R skills/* ~/.cursor/skills/
python3 -m pip install --user -r requirements.txt
```

After install, restart Cursor (or just open a new chat) so the skills are picked up.

## Try It

Sprite examples:

```text
Use generate2dsprite to create a 2x2 idle for an ultimate earth titan.
```

```text
Use generate2dsprite to create a side-view fire mage spell bundle:
  cast sheet, projectile loop, and impact burst.
```

```text
Use generate2dsprite to create a top-down 4x4 player_sheet for a wandering young samurai
with a red scarf and short katana. Row order: down, left, right, up. Solid #FF00FF background.
```

Reference-to-sprite (attach an image, then ask):

```text
Use generate2dsprite to create this character casting a spell.
Preserve face, palette, and outfit. Use a 2x3 cast sheet.
```

Map examples:

```text
Use generate2dmap to create a top-down RPG forest shrine map.
Use a layered raster pipeline, a 3x3 prop pack for small environmental props,
precise collision, encounter grass zones, a rest point, and y-sort placement.
```

```text
Use generate2dmap to create a small fixed-screen pixel-art battle arena
with simple collision.
```

## Output Shape

For a typical sprite sheet:

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

For a layered map (typical):

```
assets/map/<name>-base.png
assets/map/<name>-base.prompt.txt
assets/map/<name>-dressed-reference.png       # planning artifact
assets/props/<prop>/prop.png                   # one folder per prop
assets/props/<name>-prop-pack.json             # extraction manifest (when using a pack)
data/<name>-props.json                         # placement
data/<name>-collision.json                     # blockers, walk bounds
data/<name>-zones.json                         # encounter / rest / exit triggers
assets/map/<name>-layered-preview.png          # flattened QA preview
```

## Repository Layout

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

## Notes

- The Python scripts are intentionally low-level. The agent picks `--rows`, `--cols`, `--fit-scale`, `--align`, `--shared-scale`, `--component-mode`, etc. on a per-asset basis — they are execution primitives, not user-facing presets.
- The `#FF00FF` magenta convention is preserved end-to-end. Don't change the background color unless you also override the post-processor thresholds.
- For commercial projects, prefer original characters or IP you control.

## Credits & License

Original project: [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge), MIT License.
This Cursor adaptation preserves the original MIT license — see `LICENSE`.

The deterministic Python scripts (`generate2dsprite.py`, `extract_prop_pack.py`, `compose_layered_preview.py`) and the prompt / mode / contract documents are vendored from the upstream project with only Cursor-specific path and tool-name adjustments. The bundled `remove_chroma_key.py` is an original implementation that mirrors the surface API of the Codex helper it replaces.
