# Orchestrate profile: Saltwind

- **Purpose:** docs/modules/PROPS.md  *(the current goal is the harbour props set; README.md says what the game is)*
- **Quality bar:** Props that look hand-made, as in A Short Hike: chunky readable silhouettes, designed irregularity, flat matte colour with a few hand-drawn details, nothing that looks like a clean asset-store kit
- **Anchors:** docs/anchors  *(DIRECTION.md holds the owner's pick from PROPS M1; references.md holds the reference set)*
- **Plans:** docs/modules  *(loop)*
- **Evidence:** docs/evidence  *(loop: review files and evidence pages)*
- **Graded examples:** docs/evidence/graded-examples.md  *(past verdicts the owner agreed with or overturned)*
- **Check:** tools/check.sh  *(loop: required; created in PROPS M1, runs the headless import and every prop check)*
- **Integrate:** local  *(loop: required; fast-forward local master only, the owner merges and pushes)*
- **Branch:** master  *(loop)*
- **Remote:** origin  *(loop: no remote is configured yet)*
- **Builders:** usually one Codex builder  *(one module, worked in order)*
- **Default host:** codex  *(loop)*
- **Codex model:** gpt-6.1-sol  *(loop)*
- **Claude model:** claude-opus-5-5  *(loop)*
- **Effort:** medium  *(loop)*
- **Claude permissions:** auto  *(loop)*
- **Codex sandbox:** workspace-write  *(loop)*
- **Writable roots:** ~/Library/Application Support/Godot, ~/Library/Application Support/Blender, ~/Library/Caches  *(loop)*

## Starting from a clean clone
- Needs Godot 4.4.x and Blender 4.x. `tools/check.sh` and `tools/capture.sh` find Godot through `$GODOT`, falling back
  to `godot` on the PATH. On the planning machine Blender is at `/opt/homebrew/bin/blender` and Godot isn't installed,
  so set `GODOT=/Applications/Godot.app/Contents/MacOS/Godot` or install it before M1.
- Run `$GODOT --headless --path . --import` once so `.godot/` exists; nothing else needs seeding.
- No services, accounts or secrets. Python tools use only the standard library or Blender's bundled Python, because
  the system Python has no Pillow or numpy.
- Parallel worktrees share nothing but Godot's user data folder, which is safe.

## Targets

| Target | What it is | Run | Capture | Edge conditions |
|---|---|---|---|---|
| godot-headless | Godot 4.4 with no window | `tools/check.sh [suite] [prop ...]` | exit code and the check's report | a prop missing from the manifest, a reimport from a clean `.godot/` |
| preview | The props preview scene, a stand-in for the game's lighting and camera until the game has scenes | `tools/capture.sh <prop or scene> [view]` (Movie Maker, fixed fps) | PNG frame sequences, contact sheets, and the movie's WAV | day and dusk lighting, full resolution and the pixelated 1/3-resolution view, near, mid and far camera |

## Rules
- **Exclusive resources:** none
- **Large captures:** raw frame sequences go in `captures/` (gitignored); commit contact sheets and chosen frames under docs/evidence. A reviewer regenerates the rest with `tools/capture.sh`.
- **Owner decides:** the art direction (PROPS M1 pick); whether a sound is acceptable to listen to; adding or dropping props from the set of 12; any paid asset or licence other than CC0 or self-made; pushing or publishing
- **Licences and paths not to touch:** no third-party or asset-store meshes or textures; sounds CC0 or self-made, credited in docs/CREDITS.md; never put reference images where Godot imports them (docs/ carries a .gdignore)

## Project guidance
- Godot conventions: metres, +Y up, glTF (.glb) imports. Everything else is in docs/modules/PROPS.md.
