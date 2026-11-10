# Review B: `capture-intent` and `domain-language`

Written 10 November 2026 by a reviewer in a new session. Nothing was edited except this file. No model session
was run. The only commands run were searches, `check_skill.py` on both skills (both print `ok`), and a parse of
the six `case.yaml` files.

## Verdict

The substance of both skills is sound. Most rules trace to the research notes or to the owner's own corrections,
the prose is mostly in the owner's style, and the commands the skills name match the script. They are not ready
for test conversations yet, for five reasons. First, `capture-intent` has no clear path for a small request: four
of its lines pull against the one line that says to go straight on, and its description would load it for nearly
any change in any repository. Second, the two skills and the settings template disagree about where the glossary
of a new project lives, and nothing connects a glossary or a brief to a project that was planned before today.
Third, the check that `domain-language` gives for "finished" cannot pass in a real project, and its rule to
update the plans conflicts with who is allowed to edit plan files. Fourth, what the owner's approval of a brief
means is stated two ways, and "skip the conversation" has three different meanings across the files. Fifth, four
of the six test cases will not place their input files, and the checks do not grade the things the owner pages
were built to hide. Several numbers quoted from other libraries are also stronger in the skills and the README
than in the research notes. The findings below are in order of seriousness. The last section lists what is good
enough to leave alone.

Each finding says how sure it is. "Confirmed" means I checked it against a file, and the file is named.
"Judged likely" means it is my reading of how a model would act on the text.

---

## Findings

### 1. `capture-intent` has no clear path for a small request, and its description loads it for almost any change

**Where.** `capture-intent/SKILL.md:3` (description), `:17-25` (what finished looks like), `:27` (the stop),
`:31-32` (go straight on), `:42-47` (the first message), `:59-60` (ask why), `:72-83` (what the brief has to
cover), `:80-81` (what it runs on). Also `build-milestone/SKILL.md:22-24` and `README.md:344-345`.

**What is wrong.** One sentence covers the small request: "If the request and the repository already answer
everything that matters, say what you understood in a few lines, and go straight on." Five other lines say the
opposite for the same request:

- Line 27: start planning or building only after the owner has approved the brief, or has said to go ahead
  without one. The owner of a small request has said neither.
- Lines 42-47: the first message "asks one thing". The source library's first message had a third shape, a short
  design to approve "when nothing is open" (survey lines 68-69). That shape was dropped, so the first message
  here always carries a question. This is the failure the skill itself describes at line 55.
- Lines 59-60: ask why, as an open question, "even when you think you can guess". The filter at line 51 says ask
  only when the answer would change what gets built. A reason often changes nothing, so the two lines disagree.
- Lines 72-75: the brief "has to cover" seven things "by the end", the reason among them.
- Lines 80-81: settle what it runs on "even when everything else is clear".

"Go straight on" also does not say to what. The finished list at lines 17-25 allows only two ends: a saved and
approved `BRIEF.md` on the main branch with a planner started, or the owner choosing to stop. There is no end
that means "this was small, so it was built in this session with no brief". The README says a small job should
be done in a single chat (`README.md:344-345`), and both libraries the skill draws on have that exit (survey
lines 60-61 and 417).

The description makes this matter more. "Use when someone describes something they want to build, add or change
and no plan exists for it yet" matches "add a `--json` flag" and "fix this bug" in every repository where the
plugin is installed. In a repository with an `ORCHESTRATE.md` it collides with `build-milestone`, whose
description takes "implementing, fixing or refactoring" and whose line 22 says: "For an ordinary fix that has no
plan, fix it." The two skills give opposite instructions for the same request.

**What would happen.** For a request like the one in the `clear-small-request` test case, Claude Fable 5.2 and
GPT-6.1 Sol will most likely ask why, or ask what it runs on, or write a `docs/modules/BRIEF.md` and wait for
approval. GPT-6 Astra is likely to stop and ask which instruction to follow. Claude Opus 5.5 will probably go
straight on and build. In an orchestrate repository, which of `capture-intent` and `build-milestone` loads for a
small change is a coin toss.

**How sure.** The conflicting lines and the collision are confirmed in the files named. What each model does
with them is judged likely.

### 2. The files disagree about where the glossary lives, and nothing links a glossary or brief to an existing project

**Where.** `capture-intent/SKILL.md:19-20` and `:126`; `domain-language/SKILL.md:19-21` and `:131-133`;
`plan-module/references/profile.md:16-17`; `plan-module/SKILL.md:17-18`; `build-milestone/SKILL.md:14`;
`review-milestone/SKILL.md:23`; `build/SKILL.md:49` and `:126-127`.

**What is wrong, in a new project.** `capture-intent` writes the glossary "beside the brief", which is
`docs/modules/GLOSSARY.md` when no `ORCHESTRATE.md` exists yet. `domain-language` says the glossary is in the
plans folder only "in a project with an `ORCHESTRATE.md`", and "anywhere else it is `GLOSSARY.md` at the root of
the repository". A new project has no `ORCHESTRATE.md` during the first conversation, so `domain-language` puts
the file at the root, and also adds a pointer line to `AGENTS.md` or `CLAUDE.md` (lines 131-133). The planner
then writes the settings from a template whose `Glossary:` line is `docs/modules/GLOSSARY.md`. The description
of `domain-language` says "Use when a project starts", so a lead is likely to have both skills loaded at exactly
this moment.

