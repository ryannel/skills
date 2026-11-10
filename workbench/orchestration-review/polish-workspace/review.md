# The orchestration rewrite of 10 November 2026: what was reviewed and what was done

This page records two independent reviews of the rewritten orchestration skills, what was changed because of
them, and what was left. The reviews themselves are [review-a.md](review-a.md) and [review-b.md](review-b.md).
The skills as they were before the rewrite are in the repository's history, at commit `6244f1b`.

## What was rewritten

The four existing skills (`build`, `plan-module`, `build-milestone`, `review-milestone`), their four reference
files, the three agent files and the authoring spec were rewritten in the vocabulary the owner agreed that day
([vocabulary.md](../vocabulary.md)), following the `skill-creator` skill. Two skills were added:
`interview-me` and `domain-language`. The script, `agent_loop.py`, was not changed by the rewrite. One setting was added to it afterwards, described at the end of this page.

## The two reviews

Each reviewer was a new session that was given the files and the standard to judge them by, and none of the
author's conclusions.

Review A compared the rewritten skills with the old ones and with the script. It looked for facts that were
lost or changed, for commands and field names that don't match the script, and for terms used before they are
defined.

Review B read the two new skills, the README sections about them and the six test cases. It looked for places
where a capable agent that reads only the skill would go wrong.

## What was changed after review A

Every finding was applied.

- The table of statuses mixed names the script stores with names it only prints. It now has a column for each.
- The agent files left out two of the fields a reviewer writes (`state` and `fails`).
- The `next` command was described as covering every case. It answers only after a failed review.
- The brief was not merged before `plan` was run, and `plan` refuses a repository with unmerged changes. The
  hand-over now merges first.
- Facts that the rewrite had dropped were restored: the default path of the graded examples, the groups that
  `ready` prints, the `DESIGN OK` and `DESIGN CHANGES` result words, the `release` verb, `accept --milestone
  design`, the `timeout` on a check, and the first-time rule for the record file.
- Command examples were missing `--worktree`.
- A heading in `plan-module` that the script's replan task cites by name had been renamed. It was renamed back.
- Three labels in the project settings had been renamed, against the rule that stored names stay. They were
  restored.
- The authoring spec had lost its rule about prose. It was restored.
- Terms used before their definition were given definitions.
- The script's own messages to agents still use the older words. Each of the three agent skills now has a short
  note that gives the older word beside the new one.

## What was changed after review B

- `interview-me` had no path for a small request, and its description loaded it for almost any change. It now
  starts with a table of three cases, and the description sends small changes to `build-milestone`.
- The files disagreed about where the glossary is. Every file now says `GLOSSARY.md` in the plans folder for an
  orchestrate project, found by its path, and the root of the repository anywhere else.
- The check for "finished" in `domain-language` could not pass. It now allows an avoided name in the glossary,
  in a record of the past, and in a sentence that gives a stored name.
- What the owner's approval means was stated two ways. Approval now changes no mark: a decision marked as the
  agent's stays the agent's.
- A change of mind updated the brief in one skill and not in two others. All three now update it, and a design
  reviewer reads the brief.
- "Wait" told an unattended agent to stop. It now says to keep using the agreed name and to report.
- The mark for an unagreed glossary entry was worded four ways. It has one form: `Proposed: by <kind of agent>,
  <date>. Not yet agreed by the owner.`
- Existing identifiers were not covered. The code keeps the word it already uses for a thing.
- Changing, removing and merging agreed entries are now the owner's decisions.
- The skill told the lead to start a subagent for a fresh reading of the brief. The lead in this set starts no
  helper agents, so the step was removed.
- The hand-over now says how to run the script, covers a folder that is not yet a git repository, names the two
  files in the `adopt` command so that nothing else is merged, says that `plan` waits, and says what the owner
  does next.
- The brief is saved as a draft from the first answer, so that a conversation spread over days keeps the
  owner's words. One brief per project, and a decision's number is never reused.
- A planner is told not to edit `BRIEF.md`, to take `Builders:`, `Integrate:` and `Owner decides` from it, and
  to write no `Assumption:` line for something the owner said they did not mind about.
- How the owner wants to work is now decided and stated by the lead, not asked.
- Claims about other libraries that the research notes did not support were corrected or removed, in the
  skills, the README and the two workbench READMEs.
