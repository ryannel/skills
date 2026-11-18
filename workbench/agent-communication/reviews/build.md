# What the builder sessions were told, and what it cost them

This review covers the 12 builder sessions from Thrum in `thrum-prompts/*-build-*.md`, all run on Codex. I read
every prompt sent to them and the last reply to each, and compared the prompts against the prompting-agents skill
and against what the build-milestone skill already tells a builder. The templates were read as they are at `HEAD`
of `agent_loop.py`, which is the 1.7.1 text; the earliest sessions ran on 1.3.1 to 1.6.2, whose build template is
the same apart from the plan paths.

The main finding is that most of the cost did not come from the template's wording. It came from three other
places: the Codex goal machinery keeps a blocked builder rechecking the same blocker for two more turns; the lead
passes on claims about the machine that it has not checked, and the builder then spends turns finding out they are
false; and nobody tells the builder that the GPU lock is a queue, so a builder that met a held lock reported it as
a fault. The template itself mostly repeats the skill. That costs the owner readability, but I found no reply
where the repetition made a builder do the wrong thing.

Each problem below says who wrote the text, quotes it, says what it cost, and proposes a fix. "Observed" means a
reply shows the cost. "Suspected" means the text is wrong or risky but no reply proves it caused harm.

## 1. A blocked builder spends two more turns rechecking the same blocker

**Who wrote it:** the host (Codex's goal text) and the script (its rule for when a report ends the run).

Codex re-sends the goal after every turn, and its text includes this rule:

> "Do not call update_goal with status "blocked" the first time a blocker appears. Only use status "blocked" when
> the same blocking condition has repeated for at least three consecutive goal turns"

The script agrees with it. A builder's `BLOCKED` or `NEEDS_CONTEXT` ends the run only when
`status != "active" or state["reports"] >= 2`, so while the goal is active the script waits through the goal's
own continuation turns.

**What it cost (observed).** In 7 of the 12 sessions a builder that had already reported a blocker spent two more
turns re-establishing it, about 19 turns in all. Most of those turns rechecked something no build turn could
change. COOKED-DRAW M1 reported that "A planner decision must reconcile the single whole-range draw with the
exact-byte parity requirement", then in turn 3 "Revalidated checkpoint `9c230ff4` and retained evidence hashes.
M1.3 still shows 1,506 differing pixels", and in turn 4 "The goal is marked blocked after three consecutive turns
confirming the same M1.3 failure." The same pattern appears in T2-CAPTURE M2 (waiting on another module), APPLE-TILE
M0 (twice: disk space, then a scope question for the planner), ATMOSPHERE M5 (a planner decision), PLATFORM-RUNTIME-MAC
M2 (three times on a locked console), APPLE-PRESENTATION M1 and APPLE-TILE M2. Three of the extra turns did useful
work: APPLE-TILE M0 turn 3 merged a pixel comparator, ATMOSPHERE M5 turn 3 saved a work-in-progress commit, and
APPLE-PRESENTATION turn 3 strengthened a test. The rest only restated the block.

The goal's "blocked" state also outlived the block. In T2-CAPTURE M2 the goal was still marked blocked from turn 4
when the lead unblocked the builder, and the lead then had to send two messages about a block the builder had not
caused (see problem 5).

**Fix: structure in the script.** When a builder ends with `BLOCKED` or `NEEDS_CONTEXT` for a cause that another
build turn cannot change, the script should end the run on that first report and set the goal to paused itself, as
it already sets it active again with `codex_goal_activate`. The working tree's typed reasons (`needs_dependency`,
`needs_human_feedback`, `needs_access`, `needs_hardware`) make that decision easy: stop at once for any of them. An
untyped `BLOCKED:` can keep one continuation turn, since that is where the three useful turns above came from.

## 2. The lead passes on claims about the machine that it hasn't checked

**Who wrote it:** the lead.

Three examples, each from a lead message sent to unblock a builder:

