Use the glossary's names everywhere, stop on a builder's first block, give a stopped builder a handoff file, and rewrite what the agents tell each other (orchestrate 2.0.0)

2.0.0 because stored names change: a project made with 1.x must run `migrate` once, and every other command
refuses it until then.

The names
- Statuses, fields, files, commands and prompts use the glossary's names: Not Started, In Progress, Ready for
  Review, Waiting (on_dependency, for_replan, for_diagnosis), Blocked (needs_human_feedback, needs_access,
  needs_hardware, needs_context, needs_dependency, too_many_failed_reviews) and Done.
- An item that needs someone has a `needs` field, {type, what}. What the owner says back is Human Feedback,
  recorded by `owner feedback --asked --said --item` under `human_feedback`. `owner reopen` replaces unpark,
  `merge` replaces land, and the reviewer agent is `orchestrate-reviewer`.
- `migrate` converts a 1.x project, and maps an old item that asked for approval or permission to Needs Access.
- A milestone stops only when it is finished or Blocked. Nobody is asked to confirm a step they already took.

Stopping and handing off
- A builder that ends with `BLOCKED <reason>` or `NEEDS_CONTEXT` ends the run on that first report, and the
  Codex goal is paused. A plain `BLOCKED:` keeps one more turn. Across the Thrum sessions this would have saved
  about 16 turns.
- A builder that stops short writes `<evidence>/<MODULE>/<milestone>-handoff.md`. The script merges it even
  though the work isn't merged, pushes the builder's branch (never forced, never the main branch), records both
  in the `blocked` field, and names them in the lead's next step, the planner's task and the next builder's
  prompt. The builder's last line is now one sentence.
- `run --message` lifts a Needs Context block.

The script states what it knows, and points to the rest
- A reviewer on a commit other than the claim is told which commit the builder claimed at, and why.
- Design re-reviews follow files `migrate` moved, list a changed DESIGN.md, say when they can't compare, and are
  refused when nothing changed after Design Changes Requested.
- An earlier round with no recorded findings names its review file.
- Planner tasks built from a block aren't cut short, and name the branch, commit and handoff. After a failed
  design review the task gives the number of Must Fix findings and leaves Suggestions to the planner.
- A failed claim check includes the end of its output and says it ran in the script's clean checkout.
- The builder's prompt says whether an approval prompt can appear in this session, and lists the project's
  exclusive resources and that `lock` waits its turn.
- Resumed turns restate the goal and point to ORCHESTRATE.md for the rules, rather than copying settings lines,
  which cut multi-line rules short. The line about items that need someone is left out after the lead writes.

Prompts and skills
- The build and plan templates carry only what the skills can't. The reviewer's note after a diagnosis states
  the scope without judging earlier reviewers, and the owner's words win over planner tasks in a design review.
- A planner ends with `PLANNED` alone; the result lists the files it changed under `files`.
- `check --items-only` runs a milestone's item checks under their locks without the project's test command, so a
  planner can try its checks while builders work.
- A Claude reviewer or planner is told its turn ending is read as its work ending.
- build: "What you pass on" is split by reader. A builder or planner gets facts the files don't hold, with their
  time and source; a reviewer gets only what the work is judged against.
- build-milestone: writing guidance, confirmed versus suspected, the commit each proof ran on, `lock` waits, long
  Codex jobs, and the handoff.
- plan-module: rewrite a changed item as if new, measure bounds, items are part of the design review, meet the
  size cap by moving text, and quote the owner only from the brief or marked words.
- review-milestone: a proof that scripts the builder's route is a Suggestion to shorten; the reply can be short.
- Every prompt is rendered from fixed data into tests/orchestration/prompts/, so a change shows as a diff.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