**What is wrong, in an existing project.** A project planned before today has no `Glossary:` line. A builder
reads the glossary "on its `Glossary:` line if it has one", and a reviewer and the lead read it "if the project
settings have a `Glossary:` line". No skill says who adds the line. `domain-language:20` says "if there is no
such line yet" and stops there. `build/SKILL.md:126-127` says a changed `ORCHESTRATE.md` is the owner's decision,
and the script's `adopt` command refuses to merge one (`agent_loop.py`, function `adoptable`). The planner's
task names the brief's path but not the glossary's (`capture-intent:196`).

The same gap exists for the brief. Until today the template's `Purpose:` line was "link to the doc saying what
the project is for" (the committed `profile.md`, line 15), so existing projects have a `Purpose:` line that names
some other document. `capture-intent` never mentions that line. It writes `docs/modules/BRIEF.md` and leaves the
old line pointing at the old document.

**What would happen.** In a new project, either two glossaries exist, or builders are pointed at a path with no
file. In an existing project, the names the lead agrees with the owner never reach a builder or a reviewer, and
the planner has two documents that both claim to say what the owner wants.

**How sure.** Confirmed in the files named. I did not check what any live project's `ORCHESTRATE.md` holds.

### 3. The check `domain-language` gives for "finished" cannot pass, and its rule to update the plans conflicts with who may edit them

**Where.** `domain-language/SKILL.md:27-28`, `:58-65`, `:106-108`, `:123-125`, `:135-136`. Also
`build/SKILL.md:55`, `build-milestone/SKILL.md:29-35` and `:111`, `README.md:196-210`.

**What is wrong.** Finished condition 5 says to search the plans and documents for each name under `Avoid`, "for
example `grep -rniw "claimed" docs`. Only the glossary itself should match." Three things in the same skill and
the same set make other files match:

- Line 108 tells documents to "give the stored name once, at the place the reader will meet it". A document
  that follows that rule matches the search.
- The skill's own example entry lists `claimed` under both `Avoid` and `Stored as`. In an orchestrate project
  the stored name is in every done-when file, which is in the plans folder under `docs`.
- Line 125 says to leave logs and finished reviews as written. Those match too.

The test case `tangled-terms` already carries the exception the skill lacks: its ninth check says "except to
give a stored name".

Line 124 says "update the plans and documents still in use", and does not say who. A builder may change three
fields of the done-when file and may not change the design, and the `run` command rejects a builder that changes
an item's wording. A lead is told "don't edit a done-when file" and, once a design is approved, `adopt` refuses
revised items. So in an orchestrate project the only agent that can apply a changed name to plan files is a
planner, started with the `plan` command. The skill does not say so.

Lines 135-136 offer a test that fails when an avoided name appears "in the plans or documents". Where the
avoided name is also a stored name, that test fails the project's test command, and the `land` command then
refuses every merge.

**What would happen.** An agent that works to the finished list either loops on a search that cannot come back
clean, or rewrites records and done-when files to make it clean. In a build, the second of these gets a
builder's work rejected as `INVALID`.

**How sure.** Confirmed in the files named. The loop or the rewrite is judged likely, most of all for Opus 5.5
and Fable 5.2, which work to a stated check.

### 4. What the owner's approval means is stated two ways, and "skip" has three meanings

**Where.** `capture-intent/SKILL.md:21`, `:27`, `:32-34`, `:116-118`, `:147-149`, `:179-180`;
`plan-module/SKILL.md:20-24`; `plan-module/references/profile.md:72-74`; `README.md:59` and `:491-494`;
`build/SKILL.md:42-43`.

**Approval.** Lines 116-118 say: "'Sounds good', after a message that covered six things, is not agreement to
each of the six. ... When a decision matters, put it to the owner by itself." Lines 21 and 179 then make the
whole brief, about a page that covers every decision, the thing the owner approves in one reply. The skill does
not say which rule wins. It also does not say what approval does to a decision marked "The agent's decision ...
Not confirmed by the owner". The owner has now read that line and approved the page it is on. A reader could
fairly change every such line to "Proposed by the agent, and agreed by the owner". `plan-module:21-22` treats
that kind as fixed, so the planner loses the freedom the marking was there to give.

**What would happen.** With an owner who agrees with everything, either the agent takes "ok" as approval and
upgrades its own guesses to the owner's decisions, or it refuses the "ok" and asks about each decision in turn.
Fable 5.2 and Astra are likely to do the second. The simulated owner in the test cases is told to approve "in a
few words", so the first test run will meet this.

**Skip.** Three files answer "what happens when the owner says to skip the conversation":

- `README.md:493-494`: "A planner then takes the safest reading of anything you left out, and lists what it
  assumed." No brief.
- `capture-intent:32-34`: the lead writes the brief anyway, shows it, and plans "on their word". That is a
  second approval from an owner who just asked not to be asked. Line 27 in the same file allows going ahead
  "without one".
- `profile.md:72-74`: the planner writes a short brief itself.

`build/SKILL.md:42-43` says to skip the conversation and then gives a `plan` command that names "the project
brief" at a path, when no brief exists.

**How sure.** Confirmed in the files named. The behaviour is judged likely.

### 5. Four of the six test cases will not place their input files, and the checks miss what the owner pages hide

**Where.** `workbench/intent-conversation/evals/` and `workbench/domain-language/evals/`.

