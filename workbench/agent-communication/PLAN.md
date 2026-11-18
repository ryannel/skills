# Fixing how the orchestrate agents talk to each other

Three reviewers each read part of the 56 Thrum sessions (`thrum-prompts/`) against the prompting-agents skill.
Their reports are in `reviews/`. This plan combines them. Each fix names the problem it answers, written as
report and number: `build` 1, `review-and-plan` 4, `agent-written` 2, and so on.

The reviews agree on one thing. The wording of the templates cost the owner readability, but it rarely cost an
agent a turn. The turns were lost elsewhere:

- The script stated facts it hadn't checked, or left them out.
- There was nowhere to put a handoff.
- The script kept blocked sessions running.
- Rules told agents to hold back facts they needed.

So most of the fixes are structure in the script and changes in what each skill asks an agent to write.
Template wording comes third.

## 1. The script states only what it knows, and points to the rest

When the script can't establish a fact, it names the file or commit that holds it, rather than stating the fact
or leaving it out.

- **The reviewer's commit.** When the commit under review isn't the claim commit, tell the reviewer which commit
  the builder claimed at and why it is on another, as the script already tells the lead. (`review-and-plan` 1)
- **What changed since the last design review.**
  - Find the old done-when file under its old path, and compare `DESIGN.md` too.
  - When the comparison fails, say so and name the earlier review.
  - Refuse to start a re-review when nothing changed after a Design Changes Requested verdict.
  
  (`review-and-plan` 2)
- **Earlier rounds.** For a round with no recorded findings, name its review file instead of saying "no findings
  recorded". (`review-and-plan` 3)
- **Tasks the script writes for a planner.**
  - Don't cut the builder's note at 300 or 400 characters.
  - Add the branch and commit the evidence is on.
  - After a failed design review, give the number of Must Fix findings and say the Suggestions are the planner's
    call.
  
  (`review-and-plan` 4 and 7)
- **A claim check that failed.** Include the end of each failing command's output. Say it ran in a clean
  checkout without the builder's environment. End with "if the item can't be met as written, leave it and say
  so". (`build` 8)
- **Facts about the session the script already has.**
  - Whether this session is headless or visible, and so whether an approval prompt can appear.
  - The project's exclusive resources, and the fact that `lock` waits its turn.
  
  (`build` 2, 3, 9)

## 2. Stop a blocked session at once, and give its handoff a home

- **Stop on the first reported block.** When a builder ends with `BLOCKED <reason>` or `NEEDS_CONTEXT`, end the run and pause the Codex goal on that
  first report. A `BLOCKED:` with no reason keeps one more turn. Across 7 of 12 sessions this would have saved
  about 16 turns. (`build` 1, 5)
- **A handoff file at a fixed path.** A builder that stops without `DONE` writes
  `docs/evidence/<MODULE>/<milestone>-handoff.md`. It says:
  - what is finished, and on which branch and commit
  - what was tried and ruled out
  - what is confirmed and what is only suspected
  - what to do first
  
  The script pushes the builder's branch and merges the handoff file, even though the code isn't merged. It then
  names the file in the next builder's or planner's prompt. The last line becomes one sentence that points to the
  file. This replaces the 500-character `blocked` field as the carrier of detail, and it replaces most of what
  the lead now reconstructs in `--message`. (`agent-written` 1)
- **Restating the rules on a resumed turn.** Restate the goal and point to `ORCHESTRATE.md` for the rules,
  rather than copying settings lines. The copy dropped real rules, and the bug is now being fixed in the rename.
  Leave out the line about owner items when the lead has sent a message. (`build` 6)

## 3. Planners can test their checks without disturbing builders

`check` gets a mode that runs only the item checks a planner wrote, each under its own lock, waiting if a builder
holds it. Then the planner's prompt can say exactly that. (`review-and-plan` 5)

## 4. What each skill asks its agent to write

These are point-of-use changes, so each sits where the agent writes the text.

- **build (the lead), "What you pass on":** split by reader.
  - A reviewer gets only what the work is judged against.
  - A builder or planner gets what it can't find in the files: where unfinished work is, what was tried, what the
    owner said and when, and what the lead knows about the machine, given with its time and source. A guess is
    marked as a guess.
  - The owner's words go in quotation marks with their date, apart from the lead's context. Better, they go in a
    separate `--owner-words` argument that the script saves.
  - When the script's state was wrong, say so as a fact, with no rebuke.
  - Ask in the reader's terms. Don't ask a planner to set a field only the script writes.
  
  (`agent-written` 2, 3; `build` 2, 5, 7; `review-and-plan` 8)
