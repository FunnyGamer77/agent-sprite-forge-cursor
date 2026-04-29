---
name: generate2dsprite
description: "Generate and postprocess 2D game assets and animation sheets from natural-language prompts: pixel-art sprites, clean HD map props, creatures, characters, NPCs, spells, projectiles, impacts, props, summons, FX, transparent PNG sheets, per-frame PNGs, and animated GIFs. Use when the user asks for sprite sheets, sprite animations, game characters, monsters, players or NPCs, spell/projectile/impact bundles, four-direction walk sheets, reference-to-sprite generation, or pixel-art assets. Triggers: sprite, sprite sheet, 2d sprite, generate2dsprite, pixel art, animation sheet, sprite animation, walk cycle, idle loop, spell bundle, projectile, impact, FX sheet, transparent GIF."
---

# Generate 2D Sprite

Use this skill for self-contained 2D sprite or animation assets. The agent decides the asset plan and writes the art prompt itself; the bundled Python script only does deterministic pixel processing (chroma-key cleanup, frame extraction, alignment, transparent PNG/GIF export).

If the user wants a complete map, layered scene, prop placement, or engine-native map data, use the `generate2dmap` skill instead (it can call back into this skill for reusable transparent props).

## Parameters

Infer these from the user request:

- `asset_type`: `player` | `npc` | `creature` | `character` | `spell` | `projectile` | `impact` | `prop` | `summon` | `fx`
- `action`: `single` | `idle` | `cast` | `attack` | `hurt` | `combat` | `walk` | `run` | `hover` | `charge` | `projectile` | `impact` | `explode` | `death`
- `view`: `topdown` | `side` | `3/4`
- `sheet`: `auto` | `1x4` | `2x2` | `2x3` | `3x3` | `4x4`
- `frames`: `auto` or explicit count
- `bundle`: `single_asset` | `unit_bundle` | `spell_bundle` | `combat_bundle` | `line_bundle`
- `effect_policy`: `all` | `largest`
- `anchor`: `center` | `bottom` | `feet`
- `margin`: `tight` | `normal` | `safe`
- `art_style`: `pixel_art` | `clean_hd` | `pixel_inspired` | `retro_pixel` | `map_style` | `project-native`
- `reference`: `none` | `attached_image` | `generated_image` | `local_file`
- `prompt`: the user's theme or visual direction
- `role`: only when the asset is clearly an NPC role
- `name`: optional output slug

Read [references/modes.md](references/modes.md) when the request is ambiguous.

## Agent Rules

- Decide the asset plan yourself. Do not force the user to spell out sheet size, frame count, or bundle structure when the request already implies them.
- Write the art prompt yourself. Do not delegate prompt writing to a script.
- Use the built-in `GenerateImage` tool for every raw image. The script never produces final art.
- When the user provides or implies a visual reference, pass it via `GenerateImage`'s `reference_image_paths` argument. If the reference is a local file the agent has not yet seen, call `Read` on the image first to load it into context, then pass its path through `reference_image_paths`.
- Do not force pixel art when the asset is a map prop for `generate2dmap` or when the user/project requests a different style. Match the map or reference style first.
- Use the script only as a deterministic processor: magenta cleanup, frame splitting, component filtering, scaling, alignment, QC metadata, transparent sheet export, and GIF export.
- Treat script flags as execution primitives chosen by the agent, not user-facing hardcoded workflow.
- If a generated sheet touches cell edges, drifts in scale, or breaks a projectile / impact loop, either reprocess with better primitive settings or regenerate the raw sheet.
- Keep the solid `#FF00FF` background rule unless the user explicitly wants a different processing workflow.

## Workflow

### 1. Infer the asset plan

Pick the smallest useful output.

Examples:

- controllable hero with four directions → `player` + `player_sheet` (4x4)
- healer overworld NPC → `npc` + `single_asset` or `unit_bundle`
- large boss idle loop → `creature` + `idle` + `3x3`
- wizard throwing a magic orb → `spell_bundle`
  - caster cast sheet
  - projectile loop
  - impact burst
- monster line request → `line_bundle`
  - plan 1-3 forms; per form, only the sheets the request actually needs

### 2. Write the prompt manually

Use [references/prompt-rules.md](references/prompt-rules.md).

Choose `art_style` before writing the prompt:

