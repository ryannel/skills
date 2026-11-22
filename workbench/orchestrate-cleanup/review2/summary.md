# Second review: the merged list

Seven reviewers each looked for one kind of mistake across every orchestrate file, including the text the script
sends agents. Their reports are beside this file, numbered by pattern. Roughly 950 lines would go in all, most of
it from text agents read on every turn.

## Script changes that unlock deletions

1. Name the brief, the module list and the plans folder in the planner and design-review prompts (`settings_paths()`
   has them). Removes hand-typed paths from stage 2, `project.md`, `design.md` and every planner `--task`. (2, 1, 4)
2. `plan` refuses unmerged plan files with `next: adopt`, as `run` does. Removes stage 2's adopt-first step. (1)
3. Fix the settings template: `Test command:` example and how a new project writes it, the full `Default host`
   order, and move the Test/Setup command and main-check lock advice from the planner files into the notes. (2, 4, 1)
4. `settings` prints default paths before ORCHESTRATE.md exists. Removes `docs/plans` from stage 1. (2)
5. Add `session_rule()` to review prompts, and make its Codex note read the sandbox setting. (4, 5)
6. Put the commit-subject convention (`ENGINE M3: ...`) in the build prompt with the real names. (1)
7. Build help numbers from their constants (escalation counts, watch timings, limits). (2)
8. Fix three messages that give the wrong way to change a setting (adopt refusal, new-project `next`,
   `hold_limit_note`), and the no-`Builders` refusal, which should give `settings --set Builders`. (2, 4)
9. Remove the script's "leave an item you can't meet as it is" copies, which contradict the builder skill's
   `BLOCKED: ... can't be met as written`. (6)

## Cuts in the script's agent text

10. CHANGES: keep what a lead must do or tell the user, about 35 lines for 366; everything before 2.6.0 becomes one
    line. (7)
11. `COMMAND_HELP`: take out internals (lock files, token accounting, reflog checks, rename tables), the duplicated
    "Routine steps" paragraph, aliases of retired names, and fix `review --help`'s broken sentence. About 150-200
    lines. (7)
12. Planner task texts the script writes repeat the task file printed below them: give facts only. `why` strings
    that restate the lead skill ("ask the user in chat, never decide for them", `WATCH_WHY`'s list of moves): cut.
    Build prompt: status rule said three or four times, NEEDS_CONTEXT twice, lock mechanics beside `lock --help`. (6, 7)

## Cuts in the skills

13. Builder (193 lines): "Without a lead", "Merging", "Shared resources", sandbox rules and the writing advice that
    `prompting-agents` covers. About 50 lines. (1, 3, 6)
14. Planner: the textbook test rows and defence-in-depth paragraph in `proofs.md`; `done-when.md`'s plan-file rules
    that `module.md` already gives; the "changing items resets the milestone" rule in seven places, kept once.
    About 60 lines. (3, 6)
15. Lead stages 1-3: stage 2's walk through the template, stage 1's interview script and preview bullets, stage 3 as
    steps around one outcome, the result contract in `SKILL.md`. About 60 lines. (4, 1, 6)
16. Reviewer: task files repeating the prompt they are inlined into. About 15 lines. (6)
17. README: values the script holds as constants, model ids as examples, the line count. (2, 5)

## False claims to fix

18. Docs say the user's pick of an option closes without a reviewer; `needs_review()` always reviews it. (5)
19. Stage 2 and README say no model line means "the host's own default"; the script passes its own defaults. (5)
20. README and top-level help say Codex lists visible threads under the project; it lists them under Recents. (5)
21. `review --help` leaves out its BLOCKED result; the glossary files it as a Blocked milestone, which it isn't. (5)
22. `plan --help` says one planner per repository; module planners run side by side. (5)
23. `run --help` says any design outcome but DESIGN OK stops the run; only with `--one-step`. (5)
24. Build prompt and builder skill promise a reviewer every time; a checks-only milestone goes straight to Done. (5)
25. Smaller: the glossary "isn't installed"; captures "merge"; "the script starts" a builder after KEEP; a resumed
    reviewer told it writes `status`; `proofs.md`'s leftover "so the lead can choose its hosts". (5)

## Decisions for the user

- Item 18: should the option pick be reviewed (fix the docs) or close without a reviewer (fix the code)?
- A wrong model or effort: should the lead rerun as set and mention it, asking only if it repeats, instead of asking
  every time? (4)
- The Codex note in the build prompt (`yield_time_ms`, `apply_patch`, `ps`): reviewer 7 says it teaches Codex what
  it knows; it came from a builder skill section the earlier rewrite moved. Keep only the browser line?
