# What the orchestrate agents write for each other

This review asks where text that one orchestrate agent wrote for the next cost that next agent something, and
what in the skills caused that text or failed to prevent it. It also asks where the skills fence in an agent for
no reason.

The costliest problem is the handoff. When a builder stops without finishing, everything the next agent needs
has to fit in the builder's last line. That line is capped at 500 characters when it is stored, and it usually
links to notes inside the builder's own working copy, where nobody else can read them. The planner or the new
builder then has to find those notes again, or the lead has to dig them out by hand. The second problem is that
the build skill tells the lead to pass on "nothing of your own". In practice the lead's own facts were the most
useful text in the whole set, and the one time it passed only a builder's line and a path, the path pointed
at nothing. The third problem is that builders state what they suspect as if it were fact. Their last lines
also claim proof for a commit the proof wasn't made on. Each of these cost at least one wasted session turn or one
failed review round that I could see in the records.

The first change I would make is a handoff file at a fixed path. A builder that stops without `DONE` writes
the file, the script merges it to the main branch even though the code isn't merged, and the script passes the
file's path to whoever starts next. The details are under problem 1.

## What I read

- The skills at `HEAD` (`6989342`, orchestrate 1.7.1), read with `git show`: `build/SKILL.md`,
  `build-milestone/SKILL.md`, `review-milestone/SKILL.md`, `plan-module/SKILL.md`, and
  `plan-module/references/done-when.md`. I also read `build/scripts/agent_loop.py` at `HEAD` wherever a skill
  depends on what the script does with an agent's text.
- The prompting-agents skill and its references `writing-style.md`, `kinds.md` and `models/gpt-6.md`.
- All 56 session transcripts in `workbench/agent-communication/thrum-prompts/`. I read every lead-written
  message and every last reply, and skipped the repeated Codex goal text, which the host adds and no skill
  writes.
- In Thrum, a copy of `origin/main` at `cff3ed74` for `docs/plans/` and `docs/evidence/`. I read the plans, logs
  and done-when files of APPLE-TILE, ATMOSPHERE, CREATOR and PLATFORM-RUNTIME-MAC, four design headers, three
  reviews, one builder evidence page, and one handoff note in a builder's worktree. I did not read `tmp/` beyond
  that handoff note.

The sessions ran on orchestrate 1.4.0 to 1.7.1, so some of what they show has already been fixed at `HEAD`. I
say so wherever that applies. "Observed" below means I saw the text and the cost in the records. "Suspected"
means I saw the text but could only infer the cost.

## 1. The handoff has no place of its own

**What was written.** Four examples, from four modules:

- An ATMOSPHERE M5 builder (Codex) ended its session with "BLOCKED: H2 fails its Metal precision bound. Current
  main retains the design instruction requiring a planner decision on this measured miss. [Evidence]
  (/Users/ryannel/Workspace/thrum/.claude/worktrees/atmosphere/docs/evidence/ATMOSPHERE/m5-h2-blocker.md)". It
  had also written "Partial work is saved in local commit `7911c75b`", without naming a branch.
- The lead passed that line on to the planner almost word for word: "Unblock ATMOSPHERE M5: H2 fails its Metal
  precision bound. Current main retains the design instruction requiring a planner decision on this measured
  miss. Evidence: docs/evidence/ATMOSPHERE/m5-h2-blocker.md".
- An APPLE-PRESENTATION M1 builder linked "[Evidence and resume steps](docs/evidence/APPLE-PRESENTATION/m1/BLOCKED.md)"
  twice.
- An APPLE-TILE M2 builder linked "[attended handoff](/Users/ryannel/Workspace/thrum/.claude/worktrees/apple-tile-m0/tmp/g3t-m2/attended/HANDOFF.md)".

**What it cost (observed).**

- The ATMOSPHERE planner runs in the script's own checkout of the main branch, so the path it was given did not
  exist there. Its report says: "The builder's blocker note and logs exist only in WIP commit `7911c75b` on
  `build/atmosphere`, not on main." It found the commit and did the work, but it had to rediscover where the
  evidence was first.
- The next ATMOSPHERE builder could only pick up the earlier work because the lead wrote it a message:
  "A previous builder session's M5 work is in commit 7911c75b on branch wip/atmosphere-m5; this worktree is at
  main. Bring that work in (cherry-pick it; .config/architecture.toml and Cargo.lock conflict with main and
  need merging)". Without that message, a 380,000-token session would have been redone or lost.