**The `case.yaml` files are malformed.** In `clear-small-request`, `existing-project-new-feature`,
`new-name-mid-task` and `tangled-terms`, the first lines are indented six spaces and `scaffold_script:` sits at
column 0, outside `context:`. The format in `skill-creator/references/testing.md:57-65` nests it under
`context:`. Ruby's YAML parser reads each of these files with `context` empty and `scaffold_script` gone. A
stricter parser would refuse the file. Either way `place-files.sh` does not run, so the agent starts in an empty
folder: no salon code, no tangled documents, no existing glossary. Confirmed by parsing the files.

**Nothing says how the owner is played or what a grader sees.** `owner.md` is not part of the layout in
`testing.md`, and `claude plugin eval` sends one prompt. Without a second agent playing the owner, the run ends
at the first question. Every check about file contents uses `focus: output`, and `testing.md:276-277` says to
point a grader at the file to grade what was made. The two `focus: trace` checks ("nothing before approval") see
only the first twelve and last twelve messages of a conversation that may run to forty turns
(`testing.md:276`). Confirmed against `testing.md`. How the eventual runner treats `focus: output` is not
something I could check.

**The hidden facts are not graded.** The owner pages hide the facts that separate a good conversation from a
bad one, and no check asks for them:

| Case | Hidden on the owner page | Graded? |
|---|---|---|
| `vague-new-product` | The back wall has no signal, so it must work offline | No |
| `vague-new-product` | Four route setters use it, on phones, at the wall. Members never do | No |
| `vague-new-product` | The three things that are out of scope | Only that some list exists (check 08) |
| `existing-project-new-feature` | A moved appointment keeps the same stylist | No |
| `tangled-terms` | The owner says "waiting for pickup" and "it's overdue" | No. Any plain name passes |

A conversation that never finds the offline rule passes all eleven checks of `vague-new-product`.

**Checks the skill's text makes true, or that cannot be decided.**

- `vague-new-product/03`: passes if the brief says what it runs on and the owner did not object. The template
  has a "Where it runs" heading and the simulated owner approves anything that matches the page.
- `vague-new-product/04` and `/08`, `existing-project-new-feature/08`: true for any brief that follows the
  template or line 19. Fair as guards. They say nothing about quality.
- `vague-new-product/06`: requires every technical choice, "how it is delivered" included, to be marked as the
  agent's and "not as something the owner said or agreed". The owner page has the owner pick "the one that works
  on both" when offered choices, which the skill records as "agreed by the owner". The skill also says to leave
  how it is built to the planner (line 85), so a good brief holds no such choices. A correct brief either fails
  this check or passes it with nothing to check.
- `vague-new-product/11`: bans questions "about process". The skill requires asking whether agents may push and
  which hosts to use. A grader could count either as process.
- `existing-project-new-feature/04`: the first half ("no file under `src/` has been changed") is true of any
  run that does not build. The second half wants the stored name `booking` recorded, and `capture-intent:126-127`
  describes an entry with no `Stored as` line.
- `existing-project-new-feature/06`: needs the agent to ask about pushing. The fixture's `ORCHESTRATE.md` says
  `Integrate: local`, so the repository already answers it, and check 01 punishes asking what the repository
  answers.
- `clear-small-request/05`: passes with no brief and with a short approved brief, so it cannot tell "went on"
  from "stopped for approval". No check in that case looks at what the agent did after its first message, which
  is the open question in finding 1.
- `new-name-mid-task/01`: "use 'locker', 'drop_off' or 'drop-off' and 'pickup'" cannot be decided. A new function
  need not mention pickup at all.
- `new-name-mid-task/02`: assumes the task needs a new name. A good agent could reuse Drop-off, add nothing, and
  fail checks 02, 03 and 04.
- `new-name-mid-task/05`: the prompt says "The owner is away until tomorrow and can't be asked anything", so the
  agent cannot stop to ask with or without the skill.
- `small-tool`, all five checks: an agent with no skill would very likely pass them. It is a guard case, which
  is fine if it is marked as one.

**Every check grades the conversation or the document.** `testing.md` ("When another agent acts on the output")
says that for a brief the result is what the next agent does with it. No case hands the brief to a planner. The
README is honest that this has not been measured. One such case would be the first evidence either way.

**What would happen.** The first round of runs would report failures that come from missing files, and passes
that come from the template.

**How sure.** The malformed files and the missing checks are confirmed. The trivial passes are judged likely.

### 6. A change of mind updates the brief in one skill and skips it in two, and no reviewer reads the brief

**Where.** `capture-intent/SKILL.md:170` and `:200-204`; `build/SKILL.md:46-47` and `:303-305`;
`plan-module/SKILL.md:198-203`; `review-milestone/SKILL.md:104-106`; `README.md:99-101`.

**What is wrong.** `capture-intent` says that when the owner changes their mind, the lead adds their words to
the brief, changes the decisions, shows the brief again, and then gives a planner their words. The lead's own
skill says: "A change of mind about what is wanted goes to a planner, with their words as the task." It does not
mention the brief. `plan-module:198-203` says to quote the words in the plan's log, and does not mention the
brief either. During a build the lead has `build` loaded, not `capture-intent`.

`capture-intent` also leaves a step out here. The first hand-over puts the brief on the main branch with `adopt`.
The change-of-mind section goes from "show them the brief again" to "give a planner their words", with no merge
in between. `build/SKILL.md:163` starts a planner "in a clean worktree".