- Use `pixel_art` or `retro_pixel` for classic sprites, 16-bit RPG actors, and requests that explicitly ask for pixel art.
- Use `clean_hd` for map props or assets intended to match clean hand-painted HD maps.
- Use `pixel_inspired` only when the user wants a pixel-adjacent look without retro chunkiness.
- Use `map_style` or `project-native` when an existing map, game, or reference should define the style.

If a reference is involved:

- The reference image must be in context. For attached images this is automatic. For freshly generated images this is automatic. For a local file path the user supplies, call `Read` on the image first, then pass the same path through `reference_image_paths` when calling `GenerateImage`.
- State the reference role explicitly: preserve identity/style, create an animation sheet for the same subject, create an evolution/variant, or derive a matching prop/FX.
- Preserve stable identity markers from the reference: silhouette, palette, face/eye features, costume marks, major accessories, material language.
- Let only the requested action or evolution change. Do not redesign the subject unless the user asks.
- Still require exact sheet shape, solid magenta background, frame containment, and same scale across frames.

Keep the strict parts:

- solid `#FF00FF` background
- exact sheet shape
- same character or asset identity across frames
- same bounding box and pixel scale across frames
- explicit containment: nothing may cross cell edges

### 3. Generate the raw image

Call `GenerateImage` with the prompt you just wrote. Pass `reference_image_paths` when applicable.

After generation:

- Note the saved file path returned by `GenerateImage`.
- If you want a stable working folder, copy the file into the user's project (e.g. `output/<name>/raw-sheet.png`) before postprocessing. The original generated file may live wherever Cursor saved it.

### 4. Postprocess locally

Run `scripts/generate2dsprite.py process` on the raw image (resolve `<skill_root>` to the absolute install path of this skill, e.g. `~/.cursor/skills/generate2dsprite/scripts/generate2dsprite.py`):

```bash
python3 <skill_root>/scripts/generate2dsprite.py process \
  --input output/<name>/raw-sheet.png \
  --target asset \
  --mode <mode> \
  --rows <rows> --cols <cols> \
  --output-dir output/<name> \
  --shared-scale \
  --align <center|bottom|feet> \
  --component-mode <all|largest>
```

The processor is intentionally low-level. The agent chooses:

- `--rows` / `--cols`
- `--fit-scale`
- `--align`
- `--shared-scale`
- `--component-mode`
- `--component-padding`
- `--reject-edge-touch`

Use the processor to gather QC metadata, not to make aesthetic decisions for you. Run `python3 <skill_root>/scripts/generate2dsprite.py --help` (or `process --help`) for the full flag list.

### 5. QC the result

Check:

- did any frame touch the cell edge
- did any frame resize differently than intended
- did detached effects become noise
- does the sheet still read as one coherent animation

If not, rerun the processor with different settings, or regenerate the raw sheet with a tightened prompt.

### 6. Return the right bundle

For a single sheet, expect:

- `raw-sheet.png`
- `raw-sheet-clean.png`
- `sheet-transparent.png`
- frame PNGs
- `animation.gif`
- `prompt-used.txt`
- `pipeline-meta.json`

For `player_sheet`, expect:

- transparent 4x4 sheet
- 16 frame PNGs
- direction strips
- 4 direction GIFs

For `spell_bundle` or `unit_bundle`, create one folder per asset in the bundle.

## Defaults

- `idle`
  - small or medium actor → `2x2`
  - large creature or boss → `3x3`
- `cast` → prefer `2x3`
- `projectile` → prefer `1x4`
- `impact` / `explode` → prefer `2x2`
- `walk`
  - topdown actor → `4x4` for four-direction walk
  - side-view asset → `2x2`
- use `--shared-scale` by default for any multi-frame asset where frame-to-frame consistency matters
- use `--component-mode largest` when detached sparkles or edge debris make the main body unstable

## Cursor Notes

- `GenerateImage` accepts `reference_image_paths`; use it instead of any "view this image first" dance.
- Do **not** use `Shell` with `cat`/`echo` to communicate with the user; output deliverables directly in the assistant message.
- Image files generated by `GenerateImage` are auto-displayed in chat; you do not need to embed them in markdown again.

## Resources

- [references/modes.md](references/modes.md) — asset, action, bundle, and sheet selection
- [references/prompt-rules.md](references/prompt-rules.md) — manual prompt patterns and containment rules
- `scripts/generate2dsprite.py` — postprocess primitive for cleanup, extraction, alignment, QC, and GIF export