- Repeated points and lines a capable reader doesn't need were cut.
- The test cases: four of the six would not have placed their input files, because of a nesting mistake in
  `case.yaml`. All six were written again. Checks were added for the facts the owner page hides, checks that
  could not be judged were reworded, `small-tool` and `clear-small-request` are marked as guard cases, and each
  `evals/` folder has a page on how to run a conversation with a second agent playing the owner.
- `domain-language` now says how the glossary reaches the main branch in an orchestrate project, and defines
  "planner" where it uses the word.

## The rename

The first of the two new skills was written as `capture-intent`, and both review files call it that. Review B
pointed out that the word "intent" appears nowhere in its body. The owner renamed it `interview-me` after the
reviews. addyosmani/agent-skills has a skill with the same name. Inside the orchestrate plugin the two don't
collide, because a plugin's skills carry the plugin's name. Installed as loose folders into one skills folder,
they would.

## What was left, and why

- "Brief" names two things in the set: the project brief, and the task given to a planner, which the script
  stores under `briefs`. The skills say "task" for the second. The stored name stays.
- An owner who agrees with everything. Each agreed recommendation becomes fixed for the planner. No library has
  a tested answer, and the brief's marks of whose decision each one was are the only guard.
- Two builders that each add a glossary entry may conflict when their branches are merged. `build-milestone`
  says to keep both entries. This has not been seen in a run.
- The table of older names in the README has no row for Blocked.

## Lines removed from the old skills

The `skill-creator` skill asks for this list, so that a line removed in error can be restored from commit `6244f1b`.

| Removed | From | Why |
|---|---|---|
| The limit of "near 400 words" for a skill | The authoring spec | The owner's rule is that shorter is not better. The lead's skill needs about 390 lines |
| `LOOP` as shorthand for the script's path | All four skills | A made-up label. Each skill now writes the command out once |
| "The loop", "the ladder", "parked", "claimed", "attended" as the names in prose | All four skills | Replaced by the agreed names. The stored words are given once, in code style |
| Bold labels at the start of bullets | All four skills and the spec | The owner's rule. They are now paragraphs or tables |
| Repeated statements of who may change a done-when file | `build-milestone`, `review-milestone` | Stated once, in `done-when.md`, and linked |
| Reminders to be thorough and to check the work | `build-milestone`, `review-milestone` | Current models do this unprompted, and the reminder causes extra testing |

Two ideas were drafted during this work and dropped before the reviews: a `Glossary:` line in the project
settings (every agent finds the file by its path instead), and the fresh reading of the brief by a subagent.

## Checks run

| Check | Result |
|---|---|
| `check_skill.py` on the six skills and the spec | `ok` for all seven |
| `claude plugin validate .` | Passed. It prints two notes about install lines in the root README, which were there before this work |
| `python3 -m unittest discover -s tests/orchestration` | 273 tests, all passing. One had failed on some runs: `test_decision_8_pause_stops_the_turn_running_in_the_app` set a stop flag half a second after the run started and expected a turn to be running by then. It now waits until the turn is running |

## Test runs

After the reviews, both new skills were run on their test cases, and three lines were added to them because of
what the runs showed. [results.md](results.md) is the record.

## Settings added afterwards

The owner asked whether a planner could run on a different model from the builders, and then asked for model
and effort for each kind of agent, with defaults that still work on a host that has no Claude models.

The project settings took one model for each host and one effort. They now also take a line for one kind of
agent (planner, builder, reviewer, design reviewer). With a host in front, the line gives a model, an effort or
both, and applies on that host only: `Claude planner: claude-fable-5-2 high`. With no host, it gives an effort
for that kind on every host: `Reviewer: high`. A model with no host is refused, because a model belongs to one
host. A flag on the command still wins, and a host with no line keeps its own model. `profile.md` has the order
the script looks them up in.

A first version, a `Claude planner model` line that carried a model only, was pushed in 1.6.0 and replaced in
1.6.1. Another session had drafted a third form in the `skill-factory` checkout (`Planner: claude
claude-fable-5-2 high`, one host for each kind). It was not used, because a line that fixes one host can't say
what a planner on any other host should run.

The change is in `agent_loop.py` (`role_lines`, `role_setting`, `resolve`), `profile.md`, the lead's skill and
the README, with a test (`test_profile_sets_model_and_effort_for_one_kind_of_agent`).