`capture-intent:170` says the decisions are numbered so that "the design, the items and the reviews can point at
one by its number", and line 203 says "the plan, the items and the reviews are judged against the brief as it
now stands". No reviewer is given the brief. `review-milestone` never uses the word. A design reviewer gets "the
owner's request and the module's entry in the module list", and is told to look for "things it adds that nobody
asked for".

**What would happen.** After the first change of mind the brief is out of date, and nothing notices. A design
that carries a brief decision the one-line request does not mention, such as the 24-hour limit, can be marked
Must Fix by a reviewer as something nobody asked for.

**How sure.** Confirmed in the files named. The Must Fix is judged possible. The planner's task does name the
brief's path, and a careful reviewer may open it.

### 7. Claims about other libraries that the research notes support only partly, or not at all

"Survey A" is `workbench/intent-conversation/references/01-library-survey.md`. "Survey B" is
`workbench/domain-language/references/01-library-survey.md`. All confirmed by reading the notes.

| Claim, and where | What the notes say | Verdict |
|---|---|---|
| "graders rated one conversation in nine as good, against seven in nine when the reason was asked for first" (`capture-intent:60-62`, `README.md:235-237`, workbench README row 2) | Survey A 616-618: the 1 of 9 was a draft that removed the required opening question. The 7 of 9 was "before", which is the version that always opened with a question. That is the version the skill criticises four lines earlier. The grade was of the "why" part of the conversation | Partly. The 7 of 9 does not belong to the rule the skill uses. The figure for the released rule is the reason coming out in 33 of 33 conversations, against 28 of 33 (609-611) |
| "agents skipped the written design and started building in 24 of 24 runs until a rule like this was added" (`capture-intent:28-29`, `README.md:238-239`) | Survey A 605-607: in one test scenario the agent "skipped the doc without asking". The rule added was to lay out approaches and write a design document. Building before approval is a separate figure: 4 times, then none (611-612, 856-857) | Partly. "Started building" and "get it approved" are not in the note. It was one scenario |
| "taken from the skill libraries that have tested theirs. We read fourteen of them" (`README.md:228`) | Survey A 594-738: three libraries have measurements of a conversation skill (superpowers, Compound Engineering, gstack). Five give reported failures or changelog fixes with no measurement. Six give nothing | Not supported as worded. Fourteen were read. Three had tested |
| Superpowers "measured each change on test conversations graded blind" (`README.md:230-231`) | Blind grading is stated for v7.0.2 only. v7.0.1 has one scenario. v7.0.0 has no measurement | Partly |
| Opus 5.5 "asking people why they wanted to fix a bug they had just described" (`capture-intent:55-56`, `README.md:231-232`) | Survey A 599-603: one issue, from a person using Opus 5.5. The example is a listed piece of technical debt. It is a report, not a test result | Partly |
| "Filler questions fell from 41 to 23" given as the effect of the filter (`README.md:232-233`) | Survey A 608-610: v7.0.2 added four things at once, and the figure is for all of them | Partly |
| "A length limit did not shorten it. A rule about what belongs in it did" (`README.md:240-241`, workbench README row 11) | Survey A 654-660: the cap result is for Claude only. The content rule is listed under "what worked". The note does not say it made the message shorter | Partly |
| "Both warn that an entry an agent wrote and nobody checked is read as fact by every later session" (`README.md:269-270`); "Both main libraries warn ..." (`workbench/domain-language/README.md:61-62`) | Survey B 378 and 476: Matt Pocock's docs say this. Compound Engineering "writes silently by design" | Not supported for Compound Engineering |
| "Each rule here comes from a name an owner rejected" (`domain-language:36`) | The workbench README gives "only names particular to the project" and "one thing has one name" to the libraries | Not supported for two of the seven rules |
| "one project's grew from 35 entries to 76 with almost nothing ever removed" (`domain-language:128-129`) | Survey B 385: "entries grew from 35 to 76 while the codebase doubled" | Supported, but the missing half matters |
| "mattpocock's notes link the word to very long sessions" (`workbench/intent-conversation/README.md:68-69`) | Survey A 691-693: the maintainer says a very long session usually means the scope was too big. The link to "relentlessly" is the research agent's own judgement (959-960) | Not supported |
| "The numbers come from tests on Claude models" (`workbench/intent-conversation/README.md:103`) | Survey A 649-650: the Compound Engineering test ran on Claude and Codex. The same README says so in its table | Contradicts itself |
| "The three the owner named were read in full" (`workbench/intent-conversation/README.md:17`) | Survey A 25-27: superpowers "except the visual companion", and three mattpocock skills were not read | Partly |
| "BMAD, Compound Engineering and get-shit-done each number decisions" (same file, row 13) | Survey A 1009-1012: Compound Engineering has provenance labels, not numbers | Partly |
| "Three parts of the brief come from our own needs and from no library" (`README.md:250-252`) | The workbench README says four. Survey A part 5 also lists "what must not change", asking first about what is expensive to undo, and a later change of mind as covered by no library. All three are in the skill | Undercounts |
| "A reviewer in a new session read it ... the review record" (both workbench READMEs); "They have been read by a reviewer" (`README.md:712-713`) | `workbench/orchestration-review/polish-workspace/review.md` does not exist. The folder holds only `old/` | The link is dead today |

These check out and need no change: 41 to 23, 8 of 8, the iOS app built as a web app, "that scope is ok", issue
#706, 380 lines added and 11 removed over 25 commits, "most-reported problem", the rename to `GLOSSARY.md` in
version 1.3.0, and the counts "eight of the libraries", "seven libraries" and "six others". The two test-run
stories at `capture-intent:12-15` match the run records (`s3-ledger-cross/friction.md:99`, `results.md:45`).

