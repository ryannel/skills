# Names the script uses that the glossary doesn't cover, 2026-11-12

The glossary, `skills/orchestration/GLOSSARY.md`, gives the agreed name for each thing in the orchestrate set,
and says the script's commands, files and messages use those names too. This review lists the names in the 2.1.0
script and skills that don't follow it. It was found by listing every result name the script prints, every field
in its results, and every word the glossary says to avoid, then reading each match in place.

Names below marked "proposed" need the owner's agreement before the glossary or the script uses them.

## Result names

Every command prints a result line, a JSON object whose `result` field says what happened, such as `MERGED`. The
lead decides what to do next from that word, and the `build` skill has a table of them. None of them is in the
glossary, and several say nothing about what happened.

| Now | What it means | Proposed | Why |
|---|---|---|---|
| `FLOOR` | The session can't go on. It covers two different things: the host failed (a non-zero exit, quota, sign-in, an outage, or a Codex goal that ended unexpectedly), or the script couldn't do one of its own steps (record a claim, unblock a milestone) | `HOST_FAILED` and `SCRIPT_FAILED` | The word means nothing to a reader, and one name for two causes led the lead to tell the owner "likely quota" for a merge that had finished after its turn ended (P3) |
| `PIN` | The session's model or effort differ from the ones it started with | `SETTINGS_CHANGED` | "Pin" is the code's word for the saved model and effort, not the owner's |
| `DESIGN_OWED` | The design review's result was not Design Approved | `DESIGN_CHANGES_REQUESTED` | The glossary already has this status, Design Changes Requested |
| `NOT_READY` | The builder kept saying it had finished when the script's checks disagreed | `CHECKS_FAILED` | Says what happened |
| `BUDGET` | The run used up the hours given with `--budget-hours` | `OUT_OF_HOURS` | Says which budget, and that it ran out |
| `RELEASED`, `UNBLOCKED`, `ADOPTED`, `MIGRATED`, `NOTHING`, `REFUSED` | Results of `lock`, `unblock`, `adopt` and `migrate` | Keep the names | Clear enough, but no skill explains them, so the `build` skill's table gains them |
| `STALLED`, `TAKEN`, `KEPT`, `PAUSED`, `WAITING`, `BLOCKED`, `MERGED`, `FAILED`, `PLANNED`, `REVIEWED`, `FINISHED`, `INVALID`, `READY_FOR_REVIEW`, `REVIEW_OWED` | Already explained in the `build` skill | Keep the names | The glossary gains a section listing every result name |

## Fields in the script's results

| Now | Proposed | Why |
|---|---|---|
| `landed` (20 places) | `merged` | The glossary says to avoid "land" and use Merge |
| `unlanded_plans` | `unmerged_plans` | Same |
| `unintegrated` | `unmerged` | The glossary says to avoid "integrate" |
| `loop`, `loops`, `loop_pct`, `loops_apart`, and the `loops` command | Keep for now | The glossary says to avoid "the loop" in prose. Renaming a command touches the lead's habits in every project, so this waits for the owner to choose a name for a running `run`, if they want one |
| `claim`, `claimed`, `unclaimed`, `claim_blocked`, `claimed_usage` | Keep for now | "Claim" is the record of a builder setting Ready for Review, and it is stored in projects' record files, so renaming it needs a `migrate` step. The glossary should gain an entry for it, since the skills already use "the claim" nine times |

## Words in the script's messages

The script's messages are read by the lead and the agents, so they should use the glossary's words too. These
are wording changes, not stored names, so they need no agreement and break nothing:

- "acceptance" in planner refusals, where the glossary's name is the record file or Done;
- "integrated tip" and "integrate it another way", where it means the main branch and merge;
- "blocking" for design review findings, where the glossary's name is Must Fix;
- "status lines", which the glossary lists under the status page's names to avoid;
- "Nothing from this turn landed", and the docstring "Lands plan files".

The migration code also uses `claimed`, `parked` and `attended`, but only to read old projects' files, which is
right.

## In the skills

The skills are nearly clean. "Lands" is used as a verb for the script's commits in `build/SKILL.md` and
`plan-module/references/done-when.md`, and the glossary itself says "the harness author" in the Background job
entry. Both are wording changes.

## How to keep this from coming back

A test in `tests/orchestration/` would fail when the script prints a result name that the glossary doesn't list,
or when a word the glossary says to avoid appears in the script's strings outside its migration tables. That
moves the rule from the authoring spec, which a writer has to remember, to a check that runs before every
commit. The spec already says the script uses the glossary's names; nothing checks it today.

## What a rename costs

The lead reads result names, so each rename also changes the `build` skill's results table. A lead running on an
older skill would meet a name it doesn't know, which is one more reason to start the lead in a new session after
an upgrade. The script stores the last result in each run's state file and reads `PIN` back from it, so the
script keeps a table of old result names and reads both, the way it already reads old milestone statuses. None
of the result or field renames touches a project's own files, so none needs `migrate`.
