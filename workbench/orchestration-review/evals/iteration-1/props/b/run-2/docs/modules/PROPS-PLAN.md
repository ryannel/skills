# PROPS plan
Reviews: design review owed (agent_loop.py review --module PROPS --milestone design); not yet run
Milestone: M1 Direction: the owner picks the look from three crate-and-barrel variants
Now: plan written, waiting for the design review (since 2026-11-09)
Next: design review, then M1
Blocked: none

## M1 Direction and pipeline: open
- [ ] Prop pipeline: Blender source to `.glb` to a Godot prop scene, with the shared material and atlas
- [ ] `tools/check_props.gd` with its self-test fixtures, and the turntable capture scene
- [ ] Shared material proven on opaque, cut-out and glowing test pieces
- [ ] Three crate-and-barrel variants, different in kind, each with its own trial atlas
- [ ] Variant sheet for the owner; the pick and reference set recorded in `docs/anchors/`

## M2 Swinging lantern with a looping creak: open
- [ ] Lantern post in the chosen direction, swing and light
- [ ] Creak loop with the same period as the swing; source recorded in CREDITS.md
- [ ] Night and day captures, swing frame sequence, owner listening pass

## M3 Dock crane: open
- [ ] Crane with a turnable `Jib`, within budget, captured from every side

## M4 Dock clutter: open
- [ ] crate and barrel rebuilt in the final atlas, plus bollard, rope_coil, sack_pile, fish_basket, signpost

## M5 Nets and pots: open
- [ ] net_rack, lobster_pot, buoy_cluster using the cut-out regions

## M6 The harbour together: open
- [ ] All twelve laid out in the showcase; whole-set coherence and final atlas

## Log
- 2026-11-09 Planned from the owner's request. One module, so no ARCHITECTURE.md. The owner couldn't be reached, so
  these were decided by the planner and should be confirmed when the owner is back:
  - The twelve props are the list in PROPS.md (crate, barrel, bollard, rope_coil, sack_pile, fish_basket, signpost,
    lobster_pot, buoy_cluster, net_rack, lantern_post, dock_crane).
  - Tools: Godot 4.4 and Blender 4.x on the PATH; meshes authored in Blender and exported as `.glb`.
  - `Integrate: local` on `master`, since no permission to push was given; one Codex builder.
  - "Single 512 atlas" read as one 512 x 512 colour texture and one shared material for all props; cut-out and glow
    must come from inside that material.
  - The creak is synthesised or recorded for the repo, or CC0; nothing else without the owner.
  - Scale is 1 unit = 1 metre at believable real-world size, since no boat or player exists to scale against.
  - Each prop gets simple collision, because a sailing game's harbour will be bumped into.
  - The crane is static; its jib is a separate node so a later module can turn it.
  - The showcase dock and lighting are stand-ins until the game has its own look; captures cover both native and
    low-resolution nearest-upscaled rendering.
  - The direction pick (M1.7) and the creak listening pass (M2.7) are attended items for the owner.
