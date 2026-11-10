# PROPS plan
Reviews: none yet; design review owed (`agent_loop.py review --module PROPS --milestone design --worktree .`)
Milestone: M1 Three lantern directions for the owner to pick from
Now: planned, waiting on the design review (since 2026-11-09)
Next: M1, once the design review passes and Godot 4.4 is installed
Blocked: none

## M1 Three lantern directions, built on the real pipeline: open
- [ ] tools/check.sh and tools/capture.sh with the suites and views the design names, and the preview scene
- [ ] atlas.json with space reserved for all twelve props; the atlas source committed
- [ ] three lantern variants different in kind, each within budget and on the atlas
- [ ] docs/anchors/references.md, with a negative anchor
- [ ] owner picks a direction (attended), recorded in docs/anchors/DIRECTION.md

## M2 The lantern sways, glows and creaks: open
- [ ] final lantern in the picked direction, with sway, glow, light and `lit`
- [ ] creak loop locked to the sway, random phase per instance, credited
- [ ] owner listens and accepts the creak (attended)

## M3 Rope and iron (dock_crane, bollard, rope_coil, anchor): open
## M4 Nets and wicker (net_rack, lobster_pot, buoys, fish_basket): open
## M5 Crates and barrel, and the whole set as one harbour: open

## Log
- 2026-11-09 Planned the module: design, plan and done-when file, and wrote ORCHESTRATE.md. The owner couldn't be
  reached, so the assumptions at the end of PROPS.md were decided by the planner and need the owner's confirmation:
  the twelve props, the post-mounted lantern, metres with a 1.7 m figure and +Z front, judging in both full-resolution
  and pixelated views, three materials sharing the one atlas, CC0-or-self-made sound, Blender authoring, and local
  integration to master. Order is by risk: the direction first (it decides everything after), then the lantern (audio
  sync is the least known mechanism), then the crane (the tightest budget), then cutout nets, then the simple pieces
  and the whole-set review. Attended items: M1.10 (the pick) and M2.10 (listening). Godot isn't installed on the
  planning machine; the builder needs it before M1.
