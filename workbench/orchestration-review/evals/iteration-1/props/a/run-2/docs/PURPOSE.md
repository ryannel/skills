# Saltwind: purpose

Saltwind is a small low-poly sailing game in Godot 4.4. The player sails between little harbours; the harbours are
where the world feels lived-in, so their props carry a lot of the game's character.

## Current goal: the harbour props set

About a dozen harbour props (crates, barrels, bollards, a dock crane, a hanging lantern with a looping creak, fishing
nets and similar) that later game modules place into harbour scenes.

The owner's words: "should feel hand-made like A Short Hike, not asset-store. max 1.5k tris each, everything on a
single 512 atlas."

The goal is finished when:

- Twelve props exist as ready-to-place Godot scenes, each at or under 1,500 triangles, all textured from one
  512 x 512 atlas.
- They read as one hand-made set in the spirit of A Short Hike, not as a generic low-poly asset pack.
- The lantern swings and creaks on a seamless loop.
- A small harbour-corner scene shows the whole set together, and the owner has approved the look and the creak.

Hard limits from the owner: 1,500 triangles per prop; one 512 x 512 atlas for the whole set. No other cost targets
have been set.

Out of scope for this goal: the boat, the water, the player, the game's own renderer settings (such as a low-res
pixelated render) and harbour layout beyond the showcase corner.
