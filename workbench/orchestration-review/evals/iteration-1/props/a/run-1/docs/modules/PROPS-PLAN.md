# PROPS plan
Reviews: design review owed: not run, because the planner could not start a reviewer; the lead runs `agent_loop.py review --module PROPS --milestone design --worktree .`
Milestone: M1 Pipeline, atlas and the style trio
Now: plan written, waiting for its design review (since 2026-11-09)
Next: M1 once the design review passes
Blocked: none

## M1 Pipeline, atlas and the style trio: open
- [ ] Blender scripts, atlas generator and `tools/build_props.sh` regenerate everything from source
- [ ] The full atlas layout, with reserved regions for every later prop, and the three shared materials
- [ ] crate, barrel and bollard as scenes under the contract
- [ ] `tools/check.sh` (import, triangle budget, atlas and material rules, sizes, contract) and the gallery scene
- [ ] Owner signs off the art direction from the M1 style sheet

## M2 The lantern, its swing and its creak: open
- [ ] Lantern and bracket post, glow material and light
- [ ] Synthesised creak loop and onset times; loop analysis script
- [ ] Swing driven by audio playback position; sync test

## M3 Dock crane and fishing net: open
- [ ] Dock crane with turning `Jib`
- [ ] Fishing net with cutout weave and floats

## M4 The small props: open
- [ ] lobster_pot, rope_coil, mooring_piling, buoy, fish_basket, anchor

## M5 The set as a whole: open
- [ ] Harbour showcase scene with all twelve; `assets/props/README.md`; recorded baseline costs

## Log
- 2026-11-09 Plan written from the owner's request. The owner could not be reached, so the planner decided: the
  twelve props, script-generated geometry in Blender, a synthesised creak, an 8 to 15 m viewing distance, and local
  integration. These are listed in docs/PURPOSE.md. M1 carries an attended art-direction sign-off so the owner sees
  the style before nine more props are built in it. Milestones are ordered by risk: the look first, then the lantern
  (audio sync is the riskiest mechanism), then the two hardest shapes, then the rest.