> "The owner is at the Mac now: it's unlocked, with the built-in Liquid Retina XDR panel online as the main display.
> That's M2's attended setup, so M2 is unblocked." (PLATFORM-RUNTIME-MAC M2, turn 8)

> "Carry on with M2. The owner is at the Mac now: it's unlocked, with the built-in panel online as the main
> display." (the same session, turn 9)

> "Screen Recording is now granted to Claude and ChatGPT (a preflight from the lead's shell returns true), and the
> owner allowed IINA in Codex Computer Use" (APPLE-TILE M2, first session, turn 5)

**What it cost (observed).** In PLATFORM-RUNTIME-MAC the builder found the opposite both times: "The panel was
online and main but asleep... then macOS reported the console locked", and in turn 9 "I ran the runbook and
watched for an unlock for five minutes. Both macOS session probes continued reporting locked". That is two turns
and two `BLOCKED` reports spent discovering that the lead's description was wrong, followed by a third goal turn
that marked the goal blocked. In APPLE-TILE M2 the Screen Recording claim was true, because the lead had checked
it from a shell, but the Computer Use claim was not: "Computer Use still rejects Thrum M2 and IINA as "not
approved," despite the recorded owner answers." The session ran headless, so the approval prompts could never
appear in it, and the milestone needed a whole second session started visibly in the Codex app. That second
session finished in 47 minutes once its prompt said why the first had failed.

The prompting-agents skill names this exactly: "check your claims before you pass them on, because once a guess
is in a prompt, it becomes the reader's requirement." The one claim the lead did check, Screen Recording, is also
the one that held.

**Fix: wording in the lead's habits, and structure from the script.** The lead should hand over the check, not
its conclusion, as in "`ioreg -n Root -d1 -l | grep CGSSessionScreenIsLocked` printed nothing at 10:14, so the
console was unlocked then." That belongs in the build skill's section on how the lead writes a message to a
builder. The part the script knows for certain it should state itself: whether this session is headless or shown
in the app (`visible_unavailable` already decides this), because that alone decides whether an approval prompt
can appear. A line such as "This session runs headless, so Computer Use and other approval prompts can't appear
in it" would have sent the first APPLE-TILE M2 session straight to `BLOCKED needs_access` instead of three tries.

## 3. Nobody tells the builder that the GPU lock is a queue

**Who wrote it:** the template and the skill, by leaving the fact out.

The template says only:

> "Take other exclusive resources with `python3 .../agent_loop.py lock <name> -- <command>`."

The skill adds that the lock is there "so two builders don't use it at once". Neither says that `lock` waits its
turn, that another builder holding the lock is normal, or what to do while waiting.

**What it cost (observed).** APPLE-PRESENTATION M1 ended its first turn with "BLOCKED: Another builder's nested
GPU lock prevents further tests and capture. The lead must restart APPLE-TILE's check without its outer `lock gpu`
wrapper." It said the same in turn 3. Four turns passed, with the builder asking the lead to restart another
builder's work, before the lead explained:

> "The GPU lock you met is not nested or stuck... `lock gpu` queues, so wrap your GPU checks and captures in it and
> wait your turn rather than stopping. Do CPU-side work while you wait. Block only if the lock is held by a process
> that has made no progress for 30 minutes, and name its pid."

After that one message the builder finished and merged. PLATFORM-RUNTIME-MAC M2 turn 12 also ended with a block
partly on the lock: "checkpoint integration needs the GPU lock released."

The lead then repeated "Hold agent_loop.py lock gpu for GPU work" or a variant of it in seven later messages
(PLATFORM-RUNTIME-MAC turns 11 and 13, APPLE-PRESENTATION turn 8, ATMOSPHERE M5 turns 1 and 5, both APPLE-TILE M2
sessions). A line repeated that often is a sign it is in the wrong place.

