# The project profile: `ORCHESTRATE.md`

Every orchestrate skill reads this file at the repository root before acting. It holds what differs between projects,
so the skills stay generic. Keep it to a page; link to longer project docs rather than copying them.

Lines marked *(read by the loop)* are parsed by `scripts/agent_loop.py`, so keep their `- **Label:** value` shape.

## Template

```markdown
# Orchestrate profile: <project>

## Purpose
- **Purpose and goal:** <link to the doc that states what this project is for and what "done" means for the current goal>
- **Quality bar:** <the standard visual and behavioural items are judged against, in words, e.g. "would pass in a
  well-reviewed shipped product of this kind: Linear and Things for interaction polish">

## Where things live
- **Plans:** docs/modules  *(read by the loop; holds <MODULE>.md, <MODULE>-PLAN.md, <MODULE>-DONE.json)*
- **Contracts:** <path to shared contracts, or "none yet">
- **Evidence:** <where review files and evidence pages go, e.g. docs/evidence>
- **Graded examples:** <path, e.g. docs/orchestrate/graded-examples.md>
- **Scratch:** <throwaway work, e.g. tmp/ (gitignored)>
- **Status ledger:** <optional: a file that records capability status, or "the plans">

## Checks and integration
- **Check:** <the command whose pass gates integration, e.g. `npm run check`, `./dev check`, `cargo test --workspace`>
- **Integrate:** main  *(read by the loop: `main` = rebase, check, push to main without force; `pull-request` = push a
  branch and open a PR)*
- **CI:** <does CI gate merges, or is the local check the gate?>

## Targets
Where behaviour is proved. Done-when items name one of these.

| Target | What it is | Run | Capture evidence |
|---|---|---|---|
| <web-chrome> | <Chrome, desktop viewport> | <`npm run dev`, open localhost:5173> | <Playwright screenshots and a trace per scenario> |
| <ios-sim> | <iPhone simulator; function only, never speed> | <`xcodebuild …`> | <`xcrun simctl io booted screenshot`> |
| <cli> | <the built binary> | <`cargo run -- …`> | <the command transcript and exit code> |

Label stand-ins as `proxy:<what it stands in for>`.

## Exclusive resources
<Shared things only one run may use at a time, e.g. "gpu: timing and capture runs", "port 5173", "the staging
database". Wrap such runs in `agent_loop.py lock <name> -- <command>`. Or "none".>

## Owner
- **Owner decides:** <e.g. changing purpose or the goal; spending; publishing, licensing or deploying; irreversible
  actions>. Everything else proceeds without asking.
- **Licences:** <e.g. no GPL or share-alike code or data>
- **Don't touch:** <other repositories or paths agents must not modify>

## Models
- **Codex generator:** gpt-6.1-sol medium  *(read by the loop)*
- **Evaluator / planner / lead:** <defaults from the orchestrate skill, or overrides>

## Project guidance
Domain rules each level reads, kept in the project:
- **Planning:** <e.g. docs/architecture.md, a project skill>
- **Building:** <e.g. .agents/skills/<project>-engineering, coding standards, performance policy>
- **Reviewing:** <e.g. calibration failures this project has already paid for>
```

## Notes on each part

- **Quality bar.** Name shipped examples and say what about them sets the standard. Never attach a target image to
  match: evaluators judge against an inspection list and this bar in words.
- **Check.** One command, runnable locally, fresh on the rebased tip. If CI is the gate, say so, and the generator
  waits for CI before claiming done.
- **Targets.** Pick capture methods the evaluator can inspect: images, frame sequences or contact sheets, traces,
  transcripts. Agents can't watch live video, so motion means a captured sequence.
- **Owner decides.** Keep it short and specific. Anything not on it is the agents' to decide.
