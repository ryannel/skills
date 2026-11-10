# Writing style: the rules at work

The main file lists the writing rules. This file shows them at work, and adds two rules that matter in longer
text.

## Examples for the rules

**Name who does each thing.**

| Unclear | Clear |
|---|---|
| "Each module is split into milestones." | "The planner splits each module into milestones." |
| "The branch should be rebased before review." | "Rebase the branch before you ask for review." |
| "Approval is required for deploys." | "Ask Priya before you deploy. She owns the release calendar." |

**Explain a term before you use it, then keep the word.** A reader can't ask what "the ledger" is. Say it once:
"The ledger is the file `state/ledger.json`, which lists every job and its status." After that, always call it
the ledger. If the next paragraph says "the state file", the reader has to work out whether that is a second file.

**Don't make up a label.** While you work you invent short names: "the fallback path", "phase two", "the big
refactor". The reader was not there. Write the plain description: "the code that runs when the cache is empty".

**Tell things in the order they happen, and name who does each step.**

1. The lead runs `plan`.
2. The planner writes the design to `docs/design.md`.
3. The reviewer reads the design and records a verdict in `review.json`.

**Be concrete.** "The test suite is slow" gives the reader nothing to act on. "The suite takes 11 minutes, and
the 63 resolver tests take 9 of them" tells the reader where to look.

**Write whole sentences.** "Auth: review. Spec: `docs/auth.md`. No style." is short, and the reader must guess
how the three parts connect.

**A script is not an agent.** Write "run `make check`". Don't write "ask the checker to verify".

## Two more rules for longer text

**Compare with the ordinary case.** A new fact is easiest to take in next to the one the reader already knows:
"Normally a subagent starts with your instruction files. The `Explore` agent starts without them, so put
everything it needs in the brief."

**Use one example, then return to the plain statement.** Three similar examples make the reader copy whatever
the three happen to share.

## Before and after

A brief for a subagent:

> Before: "Investigate the flaky tests. IMPORTANT: be thorough and check all possible causes. First read the CI
> config, then read the test files, then look at recent commits, then form hypotheses. Report back with a
> detailed analysis including root cause, contributing factors, and recommendations."
>
> After: "Three tests in `tests/sync/` fail about one run in five on CI and never on a laptop. The failing runs
> are linked in `notes/flaky.md`. Find out why, and fix it if the fix stays inside `tests/sync/` and
> `src/sync/`. A fix counts when the three tests pass 20 times in a row with `make test-sync-loop`. If the cause
> is outside those folders, stop and tell me what you found. Say which parts you confirmed by running something
> and which you only suspect."

The capitals and the reading order went. The facts the subagent could not have found came in: how often the
tests fail, where the evidence is, how far the subagent may go, and what counts as fixed.

A line in an instruction file:

> Before: "NEVER touch the generated code!!!"
>
> After: "`src/gen/` is written by `make codegen` from `api/schema.yaml`. To change it, edit the schema and run
> `make codegen`."

The line now says what to do, and the reason is in it.

## Without the jokes

Keep the clear order, the named actors, the plain words and the concrete numbers. Leave out asides, playful
examples and a clever last line. End on the last useful fact.
