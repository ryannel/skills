# Orchestrate profile: Saltwind

- **Purpose:** docs/PURPOSE.md
- **Quality bar:** Props that could sit in A Short Hike (2019) without looking out of place: chunky, slightly wonky, faceted low-poly shapes with soft flat-and-gradient colour from a small warm palette and silhouettes that read at a glance. The look to avoid is the uniform, ruler-straight, evenly bevelled generic pack, such as Kenney's Pirate Kit or a typical asset-store "low poly harbour" bundle.
- **Plans:** docs/modules  *(loop)*
- **Evidence:** docs/evidence  *(loop: review files and evidence pages)*
- **Graded examples:** docs/evidence/graded-examples.md  *(past verdicts the owner agreed with or overturned; none yet)*
- **Check:** scripts/check.sh all  *(loop: required; created in PROPS M1; runs the headless Godot suites and the regeneration check)*
- **Integrate:** local  *(loop: required; fast-forward local master only, the owner merges and pushes; there is no remote yet)*
- **Branch:** master  *(loop)*
- **Remote:** origin  *(loop: no remote is configured yet; unused while Integrate is local)*
- **Builders:** usually one Codex builder  *(how many builders, on which hosts, when the owner doesn't say)*
- **Default host:** codex  *(loop)*
- **Codex model:** gpt-6.1-sol  *(loop)*
- **Claude model:** claude-opus-5-5  *(loop)*
- **Effort:** medium  *(loop)*
- **Claude permissions:** auto  *(loop)*
- **Codex sandbox:** workspace-write  *(loop)*
- **Writable roots:** ~/Library/Application Support/Godot, ~/Library/Application Support/Blender, ~/Library/Caches  *(loop)*

## Starting from a clean clone

1. Tools: Godot 4.4.x (standard, not .NET) and Blender 5.2 LTS. Blender is at `/opt/homebrew/bin/blender` on the
   owner's Mac. Godot was not found on this machine when the plan was written; install 4.4.x from
   godotengine.org (or `brew install --cask godot` if it still ships 4.4) and either put `godot` on `PATH` or set
   `GODOT=/path/to/Godot.app/Contents/MacOS/Godot`. `scripts/check.sh` (PROPS M1) finds Godot via `$GODOT`, then
   `PATH`, then `/Applications/Godot.app`, and fails with a clear message if it can't.
2. `scripts/build_props.sh` regenerates the atlas, the creak and every prop from their generators (Blender headless
   for meshes and atlas). Committed outputs are expected to equal what it produces.
3. `"$GODOT" --headless --path . --import` builds the import cache in `.godot/` (not committed).
4. `scripts/check.sh all` runs every suite headless.

No services, ports, databases, secrets or accounts. Each worktree has its own `.godot/` cache, so parallel worktrees
don't interfere.

## Targets

| Target | What it is | Run | Capture | Edge conditions |
|---|---|---|---|---|
| godot-headless | Godot 4.4 `--headless` on the owner's Mac | `scripts/check.sh <suite>` | transcript and exit code | missing Godot or Blender, a prop scene that fails to load, an over-budget fixture |
| godot-lookdev | Godot 4.4 Forward+ in a window on the owner's Mac, `res://lookdev/` scenes with a reference harbour lighting rig (stands in for the game's lighting, which doesn't exist yet) | `scripts/capture.sh <prop> <out-dir>` | PNG turntables and frame sequences, plus the run log | day and dusk lighting; 1.5 m, 12 m and 25 m camera distance; eye height 1.2 m and boat height 0.5 m; underside views |
| owner-ears | The owner listening on their Mac, speakers or headphones | the lantern lookdev scene, run from the Godot editor | the owner's words, recorded in the plan log | 1 m and 10 m from the lantern; several lanterns at once; two minutes of loop |

If the capture window can't render (for example no display session), the capture script records that in its log and
exits non-zero; checks on godot-headless never depend on it.

## Rules
- **Exclusive resources:** none
- **Large captures:** PNG frames go in `docs/evidence/PROPS/<milestone>/`, at most 1280 x 720 and about 300 KB each; frame sequences at 12 fps, no video files.
- **Owner decides:** changing the prop list, the 1,500-triangle budget or the 512 atlas; using any third-party mesh, texture or sound; approving the M1 look and the M2 creak; publishing or pushing anywhere  *(loop: restated on resumed turns)*
- **Licences and paths not to touch:** no asset-store, marketplace or other third-party meshes, textures or sounds (everything is made in this repo); don't change project.godot's renderer or engine version; never write outside this repository  *(loop: restated on resumed turns)*

## Project guidance
- Props design and contract: docs/modules/PROPS.md
