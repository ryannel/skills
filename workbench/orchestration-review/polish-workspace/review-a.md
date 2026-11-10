# Review A: the orchestration rewrite of 10 November 2026

## Verdict

The rewrite kept almost every rule, and it invented no command, flag, result word or field: every one the new files
name exists in `agent_loop.py`. All 46 relative links and anchors resolve, and `check_skill.py` passes on all six skill
folders and the spec. A builder that adds to `GLOSSARY.md` in the plans folder and merges with `land` is not rejected
by `run`, and a planner that writes `BRIEF.md` or `GLOSSARY.md` there trips nothing in `plan`. Five things should be
fixed before agents act on these files: (1) `done-when.md` no longer lists the six legal values of `state`, and its
new table mixes them with printed words that are not legal values; (2) the three reviewer agent files now say a
reviewer changes only `verdict` and `review`, which contradicts `review-milestone` and the script, both of which
require `state` and `fails`; (3) `build/SKILL.md` describes the `next` command as working for any milestone state,
when it only handles a failed review; (4) `build/SKILL.md` tells the lead to write or update the brief and then run
`plan`, but `plan` refuses a worktree with uncommitted files; (5) `review-milestone` lost the default path of the
project's graded examples. The rest are small losses of detail, stored names not given where the reader meets them,
and a few terms used before they are defined.

How I checked: I read each old file beside its new one, line by line, and read these parts of the script: the
constants and prompt templates (lines 301-364), `profile` (373-464), `validate`, `definitions`, `delta_problems`
(759-992), `adopt`/`project`/`next_step` (997-1188), `next_for` and the drift functions (1269-1616), `land`,
`loop_write`, `claim_problems` (2207-2424), `binding` (3264-3290), `cmd_run` (3947-4264), `review_once` (4322-4590),
`cmd_plan` (4641-4863), `cmd_ready`/`cmd_status`/`cmd_next` (4880-5007), `cmd_check`/`cmd_land` (5090-5149),
`adoptable`/`cmd_adopt` (5506-5814), `cmd_owner` and the parser (5852-6102). I ran `--help` for the script and every
subcommand, and nothing else. "Confirmed" below means I read the lines cited. "Suspect" means I inferred it.

Paths: `old/` is `workbench/orchestration-review/polish-workspace/old/`; new files are under `skills/orchestration/`;
"script" is `skills/orchestration/build/scripts/agent_loop.py`.

---

## 1. Facts lost, or changed in meaning

Most serious first.

**1.1 The legal values of `state` are gone, and the table that replaced them mixes stored values with printed words.**
Old `old/plan-module/references/done-when.md:97` said "`state` is `open`, `in_progress`, `claimed`, `done`, `blocked`
or `parked`". New `plan-module/references/done-when.md:109` says "`state` is the milestone's status, as the next
section lists", and that section (lines 118-133) has a column "Stored or printed as" that holds `waiting`, `taken` and
`replan_owed` beside the real values. Those three are never stored: the script accepts only the six
(`STATES`, script:310; rejected at script:778-779). A planner that writes `"state": "waiting"` or
`"state": "replan_owed"` gets its whole plan refused as `INVALID`. Confirmed.

**1.2 The reviewer agent files now forbid two fields the reviewer must set.**
Old `old/build/agents/claude/orchestrate-evaluator.md:8-9` and `old/build/agents/codex/orchestrate-evaluator.toml:6`
said "change only the review file and the verdict fields of the done-when file". New
`build/agents/claude/orchestrate-evaluator.md:9-10` and `build/agents/codex/orchestrate-evaluator.toml:7` say "Change
only the review file, its folder of screenshots, and the `verdict` and `review` fields". The script requires the
reviewer to set the milestone's `state` and `fails` as well (`REVIEWER_FIELDS`, script:929; enforced at
script:983-991, 4477-4480), and `review-milestone/SKILL.md:72-74` tells it to. A reviewer that obeys the agent file
leaves `state` at `claimed`, and the `review` command returns `INVALID` and saves nothing. The old wording had the
same gap in looser words; the rewrite made it exact and exclusive. Under the script the prompt also says "set the
verdict fields, state and fails" (script:343-344, 3273), which lowers the risk there; a Codex chat that starts the
reviewer without the script has only the agent file and the skill. Confirmed.