### 8. `domain-language` inside a long unattended build

**Where.** `domain-language/SKILL.md:3`, `:17-28`, `:119-129`; `plan-module/SKILL.md:25-27`;
`build-milestone/SKILL.md:102-103`; `build/SKILL.md:330`.

- **"Say why you think it should change, and wait" (line 123).** "Wait" has no object. A builder or planner that
  nobody is watching, and that reads this, may stop. Astra is the most likely to. The meaning is "keep using the
  agreed name, and put your reason in your report". Judged likely.
- **The description loads the skill for every naming act.** "When a new name is about to be introduced" is the
  design the workbench README says it rejected, because "that is a glossary search before each local variable".
  The other four skills each carry their own line so that this one need not load. A builder that does load it
  meets a finished list that asks for the whole glossary, the owner's agreement and updated plans. Judged likely.
- **"When a thing goes away, delete its entry. When two entries turn out to be one thing, merge them"
  (lines 127-128).** Nothing says who may do this to an entry the owner agreed. Merging two agreed entries
  chooses between two agreed names, which line 123 says is the owner's decision. The survey's source required
  positive evidence before removal (survey B line 148). Judged likely to cause a wrong deletion sooner or later.
- **The mark for an unagreed entry is worded four ways.** `domain-language:64` shows "Proposed by a builder on
  12 March. The owner has not agreed it yet." and calls it "a `Proposed` line". `plan-module:26-27` and
  `build-milestone:102-103` say "a line that says" an agent proposed it, with no form. `capture-intent:126-127`
  has no mark. The lead has to find these lines for every report (`build:330`) and remove them on agreement. By
  design the builder and planner never see the form. The example date also has no year. Confirmed.
- **A proposed name goes into code.** Line 113 says new code uses the glossary's names in identifiers. A builder
  that proposes a name writes it into identifiers and saved values. When the owner later "picks another name",
  line 110 makes the rename building work. So the owner's pick changes the prose and not the code, and the skill
  does not tell the owner or the agent that. Confirmed in the text. The consequence is judged.
- **Existing identifiers are not covered.** Lines 106-107 keep "a saved file, a database column, an API or a
  command that people type". A function such as `createBooking` is none of these. `build-milestone:15` says to
  use the glossary's names "in identifiers". A builder may rename working code, or write `moveAppointment`
  beside `createBooking`. Judged likely to split one way or the other.
- **Two builders each add an entry to one file.** Each `land` rebases, and two additions at the end of one file
  conflict. The survey lists this as a gap no library covers (survey B part 7, point 10). Judged likely with two
  or three builders.

### 9. `capture-intent` when the owner cannot be reached, and gaps in the hand-over

**Where.** `capture-intent/SKILL.md:3`, `:8`, `:189-198`.

- **A planner can load this skill.** A planner's task is the owner's request word for word, which "describes
  something they want to build". The planner agent has the Skill tool. The body opens "You are talking with the
  owner" and forbids planning before approval. Nothing says "if you cannot reach the owner, this skill is not
  for you". On the "just plan it" path there is no brief, so a cautious planner could end `BLOCKED` waiting for
  an approval nobody can give. Judged possible. One clause in the description would remove it.
- **"In a single chat with no script" (line 198) cannot be decided, and is the wrong name.** The script is
  present whenever the skills are installed, and a single chat still runs it (`build-milestone:68-73`). The
  README and `build-milestone` call this mode "one chat with no lead". Nothing tells the reader which mode it is
  in. That is the owner's choice, and the skill neither asks for it nor gives a default. Confirmed in the text.
- **An existing repository with no `ORCHESTRATE.md` fits neither bullet** (lines 191-193). The first bullet is
  for a project that has one. The second is for "a new project". The `clear-small-request` fixture is such a
  repository. Confirmed.
- **"Commit the files with git" (line 193) is a commit to the owner's main branch that the owner did not ask
  for.** Both hosts tell agents to commit only when asked. The reader will either stop and ask, or skip the
  step. One sentence in the message that shows the brief ("when you approve, I will commit it and start
  planning") would make the approval cover it. Judged likely.
- **A bare `adopt` merges every plan file that is not yet merged in that working copy,** and approves revised
  items for a module whose design is not yet approved (`build/SKILL.md:122-124`). The command accepts paths
  (`agent_loop.py:6051`). Naming the brief and the glossary would merge only those two. Confirmed in the script.
- **The skill ends at "planning has started".** It does not say that the `plan` command waits for the planner
  and can run for a long time, what to tell the owner then, or what the owner does next. The `build` skill
  cannot be loaded by the agent (`disable-model-invocation: true`), so the owner has to type `/build`. The
  README says "Say 'build it'" (`README.md:498`). Confirmed in the files. The stall is judged likely.

### 10. An owner who answers hours later

**Where.** `capture-intent/SKILL.md:68-70`, `:126`, `:174-180`.

- **The brief is written once, at the end** (line 174, "Before you save the brief"). The glossary is written as
  each name is agreed (line 126). A conversation spread over days, in a chat whose early messages are shortened
  or replaced, loses the owner's exact words, and the brief has to quote them. The README's own rule is that
  everything is kept in files (`README.md:390-393`). Survey A names this gap (part 5, point 14). Judged likely
  for a slow owner.
- **One question in a message, with no exception for a slow owner.** The exception at lines 68-70 applies only
  if the owner asks for it. The map has seven topics. At one question for each reply, an owner who answers twice
  a day needs most of a week. Matt Pocock's rounds exist for this reason. Judged.
- **Two messages before approval, with a wait after each one implied.** Lines 174-177 play back the
  understanding. Line 179 then shows the whole brief. The skill does not say whether these are one message or
  two. The source's finding was that the short playback is the approval point (survey A lines 413-416, 422 and
  658-660). Pasting the full page afterwards brings back the long summary that "gets approved without being
  read". Confirmed against the survey.
