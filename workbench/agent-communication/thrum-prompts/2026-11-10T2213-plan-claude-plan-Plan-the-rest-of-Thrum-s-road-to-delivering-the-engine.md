# plan: Plan the rest of Thrum's road to delivering the engine, as a

Host: claude. Role: plan. Started: 2026-11-10T22:13:28Z. Session: 411b8249-282f-4ce5-a36d-4e916c3230f8

## Turn 1: prompt sent

````text
Use the plan-module skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/plan-module/SKILL.md) for this task: Plan the rest of Thrum's road to delivering the engine, as a project-level plan that brings water and clouds into it.

Purpose. The owner wants work lined up continuously toward the V1 exit in docs/BUILD-PLAN.md, so builders always have a next milestone, and wants water and clouds finished and consolidated. Today only PLATFORM-RUNTIME-MAC M2 and APPLE-TILE (G3t) are planned and open; everything after them is unplanned.

Water and clouds are built in the Broadsides repository at /Users/ryannel/Workspace/Broadsides, not here. Water is on branch codex/water-rust-system, with notes/water/DESIGN.md, DESIGN-PLAN.md and HANDOFF.md. Three spikes on 10 November left results on branches claude/fable-hull-release, claude/fable-near-waterline and claude/fable-foam (notes/water/FABLE-*.md on each). Two cloud paths, a baked library and a procedural one, were built by separate Codex agents in Broadsides; find their branches and notes there. docs/design/decisions/SEA-AND-CLOUD-PORT.md governs bringing them into Thrum: it says Thrum wasn't ready on 6 November and that the owner schedules porting. The owner has now asked for both to be finished and consolidated. Decide, with reasons, what finished means for each, whether that finishing happens in Broadsides first or as Thrum modules, and where in the build order the port's readiness conditions are met.

Done means: the project plan (module map, build order, contracts and a brief per module) covers the remaining work to the V1 exit plus water and clouds; each module that can start next has its design, plan and done-when file, so a builder can start it; and the build plan's active section points to it. List anything that needs an owner decision, such as port timing or spending, in your result rather than deciding it.

Boundaries. Don't change the definitions of PLATFORM-RUNTIME-MAC M2 or APPLE-TILE, because builders are on them. Read Broadsides but don't change it.

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file, and don't commit, merge, pull or land. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then. To dry-run a milestone's checks, run `python3 /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/build/scripts/agent_loop.py check --module <M> --milestone <id> --worktree .`. The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report.
````

### Turn 1: last reply

````text
ame; Thrum's bar is full refresh.
  - Its sky, exposure and temporal path are not ported, so every look verdict has to be earned again under G3s.
  - Most of its open work is in plumbing the port decision already says to rewrite.
  - The three 10 November water spikes all ended without a pass.
- **What finished means for sea:** open sea from calm to gale, floating bodies through one asynchronous query, a persistent wake, transported foam, and shared-contract optics, at full refresh on Mac and Chrome.
- **What finished means for clouds:** one provider drawing weather layers and the twelve accepted baked volumes with one march and one light, shading the world once, running shadow-only, at full refresh.
- **Where readiness is met:** a first sea or cloud frame can be built once `APPLE-TILE:M3`, `APPLE-PRESENTATION:M3`, `ATMOSPHERE:M5` and `EFFECT-GRAPH:M1` are Done, which falls before G7. The ports close after the governor (`APPLE-PRESENTATION:M7`).

## Plans still owed

Each is a plan run from its brief: G4 M4–M11, `CULLING` (G3c), `EFFECT-GRAPH`, `CONTENT-LOOP` (G5 close), `SEA`, `CLOUDS`, `SHOWCASE` (G7). None can start today; each waits on `APPLE-TILE` or on port timing.

## Checks

- `./dev check-docs` passes and the three done-when files validate against the loop's rules.
- The new script checks fail as expected when run by hand, except the Chrome one below.
- Not run: the full `agent_loop.py check`, because it runs `./dev check` on the GPU the live builder is using; and `check_v1_browser.mjs --case environment`, where I only read that an unknown case throws.
- A mistaken `--help` call ran the existing starter live-reload check once, which passed; I deleted its output folder.

Sources: [Nubis Evolved, SIGGRAPH 2022](https://advances.realtimerendering.com/s2022/SIGGRAPH2022-Advances-NubisEvolved-NoVideos.pdf), [3D water effects survey](https://www.gamedeveloper.com/programming/3d-water-effects-here-s-what-s-involved-)

## Decisions for the owner

1. **Port timing.** The water decision says implementation follows G7. Readiness is met earlier, so `SEA` and `CLOUDS` builders could start at their CPU milestones now, at their GPU milestones mid-order, or after G7. Until you say, they have briefs and no done-when file.
2. **Licence.** Broadsides code is `UNLICENSED` and the cloud library is owner-only; lifting either into Thrum, whose demos are meant to have public source, needs your licence first.
3. **V1 exit.** It is unchanged; sea and clouds are not added to it.
4. **Second builder.** `CREATOR` M1–M2 and `ATMOSPHERE` M5 are safe beside `APPLE-TILE` if you allow one.
5. **Broadsides threads.** This plan needs nothing more from them; whether they stay paused is yours.
6. **Spending.** None requested; physical-device runs stay owed.

Assumptions you can overturn in a line:
- Finished sea excludes chase-distance hull spray, the attached sheet, a rising gas cloud, inland water and coasts.
- Finished clouds excludes the ten genera, squall and warm front.
- Cloud consolidation is the port decision's hybrid of weather layers and placed volumes.
- The starter gets a Chrome form now; the G6 decision had left that as an owner question.
- "Profiler" in the exit is met by demo-UI readouts.
- G3s closes with the west-lookout crossing still parked.
- Readiness work (`ATMOSPHERE` M5) proceeds before port timing is settled.
- G4 seams 1–4 are accepted as the design wrote them.

PLANNED: docs/design/modules/ARCHITECTURE.md, docs/design/modules/SEA-BRIEF.md, docs/design/modules/CLOUDS-BRIEF.md, docs/design/modules/CREATOR.md, docs/design/modules/CREATOR-PLAN.md, docs/design/modules/CREATOR-DONE.json, docs/design/modules/ATMOSPHERE.md, docs/design/modules/ATMOSPHERE-PLAN.md, docs/design/modules/ATMOSPHERE-DONE.json, docs/design/modules/APPLE-PRESENTATION.md, docs/design/modules/APPLE-PRESENTATION-PLAN.md, docs/design/modules/APPLE-PRESENTATION-DONE.json, docs/design/modules/CLOUDS.md, docs/design/decisions/SEA-AND-CLOUD-PORT.md, docs/BUILD-PLAN.md
````