**1.3 The `next` command is described as general, and it is not.**
Old `old/build/SKILL.md:157-159` put it under a failed review: "`LOOP next …` gives the same, with the message to
send". New `build/SKILL.md:189-190` lists it under "Starting agents" as "prints the command for a milestone's present
state, with the message to send". The command only works out the escalation step from `fails` and `replans`
(script:4989-5007). For a milestone with no failed review it prints `"action": "none"`, no `next`, and a `message`
that begins "The reviewer failed M2" (script:5004, 360-364). A lead that runs it on a Blocked or Waiting milestone
gets a failed-review message to send to a builder. The output field is also `action`, not `ladder`. Confirmed.

**1.4 The default path of the project's graded examples is gone.**
Old `old/review-milestone/SKILL.md:13-14`: "the file the profile's `Graded examples` line names (by default
`<evidence>/graded-examples.md`, which a new project won't have yet)". New `review-milestone/SKILL.md:19-20`: "in the
file named on the `Graded examples:` line". The script still defaults to `<evidence>/graded-examples.md`
(script:452) and `report` counts that file (script:5352-5354). In a project whose settings have no such line, a
reviewer does not look for the file, and at `review-milestone/SKILL.md:136` has nowhere to add an overturned result.
Confirmed.

**1.5 The list of what `ready` prints is gone.**
Old `old/build/SKILL.md:68-72` named every group: ready, waiting (`needs`), owed review, owed a re-plan
(`replan_owed`, with the planner's command under its own `next`), owed a design review, blocked, parked, taken,
invalid, and finished modules. New `build/SKILL.md:112-115` says only "lists each module's next milestone with its
status". The JSON keys are `ready`, `waiting`, `review_owed`, `replan_owed`, `design_owed`, `blocked`, `parked`,
`taken`, `finished`, `invalid` (script:4883-4884). Five of those (`ready`, `review_owed`, `design_owed`, `finished`,
`invalid`) are in no table in the new files. A lead has to guess that `review_owed` is Ready for Review and that
`ready` is Not Started with nothing in the way. Confirmed.

**1.6 `build/SKILL.md` no longer gives the printed design results.**
Old `old/build/SKILL.md:146, 166-167, 174` used `DESIGN OK` and `DESIGN CHANGES`. New `build/SKILL.md:122, 222,
271-275` says only Design Approved and Design Changes Requested, and line 251 says a review prints `REVIEWED` "with
the result" where the field is `verdict` (script:4587). The lead meets `"verdict": "DESIGN CHANGES"` in the result and
under `design_review` (script:4007-4013). The mapping is only in `done-when.md:135-136`. A lead can infer it, so this
is small, but it breaks the rule that a stored name is given where the reader meets it. Confirmed.

**1.7 "Definitions" became "an item's wording", which is narrower than what the script checks.**
Old `old/build-milestone/SKILL.md:20-21`: "the loop rejects a claim whose definitions changed". New
`build-milestone/SKILL.md:33-34`: "The script rejects a builder's work when an item's wording has changed". Old
`old/review-milestone/SKILL.md:69-70`: "if you change the definitions"; new `review-milestone/SKILL.md:83`: "If you
change an item's wording". The script hashes `statement`, `check`, `inspect`, `ask`, `target`, `lock`, `attended`,
and the milestone's `bar` and `needs` (script:313, 824-828), and rejects a change to any field that is not the
agent's own (script:968-980). An agent could read "wording" as the statement only and repair a broken `check` command
or a `target`. Both files also say "three fields and no others" or "only those two files", so the risk is low.
Confirmed.

**1.8 The planner's row in the who-changes-what table got narrower.**
Old `old/plan-module/references/done-when.md:136`: "the definitions | Planner | A re-plan". New
`plan-module/references/done-when.md:174`: "The planner's fields | Planner | A rewrite of a milestone that is
Awaiting Replan". A planner also changes those fields when the owner changes what is wanted
(`plan-module/SKILL.md:198-203`) and when a design review asks for changes. Read alone, the table now says a planner
may change them only after four failed reviews. Confirmed by reading the files.

**1.9 Smaller details dropped from `build/SKILL.md`.** All confirmed by reading; each is low.

| Old line | What it said | New | What goes wrong |
|---|---|---|---|
| `old/build/SKILL.md:41` | run a blocked command "outside the sandbox, or with escalation" | `build/SKILL.md:76-77`, "outside the sandbox" only | A Codex lead may not think to ask for escalation, which the script's own `next` suggests (script:6123). |
| `old/build/SKILL.md:132-133`, `old/…/profile.md:27` | a design review goes to the other host "when a loop planner turn wrote it" | `build/SKILL.md:198`, `profile.md:68-69`, unconditional | When no `plan` command wrote the plan, the script falls back to the builder's or default host (script:3194-3203); the lead expects the other host. |
| `old/build/SKILL.md:136-137` | "a milestone review takes the builder's host from the claim and picks the review host from that" | absent | The lead may add `--host` by hand to a milestone review that would have chosen correctly. |
| `old/build/SKILL.md:148` | `next.owner_answers` covers each attended item "that hasn't passed" | `build/SKILL.md:240-241`, "each such item" | Minor: the lead may expect a question for items already settled. |
| `old/build/SKILL.md:148` | the script records `state: blocked` | `build/SKILL.md:225` | The stored name is not given where the lead meets it. |
| `old/build/SKILL.md:214-216` | what `report --write` writes (what closed, verdicts, assumptions, what waits, attended items, decisions, tokens) | `build/SKILL.md:318-319`, "writes the factual half" | The lead can't tell which parts of the list at 321-334 it still has to write. |
| `old/build/SKILL.md:115` | a `fail` from `check`: "read the output" | `build/SKILL.md:186` | Minor. |
| `old/build/SKILL.md:9` | "Any agent host that can run shell commands can do this job" | only in the description | Minor. |

**1.10 Smaller details dropped elsewhere.** All confirmed by reading; each is low.

- `old/plan-module/SKILL.md:130-131`: the design review is recorded "so the loop won't build the module until a design
  review passes". New `plan-module/SKILL.md:165-169` drops the consequence. It is still in
  `review-milestone/SKILL.md:131` and `build/SKILL.md:277-278`, which a planner does not read.
- `old/review-milestone/SKILL.md:57-58`: the link to the who-changes-what table. `old/…:64-65`: the script "sets failed
  items back to `open`". New `review-milestone/SKILL.md:72-74, 82` has neither. A reviewer that resets `status` itself
  is rejected (script:976-980). The fact is still in `done-when.md:172`.
- `old/review-milestone/SKILL.md:47`: "Don't guess." `old/…:100`: "the milestone reviews catch what's left". Absent.
- `old/plan-module/references/proofs.md:105-106`: "every round re-reads the captures, so stop at the first round that
  finds nothing". New `proofs.md:120` keeps the rule and drops the reason.
- `old/plan-module/references/profile.md:13, 37, 43, 50`: the template's title, the heading "Starting from a clean
  clone", the Targets column `Capture`, and the label `Large captures`. New `profile.md:14, 39, 45, 52` renames them to
  "Project settings", "clean copy", `Record` and `Large recordings`. These are names stored in existing
  `ORCHESTRATE.md` files, so the rule was to keep them. The script reads none of the four (it reads the `## Targets`
  heading and each row's first cell, script:3377-3383), and no skill names them, so nothing breaks.

**1.11 The authoring spec.** Confirmed by reading.

- `old/orchestration-skill.SKILL.md:27-30`, the plain-prose rule (write like Randall Munroe, lists only for real
  checklists, "avoid bold-led bullets, chains of semicolons") is absent from `.agents/skills/orchestration-skill/SKILL.md`.
  The new `plan-module/SKILL.md:88-159` is fourteen bold-led paragraphs, which the old rule forbade. If the removal
  was meant, it was not on the list of deliberate removals.
- `old/…:15-16`, what "written to `prompting-agents`" means (outcome, done-when, constraints and pointers; no emphasis
  or pressure lines; descriptions that say when to use and when not, and don't overlap a sibling's) is now one clause
  at new line 11-12.
- `old/…:31`, the four parts of a skill ("outcome, done-when, method, permissions") went with the 400-word limit.

---

## 2. Commands, flags, result words and fields that do not match the script

Every command, flag, result word and field in the new files exists. These descriptions are wrong or incomplete.

**Introduced today**

- `build/SKILL.md:15-16`: "Each command starts an agent or verifies some work, saves the records, and prints one line
  of JSON … Its `next` field holds the exact command to run next". Only `run`, `review`, `plan` and a few others print
  one line. `status` prints plain text (script:4916-4986), `ready` prints indented JSON over many lines (script:4913),
  `check`, `report`, `cost` and `quota` print text unless given `--json` (script:5114), and `next` is present only on
  results that stop short (the script's docstring, about line 95). The old text (`old/build/SKILL.md:103-106`)
  said this of `run` only. Confirmed.
- `build/SKILL.md:189-190`, the `next` command: see 1.3. Confirmed.
- `build/agents/claude/orchestrate-evaluator.md:9-10` and `build/agents/codex/orchestrate-evaluator.toml:7`: see 1.2.
  Confirmed.
- `plan-module/references/done-when.md:118-133`: the status table. `waiting`, `taken` and `replan_owed` are printed
  statuses, not values of `state`; `ready`, `review_owed`, `design_owed`, `finished` and `invalid` are printed and
  missing (script:1135-1188). Line 133 says Done is "accepted" in the record file; the key is `accepted`
  (script:1052-1054) and should be in code style. Design Ready for Review is printed as `design_owed` /
  `DESIGN_OWED`, which line 135-136 does not give. Confirmed.
- The script's task for a planner cites a heading that no longer exists: script:1298-1299 says `(plan-module, "When a
  milestone fails review four times")`. The heading is now "When a milestone has failed four reviews"
  (`plan-module/SKILL.md:178`). The script was not changed, so the rename left its pointer stale. Confirmed.

**Already wrong before today, and carried over.** Not caused by the rewrite; listed because an agent still acts on them.

- `build/SKILL.md:292`: `owner <verb> --module <M> --milestone <id> --text "..."` omits `--worktree`, which the
  parser requires (script:6059-6060). The command fails as written. Confirmed with `owner --help`.
- `build/SKILL.md:304`: `plan --task "<their words>"` omits the required `--worktree` (script:6025). Confirmed.
- `build/SKILL.md:224`: for `TAKEN`, "`holder` says which process and worktree". `holder` is present only when
  another `run` in the same repository holds the module (script:3959-3961). When another lead holds the milestone,
  the result has `by` and no `holder` (script:4026). Confirmed.
- `build/SKILL.md:185`: `check` prints `pass`, `fail` or `error`. It also prints `timeout`, and "no check" for an item
  with none (script:5104, 5111). Confirmed.
- `build/SKILL.md:295-301`: the `owner` verbs. The script also has `release` (drops another lead's hold; the `TAKEN`
  result's `next.owner` names it, script:1517-1518) and accepts `owner accept --milestone design` (script:5884-5890).
  Neither is described. Confirmed.
- `plan-module/references/done-when.md:154-155`: "A module with no record file yet is taken as it stands the first
  time the script reads it." That is true only in a repository that has never had a record file. Otherwise the
  module is new, nothing in it is Done, and its design needs a review (script:997-1022, 1094-1097). The README has it
  right at lines 634-638. Confirmed.
- `build-milestone/SKILL.md:36`: builders are not told that `land` prints `LANDED` or `FAILED` (script:5148). Confirmed.

---

## 3. `GLOSSARY.md` and `BRIEF.md` in the plans folder

**A builder that edits or adds `GLOSSARY.md` and merges with `land`: not rejected.** Confirmed by reading.

- `land` has no rule about paths. It needs a clean working copy, then rebases, runs the test command and merges
  (script:5138-5149, 2207-2250).
- After each builder turn, `run` checks three things: the module's own done-when file is valid (script:4164-4166);
  only the builder's fields changed in that one file (script:4171, 932-992); and the claim holds (script:2387-2424):
  the state, evidence on every item, no uncommitted or untracked files, `HEAD` on the main branch, no commit that
  touched a `*-ACCEPTED.json` file (script:2304-2313), the items still the approved ones, and the checks passing in a
  clean copy. None of these looks at any other file in the plans folder.
- The design's hash covers only `<MODULE>.md` (script:1085), so a glossary edit does not send the design back for
  review.

Side effects worth knowing:

- The glossary edit must be committed. `land` and the claim both refuse a working copy with uncommitted or untracked
  files (script:5144-5146, 2397-2399). `build-milestone/SKILL.md:102` says "in the same commit", which covers it.
  Confirmed.
- A commit that touches only files in the plans folder does not count as progress for the `BUDGET` stop
  (script:689-701). Harmless when the entry goes in with code. Confirmed.
- Any file under the plans folder that is uncommitted or not yet merged is reported as `unlanded_plans`, with `next`
  set to `adopt` (script:1562-1571, 1603-1616). So a glossary edit a builder left unmerged shows up to the lead as a
  plan file to adopt. Confirmed.
- Two builders that each append an entry at the end of the same file will conflict when the second one rebases.
  `land` then aborts the rebase and prints `FAILED` (script:2219-2222), and the builder has to resolve it by hand.
  Suspect: I read the code and did not run it. Nothing in `build-milestone` warns of it.
- A reviewer that edits the glossary is rejected, because a reviewer may change only its review, its folder and the
  done-when file (script:4445-4448). `review-milestone/SKILL.md:23-25` asks it only to read the glossary, so the
  files agree. Confirmed.
- `build-milestone/SKILL.md:14, 102-103` does not say what to do when the settings have no `Glossary:` line.
  `domain-language/SKILL.md:19-21` says to create `GLOSSARY.md` in the plans folder. The script allows that too.

**A planner that writes `BRIEF.md` or `GLOSSARY.md` in the plans folder: nothing in `plan` trips.** Confirmed.

- `plan` needs the last line `PLANNED: <files>`, each named file present and changed, and a design beside each
  changed done-when file (script:4641-4663). It rejects only a changed `*-ACCEPTED.json`, an invalid done-when file,
  and a done-when file that marks something passed (script:4773-4787). Then it commits everything the planner left,
  with `git add -A`, and merges it (script:4797-4805).
- The settings parser reads a fixed list of labels and ignores the rest (script:373-376, 406-418), so the `Purpose:`
  and `Glossary:` lines, and the value `none`, never make `profile` fail. A planner that adds a `Glossary:` line to an
  existing `ORCHESTRATE.md` has that change merged with the plan.

**What does trip, on the lead's side.** Confirmed.

- `plan` refuses to start when the working copy has any uncommitted or untracked file: `INVALID`, "the planner needs a
  clean worktree", with no `next` (script:4698-4700). `build/SKILL.md:40-47` says to make sure there is a brief and
  "Then run `plan`", and for later requests "update the brief, and then run `plan`", with no step that merges the
  brief. `capture-intent/SKILL.md:187-196` and `profile.md:79-80` have the step. A lead that follows `build` alone
  hits the refusal.
- In an existing project, a brief committed by hand and not merged also stops `plan`: `INVALID`, "this worktree has N
  commits the integrated tip doesn't", with `adopt` as the alternative (script:4703-4721).
- `adopt` takes any file under the plans folder except a record file (script:5506-5519), so `profile.md:79-80` is
  right. It needs an `ORCHESTRATE.md` with `Check` and `Integrate` (script:5671), so in a new project the brief is
  committed with git, as `capture-intent/SKILL.md:193` says. It refuses to run inside a session the script started
  (script:5672-5674), so a builder or planner can't use it.
- Suspect: a module named `BRIEF`, `GLOSSARY` or `ARCHITECTURE` would have its design at the same path as that file,
  because the design is `<MODULE>.md` (script:1085). On macOS a module named `Glossary` collides too. Nothing checks
  for it.

---

## 4. Old terms, terms used before they are defined, and disagreements

**Stored or printed names not given where the reader meets them**

- The script's own messages to agents still use the old words, and no SKILL.md says what they mean. A builder's
  prompt says "the loop stops the run", "the profile's Check", "integrated" (script:324-339). The message after a
  failed review says "Every blocking finding counts … advisory ones are your call" (script:360-364), while the review
  it points to marks findings Must Fix or Suggestion. `build-milestone/SKILL.md` never says that "the loop" is the
  script, "the profile" is the project settings, or that blocking and advisory are Must Fix and Suggestion. Only the
  README does (lines 24-25), and each SKILL.md is read without it. Confirmed.
- `review-milestone/SKILL.md:56`: "the project's references where it keeps any". The settings line is `Anchors:`
  (`profile.md:19`, `proofs.md:110`). The old text said "the profile's anchors". A reviewer reading the settings
  may not connect the two. Confirmed.
- `review-milestone/SKILL.md:104-105`: a design reviewer is given "the owner's request". The script's prompt tells it
  to read the planners' tasks under `briefs` in the record file (script:4396-4399). The field `briefs` is not
  mentioned, and it now sits beside "project brief", which means a different file. Confirmed.
- `build/SKILL.md:122, 271-275`: `DESIGN OK` and `DESIGN CHANGES`, see 1.6.
- `build/SKILL.md:225`: `state: blocked`, see 1.9.

**Old terms in prose**

- `plan-module/references/done-when.md:105`: "`status` is the builder's claim for one item".
- `plan-module/references/done-when.md:133`: "accepted", in quotation marks and not code style.
- `plan-module/SKILL.md:154` and `proofs.md:42`: "the project's purpose", where the vocabulary says "project brief"
  (was "purpose doc").
- `proofs.md:117`: "a taste item", where the section is now "Subjective work".
- `review-milestone/SKILL.md:129`: `DESIGN CHANGES: <n> blocking findings` keeps "blocking" inside the literal last
  line. The script matches only `DESIGN CHANGES` (script:4319), so the word could change, but the line is in code
  style and the sentence after it maps it to Must Fix. Acceptable.

**Terms used before or without a definition**

- `build/SKILL.md`: line 18 uses "milestone", "module list" and "Done" before the section at 21-27 defines them.
  "host" (72, 94) is never defined. "Design Approved" (122), "Must Fix" (272), "Automated Checks" (184), "Reviewer
  Inspection" and "quality bar" (325) are used and never defined. The milestone statuses in the table at 217-231 are
  named and not defined, though the link at 29-32 covers them.
- `plan-module/SKILL.md`: lines 8-9 use "builder", "milestone" and "reviewer" before 31-33. "lead" (169, 176, 200) and
  "Must Fix" (114) are never defined. "Not Started" (189) is used where the planner needs the stored value `open`.
  "Awaiting Replan" (180) and "Too Many Failed Reviews" (194) are used with no stored name.
- `build-milestone/SKILL.md`: "lead" (51, 66), "host" (69), "planner" and "reviewer" (31) are never defined.
- `review-milestone/SKILL.md`: "Suggestion" is used at 24-25 and defined at 40. "Could Not Judge" is used at 46 and
  mapped to `cant_tell` at 50. "module list" (105) is never defined and its file name, `ARCHITECTURE.md`, is not
  given, so a design reviewer is not told where to find the module's entry. "module", "builder" and "planner" are
  never defined.

**Disagreements**

- The reviewer agent files against `review-milestone/SKILL.md:72-74` and the script, on which fields a reviewer
  changes. See 1.2.
- `plan-module/references/profile.md:72-74` tells a planner to write a short `BRIEF.md` when there is none.
  `plan-module/SKILL.md:20` and the vocabulary say the brief is a file "the owner approved before planning". A later
  planner reading a planner-written brief treats its decisions as fixed by the owner. `profile.md` should say to mark
  such a brief as not approved. Confirmed by reading.
- `plan-module/references/done-when.md:120-121` says its status table is "the only place the two are matched up", and
  the spec (line 20-21) says it "holds the one table". The README has a second table (lines 199-210) and
  `build/SKILL.md:217-231` a third. They differ: the README table has no Blocked row, and none of the three has
  `ready`, `review_owed`, `design_owed`, `finished` or `invalid`.
- README line 93 says the `plan` command "confirms the planner wrote only plan files". `build/SKILL.md:169-170` says a
  `PLANNED` result merges files the planner wrote outside the plans folder too. The script agrees with `build`
  (script:4797-4800).
- `plan-module/references/done-when.md:154-155` against README lines 634-638, on a module with no record file. The
  README is right. See section 2.
- `review-milestone/SKILL.md:104-105` says a design reviewer is given the owner's request and the module's entry in
  the module list. `plan-module/SKILL.md:166-167` and README line 99-100 say only the request and the design. The
  script's prompt points at the request and the clean copy (script:348-351, 4396-4399).
- `workbench/orchestration-review/vocabulary.md:94` lists `question` for what was `next.ask`. The script prints `ask`
  (script:1410-1415, 1436), and `build/SKILL.md:214` says `ask`. The skill is right; the vocabulary row describes a
  rename that has not been made.

---

## 5. Broken relative links or anchors

None. I checked all 46 relative links and in-page anchors in the eleven rewritten markdown files, the README and the
two new skills (the `.toml` agent file has no links) with a script that resolves each path and compares each fragment with the target's headings. All resolve,
including the new `done-when.md#statuses-and-their-stored-names`, `proofs.md#subjective-work` and the three in-page
anchors in `build/SKILL.md`. Confirmed.

One pointer outside the markdown is stale: the script's re-plan task names a `plan-module` heading by its old title
(script:1298-1299). See section 2.

---

## Checked and found sound

So that these need not be checked again. All confirmed against the script.

- Every row of the result table in `build/SKILL.md:217-231`, the `ladder` values at 260-265, and the `next.by` values.
- `CLAIMED` with `review: false` means the script recorded the milestone as Done on its checks (script:4198-4203).
- The rules for which milestones need a reviewer (script:883-887), the escalation steps (script:904-911), what the
  script resets after a failed review (script:914-923, 4542-4545), and what it does for a milestone that was Awaiting
  Replan (script:1332-1348).
- The builder's three fields and the planner's limits (script:928, 939-951).
- Every flag shown for `run`, `review`, `plan`, `check`, `next`, `land`, `lock`, `loops`, `pause`, `quota`, `report`,
  `adopt`, `profile` and `status`, apart from the two missing `--worktree` flags in section 2.
- `profile.md`: the line shape the parser needs, the required lines, the meaning of `Review host`, and that `adopt`
  merges any file in the plans folder.
- `graded-examples.md`: wording only; nothing lost.
- The spec's new claims: the script and the installer use the agent files' names (script:2926, `install.py:387`,
  `.claude-plugin/marketplace.json:78-79`), and `skills/skill-creator/scripts/check_skill.py` exists and passes.
- `tests/orchestration/test_agent_loop.py:2208-2210` reads `review-milestone/SKILL.md` for two exact strings, one of
  them split across a line break ("A Suggestion never changes the\n`state`."). Both are present today. Re-wrapping
  lines 79-80 of that file would fail the test.