- **"Show them the brief again after any change" (line 180).** For a correction the owner dictated, this is
  another round trip. Fable 5.2 will take it every time. Judged likely.

### 11. Where `capture-intent` asks too much

Finding 1 covers the forced question in the first message and "ask why even when you think you can guess". The
rest:

- **"How the owner wants to work" (lines 82-83) fails the skill's own filter.** Which hosts to use, whether
  agents may push, and which decisions the owner wants are three questions that change nothing about what gets
  built. Line 56 says "Don't ask about process either". The test owner is scripted to answer "what does that
  mean?" to the push question. In an existing project the settings already answer two of them (`Integrate:`,
  `Builders:`, `Owner decides`). By the skill's own rule these should be decided and stated: no pushing, the
  host this chat is in, and the usual list. Confirmed as a conflict in the text.
- **"Settle the name of each thing as it comes up" (line 122)** has no limit to things particular to the
  project, which `domain-language:50` has. Each clash is then a question ("say so and ask which") that the
  filter would not allow. Judged likely to add questions on Fable 5.2.
- **"Word a yes-or-no question so that 'yes' accepts your recommendation" (lines 65-66)** is right for a
  careful owner. With an owner who agrees with everything, every recommendation becomes "agreed by the owner"
  and is fixed for the planner. The workbench README says nobody has a tested answer. This is a known gap, not
  an error. It is listed so that the test with the agreeable owner is read with it in mind.

### 12. The fresh reading: three problems in four lines

**Where.** `capture-intent/SKILL.md:182-185`.

- "For a project of several modules": modules do not exist until a planner makes them, and line 132 says the
  brief says nothing about modules. The reader cannot tell whether this applies. The term is also not defined
  in this skill.
- "Get one fresh reading first" comes after the paragraph that shows the owner the brief, so "first" points
  backwards. The owner's rule is to tell things in the order they happen.
- "Start a subagent": `README.md:308` is headed "the lead does not use subagents", and `build/SKILL.md:175-176`
  says reviewers are never started as the lead's own subagents. On Codex a subagent starts with a copy of the
  lead's whole conversation unless told otherwise (`README.md:327-328`), so "the brief and nothing else" needs a
  setting the skill does not name.

Confirmed in the files. The Codex point is judged from the README's own statement.

### 13. A second request in the same project, and what a planner may do to the brief file

**Where.** `capture-intent/SKILL.md:19`, `:38`, `:132`, `:170`; `build/SKILL.md:46-47`; `plan-module/SKILL.md:20-24`.

- There is one `BRIEF.md` for each project, "about a page". The description covers "add or change", so the
  second feature arrives at a brief that already exists. `build:46-47` says "update the brief". Nothing says
  whether to add to it, replace it or start a second file. Nothing says that a decision's number must never be
  reused or changed, though designs point at decisions by number. Confirmed as absent. The breakage is judged.
- `plan-module` says which decisions a planner may change in the design. It does not say whether a planner may
  edit `BRIEF.md` itself. The `plan` command merges whatever a planner changed. A tidy planner that overrides
  decision 3 may "update the brief to match", and then the page the owner approved has changed without them.
  Confirmed as absent. Judged possible.
- Only the numbered decisions and "Still open" are marked with whose they are. "Where it runs", "Must not
  change" and "How it will be judged" have no marking, and `plan-module` reads only the numbered list that way.
  A platform the lead chose itself, written under "Where it runs", reads as the owner's. Judged likely.
- Line 132 says the brief says "nothing about ... mechanisms". Lines 86-87 say a technical choice the owner
  names "goes in the brief". The exception belongs inside the rule.
- The headings are found by name by `plan-module` ("Something under 'Still open'"). The skill does not say that
  the headings stay as written.

### 14. `domain-language`: how much to write, and whose names win with an agreeable owner

**Where.** `domain-language/SKILL.md:22-26`, `:84-98`.

- Finished condition 2 is "each thing that is particular to this project, and that the owner or an agent talks
  about, has one entry". In a real project that has no upper limit, and the skill's own warning at line 128 is
  about a glossary that only grows. Condition 3, the steps test, is the better stopping rule, and the two
  disagree about how much is enough. Judged likely to over-fill on Opus 5.5 and Fable 5.2.
- Step 3 gives "the name you recommend" for each clash. Nothing tells the agent to ask what the owner calls a
  thing before it proposes a name. "The owner's own word wins" then applies only to words the owner happened to
  use already. The `tangled-terms` owner page shows this: the owner's words "waiting for pickup" and "overdue"
  come out only if asked, and the owner accepts any plain name offered. `capture-intent` learned the same lesson
  for reasons ("options steer"), and it is not applied to names. Judged likely.
- Condition 4 lets one "looks fine" to fifteen entries make all fifteen "the owner's decision", which line 123
  then locks. `capture-intent:116-118` says a reply like that approves nothing in particular. The two skills
  hold agreement to different standards. Confirmed in the text.

