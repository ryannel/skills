# The project profile: `ORCHESTRATE.md`

Every orchestrate skill reads this file at the repository root before acting. It holds what differs between projects,
so the skills stay generic. Keep it to a page; link to longer project docs rather than copying them.

Lines marked *(read by the loop)* are parsed by `agent_loop.py` in the build-parallel skill, so keep their
`- **Label:** value` shape. `agent_loop.py profile --worktree <repo>` checks them.

## Template

```markdown
# Orchestrate profile: <project>

## Purpose
- **Purpose and goal:** <link to the doc that states what this project is for and what "done" means for the current goal>
- **Quality bar:** <the standard visual and behavioural items are judged against, in words, e.g. "would pass in a
  well-reviewed shipped product of this kind: Linear and Things for interaction polish">

## Where things live
- **Plans:** docs/modules  *(read by the loop; holds <MODULE>.md, <MODULE>-PLAN.md, <MODULE>-DONE.json)*
- **Architecture:** <the architecture brief and build order, e.g. docs/architecture.md; module briefs go in
  <plans>/<MODULE>-BRIEF.md>
- **Contracts:** <path, e.g. docs/contracts.md; `/plan-project` creates it when the first shared invariant appears>
- **Evidence:** <where review files and evidence pages go, e.g. docs/evidence>
- **Graded examples:** <path, e.g. docs/orchestrate/graded-examples.md>
- **Scratch:** <throwaway work, e.g. tmp/ (gitignored)>
- **Status ledger:** <optional: a file recording what's implemented, correct and verified per capability, kept
  separate from plans; or "the plans">

## Checks and integration
- **Check:** <the command whose pass gates integration, e.g. `npm run check`, `./dev check`, `cargo test --workspace`>
- **Integrate:** main  *(read by the loop: `main` = rebase, check, push to the base branch without force;
  `pull-request` = push a branch and open a PR whose checks must pass)*
- **Branch:** main  *(read by the loop: the base branch)*
- **Remote:** origin  *(read by the loop)*
- **Merge:** <pull-request mode only: `owner` (streams wait for the owner to merge) or `lead` (the build-parallel lead
  merges once checks pass and any review passes)>
- **CI:** <does CI gate merges, or is the local check the gate?>

## Targets
Where behaviour is proved. Done-when items name one of these.

| Target | What it is | Run | Capture evidence | Edge conditions to cover |
|---|---|---|---|---|
| <web-chrome> | <Chrome, desktop viewport> | <`npm run dev`, open localhost:5173> | <Playwright screenshots and a trace per scenario> | <empty, loading, error, slow network, resize, back-navigation> |
| <ios-sim> | <iPhone simulator; function only, never speed> | <`xcodebuild …`> | <`xcrun simctl io booted screenshot`; `recordVideo` then extracted frames for motion> | <rotation, background and foreground, dynamic type, no network> |
| <cli> | <the built binary> | <`cargo run -- …`> | <the command transcript and exit code> | <bad arguments, piped stdin with no TTY, large input, Ctrl-C, exit codes> |

Label stand-ins as `proxy:<what it stands in for>`, e.g. Playwright WebKit with device emulation is
`proxy:mobile-safari`; the real thing is Safari in the iOS simulator.

## Exclusive resources
<Shared things only one run may use at a time, e.g. "simulator: booted iOS simulator runs", "port-5173: the dev
server", "gpu: timing runs", "staging-db". Wrap such runs in `agent_loop.py lock <name> -- <command>`. Or give each
stream its own (a port per worktree). Or "none".>

## Owner
- **Owner decides:** <e.g. changing purpose or the goal; spending; publishing, licensing or deploying; irreversible
  actions>. Everything else proceeds without asking.
- **Licences:** <e.g. no GPL or share-alike code or data>
- **Don't touch:** <other repositories or paths agents must not modify>

## Models
- **Codex generator:** gpt-6.1-sol medium  *(read by the loop)*
- **Codex sandbox:** workspace-write  *(read by the loop: or `danger-full-access`)*
- **Writable roots:** <comma-separated paths the build needs beyond the worktree, e.g. ~/.cargo, ~/.npm,
  ~/Library/Developer>  *(read by the loop)*
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
- **Cost.** Real targets from the purpose doc or the owner (Core Web Vitals, an SLO, a startup-time promise, a frame
  budget) are requirements and can be done-when items. Invented budgets aren't.
- **Worktrees.** Fan-out puts stream worktrees in `.claude/worktrees/`; make sure that path is gitignored and excluded
  from tools that scan the repository (test runners, linters, type checkers).
