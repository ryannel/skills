# PROPS plan
Reviews: design review owed (`agent_loop.py review --module PROPS --milestone design --worktree .`); not run during planning
Milestone: M1 A crate and a barrel that look hand-made, on the one atlas, inside budget
Now: planned; waiting for the design review before building (since 2026-11-09)
Next: design review, then M1
Blocked: none

## M1 A crate and a barrel that look hand-made, on the one atlas, inside budget: open
- [ ] `scripts/check.sh` with the budget, atlas, contract and repro suites, each with a bad fixture it rejects
- [ ] `scripts/build_props.sh`: Blender-headless generators for the atlas and props, exported as .glb
- [ ] Shared hand-made helper with named constants and per-prop seeds
- [ ] Atlas v1 (palette ramps, padding, first painted details) and the two shared materials
- [ ] `crate` and `barrel` scenes to the contract
- [ ] `res://lookdev/` day and dusk rig on a simple dock, and `scripts/capture.sh`
- [ ] Style sheet and turntables in docs/evidence/PROPS/M1/; owner sign-off recorded in the log

## M2 A hanging lantern that swings and creaks in time, on a loop that never clicks: open
- [ ] Creak generator (stick-slip synthesis), seamless WAV, and the `audio` suite
- [ ] `lantern` scene: swing driven by playback position, position-hashed phase, game-time fallback, SFX bus, light
- [ ] Waveform and spectrogram evidence; owner listening verdict recorded in the log

## M3 The dock crane: the set's centrepiece, inside 1,500 triangles: open
- [ ] `crane` with a rotatable jib node and hanging rope and hook

## M4 Netting: a fishing net drying on its rack, and a lobster pot: open
- [ ] Net region in the atlas with transparent holes; `net_rack` and `lobster_pot`

## M5 The rest of the dockside: open
- [ ] `bollard`, `piling`, `rope_coil`, `buoy`, `fish_basket`, `sacks`

## M6 A harbour corner dressed with all twelve props, reading as one set: open
- [ ] `res://lookdev/harbour_corner.tscn`, the twelve-prop line-up, and docs/props/CATALOGUE.md

## Log
- 2026-11-09 Planned the module from the owner's request. Single module, so no ARCHITECTURE.md. Milestones ordered
  by risk: the look (M1, with an owner sign-off before ten more props copy it), the creak (M2), the crane's budget
  (M3), cutout nets at distance (M4), then the remaining props and the whole-set read. The owner couldn't be reached;
  the assumptions taken in their place are listed at the end of PROPS.md (the six props beyond those named, Blender
  scripting, a synthesised creak, a second cutout material on the same atlas, nearest filtering, no variants,
  1.2 m eye height). Godot wasn't found on the machine and has to be installed before M1 can run its checks. The
  design review is owed: it wasn't run during planning, and the lead should run it before the loop builds M1.
