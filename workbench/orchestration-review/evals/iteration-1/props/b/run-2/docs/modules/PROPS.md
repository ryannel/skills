# PROPS: the harbour props set

This is the only module in the current goal, so there is no `ARCHITECTURE.md` yet. When the boat, water or player
goals start, the project gets one and this module's promises below become its contract.

## What the player should see, hear and feel

A harbour that looks like someone made every object in it by hand for this game. Crates that are slightly out of
square, a bollard worn smooth on top, a lantern that swings and creaks in the wind, a crane that is the first thing
you recognise from the water. Seen from a boat at gameplay distance (about 15 m) each prop reads by silhouette and two
or three colours; walked up to, it still holds up, with a few chosen details and no mush.

The bar is A Short Hike's props, with Lil Gator Game as a second reference: few, large facets; shapes exaggerated
toward their idea (a barrel that is very barrel); a small soft palette with painted gradients rather than photo
texture; wonkiness that looks deliberate, not broken. The anti-bar is an asset-store pack: even bevels, every plank
identical, PBR wood grain, uniform precision.

## The twelve props

| id | Prop | Notes |
|---|---|---|
| crate | Wooden crate | Stacks flush on itself and on the barrel lid |
| barrel | Barrel | Upright; reads round at gameplay distance with very few sides |
| bollard | Mooring bollard | Cast iron, worn top, rope groove |
| rope_coil | Coiled rope | Flat on the dock |
| sack_pile | Pile of cargo sacks | Two or three sacks, one slumped |
| fish_basket | Wicker basket of fish | The one prop with a little colour pop |
| signpost | Harbour signpost | Hand-lettered board; lettering lives in the atlas |
| lobster_pot | Lobster pot | Slatted frame with netting |
| buoy_cluster | Floats and buoys | Hung together on a rope |
| net_rack | Fishing net drying on a rack | The large cut-out prop |
| lantern_post | Lantern on a post and bracket | Swings, glows, creaks on a loop |
| dock_crane | Wooden dock crane | The landmark; jib can turn |

The list is the planner's reading of "crates, barrels, bollards, a dock crane, a lantern, fishing nets, that kind of
thing". Changing it is the owner's call.

## Mechanisms

**Hand-made comes from shape and paint, not from detail.** Each prop is built from a few chunky parts whose edges are
deliberately not straight or parallel where the real thing would warp, sag or wear: planks vary in width, lids sit
slightly askew, posts lean a degree or two. Irregularity is placed by intent (one slumped sack, one bent hoop), never
by uniform random vertex noise, which reads as broken rather than made. Facets are visible; smooth shading is used only
where a surface should read round (barrel bulge, buoys), with hard edges between parts.

**One atlas, one material, everywhere.** Every prop samples one 512 x 512 PNG, `assets/props/atlas/props_atlas.png`,
through one shared material resource. Colour comes from palette swatches and small hand-painted gradient strips
(wood light-to-dark, rope, hessian, iron, painted signage) plus a few detail regions (sign lettering, net mesh,
wicker weave, fish). At 512 for twelve props the texels are large on screen, so the atlas is painted for that: flat
areas and soft gradients, nothing that needs resolution. Texture filtering (nearest or linear) is settled by the
direction pick in M1.

**Cut-out and glow live in the same material.** The net, lobster-pot mesh and wicker gaps use alpha scissor from the
atlas alpha channel. The lantern glass glows. Neither may add a second texture or a second material: the glow is
selected inside the one material, for example from vertex colour or from an atlas region, and lit by a real
`OmniLight3D` in the lantern scene. Whether this works is checked in M1, before any prop depends on it.

**The lantern's swing and creak share one clock.** The swing is a pendulum animation with easing at its extremes; the
creak is a looping audio file whose length equals the swing period (or a whole multiple), with creaks placed at the
turn of the swing. Because both run from the same period, the creak lands on the same point of every swing for as
long as the scene runs, instead of drifting. The loop is seamless: no step at the seam larger than the largest step
inside the file, and the import has looping on. The player is an `AudioStreamPlayer3D` so many lanterns can share a
harbour and fall off with distance. The sound is synthesised or recorded for this repo, or CC0, with its source in
`assets/props/CREDITS.md`.

**Built in Blender, judged in Godot.** Sources are `.blend` files (generator scripts are welcome, but the `.blend` is
committed so the owner can push a vertex by hand) exported to `.glb` and wrapped in a Godot scene per prop. Every
floor rule is enforced on the imported Godot scene, so the check sees exactly what the game will.

**The game's render look doesn't exist yet**, so the props must hold up under both plausible ones: native-resolution
Forward+, and a low-resolution nearest-upscaled view like A Short Hike's. Captures show both.

## What this module promises other modules

- **Prop scenes.** `res://assets/props/<id>/<id>.tscn` for each id above. Root is a `Node3D` at the prop's footprint
  centre on the ground plane, +Y up, facing -Z, 1 unit = 1 metre, at believable real-world scale. Each has simple
  collision (a `StaticBody3D` with box, cylinder or convex shapes, never trimesh) and no scripts other than the
  lantern's.
- **Manifest.** `res://assets/props/manifest.json` lists every prop: id, scene path, and any sound or animation it
  carries. Other modules find props through it.
- **Shared material and atlas.** `res://assets/props/atlas/props_material.tres` and `props_atlas.png`. The atlas
  layout is recorded in `res://assets/props/atlas/atlas_regions.json` (named rectangles, each owned by one prop or by
  the shared palette). Regions don't overlap, and a prop's UVs fall only in its own regions or the palette.
- **Lantern.** Plays its swing, light and creak on its own when added to a scene. Exposes the creak player's bus and
  volume so the future audio mix can own them.
- **Crane.** The jib is a child `Node3D` named `Jib` pivoting about the mast's vertical axis, so a later module can
  turn it. The prop does not animate it.

## Tooling the module owns

- `tools/check_props.gd`: the floor gate, run headless. For every manifest entry it checks the scene loads; total
  triangles across all mesh surfaces at most 1,500; every surface uses the shared material and nothing else; the
  only texture is the 512 x 512 atlas; UVs stay inside the prop's atlas regions; collision exists and is not trimesh;
  and, for props with sound, the loop and period rules above. `-- --require <id,id>` also fails if any named id is
  missing; `-- --manifest <path>` checks another manifest (used for the M1 variants); `-- --self-test` runs it
  against deliberately broken fixtures and fails unless each one is rejected.
- `showcase/harbour_showcase.tscn`: a plain stand-in dock (not a deliverable prop) with day and night lighting,
  where all the props are laid out as a harbour.
- `showcase/turntable.tscn`: renders one prop turning, at gameplay distance and close up, day and night, for Movie
  Maker captures. It also produces the low-resolution nearest-upscaled view.

## Cost

No cost targets beyond the owner's per-prop triangle budget and the single atlas. Record each prop's triangle count
and atlas area in the evidence; nothing else is budgeted, so set no other numbers.

## Risks, in build order

1. The direction is wrong for the owner. M1 makes three variants of the crate and barrel, different in kind, for the
   owner to pick before anything else is built.
2. The single material can't do cut-out and glow. M1 proves it on test pieces.
3. The lantern's motion and sound are the parts agents can't judge alone. M2 builds it next, with the sound marked for
   the owner.
4. The crane is the most complex silhouette in the tightest budget relative to its size. M3.
5. Atlas space runs out once all twelve are painted. The region map makes this visible early; M6 checks the whole set.
