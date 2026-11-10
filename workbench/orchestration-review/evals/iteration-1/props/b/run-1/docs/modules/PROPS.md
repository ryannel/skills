# PROPS: the Saltwind harbour props set

## Brief

Twelve low-poly harbour props for Saltwind, a small sailing game in Godot 4.4. They should feel hand-made, like the
props in A Short Hike, not like an asset-store kit. Each is at most 1,500 triangles, and every prop takes its texture
from one shared 512×512 atlas. One of them, a hanging lantern, has a looping creak. The repository is an empty Godot
project, so this module also builds the small tools that check and capture the props.

This is the project's only module for now, so there's no ARCHITECTURE.md. When the game gets level, boat or lighting
modules, they consume the contract below, and the module map should be written then.

## What the player should see and hear

A harbour that looks as if one person whittled every piece of it. At a glance the set reads as one family: the same
palette, the same chunky proportions, the same way edges and planks are a little off. Each prop reads from its
silhouette alone at the distance a sailing camera sees a dock from, and still holds up when the camera comes close
enough to see a single plank. At dusk the lantern throws a warm pool of light and creaks as it sways, quietly enough
to sit under the rest of the harbour without becoming irritating.

The range to hold it across:
- **Distance:** near (prop fills a third of the frame), mid (a dock's length away), far (a whole harbour in frame).
- **Lighting:** day and dusk, in the preview scene's stand-in rig.
- **Presentation:** full resolution, and a pixelated view at one-third resolution with nearest upscaling. A Short
  Hike's look depends heavily on that low-resolution rendering, and the game hasn't chosen its presentation yet, so
  props must read in both.

### The set (12)

| Prop | Notes |
|---|---|
| lantern | Iron-and-glass lantern hanging from a bracket on a wooden post. Sways, glows, creaks. |
| dock_crane | Hand-cranked wooden jib crane: post, jib, winch with handle, rope over the jib tip to a hook. The tightest budget. |
| bollard | Cast-iron mooring bollard with a mooring rope loop. |
| rope_coil | A coiled mooring line lying on the deck. |
| anchor | A small fisherman's anchor leaning against something, with a bit of chain. |
| net_rack | Fishing net hung to dry over a simple pole rack. |
| lobster_pot | Slatted wooden creel with netting ends. |
| buoys | A cluster of cork and glass floats tied on a short rope. |
| fish_basket | Wicker basket with a few fish showing. |
| crate | Small wooden crate. |
| crate_long | Long slatted crate, stackable with the small one. |
| barrel | Wooden barrel with iron hoops. |

The dock, pier and quay walls aren't props; they belong to whatever module builds the harbour level.

## Mechanisms

These are settled. The builder chooses everything else.

**Hand-made comes from designed irregularity, not noise.** Each piece gets a few deliberate imperfections chosen for
it: a plank set a few degrees off, a hoop thicker on one side, a post that leans, a lid that doesn't quite sit flat.
Uniform random vertex jitter over a whole mesh reads as a filter, and it's the commonest way a scripted mesh ends up
looking procedural. Proportions are chunky and exaggerated, with a few big forms rather than many small ones, because
small detail is what the triangle budget and the pixelated view both throw away.

**One atlas, palette plus a few drawn details.** `harbour_atlas.png` is 512×512. Most of it is flat palette swatches,
each a hand-picked colour or short painted gradient, and faces are UV-mapped onto a swatch. A small number of
hand-drawn detail tiles (wood grain, rope, wicker, net mesh, rust, the lantern glass) cover what flat colour can't.
It's sampled with nearest filtering. Detail tiles share one texel density across the set, chosen in M1 and recorded in
the atlas map, so no prop looks sharper or blurrier than its neighbours. Flat-colour UVs sit inside their swatch,
clear of its edges, so mipmaps and filtering can't bleed a neighbour's colour in. The atlas map `atlas.json` names every
region, and M1 reserves space for all twelve props so later milestones don't have to repack it. The atlas is made
from a source the builder commits (a script or a layered file), so a region can be repainted without starting over.

**Up to three materials, one texture.** Opaque (most things), alpha-scissor and double-sided (net mesh, the lobster
pot's netting), and glow (the lantern glass, emissive from its atlas region). All three use the same atlas. All are
matte: roughness 1, no metallic or normal maps. Metal is painted, not simulated, because physically based shine is
what makes a low-poly prop look like a store kit.

**Nets are textured cards, not modelled strands.** A net is a few draped, slightly bunched surfaces textured with the
net-mesh tile under the alpha-scissor material. Modelling strands would cost thousands of triangles. Shimmer at mid
distance is the known risk of a cutout texture, so it's inspected in motion.

**The lantern's sway and creak share one clock.** The sway is a pendulum loop in an AnimationPlayer, and the creak is
a seamless audio loop exactly one or more whole sway periods long, with each creak placed at a swing extreme, where a
real lantern's hook would creak. Each lantern instance starts at a random phase, applied to the animation and the audio
together, so several lanterns don't creak in unison. The audio plays from an AudioStreamPlayer3D in the lantern scene,
with distance attenuation, and loops through the import's loop setting rather than a script restarting it, because a
restart leaves a gap. A single creak looped on its own sounds mechanical within seconds, so the loop holds a few
creaks that differ in pitch and length.

**The sound is CC0 or made for the game.** Recorded creaks (for example CC0 entries on Freesound) may be cut, layered
and pitched; synthesis is fine too. Source, licence and edits go in `docs/CREDITS.md`.

**Authoring is reproducible.** Each prop's mesh is authored in Blender, with the source (.blend or the Python that
builds it) committed beside the exported .glb, so a reviewer's finding can be fixed without remodelling from scratch.
The scene is a Godot `.tscn` that instances the .glb.

## Contract: what this module promises other modules

- Every prop is `res://assets/props/harbour/<name>/<name>.tscn`, listed in `res://assets/props/harbour/props.json`
  (name, scene path, triangle count, footprint in metres).
- Root is a `StaticBody3D` on collision layer 1, with simple collision shapes (boxes, cylinders, or one convex hull)
  covering the footprint. The visual mesh is never the collision mesh.
- Units are metres, +Y up, origin at the centre of the prop's ground contact, front facing +Z (glTF convention). A
  1.7 m figure is the scale reference: crates reach about the knee, the crane jib clears head height.
- Every visual surface uses one of the three shared materials in `res://assets/props/harbour/materials/`, which all
  sample `res://assets/props/harbour/atlas/harbour_atlas.png`.
- The lantern exports `lit: bool` (glow, light and creak on together) and `audio_bus: StringName`, defaulting to
  `Master`, since the project has no bus layout yet. Its light casts no shadows.
- crate and crate_long stack: their tops are flat at a documented height, so one sits on another with no gap or
  overlap.

Other modules don't edit anything under `assets/props/harbour/`. To change the contract they propose it in this
module's plan log.

## Tools this module builds

The project starts empty, so M1 builds the tools every later item depends on. Their interface is fixed here because
done-when items call them; how they work is the builder's choice.

- `tools/check.sh [suite] [prop ...]` runs one suite (`import`, `budget`, `atlas`, `scene`, `audio`, `set`) or all of
  them, for the named props or every prop in the manifest, and exits non-zero on any failure. With no arguments it's the
  profile's `Check`.
  - `budget`: triangles summed over every surface of every MeshInstance3D in the scene, at most 1,500.
  - `atlas`: every surface uses a shared material; the atlas is 512×512 with nearest filtering; every UV triangle
    lies inside one region of `atlas.json`; detail-tiled faces are within 25% of the set texel density.
  - `scene`: the contract above (root type, collision present, origin at the base within 2 cm, manifest entry correct).
  - `audio`: the lantern loop (see M2).
  - `set`: the manifest has the twelve props and they all pass.
- `tools/capture.sh <prop or scene> [view]` renders the preview scene with Godot's Movie Maker at a fixed frame rate
  into `captures/`, and makes contact sheets. Views include a turntable with the underside, near/mid/far, day/dusk,
  and the pixelated view.
- The preview scene in `tools/preview/` holds the lighting rig and the 1.7 m scale figure. It stands in for the game's
  lighting, so it should be plain and warm, not flattering.

`docs/` and `captures/` carry a `.gdignore`, so Godot never imports reference images or captures into the game.

## Cost

Real targets from the owner: at most 1,500 triangles per prop, and one 512×512 atlas for everything. Nothing else has
a target. Record the set's total triangles, draw calls per prop, and the creak's peak and integrated loudness in the
manifest or evidence, as a baseline for later tripwires.

## How taste is judged

M1 builds three lanterns that differ in kind, and the owner picks one. That pick, with the reference set, is the anchor
for every later milestone. The reference set in `docs/anchors/references.md` holds links to A Short Hike (press kit and
store screenshots) and a couple of other hand-made low-poly games, plus a negative anchor: a clean commercial low-poly
harbour kit, which is what the set must not look like. Images may be kept there only if they come from an official press
kit; otherwise it's links and the builder's notes.

Before claiming a taste item, the builder gets a critique from a fresh context given only the item, the bar, the anchors
and new captures, fixes what it finds, and goes round again while the findings still matter.

Nobody but the owner can judge how the creak sounds, so that item is attended.

## Assumptions made without the owner

The owner couldn't be reached while this was planned. Each of these is a guess to confirm or overturn:
- The twelve props in the table, including anchor, buoys, lobster pot and fish basket for "that kind of thing", and
  excluding the dock itself.
- The lantern hangs from a post-mounted bracket, and is a standalone prop rather than something that hangs off the
  crane or a wall.
- Scale is metres with a 1.7 m reference figure, and front is +Z.
- Props must read at full resolution and in a pixelated view, because the game's presentation isn't chosen.
- Up to three materials share the atlas (opaque, cutout, glow); "single atlas" was read as one texture, not one material.
- Sound licences limited to CC0 or self-made; no paid packs.
- Blender for authoring, because it's installed on this machine; Godot 4.4 must be installed before building.
- Integration is local to `master`, with no pushing, because there's no remote and no permission to push.