**Fix: move it to the skill, and let the script state the project's resources.** The lead's turn-5 message is
already the right text: it gives the fact, what to do meanwhile, and the exact point at which waiting becomes a
block. Put it in the build skill next to the `lock` command. The template should name the resources itself,
since the script reads them from the `Exclusive resources` line: "This project's exclusive resources are: gpu."
It would also help if `lock` printed which process holds the lock and for how long, so the builder sees a queue
rather than a hang.

## 4. The lead's message for one moment becomes the goal for the whole run

**Who wrote it:** the script's goal line, and the lead's message placed after it.

The script opens a Codex prompt with:

> "Call your create_goal tool with this objective, then work it."

"This objective" is not marked off, so the builder takes the whole message, including the lead's note at the end.
In PLATFORM-RUNTIME-MAC M2 the lead's note was:

> "The owner is away from the Mac. Do every part of M2 that runs unattended on a locked console... and then report
> BLOCKED on that attended step alone."

**What it cost (observed).** The goal the builder created ended with "Complete all unattended locked-console work
and prepare a one-command runbook for the attended built-in-panel cadence run, then report BLOCKED on that
attended step alone if it cannot run." Codex re-sent that sentence on every continuation turn for the rest of the
session, including turns 7 and 10, after the owner had come back and the lead was telling the builder to run the
attended step. In turn 10 the stale goal's own blocked audit marked the goal blocked again. In COOKED-DRAW M1 the
same thing happened from the other side: after the script's claim-failure message, the goal became "Fix the plain
./dev check failures blocking COOKED-DRAW M1 acceptance", which is narrower than the milestone.

I glanced at the working tree's new template, and it puts `{lead}` directly after "The goal:" paragraph. Unless
the goal line names the paragraph, that placement makes this more likely, not less.

**Fix: wording in the goal line.** Name the paragraph and say what the rest is: "Call your create_goal tool with
the paragraph that starts 'The goal:' as the objective, word for word. The rest of this message is for this turn
only and is not part of the goal." The lead's note should then sit under its own heading, after the rules.

## 5. Turns that end mid-work are read as reports, and the lead corrects the builder for the script's state

**Who wrote it:** the lead, reacting to the script's record.

In T2-CAPTURE M2 turn 5, the builder's turn ended with a progress note: "The final profile Check is running
through the workspace tests under the GPU lock." The goal's next turn finished with `DONE` and the merge. The lead
had not seen that, and sent:

> "Your last turn ended while the final profile Check was still running, so the loop recorded M2 as blocked;
> nothing is actually blocking it. Wait for that Check to finish (or rerun it), restore the two simulators you
> noted, integrate the committed claim, and end with DONE."

and then, after the builder confirmed it was done:

> "M2 isn't blocked: your goal was left in the blocked state while the final profile Check ran, and the loop has
> reactivated it... Only set the goal or report BLOCKED for something you genuinely can't proceed past."

**What it cost (observed).** Two turns re-verifying finished work. The builder had already said the simulators'
"prior in-app sessions could not be restored", so "restore the two simulators you noted" asked for something it
had explained it could not do, and it said so again twice. The last sentence of the second message rebukes the
builder for a goal state the script left behind (problem 1). On GPT-6 models a caution like that is taken at full
strength, which makes it more likely the next builder holds back a block it should report.

ATMOSPHERE M5 shows the same mechanism with a different cause. Its turns 1, 3, 5 and 7 all end with progress notes
("I'm verifying the lossless archives", "The fresh MF1 campaign is still queued behind other GPU jobs"), and the
lead had to send: "Your last two turns timed out (a long-running process was lost: write_stdin failed, unknown
process id)... Run long jobs with a bounded timeout or in the background with their output to a file, rather than
holding one shell open for the whole turn." That is two lost turns and a lost process.