- In COOKED-DRAW, the lead had to send the planner into a builder's worktree: "The builder's blocked checkpoint
  9c230ff4 (local in /Users/ryannel/Workspace/thrum/.claude/worktrees/cooked-draw; ...)", and in a second task
  "on the builder's local checkpoint b0dae34c (branch-less, in .claude/worktrees/cooked-draw; read it with git
  show)".
- `APPLE-PRESENTATION/m1/BLOCKED.md` was never committed. `git log --all` has no record of it, and it is gone
  from the worktree now. Whatever resume steps it held are lost.
- The APPLE-TILE handoff note worked, but only because the lead found it from the link and wrote it into the
  new session's brief: "read tmp/g3t-m2/attended/HANDOFF.md first and don't redo them". The note is in `tmp/`,
  which git ignores, so it survives only as long as that worktree does.
- The APPLE-TILE M0 reviewer raised the same risk for proof: "the 481-frame Chrome baseline that M1 needs, and
  the 2.4 GB of capture sources, exist only in the builder's worktree ... Removing that worktree would lose
  them."

Builders don't agree on what to do with work they haven't finished. One T2-CAPTURE builder merged its blocker
evidence ("Integrated blocker evidence in `e6cb0425`"). The ATMOSPHERE and COOKED-DRAW builders kept theirs in
local commits.

**What in the skills led to it.** `build-milestone` gives a stopped builder one channel, its last line:
"`BLOCKED: <what you tried, the evidence, and what would unblock it>`". The log entry and the evidence folder
reach the main branch only through `land`, which a blocked builder has no finished work to run. The script then
stores the last line, cut to 500 characters, as the milestone's `blocked` field (`record_block` in
`agent_loop.py`), and shows the lead the last 1,500 characters of the builder's reply. The skill never says
where unfinished work and its notes should be, and the script has no idea of a handoff at all: a `--fresh`
session gets "only the files and the review". Every builder in the records worked around this by putting a link
in its last line, and every link pointed into a worktree.

**The fix.** Give the handoff a fixed place, and make the script carry it.

- A builder that ends with anything other than `DONE` writes `docs/evidence/<MODULE>/<milestone>-handoff.md`.
  It holds what is finished and where it is (commit and branch), what was tried and ruled out, what is verified
  and what is only suspected, and what the next agent should do first. Each new handoff replaces the old one,
  because it describes the present; the log keeps the history.
- On `BLOCKED`, `NEEDS_CONTEXT`, `STALLED` or a time-out, the script pushes the builder's branch under a
  predictable name and merges the handoff file the way `adopt` already merges build reports. It then names
  both in the result line.
- The script names the handoff file in the prompt of the next builder session and of any planner it starts for
  that milestone, so the lead no longer has to find it.
- In `build-milestone`, the last line goes back to being a short verdict that names the file:
  "`BLOCKED: <one sentence on what would unblock it>`. The rest is in the handoff file." That also takes the
  pressure off the 500-character cap described under problem 7.

## 2. "Nothing of your own" is the wrong rule for builders and planners

**What the skill says.** `build/SKILL.md`, "What you pass on": "Give a planner, builder or reviewer file paths
and the owner's own words, and nothing of your own. If you add your summary or your opinion, the agent tends to
agree with it, and its work is no longer independent."

**What the lead actually wrote (observed).** The lead broke this rule all the time, and its best messages are
the ones that broke it. Each of these gave the reader a fact it could not have found for itself:

- To a builder that had stopped on a lock: "The GPU lock you met is not nested or stuck. The APPLE-TILE M2
  builder holds it for its own GPU work ... `lock gpu` queues, so wrap your GPU checks and captures in it and
  wait your turn rather than stopping. ... Block only if the lock is held by a process that has made no progress
  for 30 minutes, and name its pid." The builder claimed M1 two turns later.
- To a new APPLE-TILE M2 session: "That session ran headless, so Computer Use couldn't show approval prompts for
  Thrum M2 and IINA. This one runs visibly in the Codex app and the owner is at the Mac to approve them". The
  session finished M2 in 47 minutes.