- **build-milestone (the builder).** This is the only skill with no writing guidance today. Add:
  - The lead reads your last line, handoff and log entry and passes them to the owner, so write whole sentences.
    Name an item by its ID and a few words, and a module by its name.
  - Keep what you confirmed apart from what you suspect. Ask the lead for what you need; don't tell it what
    another builder should do.
  - `lock` waits its turn, so do other work meanwhile. This is the lead's own wording from Thrum, which worked
    first time.
  - Record the commit each proof ran on. If `merge` rebased onto changes that could affect an item, run its proof
    again.
  - In Codex, run long jobs with a timeout or in the background with their output in a file.
  
  (`agent-written` 4, 7; `build` 3, 5)
- **plan-module (the planner):**
  - Rewrite a changed item from what it claims, as if new, and move its history to `LOG.md`.
  - A bound nobody measured is a guess. Measure it while planning, or make measuring it the first item.
  - The done-when items are part of what a design review approves.
  - Meet the size cap by moving text to the design and the log, not by squeezing it into labels.
  - Quote the owner only from `BRIEF.md` or from marked owner's words. Otherwise say no words were passed on.
  
  (`agent-written` 3, 5; `review-and-plan` 9)
- **review-milestone (the reviewer):**
  - A proof that scripts how the builder must test is a Suggestion to shorten it.
  - The reply can be short, because the review file carries the findings.
  
  (`agent-written` 5, smaller findings)
- **The planner's last line.** It becomes `PLANNED` alone, and the script prints the changed files itself.
  (`agent-written` 6)

prompting-agents is named in plan-module and review-milestone already. Adding it to build-milestone, where the
builder writes its last line and handoff, closes the gap. No agent is told to load it on every turn.

## 5. The templates, rewritten from what only they can supply

The builder's template should carry five things:

- the milestone, its module and the done-when path
- the paths to the script and the skill for this installed version
- whether the session is headless or visible
- the exclusive resources
- the lead's note for this turn

Everything else is in the skill. The other changes:

- **The goal line** names the goal paragraph, and says the rest of the message is for this turn only. Codex made
  a lead's note into a permanent goal. (`build` 4)
- **Lines with no cost seen** come out, because they make every prompt harder for the owner to read:
  - the PLAN.md format rule, which the script enforces
  - the PATH note
  - the nested exception in the planner's last-line sentence
  
  (`review-and-plan` closing list)
- **The reviewer's prompt.**
  - The diagnosis note states the scope as a fact, without judging earlier reviewers.
  - Where the owner's words and the planner tasks disagree, the owner's words win.
  
  (`review-and-plan`, suspected risk)
- **Claude sessions.** A turn that ends while a background command is still running ends the session. Turn off
  background tasks for headless Claude, or say so in the prompt. Check what the CLI offers first.
  (`review-and-plan` 6)

## 6. Proving it

- Render every prompt from fixed test data into text files under `tests/orchestration/prompts/`, so each change
  shows as a readable diff that the owner can review.
- A cold-read test: a new agent given only a saved prompt says what its task is, what's done, what it may not do
  and how it finishes. This spends Claude plan quota, so ask the owner before each batch.

## Order

1. Wait for the rename to land and its tests to pass.
2. Do section 2's stop-on-first-block, then section 1. These are small changes in the script and save the most
   turns.
3. The handoff file and the session facts.
4. The skills (section 4) and the templates with their saved copies (sections 5 and 6), together, so the
   templates can shrink as the skills take on the rules.
5. The planner's check mode (section 3), and the Claude background-task question.
6. Run the cold-read test once.

## Keep as they are

- The fixed last-line forms that agents end on.
- Recording what the owner says in the script's record.
- The rule that a condition the work must survive is not a condition for checking it.
- The design review's table of earlier findings.
- The core of the milestone review prompt.
- The lead's evidence-carrying tasks, such as COOKED-DRAW on 9 November and PLATFORM-RUNTIME-MAC at 12:41 on
  11 November, which are the model for section 4.
