# Orchestrate profile: Saltwind

- **Purpose:** docs/PURPOSE.md
- **Quality bar:** Props a player would believe were made by hand for this one game, in the spirit of A Short Hike (and Lil Gator Game): chunky readable silhouettes, a small soft palette, deliberate wonkiness; never the even bevels, photo textures and uniform precision of an asset-store pack
- **Anchors:** docs/anchors  *(the owner's direction pick from PROPS M1, the reference set, and the best prop so far)*
- **Plans:** docs/modules  *(loop)*
- **Evidence:** docs/evidence  *(loop: review files and evidence pages)*
- **Graded examples:** docs/evidence/graded-examples.md  *(past verdicts the owner agreed with or overturned)*
- **Check:** godot --headless --path . --import && godot --headless --path . --script res://tools/check_props.gd  *(loop: required; tools/check_props.gd is written in PROPS M1)*
- **Integrate:** local  *(loop: required; the owner has not given permission to push, so the owner merges)*
- **Branch:** master  *(loop)*
- **Remote:** origin  *(loop)*
- **Builders:** one Codex builder  *(the work is serial: one atlas, one direction)*
- **Default host:** codex  *(loop)*
- **Codex model:** gpt-6.1-sol  *(loop)*
- **Claude model:** claude-opus-5-5  *(loop)*
- **Effort:** medium  *(loop)*
- **Claude permissions:** auto  *(loop)*
- **Codex sandbox:** workspace-write  *(loop)*
- **Writable roots:** ~/Library/Application Support/Godot, ~/Library/Application Support/Blender, ~/Library/Caches/Godot  *(loop)*

## Starting from a clean clone

Needs Godot 4.4 as `godot` and Blender 4.x as `blender` on the PATH (`brew install --cask godot blender` if missing;
assumed present, not yet confirmed by the owner). `godot --headless --path . --import` imports every asset; there is
no other setup, no services, no secrets and no ports, so parallel worktrees don't collide. Prop sources (`.blend` and
any generator scripts) live beside their exports under `assets/props/`, and a builder re-exports with
`blender --background <file>.blend --python <export script>`.

## Targets

| Target | What it is | Run | Capture | Edge conditions |
|---|---|---|---|---|
| godot-headless | Godot 4.4 headless, imported project | `godot --headless --path . --script <script>` | stdout and exit code | missing manifest entry, re-import after a source change |
| godot-desktop | Godot 4.4 on macOS, Forward+, the showcase and turntable scenes | `godot --path . <scene>` | Movie Maker PNG sequences: `godot --path . --write-movie <out>.png --fixed-fps 30 --quit-after <frames> <scene>` | day and night light; gameplay distance (about 15 m) and close-up; native resolution and a low-resolution nearest-upscaled view like A Short Hike's |
| owner-ears | The owner listening in the running showcase | `godot --path . res://showcase/harbour_showcase.tscn` | the owner's note in the evidence page | near and far from the source, several loops in a row |

## Rules
- **Exclusive resources:** none
- **Large captures:** PNG sequences go in `docs/evidence/captures/<milestone>/`, which is git-ignored; commit a contact sheet (one PNG per sequence) and the command that regenerates the sequence
- **Owner decides:** the art direction (PROPS M1); anything that sounds right or wrong; changing the prop list, the 1,500-triangle budget or the single 512 atlas; any asset under a licence other than CC0 or made in this repo; spending; publishing
- **Licences and paths not to touch:** only CC0 or self-made assets, each recorded in assets/props/CREDITS.md; never copy, trace or sample assets from A Short Hike or any other game; never edit project.godot rendering settings beyond what the showcase needs

## Project guidance
- Design for the props: docs/modules/PROPS.md
- Assumptions made while the owner was unreachable are listed in the log of docs/modules/PROPS-PLAN.md