**Fix.** Cut the rebuke from the lead's habits; when the script's state is wrong, say so as a fact ("the script
recorded a block by mistake; you did nothing wrong") and ask only for what is missing. Before the lead writes a
correction, the script should show it the builder's latest reply, including goal-chained turns, so the lead does
not act on an older one. The advice on long jobs is a standing fact about Codex sessions, so it belongs in the
build skill's Codex paragraph, next to the sandbox advice that is already there.

## 6. The restatement on resumed turns is cut short and can contradict the lead

**Who wrote it:** the script (`binding()`), appended after the lead's message whenever the goal is not active.

This is the text that followed the lead's message in ten turns across five sessions:

> "Licences and paths not to touch: no GPL or share-alike code or data (restrictive-licence code may inform ideas.
> Owner decides: changing purpose or the V1 exit; spending; publishing, licensing or deploying; irreversible."

Thrum's `ORCHESTRATE.md` wraps both lines onto a second line, and `profile_value()` reads only the first. So the
builder was sent an unclosed bracket and a dangling "irreversible", and three rules were dropped: "never modify
Broadsides", "preserve the owner's uncommitted files", and the grant "Gate order within the V1 exit is the agents'
call." The last is a freedom, and losing it is the kind of thing that makes a builder ask for approval it doesn't
need.

The restatement also adds the attended rule whatever the lead has said. In PLATFORM-RUNTIME-MAC turn 13 the lead
wrote "make the attended recordings now: the console is unlocked", and the script appended "Attended items M2.2,
M2.5: do the rest, then BLOCKED naming them."

**What it cost (suspected).** I found no reply that broke one of the dropped rules or obeyed the contradiction;
the turn-13 builder queued for the GPU rather than blocking. The defect is certain, though, and the dropped lines
are real boundaries.

**Fix: structure in the script.** Read a profile bullet up to the next bullet, not to the end of its first line.
Better, restate only the objective and point to the file for the rest ("The project's rules are in the Rules
section of ORCHESTRATE.md; re-read it"), since the builder reads that file at the start anyway. Leave out the
attended line whenever the lead has sent a message, because the lead's message is the newer fact.

## 7. "Block at once" stops a builder that could have carried on

**Who wrote it:** the lead.

> "If the panel sleeps or the console locks, block at once naming what you need." (PLATFORM-RUNTIME-MAC turn 11)

**What it cost (suspected, with supporting evidence).** In that turn "The panel then became asleep and inactive
while the console remained unlocked. I stopped the queued second diagnostic before recording", and the builder
reported `BLOCKED: Wake the built-in panel`. In turn 7 of the same session it had woken the panel itself "with
bounded assertions", so it could probably have done it again. The lead's next message was "the lead is holding the
display awake with caffeinate -d for the next 2 hours", an action the builder could have taken. The instruction
did not separate what only the owner can fix from what the builder can.

**Fix: wording.** Say where the boundary is and why: "If the console locks, block at once, because only the owner
can unlock it. If the panel sleeps, wake it with `caffeinate -d` and carry on."

## 8. A failed claim check arrives with no output, and "Fix that" assumes the fault is the builder's

**Who wrote it:** the script, on the line that sets `a.message` after a refused claim.

> "The loop can't accept the claim yet: Check `./dev check` exited 2: ; M1.1 `./dev check` exited 2: ; M1.2
> `./dev check` exited 2: . Fix that, then end with DONE." (COOKED-DRAW M1 turn 7)

**What it cost (observed).** The message has no output and doesn't say the check ran in a clean copy under
`.git/orchestrate/verify/`. The builder replied "Plain `./dev check` passed all 666 Rust tests" and spent a turn
before finding that the clean copy lacked its `RUSTC_WRAPPER` setting. Two turns later the script reported M1.7
and M1.8 failing on "RuntimeError: locked-console proof required". Told to "Fix that", the builder asked the owner
to lock the Mac and added a 120-second wait to the harness for manual locking. The planner then revised the item,
because a locked console should never have been required, and the builder had to change the harness back in
turn 11. The build skill says to leave a wrong item as written and report it, but the message pointed the other
way. That link is suspected; the extra turns are observed.

**Fix: structure and wording.** Include the last 30 lines of each failing command's output, and say where and how
it ran: "These ran in a clean checkout of main at `<path>`, without your shell's environment." End with "Fix the
cause and end with DONE. If the item itself can't be met as written, leave it and say so", which matches the skill.

## 9. The template's attended line states as fact something that is often false

**Who wrote it:** the template.

> "Items with `attended` need a person or hardware you can't reach: do everything else first, then end with
> BLOCKED and list them."

**What it cost (observed in combination).** "You can't reach" is stated as a fact, but in several sessions the
owner was at the Mac, and the lead had to override it each time ("The owner is at the Mac now, for a limited time,
so do the attended rows first"). It also says nothing about approval prompts, which is what actually stopped
APPLE-TILE M2 (problem 2). The working-tree skill has replaced `attended` with typed `needs` and says "If it is
there, use it", so the template and the skill now disagree.

**Fix: cut it from the template.** The skill carries the rule, and the template only needs to state what this
session can and can't reach, which the script or the lead knows: headless or visible, and whether the owner is
present.

## 10. "Change only..." can read as covering the whole repository

**Who wrote it:** the template, and the restatement.

> "Change only M2's state and its items' status and evidence; the rest of the done-when file belongs to the
> planner and reviewer"

**What it cost (suspected, weak).** In the second APPLE-TILE M2 session the builder reported "Automatic approval
review rejected the maturity-ledger edit as out of scope; it was omitted." Codex's approval reviewer may have read
"Change only" as applying to everything, though I can't tell from the reply. The restatement makes it worse by
putting the file name last: "change only M2's state and its items' status and evidence in
docs/plans/PLATFORM-RUNTIME-MAC/DONE.json".

**Fix: wording.** Put the scope first: "In the done-when file, change only..."

## What the template repeats, and what only it supplies

Almost everything in the template's second and third paragraphs is also in the build-milestone skill: changing
only three fields of the done-when file, the rule about work another module owns, the attended rule, what `land`
does, the `lock` command, not starting a reviewer, and the three last-line forms. Each prompt also prints the
script's absolute path three times, about 110 characters each. I found no reply where the repetition made a
builder misread anything, so the cost here is to the owner, who has to read past it to find what is particular to
the run.

What only the prompt can supply is short: the milestone, the module and the done-when path; the script's and the
skill's paths for this installed version; whether the session is headless or shown in the app; the project's
exclusive resources; and the lead's facts for this run. A template of those five things plus "Use the
build-milestone skill for how to build, prove and merge" would lose nothing the builder needs, provided the skill
holds the rules the template now repeats.

## What worked, to copy

The lead messages that worked first time gave facts the builder couldn't find and said what not to redo. The
second APPLE-TILE M2 session's opening is the best example: "read tmp/g3t-m2/attended/HANDOFF.md first and don't
redo them... That session ran headless, so Computer Use couldn't show approval prompts... This one runs visibly in
the Codex app". It finished in 47 minutes. ATMOSPHERE M5's restart named the commit to bring in and the two files
that would conflict. T2-CAPTURE M2's opening passed on the previous review's advice and said "Its advisories are
your call", which left the judgement with the builder. The lead's GPU-lock explanation in problem 3 is the
pattern for a steer: a fact, what to do meanwhile, and where waiting turns into a block.

## The change to make first

Make the script end the run, and pause the Codex goal, on a builder's first `BLOCKED` or `NEEDS_CONTEXT` with a
typed reason (problem 1). It is a small change in one place, it removes the most wasted turns across the most
sessions, and it also removes the stale blocked goal behind problem 5. The second change is to have the script
state, as structure, the two facts it already knows and the lead keeps having to supply: whether the session is
headless, and which resources are exclusive and that `lock` queues for them.