- To a COOKED-DRAW planner: the measurements, what had been ruled out ("keeping all meshlets doesn't change
  that"), and a guess marked as a guess ("The likely cause is pixel-quad derivatives or ordering at draw
  boundaries, which is unverified").

These are exactly what prompting-agents asks for in a brief: "approaches already tried and ruled out", "which
source is the authoritative one", and claims checked before they are passed on. The one time the lead kept to
the rule, it passed the builder's own line and a path, and that is the ATMOSPHERE task in problem 1, where the
path didn't exist on the main branch.

**Where the lead's own text did cost something (observed).** In PLATFORM-RUNTIME-MAC M2, the lead twice told
the builder "The owner is at the Mac now: it's unlocked". Both times the builder found the console locked and
the panel asleep. The second time it "watched for an unlock for five minutes" before it stopped again. The lead
was passing on a state the owner had reported earlier, without saying when. Its later messages fixed this
themselves: "the lead is holding the display awake with caffeinate, and the owner was at the Mac recently ... If
the console locks or the panel sleeps, block at once."

**What in the skill led to it.** The rule's reason is right for a reviewer, whose value is not having seen how
the work was made. Prompting-agents says the same thing about a review request: "leave out your worries, your
account of why the work is right, and your own conclusion". The build skill applies that reason to builders and
planners too, and they are the ones who need the lead's facts. A capable lead ignores the rule. A careful one
obeys it and starves the next agent.

**The fix.** Rewrite "What you pass on" around the kind of reader:

- For a reviewer, pass only what the review is judged against, and nothing about how the work was made. The
  script already writes this prompt.
- For a builder or a planner, pass what it can't find in the files: where unfinished work is, what has been
  tried, what the owner said and when, and what you know about the machine, such as who holds a lock or whether
  the owner is at the Mac. Mark a guess as a guess. Give a physical state with its time and source ("the owner
  said at 08:37 they were at the Mac"), so the builder checks it before relying on it.
- Keep the existing line that the owner's words go to a planner word for word, but put them in quotation marks
  with the date, apart from the lead's own context. Problem 3 shows why.

The `--owner-rule` mechanism and the "decides: owner" flow are separate from this. They worked, and should stay
as they are.

## 3. Designs quote the lead's words as the owner's

**What was written (observed).** `plan-module` tells the planner: "Quote the owner's request word for word at
the top of the design". Three designs on `main` do that by quoting someone else:

- `CREATOR/DESIGN.md`: "## The owner's request. From the 10 November planning task, word for word: 'The owner
  wants work lined up continuously toward the V1 exit in docs/BUILD-PLAN.md, so builders always have a next
  milestone ...'"
- `ATMOSPHERE/DESIGN.md` quotes the same sentence under "**The owner's request**".
- `APPLE-PRESENTATION/DESIGN.md` gives as the owner's request, word for word, "Revise APPLE-PRESENTATION's
  design and plan as docs/evidence/APPLE-PRESENTATION/design-review.md asks". That sentence is the task the
  script writes after a failed design review.

The 10 November sentence is the lead's summary. It is the opening of a task the lead wrote ("Purpose. The owner
wants work lined up continuously ..."), not anything the owner said.

**What it cost (suspected).** Design reviewers judge a design against this quote. The CREATOR and ATMOSPHERE
designs are judged against "work lined up continuously", which describes how the lead wanted to schedule
builders, not what either module is for. The skill itself records one case where a reviewer judged against a
planner's summary because the request had been cut short. I did not find a review in Thrum that went wrong
because of these quotes. The owner reading a design would still be misled about what they had asked for.

**What in the skills led to it.** The build skill says the owner's request goes "to a planner word for word, in
`--task`". The lead also uses `--task` for its own context, as problem 2 says it should. Nothing marks which
part of the task is the owner's, so the planner, told to quote the request word for word, quotes the task.

**The fix.**

- In `build`, ask the lead to put the owner's words in the task in quotation marks with their date. Better
  still, give the `plan` command a separate `--owner-words` argument that the script saves apart from the task.
- In `plan-module`, quote the owner from `BRIEF.md` or from the marked owner's words. When there are none,
  write "The owner's words were not passed on; this design answers the lead's task" rather than presenting the
  task as a quote.

## 4. Builders state guesses as facts, and claim proof for the wrong commit

**What was written, and what it cost (observed).**

- An APPLE-PRESENTATION M1 builder ended two turns with "BLOCKED: Another builder's nested GPU lock prevents
  further tests and capture. The lead must restart APPLE-TILE's check without its outer `lock gpu` wrapper."
  The diagnosis was wrong. The lock was simply held, and `lock` waits its turn. The builder's guess became an
  instruction to another builder. It cost two stopped turns and a correction from the lead, quoted under
  problem 2.
- An APPLE-TILE M2 builder ended with "M2 is claimed: all five items pass, committed and integrated on `main` at
  `a6101020`." The reviewer found that "none of the builder's evidence was produced from the commit it claimed".
  `land` had rebased the branch onto an APPLE-PRESENTATION change that turned on camera jitter. The builder's
  evidence came from the commit before that rebase, and at `a6101020` its byte-exact comparisons failed. That
  cost a failed review round, and the milestone now waits on the other module's fix. The builder's evidence page
  never names the commit its runs used. The reviewer had to match binary hashes to find out.

**What in the skills led to it.** `build-milestone` asks the log entry to keep "what you verified kept apart
from what you think is probably true". The last line, which is the text the lead acts on, has no such rule. The
skill says to wrap an exclusive resource in `lock` "so two builders don't use it at once", but not that `lock`
waits rather than failing, so a held lock looked like a fault. The skill also says `pass` means the proof came
from the item's target. It doesn't say the proof has to come from the commit being claimed, or that a rebase
which brings in rendering changes means the proof has to run again.

**The fix.** Three sentences in `build-milestone`:

- "In your last line and your handoff, say which parts you confirmed by running something and which you only
  suspect. Ask the lead for what you need; don't tell it what another builder should do."
- "`lock` waits until the resource is free. A held lock is not a reason to stop, so do other work while you
  wait."
- "Record in your evidence the commit each proof ran on. If `land` rebased your branch onto changes that could
  affect an item, run that item's proof again on the merged commit before you claim the milestone."

## 5. Items that are revised by adding clauses until they become procedures

**What was written (observed).** `done-when.md` already explains why long items fail: "On one engine project the
items grew to a median of 135 words". On `main` now, the open items have medians of 78 words (APPLE-PRESENTATION),
80 (ATMOSPHERE), 93 (APPLE-TILE), 94 (CREATOR) and 180 (PLATFORM-RUNTIME-MAC), counting the statement and its
proofs. Two examples:

- PLATFORM-RUNTIME-MAC M2.1's `inspect` field runs to about 350 words. It is a script of steps, and it keeps the
  remains of earlier fixes as prohibitions: "Do not wait for manual locking or gate admission or success on lock
  values. ... Do not substitute a fixed-step route, endpoint redraw or static parity. Preserve the historical
  0d53d3aa motion pass and its 38.3/51.7 ms content holds as historical evidence only."
- ATMOSPHERE M5.2's `ask` holds about ten questions. They include how the test must be built ("is the expected
  value an f64 filtered decode written apart from the library's code, on the live product and on the known
  field"), and the bound added after the latest re-plan ("Is their allowance the design's C/32 + 1e-5 M + Q, with
  Q one stored half-float step"). The planner's report says this is how the change was made: "M5.2's reviewer
  question now names the new allowance and the 32-step floor."

**What it cost.** The PLATFORM-RUNTIME-MAC M2 builder session ran for 13 turns, through two re-plans and a
design review. The ATMOSPHERE bound shows the pattern more cleanly (observed). After the first design review
asked for "numerical acceptance", a planner wrote a bound, `C/32 + 1e-5 × M`, that it had not measured, and
said so to the lead: "the `C/32` weight allowance rests on GPU samplers keeping 8-bit filter weights, which is
common practice but not measured on the M3 Max or in Chrome." The design review passed it. The next builder met
the miss and stopped, as the plan told it to. The bound was wrong for another reason, half-float rounding of the
filtered result, so the miss cost a builder session, a planner, a design review and a second builder session.
The stop rule worked. A measurement during planning would have made it unnecessary. How much of the
PLATFORM-RUNTIME-MAC cost came from long items, rather than from the hardware, is suspected, not shown.

**What in the skills led to it.** The skill's advice on short items sits in `done-when.md` under "What makes a
good item", which says "This section is for the planner". The sections a planner follows when revising (after a
design review, a re-plan, or a change from the owner) say only "change the items" and "change only what their
words reach". Patching in place by adding a clause is the shortest way to obey both. The design review then asks
"whether a convincing fake would pass" each item, which a planner answers by adding another prohibition.
`plan-module` says "Use only cost targets that are real ... don't make a number up", but only about cost, so a
precision bound invented to satisfy a reviewer is not covered.

**The fix.**

- In `plan-module`, in each revision section: "Rewrite a changed item from what it claims, as if new. Move the
  history and the reason for the change to `LOG.md`, and don't keep old cautions in the item." This is
  prompting-agents' advice for updating an old prompt: "don't fix it line by line".
- Extend the cost rule to every number an item tests against: "A bound you have not measured is a guess. Measure
  it while you plan, or make measuring it the milestone's first item, with the bound set from the result."
- In `review-milestone`'s design section, say that a proof which scripts how the builder must test is a
  Suggestion to shorten, not a reason to add more.

## 6. The `PLANNED` file list pushes the planner's report out of view

**What was written (observed).** `plan-module` ends a planner's report with "what is left for the owner ... Put
them last, because the lead is shown the end of a long report". The script's prompt then requires the very last
line to be "`PLANNED: <every file you wrote or changed, comma-separated>`". The planner that reshaped Thrum's
plans for 1.7.0 changed well over a hundred files. In the recorded transcript, its last reply is entirely file
paths, beginning partway through one: "e/ATMOSPHERE/review-briefs.md, docs/evidence/COOKED-DRAW/...".

**What it cost.** The script gives the lead the last 6,000 characters of a planner's reply. The file list alone
fills more than the 4,000 characters the transcript kept, so the lead saw at most about 2,000 characters of the
report itself. The owner's decisions should have been in those characters, though I can't confirm what the lead
saw (suspected). The list does no other work. The script already computes the changed files itself, and uses
the planner's list only to nudge it when the two disagree (`plan_owed`).

**The fix.** Make the last line `PLANNED` on its own, and have the script print the changed files in its result.
This is a rule worth cutting: it makes every planner's report longer and puts the least useful text where the
lead looks.

## 7. Telegraphic last lines and logs that the owner can't follow

**What was written (observed).** The Claude planners and reviewers wrote clear prose, with the worst finding
first and "For the lead" and "For the owner" sections. The Codex builders wrote in noun stacks and item IDs:

- "BLOCKED: D2.3 needs approved 1× playback inspection. Attended D2.5 needs OS-window capture setup and
  both-recipe window proof."
- In APPLE-TILE's `LOG.md`: "M2 implements one scene/surface graph with checked pre-/post-acquire execution,
  preserving the existing host loss/refusal/history contract and SDR intermediate."
- Gate labels instead of module names: "BLOCKED: G5 / `thrum-asset-gpu` needs a simulator-compatible cooked draw
  path" and "G3b/render-owner support ... is required". The module was COOKED-DRAW in the first case. In the
  second, the lead had to start a planner partly to find out which module "G3b" meant: "Decide which module owns
  matching the scene ... (PLATFORM-RUNTIME-IOS-PLAN.md and PLATFORM-RUNTIME.md mention G3b)".

**What it cost.** The gate label cost a planner turn spent on finding the owner (observed, though the planner had
other work in that task). That the owner finds these lines hard to follow is what you reported. I did not see
the lead's chat with the owner, so I can't show where a line reached them unrewritten (suspected).

**What in the skills led to it.** `build-milestone` is the only one of the four skills with no writing guidance
at all. `plan-module` points planners at prompting-agents for the files they write, and `review-milestone` points
reviewers at it for findings. The builder's last line, log entry and evidence page are read by the lead, a
planner or a reviewer, and through the lead by the owner. Nothing tells the builder that. Its last-line form
pushes the other way, because it asks for "what you tried, the evidence, and what would unblock it" on one line.
Prompting-agents' GPT-6 file notes that the model "answers in lists and tables by default. If you want prose, ask
for paragraphs." Builders run on Codex here, and nothing asks them for prose.

**The fix.** One paragraph in `build-milestone`, next to "What finished looks like": "The lead reads your last
line, your handoff and your log entry, and passes them to the owner. Write them in whole sentences. Name an item
by its ID and a few words of what it is about, and name a module by its name in the module table, not by a gate
or crate." The handoff file from problem 1 takes the length out of the last line, so the line can be one plain
sentence.

## Smaller findings

- **Review replies are cut where their worst finding is (observed text, suspected cost).** The script keeps the
  last 1,500 characters of a reviewer's reply, but reviewers put the worst finding first, as the skill asks. The
  CREATOR M1 round-1 reply was about 2,350 characters, so the cut would have dropped the opening, which holds
  the result and the first Must Fix finding. The lead's later message to the APPLE-PRESENTATION builder summarised its
  Must Fix correctly, so the lead seems to read the review file. Either ask reviewers for a short reply, since
  the review file carries the findings, or have the script keep the start of a review reply rather than the end.
- **Links to temporary copies (observed).** Builders link evidence by absolute paths into their worktrees, and
  Codex reviewers link into the script's verification checkout, such as
  `/Users/ryannel/Workspace/thrum/.git/orchestrate/verify/COOKED-DRAW/docs/evidence/COOKED-DRAW/M1-review.md`.
  These stop working when the copy is reused or removed. Ask for paths relative to the repository root. The
  handoff file in problem 1 removes most of the need for them.
- **Status lines left in approved designs (observed, already understood).** The PLATFORM-RUNTIME-MAC and
  APPLE-PRESENTATION design headers still say a review "is owed". An APPLE-TILE planner listed three such lines
  and left them, because "editing the design header would void its approval". This is the reason
  `plan-module` already gives for keeping status out of designs, so the rule is sound. The leftovers predate it.

## Where the skills over-steer

These rules fence in a capable agent, or make it write longer and worse. I would cut or rewrite them.

- **"Nothing of your own"** (`build`). Rewrite it as in problem 2. The lead's own facts were the most useful
  text it wrote.
- **"`PLANNED: <every file you wrote or changed>`"** (the script's prompt to planners, which `plan-module`
  depends on). Cut the list, as in problem 6.
- **The 1,500-word plan cap, as the reshaping planner met it.** The cap is right, because it is what stopped
  800-line plans. But a planner told only that its "first landing will be refused until the oversized plans are
  trimmed" squeezed rather than cut. APPLE-TILE's work list reads "Add truthful registry/override, per-variant
  storage and ready fallback; preserve COOKED-DRAW facts/selection." Every milestone repeats "Retain actual
  target proof and run scoped checks plus `./dev check` before claiming", which reminds the builder to do what it
  does anyway. Prompting-agents puts the principle as "A prompt stays short through what you leave out, not by
  squeezing what's left into labels". Add one sentence to `plan-module` saying how to meet the cap: move design
  to `DESIGN.md` and history to `LOG.md`, and drop lines a builder would follow anyway. I suspect, but did not
  see, that the squeezed lines cost a builder anything. The M1 and M2 builders of APPLE-TILE did well.
- **The eight-line log entry.** This one is harmless rather than harmful. Planners and builders met it by moving
  text into `docs/evidence/<MODULE>/log-entries.md`, which comes to 6,460 words across nine modules, with "[Full
  entry]" links from the log. Nothing was shortened, and there are now two places to read. I would keep the cap
  but say plainly that the log entry is the summary and the evidence file is the detail. That is what agents
  already do.