### 15. The descriptions

**`capture-intent`.** It would load for its intended requests. It also loads for almost any change (finding 1),
for a planner's task (finding 9), and beside `plan-module`, whose description takes "starting ... a project" and
names no boundary back. Suggested shape, for the owner to judge: name who the reader is ("the agent the owner is
chatting with"), name the size ("a project or a feature that will be planned"), and add "Not for a change small
enough to build in this session".

**`domain-language`.** "Asks for a glossary, a domain language or clearer terms" and "using different words for
the same thing" would load it for the `tangled-terms` request. Three other triggers are too wide:

- "When a project starts" loads it beside `capture-intent`, which carries its own name rules so that this need
  not happen. The two then disagree on one question in a message against "a few at a time" (line 90), and on
  where the file goes (finding 2).
- "When a new name is about to be introduced" loads it for any naming act in any session (finding 8).
- "Clearer terms" also matches "use clearer terms in this email" and "rename this function".

It has no "Not for" clause, and it is the only one of the six without "as part of the orchestrate set". The
second is correct if the skill is meant to work alone. In that case the body should define the orchestrate terms
it uses (finding 16).

`README.md:32` says the skill is read by "the lead, and any agent that needs a new name". The workbench README
says the other skills carry their own line so that none depends on it. The owner should pick one of these, and
the description should follow.

All of this is judged from the text. Whether a description loads can only be settled by the loading test in
`testing.md`.

### 16. Where the prose breaks the owner's preferences

**A term used before it is defined, or never defined.** Each skill is read alone, so the README's definitions do
not count.

| File and line | Term |
|---|---|
| `capture-intent:11` | "the orchestrate set" |
| `capture-intent:20` | `ORCHESTRATE.md`. The skill never says what the file is |
| `capture-intent:39` | "the glossary", 87 lines before line 126 says what it is |
| `capture-intent:82`, `:164` | "hosts". Beside "what it runs on", a reader can take it for web hosting, and may put the word to the owner as it stands |
| `capture-intent:102` | "milestone" |
| `capture-intent:132`, `:182` | "modules" |
| `capture-intent:170`, `:203` | "the design", "the items", "the reviews" |
| `capture-intent:182` | "subagent" |
| `domain-language:19`, `:132` | `ORCHESTRATE.md` at line 19 and "the project settings" at line 132 are one thing with two names, in the skill about one name for one thing |
| `domain-language:20` | "the plans folder". `capture-intent` defines it, and this skill does not |
| `domain-language:77`, `:85` | "the brief", "the project brief", "the design" |
| `domain-language:131` | "the orchestrate set" |

**A second name for one thing.** `capture-intent:198` says "a single chat with no script". The set's name is
"one chat with no lead" (`README.md:502`, `build-milestone:68`). `domain-language:26` says "hasn't seen" and
line 72 says "hasn't agreed" for the same mark.

**Who does it is not named.**

| File and line | Sentence |
|---|---|
| `capture-intent:203-204` | "The plan, the items and the reviews are judged against the brief as it now stands." Who judges is not said, and no reviewer is given the brief (finding 6) |
| `domain-language:110-111` | "It happens when the owner asks for it, and it is planned like any other change." |
| `domain-language:124` | "update the plans and documents still in use" has no agent named (finding 3) |
| `domain-language:20` | "if there is no such line yet". Who adds the line is not said |
| `README.md:58-59`, `:239` | "Nothing is planned before that." |

**A step skipped.**

- `capture-intent:174-180`: when the file is written, before or after approval, and whether the playback and the
  brief are one message or two.
- `capture-intent:191-193`: the script is run as `python3 <the build skill's folder>/scripts/agent_loop.py`.
  `build-milestone:20` spells that out, and this skill gives only the folder. A new project that is not yet a
  git repository needs `git init`. The `vague-new-product` case starts in such a folder.
- `capture-intent:202-204`: the merge between changing the brief and starting a planner.
- `domain-language`: how the glossary reaches the main branch in an orchestrate project. `capture-intent` and
  `profile.md` say `adopt`, and this skill says nothing.
- `domain-language:131-133`: "`AGENTS.md` or `CLAUDE.md`" is a choice with no default. Older versions of Claude
  Code do not read `AGENTS.md` (`README.md:480-481`), so a project built with both hosts needs both files.

**Words that are not plain.**

- `capture-intent:34`, "plan on their word". It can be read as "plan from what they said". The meaning is
  "start planning when they say to".
- `capture-intent:202`, "change the decisions they reach". "Reach" means "affect" here, and reads as "arrive at".
- `capture-intent:45`, "bears on it".
- `domain-language:68-70`, "the neighbour". "The thing it is most easily confused with" is plainer.
- The name `capture-intent`. The word "intent" appears nowhere in the body, which says "what they want and why"
  and "project brief". This is the short coined name where an explicit one exists. Changing a name has a cost,
  so this is for the owner to weigh, not a defect.

**A point made more than once.**

- `capture-intent:72-83` (the map) and `:141-167` (the template's headings) list the same seven things. Line 77
  and line 152 are the same sentence.
- "A decision of yours is marked as yours" is at lines 33, 52-53, 97, 113-114, 149, 175 and 184. Lines 97,
  113-114 and 149 state the same rule in the same sense.
- "Nothing is planned before approval" is at lines 21, 27 and 179-180.
- `domain-language:47-49` and `:87-89` both list "two names for one thing" and "one name for two things".
  Finished condition 3 and step 4 both describe the steps.

**The story of how the skill was made, inside the skill.** `capture-intent:28-29` and `:60-62` are test
statistics from another library, in sentences longer than the rules they support, and both are only partly
right (finding 7). `domain-language:36` is a claim about where the rules came from. The standard asks for a
reason in one clause (`skill-creator/SKILL.md:101-103`, `:124`). The anecdotes that do earn their place are
listed in the last section.

"A script is not an agent" is kept throughout both skills and both new README sections. I found no sentence
written in fragments outside the tables and the templates, where that form is right.

### 17. Lines a capable reader does not need

- `capture-intent:68`, "let each answer shape the next question".
- `capture-intent:43-44`, "in your own words, in a paragraph". A format rule with no reason given.
- `domain-language:80`, "more than about fifteen entries". A number with no source in the notes, for a layout
  choice the reader would make unprompted. Lines 138-139 give a second heading scheme that can collide with it.
- `domain-language:97`, "offer two or three others".
- `domain-language:87-89`, the five kinds of clash. They restate the rules above them.

These are small. Removing them is worth doing only when the larger changes are made.

### 18. Smaller disagreements between files

- `capture-intent:126-127` describes an entry as a name, a meaning and the names to avoid. `domain-language`
  adds `Not`, `Stored as` and the `Proposed` line. A lead that follows `capture-intent` alone in an existing
  project lists `booking` under names to avoid and records nowhere that the code stores it. Confirmed.
- The settings line that names the project brief is labelled `Purpose:`. That is a stored name beside a clearer
  one, and `capture-intent` never gives it.
- The script's record file keeps the tasks given to planners under `briefs` (`agent_loop.py:4396-4399`), and
  the design reviewer's prompt uses that word. "Brief" now names two things in the set.
- `plan-module` does not tell a planner to take `Builders:`, `Integrate:` and `Owner decides` from the brief's
  "How the owner wants to work". That is the only reason the brief collects them (`README.md:71-73`).
- An answer of "I don't mind" becomes "Still open: the planner chooses" (`capture-intent:96`). It then comes
  back to the owner as an `Assumption:` line in the report (`plan-module:23-24`, `build:326-327`). The owner is
  asked to look again at something they said they did not mind about.
- `domain-language:97-98` writes each entry as soon as its name is agreed. Survey B line 426 says that this
  timing is where the source library's file turned into a running plan. The rule "names and nothing else" is
  the guard. The workbench README does not record that the risk was seen and accepted.

---

## Good enough to leave alone

**In `capture-intent`:**

- Lines 8-15: who the reader is talking to, why the brief matters, and the two test-run stories. Both stories
  match the run records.
- Lines 51-53: the two-part test for asking, and "ask first about what would be expensive to undo".
- Line 40: "Looking facts up is your job. The owner's job is the decisions."
- Lines 64-66: choices, each with its cost and a recommendation. The research measured this (8 of 8).
- Lines 85-87: leave how it is built to the planner unless the owner shows they care.
- Lines 89-97: the table of three answers. It is the skill's own idea, it is clear, and `plan-module` reads it
  consistently. Only the report noise in finding 18 touches it.
- Lines 99-108: what talk cannot settle, and a request that is several projects.
- Lines 112-114: quote the words that carry a number, an order, a limit or a "never".
- The brief template as a whole, and the rule to put the brief in the chat because the owner will not open a
  file.
- The `plan` command at line 196. It matches `build/SKILL.md:43`. The claim that `adopt` merges any file in the
  plans folder is true (`agent_loop.py`, function `adoptable`).

**In `domain-language`:**

- Lines 8-15: the definition and the reason. The "claimed", `pending_review`, "ready for review" example does
  its job.
- Lines 30-32: fit the work to the project. This is the small-request path that `capture-intent` lacks.
- Lines 38-54: the seven rules for choosing a name, with the owner's examples.
- Lines 56-74: the entry format, and the reason for the `Proposed` line.
- Lines 76-78: names and nothing else. Supported by the notes.
- Finished condition 3 and step 4: the steps test. It is the best idea in the skill.
- Lines 100-102: say so when the owner's word disagrees with the glossary.
- Lines 104-113: stored names stay, apart from the one gap about identifiers in finding 8.
- Lines 119-121: add the entry as proposed, name it in the report, and do not stop to ask. This is right for an
  unattended build.
- Lines 138-139: one glossary.

**In the README:**

- Steps 1 to 5 under "Saying what you want" match the skills.
- The plain statements of what has not been measured (lines 247-248 and 272-274). Keep them.
- The paragraph at lines 256-261 on the set's own vocabulary.

**In the test cases:**

- The owner pages. They answer only what is asked, they hold hidden facts, and they are told to let the agent
  build early.
- `vague-new-product` checks 01, 05, 07, 09 and 10.
- `existing-project-new-feature` checks 02, 03 and 05.
- `tangled-terms` checks 02, 03, 04, 06, 07 and 09.
- `new-name-mid-task` checks 03, 04 and 06.

---

## What I did not check

- Whether either description loads in a real session. That needs the loading test.
- How a real runner treats `focus: output` and `owner.md`.
- What any live project's `ORCHESTRATE.md` holds.
- The libraries themselves. Every claim was checked against the two research notes only.
- Whether the script rejects a builder's change to `GLOSSARY.md`. A search of `agent_loop.py` found checks on
  the done-when file only, so I believe it does not, but I did not trace the whole path.
