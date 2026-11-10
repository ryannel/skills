# Iteration 2: end-to-end scenarios

Written on 10 November 2026 before any run started. Each scenario takes a fictitious project from an empty
repository to built and accepted, through the loop, with real Claude and Codex sessions. A Claude Opus 5.5 subagent
plays the engineer's agent (the lead) and stands in for the owner where the process needs one.

Suite under test: the working tree on branch `orchestrate-polish`, on top of orchestrate 1.5.4 (`f3cc653`).
All loop sessions run headless (`ORCHESTRATE_HEADLESS=1`), so nothing opens in the owner's desktop apps. The visible
app path is therefore not covered here; the Thrum project uses it daily.

| Scenario | Kind | Planner | Builders | Reviewers | Also tried |
|---|---|---|---|---|---|
| `s1-slug-claude` | measurable, one module | the lead itself, with `plan-module` | 1 Claude | Claude | pause mid-build and resume; a second lead on the same module |
| `s2-slug-codex` | the same ask | `LOOP plan` on Codex | 1 Codex | Codex | checking in as an owner would (`status`, `ready`, `quota`) |
| `s3-ledger-cross` | measurable, two modules, one needs the other | `LOOP plan` on Claude | 1 Claude and 1 Codex at once | the other host from the builder | two builders at once; the daily report |
| `s4-icons-taste` | taste-led | `LOOP plan` on Claude | 1 Claude | Codex | owner picks, attended items, the owner's commands |
| `s5-game-mixed` | a game: measurable and taste-led | `LOOP plan` on Codex | 1 Codex | Claude | first-time setup from the README alone |

## The asks, as typed

`slugline` (s1 and s2):

> need a tiny python lib + cli called slugline. turns titles into url slugs: transliterate accents (é->e, ß->ss),
> lowercase, hyphens, max length (default 60) without cutting a word in half, and when the slug's already in a given
> file of existing slugs it adds -2, -3 etc. cli reads titles from args or stdin one per line. stdlib only, tests with
> unittest. keep it small, two milestones is plenty

`ledgerlite` (s3):

> want a small plain-text accounting thing in python, ledgerlite. two parts: a core lib that parses a journal file
> (date, payee, postings with account + amount + currency, one posting per txn may leave the amount blank and gets
> the balance) and refuses transactions that don't balance per currency, and a report cli on top of it: `balance`
> (totals per account, tree-indented) and `register <account>` with a running total, both with --json. stdlib only.
> core and report as separate modules so two agents can work at once. small, one or two milestones each

`saltmarsh` icons (s4):

> we're building a tide-times app (saltmarsh) and need a small weather icon set: sun, cloud, rain, wind, fog, high
> tide, low tide, moon. svg, 24px grid, stroke only using currentColor, under 1.5kb each. they should look
> hand-inked, a bit wobbly like a field notebook sketch, not the usual geometric icon-pack look. plus a preview html
> page showing them all at 24 and 48px on light and dark. plan it so agents can build it, keep it to two or three
> milestones

`lighthouse` (s5):

> make a little browser game, lighthouse. single index.html, no dependencies, canvas. you swing the lighthouse beam
> with the mouse (or arrow keys) to light up boats so they don't hit the rocks; 60 second rounds, score, restart. it
> needs to feel good to play, the beam should have weight, a saved boat should feel satisfying, and it has to hold
> 60fps with 30 boats on screen. two or three milestones

## Statements

For every scenario:

1. Every planned milestone ends accepted in the loop's record, or the run stops at something the docs say is the
   owner's.
2. Used directly, the built product does what the ask says (the lead's own check, and a spot check afterwards).
3. Every loop stop the lead met carried a `next` it could follow.
4. The lead never had to read `agent_loop.py` to get past something.
5. Getting from the README to the first builder running took no step the docs don't give.
6. Every headless claim and review result carried `usage`.
7. No session changed a file its role doesn't own without the loop saying so.

Per scenario:

- **s1:** `pause` stops the builder cleanly, `run` resumes the same session, and the milestone is still accepted. A
  second `run` on the same module is refused rather than duplicating work.
- **s2:** the readouts an owner would check (`status`, `ready`, `quota`) can be understood without the docs open.
- **s3:** the two builders overlap in time and neither's integration breaks the other's. `report` doesn't build ahead
  of the `core` work it needs. Each review runs on the other host from its builder.
- **s4:** the plan opens with the owner picking a direction from variants. Items an agent can't judge stop for the
  owner. The pick is kept where the profile says, and the reviewer compares against it.
- **s5:** the frame-rate requirement is proved by a command. Feel is sent to the owner. The game runs from the single
  file.

## Measured

Wall-clock per phase (plan, design review, each build, each review), tokens per claim and review from `usage`, loop
commands the lead ran, reviews and fails per milestone, and how many times the lead had to decide as the owner.
