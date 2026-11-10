# Orchestrate profile: Saltwind

- **Purpose:** docs/PURPOSE.md
- **Quality bar:** As hand-made and readable as the props in A Short Hike (its crates, signposts, docks and fishing gear): chunky, slightly wonky, soft flat colour from a small warm palette, readable as a silhouette from the boat. Not asset-store: no photo textures, no normal maps or PBR sheen, no perfectly regular CAD geometry.
- **Plans:** docs/modules  *(loop)*
- **Evidence:** docs/evidence  *(loop: review files and evidence pages)*
- **Graded examples:** docs/evidence/graded-examples.md  *(none yet; past verdicts the owner agreed with or overturned)*
- **Check:** tools/check.sh  *(loop: required; written in PROPS M1, runs the Godot import and every prop check; before M1 lands it does not exist)*
- **Integrate:** local  *(loop: required; the owner has not given permission to push, so the owner merges)*
- **Branch:** main  *(loop)*
- **Remote:** origin  *(loop)*
- **Builders:** one Codex builder; the props share one atlas, so parallel builders would collide on it
- **Default host:** codex  *(loop)*
- **Codex model:** gpt-6.1-sol  *(loop)*
- **Claude model:** claude-opus-5-5  *(loop)*
- **Effort:** medium  *(loop)*
- **Claude permissions:** auto  *(loop)*
- **Codex sandbox:** workspace-write  *(loop)*
- **Writable roots:** ~/Library/Application Support/Godot, ~/Library/Caches/Godot, ~/Library/Application Support/Blender  *(loop)*

## Starting from a clean clone

Needs Godot 4.4 on the PATH as `godot`, Blender 4.2 LTS or later as `blender`, and `python3` with `numpy`, `scipy`
and `Pillow`. No services, accounts, secrets or network. `tools/build_props.sh` regenerates the atlas, every prop's
`.glb` and the creak from source; `godot --headless --path . --import` imports them. Worktrees share nothing but the
Godot and Blender user folders above, which are caches.

## Targets

| Target | What it is | Run | Capture | Edge conditions |
|---|---|---|---|---|
| pipeline | Blender and Python sources, the Godot headless import, the prop checks | `tools/build_props.sh`, then `tools/check.sh [prop ids]` | the commands' transcripts and exit codes | a clean clone with no `.godot/` cache; regenerating twice |
| godot-render | Godot 4.4 Forward+ with a window, rendering the prop gallery scene | `godot --path . res://tools/gallery/gallery.tscn -- --props=<ids> --out=docs/evidence/props/<milestone>` | PNGs: per prop, an 8-angle turntable plus top and underside, at 1.5 m, 10 m and 25 m, under the day and dusk rigs | dusk light; 25 m (mipmaps, silhouette); underside; night for the lantern |
| audio | rendered sound files and their analysis | `python3 tools/audio/analyse.py <wav> --out=<dir>` | waveform and spectrogram PNGs of two loop repeats joined, and a numbers report | the loop seam; first and last 50 ms |

## Rules
- **Exclusive resources:** display: one windowed gallery capture at a time
- **Large captures:** gallery PNGs go in docs/evidence/props/<milestone>/ and are committed; keep each under 400 KB
- **Owner decides:** changing the prop list or the limits; the art direction sign-off in PROPS M1; whether the creak sounds right; spending money; adding any third-party asset; pushing or publishing  *(loop: restated on resumed turns)*
- **Licences and paths not to touch:** no third-party models, textures or sounds of any licence; everything is generated from sources in this repo; do not edit project.godot settings beyond what a milestone names  *(loop: restated on resumed turns)*

## Project guidance
- The prop contract and art rules are in docs/modules/PROPS.md; builders and reviewers read it before any prop work.
