# Audit: what the skills teach a capable model that it already knows

Scope: every agent-facing file in `skills/orchestration/` (the four skills, their stages, tasks, references and
prompts) and the prompt strings in `lead/scripts/agent_loop.py` (`GOAL_LINE`, `scope_text`, `resources_rule`,
`session_rule`, `needs_rules`, `handoff_note`, `checks_note`, `binding`, `CLAUDE_TURN_NOTE`, `SCRIPT_SETS_STATE`).
`README.md` and `GLOSSARY.md` are written for people, where rationale and history are the point ("Why it is built
this way", "Our own practice"); I checked them and left them out of the findings.

Line numbers are as on disk on 2026-11-22. "Cut to" gives the replacement clause. Facts about the set (stored
names, rules the script enforces, the user's decisions) are kept even where short; only general knowledge,
over-explanation, history and within-file repeats are listed.

Ranked by size of win. Groups first, where one fix covers several passages.

---

## Group A. The same point repeated across files and inside one prompt (biggest win)

These are not general knowledge, but the brief's "same point made twice" applies with force because several of them
land in **one agent's context twice**: the planner and reviewer prompts inline their `tasks/<kind>.md` file
(`kind_text`, agent_loop.py:627), and the builder prompt carries `needs_rules` and `resources_rule` beside a skill
that says the same.

A1. **The reviewer is told twice in one prompt that the script already ran the checks.**
- `checks_note` (agent_loop.py:7918): "Before it set Ready for Review, the script made sure that ... passed ... Run
  one again only if you doubt that result."
- `reviewer/tasks/milestone.md:34-36`, inlined in the same prompt: "The script ran every check on the commit your
  prompt names, and you can rely on that result, so run a check again only when you have a reason to doubt it".
- `reviewer/tasks/milestone.md:3-4` says it a third time: "The script then ran the project's test command and every
  item's check on the merged work".
- Fix: keep `checks_note` (it names the commit and the commands). Cut milestone.md:34-36 to "For a `check`, judge
  whether the command tests what the item says, because a check a fake would pass proves nothing." Cut
  milestone.md:3-5 to "A builder merged the milestone; the script's checks passed on it, and nobody has judged it
  yet. You are in a clean checkout of the commit you are judging."

A2. **The builder gets the `needs` rules twice.** `needs_rules` (agent_loop.py:7135) puts one rule per needed kind
into the prompt, naming the items, and `builder/SKILL.md:94-109` describes the same three kinds and endings at
length. Fix: the prompt is per-milestone and exact, so keep it; cut SKILL.md:94-109 to "Items with a `needs` field
(`human_feedback`, `access`, `hardware`) need the user or a device. Do every other item first; your prompt says how
to end for each. When the user turns down every option and their words don't say what to change, end with `BLOCKED:
the user turned down every option` and their words." (The last sentence is the only part the prompt lacks.)

A3. **"A lock keeps out only runs that take it, so it doesn't make the machine quiet for a timing" appears six
times**: `builder/SKILL.md:187-188`, `resources_rule` (agent_loop.py:7075-7076), `lead/references/locks.md:14-15`,
`planner/references/done-when.md:225` and `:252`, `planner/references/proofs.md:111-113`. Within proofs.md it is also
said at 62-66 and again at 111-113. Fix: keep it once per reader: in `resources_rule` for builders (delete from
builder SKILL.md:187-188), in done-when.md's `lock` field for planners (delete :252's "because a lock keeps out only
the runs that take it" and proofs.md:111-113), and in locks.md for the lead.

A4. **Status stale-ness rationale ("status written anywhere else goes stale") appears five times**: `lead/SKILL.md:93-94`,
`builder/SKILL.md:63-64`, `planner/references/done-when.md:63-64` and again `:103-105` (within-file repeat),
`planner/references/profile.md:109-110`. Fix: keep the rule in each, drop the reason everywhere but done-when.md:63-64.
- lead/SKILL.md:93-94 cut to "Where the work stands belongs on the status page and nowhere else."
- done-when.md:103-105 cut to "It holds no status lines; the script writes them to `STATUS.md`."
- profile.md:109-110 cut to "This file holds settings, not progress."
- builder/SKILL.md:63-64 cut to "Leave status out of the plan files."

A5. **The look-options plan (two milestones, minimum bar, pick saved to `References:`) is written out in full twice
in the planner's own material**: `planner/SKILL.md:124-134` and `planner/references/proofs.md:162-173`, plus the
options bar again at proofs.md:180-182 and `reviewer/tasks/design.md:21-22`. The "rough playable version ... because
a bad answer at the end would reopen finished modules" sentence is near-verbatim in `planner/SKILL.md:147-150` and
`proofs.md:184-187`. Fix: keep the full version in proofs.md (it is the reference); cut SKILL.md:124-134 to "When the
look is the product, plan a set of options for the user to pick from before builders commit to a direction, as
[subjective work](references/proofs.md#subjective-work) describes." Delete SKILL.md:147-150's second half ("Where the
whole product turns on ...") and leave it in proofs.md.

A6. **"Evidence stays out of git because captures would grow the repository"**: `lead/references/cleanup.md:7-9`,
`lead/references/older-projects.md:19-20`, `planner/references/done-when.md:47-50`. Fix: delete the reason in all
three; the fact (working folder, uncommitted, shared by worktrees) stays.
- cleanup.md:7-9 cut to "Everything the build makes outside git lives in the repository's `.git` folder:"
- older-projects.md:18-21 cut to "Before 2.6.0 the script committed evidence under the `Evidence:` folder
  (`docs/evidence` by default). Every command refuses such a project until `migrate` has run."
- done-when.md:47-50 cut to "Evidence is never committed. The `Evidence:` path opens in every worktree onto one
  working folder in `.git`, and stays until the user runs `cleanup`."

A7. **Context economics (one long wait, not many short looks; read log tails; a few frames)** in both
`builder/SKILL.md:207-209` and `reviewer/SKILL.md:77-81`. This is general agent practice that current models follow.
Fix, both files: cut to "Start a command that may outlast your turn with `background -- <command>` and wait with
`wait <id>`, which returns when it ends or after nine minutes." Delete "Each time you look at a job, your whole session
is read again ... rather than the video" and "Everything you look at stays in your session ... One long wait costs
far less than many short looks with `sleep` and `tail`."

A8. **"A builder may not set Ready for Review / Done, because other builders rebase onto main and would take it as
checked"**: `builder/SKILL.md:59-60` and `planner/references/done-when.md:379-381`, plus `SCRIPT_SETS_STATE`. `merge`
refuses it, so the reason is not needed. Fix: builder SKILL.md:58-60 cut to "...prints `MERGED`, and the milestone's
`status` is still `in_progress`; `merge` refuses a commit that sets Ready for Review or Done." Delete done-when.md:379-381
(the table row at :361-362 already says the script sets them).

A9. **Cross-host review rationale ("a reviewer from another company shares fewer of the builder's blind spots")** in
`lead/stages/4-build.md:175-176` and `planner/references/profile.md:100-101`. Keep one (profile.md, where the line is
written); cut 4-build.md:175-176 to "When the user works with two hosts, run each review on the host that didn't
build the milestone."

A10. **File tree of the plans folder** in `planner/SKILL.md:21-34`, `planner/references/done-when.md:25-41`,
`lead/SKILL.md:76-80` and `planner/tasks/module.md:6-7` (inlined in the planner's prompt after the skill). Fix:
delete module.md:6-7's file list (keep "Builders and reviewers act on the design and the notes in the plan file, so
write them the way the `prompting-agents` skill describes"); keep the tree in SKILL.md and drop the one in
done-when.md:25-41 in favour of a link, or the reverse. (A `paths` command, if another auditor proposes one, would
replace all four.)

---

## Group B. General git, shell and tool knowledge

B1. `lead/stages/4-build.md:37-41`, "A worktree is a second working copy of the repository, so two builders can
work at once. If the repository ignores no folder, add one to `.git/info/exclude`." and the full `git worktree add`
line. Explains what a worktree is and how to make one. **Delete** the definition and the exclude sentence. Cut the
paragraph to: "Give each module its own worktree on branch `build/<module>`, in a folder git ignores, branched from
`<remote>/<branch>` under `Merge: push` or the local main branch under `Merge: local`." (The script has no command
that makes worktrees: no `worktree add` call in agent_loop.py; if another auditor moves this into the script, the
whole paragraph goes.)

B2. `lead/SKILL.md:89-91`, "Undoing a commit that broke the main branch is a new commit, made with `git revert`,
which keeps them." and `lead/references/locks.md:49-50`, "A revert is `git revert <commit>` on the main branch,
merged as any other commit, so the history the records name stays." Two explanations of what a revert is. Cut
SKILL.md to "...without rewriting or dropping any, because the record names the commits it checked; undo one with
`git revert`." Cut locks.md:49-50 to "Revert with `git revert <commit>` on the main branch." (Keep the rest of
locks.md:50-53: tell the builder, `human rereview`, `main-check --start`; those are set facts.)

B3. `builder/SKILL.md:237-238`, "A force-push would replace history the other worktrees rest on." Explains
force-push. **Delete.** Keep "Bring work in only with `merge`, which adds your commits on top."

B4. `lead/references/older-projects.md:38-39`, "Rewriting history gives every commit a new hash, while the records
and the run state still name the old ones, so a review ... comes back INVALID." Explains that a rewrite changes
hashes. Cut to "After rewriting history, straight away and with every run still stopped, run `migrate --commit-map
<map> --worktree <repo>` (the rewrite's `old new` list, such as `.git/filter-repo/commit-map`), so the records name
the new hashes."

B5. `lead/references/older-projects.md:46-47`, "A rebase by hand conflicts in the files the renames rewrote, and
those conflicts are easy to resolve wrongly." Cut to "Rather than rebasing by hand, run `migrate --branch --worktree
<its worktree>`..."

B6. `lead/SKILL.md:60-63`, "Words added without a flag, or brackets left unquoted, are read by the shell, and zsh
stops on them before the script starts." Shell quoting. **Delete**; "in single quotes" in the sentence before
already carries it.

B7. `builder/SKILL.md:230-231`, "Edit files with the `apply_patch` tool, which fails when the text it expects isn't
there. A script that replaces text, such as Python's `str.replace`, changes nothing and says nothing in that case."
Cut to "Edit files with `apply_patch` rather than a script that replaces text, which fails silently."

B8. `lead/SKILL.md:40-41`, "Don't send them to `/dev/null` or cut them with `tail`, because a refused command line
looks like success when its error is thrown away." Cut to "Let the output and the exit status reach you, uncut." And
delete :42-43's "A file that still says `RUNNING` after its process has gone was stopped before it finished." (an
inference any model makes).

B9. `lead/stages/4-build.md:274-275`, "On macOS, a first screen recording or camera use fails until they grant the
permission to the app you run in." General macOS behaviour. **Delete.**

B10. `planner/references/profile.md:84-86`, "which is why `npm ci` is better here than `npm install`." General npm
knowledge. Cut to "It should install into ignored folders and leave tracked files as they were, such as `npm ci`."

B11. `planner/references/profile.md:118-119`, "because Claude Code can't run a GPT model and Codex can't run a Claude
one". Obvious. Cut to "A model belongs to one host, so a line that names a model names the host first:".

B12. `lead/stages/4-build.md:283-284`, "Stopping processes by matching their names stops every builder that matches,
with its unsaved work." Cut to a clause on the sentence before: "...stops the running sessions cleanly (rather than
killing processes by name)".

---

## Group C. General testing, debugging, review and design practice

C1. `builder/SKILL.md:211-218`, "When a behaviour won't come": "Find out how shipped products and published work do
it, and build the smallest reproduction ... A result you can't explain, such as a test that fails on one machine, is
a problem to find and fix, not a reason to stop." General debugging practice. Cut the section to: "If the mechanism
can't produce the behaviour, end with `BLOCKED` and what you found. If fixing something needs a fact or choice only
the user has, end with `NEEDS_CONTEXT:` and the question." (The two endings are set facts; the rest goes.)

C2. `planner/SKILL.md:96-98`, "such as a unit, integration or end-to-end test, a property test, or a comparison with
a known-good output. Hold it to good testing practice: exact expected values, the edge cases the design names, and
the same result on every run." General testing practice. Cut to "A `check`, for objective outcomes: a command that
passes or fails, covering the edge cases the design names."

C3. `reviewer/tasks/milestone.md:54-57`, "hard-coded return values, canned data, buttons that do nothing, feature
flags that default to on, branches that run only under test, tests weakened or deleted, silenced warnings, and
output files committed instead of computed." A code-review list the model knows. Cut to "Read every changed line of
the milestone, and on a module's last milestone the whole module, for signs of work that only looks finished, such
as stubs, canned data or weakened tests. Report an item too weak to catch a fake as a finding too."

C4. `reviewer/SKILL.md:62-66`, "Lead with what isn't true yet, then give what shows it: what you did, what happened,
what should have happened, and where, as a file and line, the steps, or a screenshot ... If an item says a workspace
can be renamed, and you found the old name in the switcher but never opened the sidebar, the reader needs both
facts." Standard bug-report form, plus an example. Cut to "Write each finding for an agent who saw none of your
session: what isn't true yet, how to see it, and what you tried and left untried." Delete the workspace example.

C5. `reviewer/tasks/milestone.md:29-30`, "If you have seen something work only on the easy path, you don't know yet
that it works." Restates the sentence before. **Delete.**

C6. `planner/tasks/project.md:29-33`, thin slice: "The slice shows that the modules fit together before any of them
is built out, and gives the user something to try early. After it, build first what is riskiest and what most other
work depends on, because that is what is most likely to force everything else to change." Walking-skeleton and
risk-first ordering are standard. Cut to "Plan the first milestones as a thin slice through the whole product: the
smallest thing an end user could do from start to finish, such as importing one statement and printing one balance;
each module on that path makes its part of the slice its first milestone. Then build the riskiest and most
depended-on work first."

C7. `planner/tasks/project.md:24-25`, "because most bugs between modules come from two of them changing the same
thing". Cut to "Draw the lines between modules around state, so each kind of state has one module in charge of it."

C8. `planner/tasks/project.md:36-37`, "because builders who each create it at once produce merges that conflict".
Obvious. **Delete the clause.**

C9. `planner/tasks/module.md:16-18`, "Most problems have been solved before, in shipped products or published work,
so find out how before you invent a mechanism, and prefer current practice." General. Cut to "Base each mechanism
on current practice, and check it can produce its behaviour across the whole range before anyone builds on it."

C10. `planner/references/proofs.md:122-123`, "because a reader without a list looks at whatever catches its eye,
decides it looks fine, and misses the broken parts." Also said in `planner/SKILL.md:120-121`. Cut proofs.md to "Work
down it." and SKILL.md:120-121 to "The `inspect` text is a checklist for the reviewer."

C11. `planner/references/proofs.md:125-130`, "A 3D model needs a few angles. An image needs close crops ... Every view
hides something: a bow wave can look right from the side and cut through the hull from the front, and a cloud can look
fine as a thumbnail and turn into bands when you zoom in." Over-explanation, and the table at :42-46 in the same file
already gives the views per kind. Cut to "Look at each entry in the views and conditions it needs (the table under
[kinds to start from](#kinds-to-start-from)), with crops at full resolution rather than a scaled copy, and the
reference beside the work for each line."

C12. `planner/references/proofs.md:137-138`, "Golden screenshots catch a regression, but they don't prove that
something looks right." General. **Delete.**

C13. `planner/references/proofs.md:78-81`, "So for each proof, weigh four things: what it would catch, how likely
that fault is here, what the fault would cost if it were caught later instead, and what the proof costs now..."
Generic cost-benefit. Cut to "Weigh each proof's catch against its cost in time and queueing. When a project has
history, its past reviews show which proofs found real faults, often code reading or a quick CPU test."

C14. `planner/references/proofs.md:72-76`, "Branches that arrive together are merged as one batch ... A test command
that takes fifteen minutes allows about four, shared by every builder, and a failure costs more runs, because the
script splits the batch in halves until it finds the branch that broke it." Worked arithmetic. Cut to "The test
command's length caps how many merge batches an hour the whole project gets, and a failing batch costs extra runs."

C15. `builder/SKILL.md:253-254`, "add a test if one would catch the fault coming back". General practice. **Delete
the clause.**

C16. `lead/stages/1-interview.md:46-52`, the four ways a brief falls short (contradiction, rule with a gap, worry
with no measure, missing size), each with an example. Requirements-analysis basics. Cut to one line: "A brief can
hold everything the user said and still fall short: a contradiction, a rule with a gap, a worry with no measure, or no
size." (Or keep one example, the "archive inactive accounts" one, as the most useful.)

C17. `lead/stages/1-interview.md:97-99`, "Run a pre-mortem: ask the user to imagine the first release has
disappointed them, and say why." Explains a pre-mortem. Cut to "Run a pre-mortem. Its answers are how the user will
judge the result: pin each to a number a check can test or a shipped example an inspection can use."

C18. `reviewer/tasks/design.md:25-27`, the five naming faults (two names for one thing, one name for two things ...).
That is the domain-language skill's content. Cut to "Then check the design's names against the glossary, as the
`domain-language` skill describes, because a design is where a new concept first gets a name."

---

## Group D. Long rationale where a clause would do, and within-file repeats

D1. `lead/stages/4-build.md:97-106` (Reading delivery). "Busy builders aren't the same as a build that is moving ...
Only you see every session at once" restates lead/SKILL.md:18-19, and the worked example "Ten builders finishing two
milestones a day between them, while the main branch takes three hundred commits, means most of the effort is going
somewhere other than the milestones." over-explains. Then :109-110 "Each builder is doing what the process asks, so
clearing them one at a time won't reach it" says :97-99 again. Cut :97-106 to "Milestones reaching Ready for Review
and Done measure delivery; commits, jobs and turns measure effort. `flow --worktree <repo>` puts the two side by side
for the last day, or `--since <hours>`; read them against the number of builders. For the longer view, read the
[delivery history](../references/delivery-history.md)." Delete :109-110's middle sentence.

D2. `lead/stages/4-build.md:331`, "The user is often away, for hours when they're asleep or travelling, and each
question costs their attention." Said at :317-319 in the same section, and in lead/SKILL.md:21. Cut to "The user is
often away, so:".

D3. `lead/stages/1-interview.md:36-38`, "Every hole in the brief is a risk. The planner has to work around it ... A
few of them, carried through every module and milestone, are enough for the project to drift and build the wrong
thing, well and on time." Repeats :21-22 of the same file. **Delete** the paragraph (or cut to "Each hole becomes a
choice the user didn't make.").

D4. `lead/stages/3-before-first-build.md:13-16`, three rationales in a row ("A reference sets how good subjective
work has to be ... The first plan names most of the project's concepts ... No design has been reviewed yet, so a
correction now costs one planner turn and no review."). Cut to "The user should agree these now, before builders aim
at a reference and names spread into code, while a correction costs one planner turn and no review."

D5. `lead/stages/3-before-first-build.md:25-26`, "A build runs for days, and the more a session holds, the sooner and
more often it is compacted." Explains compaction. Cut to "This is also the moment to make room for the build, which
runs for days."

D6. `lead/stages/4-build.md:55-57`, "Your host wakes you when a background command ends, so one command per module
wakes you for each stop as it happens, while a chain wakes you only when its last command ends." Cut to "Start each
`run` and `plan` as its own background command, not a chain, so each stop wakes you."

D7. `lead/stages/4-build.md:267-268`, "Every worktree keeps its own build outputs, so a long build can fill the disk."
Cut to "Clear build outputs in worktrees nothing is using."

D8. `planner/SKILL.md:84-89`, the "Each level of the plan settles its own choices" table restates the prose at
:69-80 just above it (mechanisms for the design, details for the builder). Keep one: the table is the shorter;
cut :77-80 to "A detail is anything that could change without changing what the user gets, such as a file name or a
data layout. Leave details to the builder."

D9. `planner/references/done-when.md:143-145`, "What must be true is in the done-when file and how the module works
is in the design, so a list of steps would say both again, in an order chosen before the code existed. The builder
sees the code close up and plans the work better from there." Same point in `planner/SKILL.md:79-80` and
`planner/tasks/module.md:43-44`. Cut done-when.md:143-145 to "The note is written in sentences, with no list of
steps."

D10. `planner/references/done-when.md:22-23`, "Every project keeps its plans in the same place, so the user and every
agent can always find them." **Delete.**

D11. `lead/references/locks.md:17-19`, "so one stuck run can't keep everyone else waiting" and "because a run stopped
part way would fail every merge and look like a broken main branch" (the second also in proofs.md:71-72). Cut to "A
command that holds a lock longer than the settings' `Lock hold limit` (30 minutes by default) is stopped; the test
command keeps its own one-hour limit."

D12. `lead/references/locks.md:22-24`, "A lock that is busy most of the day, with hours queued against it, is a limit
that more builders make worse. Its failed holds cost the most, because nobody else could use the time they took."
Cut to "A lock busy most of the day, with hours queued, is a bottleneck more builders make worse."

D13. `lead/references/locks.md:32-33`, "The other modules carry on meanwhile, which is the point of running the
check after the merge." **Delete.** And :46-47 "because the lead doesn't read or judge code" repeats lead/SKILL.md:23;
**delete the clause.**

D14. `lead/references/delivery-history.md:16-23`. "Claude Code deletes its session files after 30 days, and Codex
moves or archives its own." and "It lives outside the hosts' folders and outside the clone, so deleting either leaves
it in place." are background the lead doesn't act on. Cut the paragraph to "After every turn the script copies that
session's figures (tokens, model, effort, time, context, tool calls, compactions, how it ended; never what was said)
into `~/.orchestrate/history/<repository>-<hash>/`, or `$ORCHESTRATE_HISTORY_DIR`, with a copy of each merged review
under `reviews/<MODULE>/`." Also delete :8-9 "Turns from different projects and milestones differ, so read a
version's figures beside its turn count." (general data reading).

D15. `lead/references/delivery-history.md:43-51` (Measuring cost). "because cache reads make up nearly all of a raw
count and cost little" and the multipliers are detail the lead never computes; the history labels each figure. Cut
to "The history keeps three measures and labels each: weighted tokens (compare Claude with Codex), Codex's share of
the weekly limit, and Claude's list price (not charged on a plan)."

D16. `lead/references/report.md:42-43`, "because a long report hides the one line that matters". General writing
advice. **Delete the clause.** Same for `lead/stages/4-build.md:389-390` "A message for every result buries the one
decision they need to see." (cut to nothing; the preceding sentence carries the rule).

D17. `builder/SKILL.md:119-124` (What you write). "Write them in whole sentences" is general; "Say which things you
confirmed by running something and which you only suspect" is the third time in the file (also :62 "what you
verified kept apart from what you think is probably true" and :78 "what you confirmed and what you only suspect").
Cut the section to "The lead reads your last line, your handoff and your log entry. Name an item by its ID and a few
words, such as "M2.5, the window resize recording", and a module by its name in the plans. What other builders should
do is the lead's to decide." and keep the confirmed/suspected point only at :62.

D18. `builder/SKILL.md:77-79`, handoff contents "say what is finished and on which commit, what you tried and ruled
out, what you confirmed and what you only suspect, and what to do first". General handoff practice. Cut to "Whoever
picks the milestone up has seen none of your session, so write it for them."

D19. `builder/SKILL.md:165-168`, batch merge mechanics: "If that run fails, the script splits the batch to find the
branch that broke it and merges the rest". Cut to "When several builders merge at once, `merge` batches them with one
test run, so it can take a while; `batch` says which branches merged with yours."

D20. `builder/SKILL.md:185-188`, lock capacity explanation beside the prompt's `resources_rule`, which says the same
with the project's real names and counts. Cut :183-188 to "Wrap a command that uses a resource your prompt lists in
`lock <name> -- <command>`, and keep `<name>.alone` commands short."

D21. `builder/prompts/findings.md:3`, "A review describes what one reviewer happened to try. Where it says an item
failed, it shows one thing that makes the item's statement untrue, and there may be others like it the reviewer never
reached. The next review is done by a new reviewer, who starts again from the items." Three sentences for one point,
also in done-when.md:404-406. Cut to "Each failed item in the review is one counter-example; there may be others, and
the next reviewer starts again from the items."

D22. `planner/references/profile.md:149`, "A larger model or a higher effort spends the user's quota faster."
**Delete.**

D23. `lead/SKILL.md:12-13`, "because fast work that has to be redone isn't fast" and `lead/SKILL.md:117-118`, "because
the script won't guess whether it may push or which command runs the tests" (also in profile.md:11-13). Delete both
clauses; low value, short.

---

## Group E. History and stories

E1. `lead/references/older-projects.md:50-66` ("The names that changed in 2.2"): the full list of renamed stored
names, the pre-2.2 re-plan rule, and the `owner` -> `human` alias. `migrate` does all the renames itself, and the
old command still works. Cut the section to "`migrate` renames the stored names and settings labels from before 2.2.
Older plans that say "the owner" need no change." Delete :58-63.

E2. `lead/references/older-projects.md:68-78` ("Ready for Review set by a builder", "A report a day"): history. Cut
each to its action: "A milestone set Ready for Review by a builder before 2.1.0 shows as `can_start`; follow the
`next` its `review` prints." and "Daily reports from before 2.4 under `<evidence>/build-reports/` need nothing;
`report` replaces them."

E3. `lead/SKILL.md:99-100`, "A note that says otherwise is from an older version of this set." History; delete if no
older notes are still in circulation (low).

E4. The script's prompt-string docstrings carry Thrum stories (`resources_rule`, `session_rule`, `checks_note`,
`resume_facts`, `stale_session`, `CLAUDE_TURN_NOTE`), but they are code comments, not text sent to agents, so they
cost no agent context. No change.

---

## What I checked and left alone

- Prompt templates `builder/prompts/build.md`, `reviewer/prompts/review.md`, `reviewer/prompts/design-review.md`,
  `planner/prompts/plan.md`, `GOAL_LINE`, `session_rule`, `handoff_note`, `binding`, `CLAUDE_TURN_NOTE`: lean, set
  facts only. `scope_text` (agent_loop.py:591) is long but every clause is a rule the script enforces.
- `reviewer/references/graded-examples.md`: worked examples are its purpose.
- `planner/tasks/diagnose.md`, `fix.md`, `change.md`, `unblock.md`, `revise.md`: set-specific throughout.
- `lead/stages/1-interview.md:76-84` (the Q2 example) and `:122-153` (the brief template): format the model can't
  guess.
- `planner/tasks/project.md:60-61` (`pytest || [ $? -eq 5 ]`): a specific fix worth keeping.
- `planner/references/proofs.md:35-48` (the kinds table): its "too weak if" column is partly general testing
  knowledge, but it is compact and doubles as the inspection views list; keep.

## CLI changes these findings depend on

None. Every finding is a deletion or a cut in prose. B1 shrinks further, to nothing, if another audit moves worktree
creation into the script, and A10 disappears if a `paths` command is added.