These rules worked, and should stay as they are:

- The three last-line forms for builders and the counted form for reviewers. The script needs them, and no agent
  misread them.
- The rule that a condition the work must survive, such as a locked screen, is not a condition for checking it.
  It came in after COOKED-DRAW M1.7 cost an owner the job of locking the Mac by hand. Since then the lock has been
  recorded as a witness, as intended.
- The recorded owner answers that builders and reviewers are told to cite (`owner_answers` in `ACCEPTED.json`).
  The APPLE-TILE M2 builder and reviewer both used them correctly.
- The design review's table of earlier findings and their state. It made each round's progress easy to follow.

## Outside the skills

Two problems in the records come from the script's own text rather than from an agent, so they are outside this
review. They are worth fixing anyway:

- The script's text that follows the lead's message to a resumed builder ends with "Licences and paths not to touch: no GPL or share-alike code or data
  (restrictive-licence code may inform ideas. Owner decides: ...". The bracket never closes, so the `Owner
  decides` list reads as part of the licence rule.
- The round-2 CREATOR M1 review was told "round 1 (2026-11-11): no findings recorded". The round-1 reviewer had
  run on 1.6.2, which recorded `fails` rather than named findings. The round-2 reviewer found the names in the
  review file. Repeat counting across that version change would have missed them.
