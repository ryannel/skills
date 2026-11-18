# plan: Add the goal after V1 to the module list in docs/design/modu

Host: claude. Role: plan. Started: 2026-11-10T22:25:10Z. Session: 160c3f60-9577-4f1d-940a-b001d9f4a954

## Turn 1: prompt sent

````text
Use the plan-module skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/plan-module/SKILL.md) for this task: Add the goal after V1 to the module list in docs/design/modules/ARCHITECTURE.md: the original swarm-survival test game in docs/design/NEXT-GOAL-SWARM-GAME.md, with the 2D support and online multiplayer it needs. Done when ARCHITECTURE.md names the new modules (2D rendering, multiplayer/networking, the game and anything else the brief needs), their owners, interfaces with existing modules, build order after the V1 exit, and a brief for each; the BUILD-PLAN 'After V1' section points at them. Don't change V1 modules' plans or the V1 exit; list any decision that belongs to the owner. No done-when files yet: this work starts after V1.

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file, and don't commit, merge, pull or land. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then. To dry-run a milestone's checks, run `python3 /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/build/scripts/agent_loop.py check --module <M> --milestone <id> --worktree .`. The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report.
````

### Turn 1: last reply

````text
s provisional until the owning module's design review passes.

- **The crowd is shared by causes, not state.** Every peer steps the same rules from the same inputs. The host stays the only authority, and a digest mismatch triggers a full-image repair.
  - **Why:** sending 3,000 movers would cost about 2.9 Mbit/s per client, 45 times the parked wire design's proposed target. Vampire Survivors' own co-op hit the same wall.
  - **Risk:** it depends on the rules matching exactly across Mac, Chrome and the iOS simulator. `SIM-2D`'s first milestone tests that, with a named fallback if it fails.
- **2D is its own scene path, not sprites in the 3D forward pass.** A 2D game then carries no sky, shadow-cascade or light-cluster work; presentation and capture are shared.
- **A native process hosts; browsers only join.** A browser cannot accept connections.

## Work asked of existing modules

These become new milestones in the owning module when track 3 starts; nothing is added now.

- **`CONTENT-LOOP`:** sprite-sheet and font products.
- **`APPLE-TILE`:** selecting the 2D scene path, and an interface stage after reconstruction.
- **`APPLE-PRESENTATION`:** accepting a scene with no temporal reconstruction.
- **`CREATOR` and the platform shells:** an app runner for a game without the sky kit. The iOS shell serves only the V1 game today.
- **Repository guard:** admitting a second external game.

## Build order after the exit

`SIM-2D` and `TRANSPORT` go first, because their first proofs can overturn the plan. `RENDER-2D` can run beside them. Then `SESSION`, `GAME-UI` and `SWARM`. `SWARM`'s concept-options milestone is built first of all, so your pick is in before any art is made.

## Decisions for you

1. **Start and order.** Track 3 is held until the V1 exit. Whether the game goes before, after or beside sea and clouds is yours.
2. **The game's identity.** Name, premise, characters and look: you pick from options in `SWARM`'s first milestone.
3. **Art and licence.** I assumed art made in the repository, original or PD/CC0. A paid generation service is spending, and the publishing licence is yours.
4. **A public host.** Internet play needs a reachable machine, a domain and a certificate, which is spending and deploying. Until you ask, "online" is proved between separate processes on this Mac over real QUIC and WebTransport under simulated latency and loss.
5. **Codex sandbox.** `TRANSPORT`, `SESSION` and `SWARM` need local sockets and Chrome for most checks. The choices are a request per run as today, `danger-full-access`, or a Claude builder for those modules.
6. **Sound.** Not in the brief, so no audio module is planned.
7. **Purpose wording.** The build plan still says "3D engine" and the architecture brief's E08 still excludes pure 2D. Your 10 November goal overrides both; I left the rewording to you.
8. **What finishes the goal.** I proposed: 2–4 players on any mix of the three targets play a whole run together with thousands on screen, smooth on the Mac, and the peers still agree under simulated latency and loss. You have not written an exit, so this stands in.
9. **Builders.** The first two steps hold three lanes that share no files, if you allow more than one.

## Assumptions you can overturn

These are in the module list's log. The loop's report will not list them until each module has a plan file.

- "2D support" means a reusable sprite path with text and interface. 2D lights, tile-map tools, skeletal 2D animation and 2D rigid bodies are not built.
- Players join by address or code. Matchmaking, accounts, relays and host migration are not built.
- Chrome is the only browser, so the WebSocket fallback is not built.
- Interest management (the build plan's "relevance") is not built, because every peer simulates the one arena.
- No gamepad: keys, pointer and touch only.
- The iOS simulator proves function, never speed, as in V1.

The brief's three defaults are unchanged.

PLANNED: docs/design/modules/ARCHITECTURE.md, docs/BUILD-PLAN.md
````

