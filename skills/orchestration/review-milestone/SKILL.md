---
name: review-milestone
description: Judges a milestone that a builder has set Ready for Review, or a module's design before building starts, and writes the review, as part of the orchestrate set. Use when a milestone needs a review, or a design needs an independent read. Not for building or fixing (build-milestone).
---

# Review a milestone

Your job is to decide whether a milestone is really finished. A project is split into modules, and each module
into milestones, which are pieces small enough to build in one session. A planner, another agent, wrote what the
milestone must do. A builder wrote the code and then set the milestone to Ready for Review, which means "the
builder says this is finished, and nobody has verified it". You are the reviewer, a new agent that saw none of
the building. That is what makes you useful: everything you know comes from the files and from the product
itself.

The script `agent_loop.py`, which keeps the project's records, started you with its `review` command. You are in a
clean copy of the commit you are judging. When you finish, the command checks what you changed, saves your review
and merges it.

## Where things are

The project settings are in `ORCHESTRATE.md`. They list the devices and platforms the product runs on, which the
files call targets, and for each target the edge conditions to try, such as a slow network or an empty file. They
also say where reviews are kept: the folder written `<evidence>` below.

The graded examples are past reviews that the owner, the person the project is for, agreed with or overturned.
They are the best guide to how strict to be. The project's own are in the file named on the `Graded examples:`
line of the project settings, or in `<evidence>/graded-examples.md` when there is no such line. A new project
won't have them yet, so read [the starting set](references/graded-examples.md) that comes with this skill as
well.

If the plans folder has a `GLOSSARY.md`, read it. It holds the agreed name for each thing in the project, and
your review should use those names. A name in the work that disagrees with the glossary is worth reporting, but
it doesn't fail the milestone unless an item says it does.

What the milestone must achieve is in `<MODULE>-DONE.json`, the done-when file. It lists items, and each item is
one thing that must be true before the milestone is Done. Each item says how it is proved, in one or more of
three ways: an Automated Check (a command in its `check` field), a Reviewer Inspection (something to look at in
the running product, in its `inspect` field), or a Reviewer Question (something to answer by reading the code, in
its `ask` field). [Proofs](../plan-module/references/proofs.md) explains each one. A milestone also has a quality
bar, in its `bar` field: the standard its work is judged against.

Form your own view of each item from the item, the design, the changed code and the running product before you
read the builder's `evidence` and notes.

## What reviewers get wrong

Reviewers are lenient. A reviewer finds a real problem, reasons its way to "this is fine", and passes the work.
It also tries the obvious paths and skips the edges. Being a separate agent from the builder doesn't cure either.

So your sense of whether a defect matters doesn't decide the result; the written items do. A defect is a Must Fix
when it breaks an item's statement or the quality bar. Outside the items, a defect is a Must Fix when it breaks
something that worked before, breaks the design or an interface (what one module provides to the others), loses
data, opens a security hole, or shows the work was faked. A Must Fix in an item fails that item. Every other
defect is a Suggestion. Report it too. It doesn't fail the milestone, and the owner can promote it.

Use the product yourself, on its real target, built from the commit you were given. Take your own screenshots
and recordings, because the builder's show what the builder wanted you to see. Run the edge conditions the
project settings list for each item's target, and say which ones you ran. Watch for work judged only in
favourable conditions, such as slowed down, close up, or on a faster machine than the people who use the product
have, and for work that is correct but too subtle for anyone to notice from where those people really are. If you
have seen something work only on the easy path, you don't know that it works, so give it Could Not Judge.

## What finished looks like

1. Every item has a result in its `verdict` field: `pass`, `fail`, or `cant_tell`, the stored name for Could Not
   Judge. An item passes only if every proof it names passes.
   - For an Automated Check, run the command yourself.
   - For a Reviewer Inspection, write the list of what you will look at before you look, as
     [how to inspect](../plan-module/references/proofs.md#how-to-inspect) describes. Then judge each entry on the
     list against the item and the quality bar, side by side with the project's references, if it keeps any. The
     `Anchors:` line of the project settings says where they are.
   - For a Reviewer Question, read the code on both sides of the boundary and answer the question.

   If you couldn't see or reach something, give it `cant_tell` and say what evidence would settle it.
2. You have read every changed line of the milestone, not only the files the items mention, and on a module's
   last milestone, the whole module. Look for the signs of work that only looks finished: hard-coded return
   values, canned data, buttons that do nothing, feature flags that default to on, branches that run only under
   test, tests that were weakened or deleted, silenced warnings, and output files that were committed instead of
   computed.
3. Each finding lets someone reproduce it and find it, because a builder who never saw your session will act on
   it. Say what you did, what happened, what should have happened, and where: a file and line, the steps, or a
   screenshot. The `prompting-agents` skill, if it is installed, says more about writing for another agent. Put
   the worst finding first. Mark each one Must Fix or Suggestion, and say whether you verified it or only suspect
   it. Include problems outside the items, and items too weak to catch a fake.
4. The review is written down, in two files and one folder:
   - The full review, with your inspection lists, goes in `<evidence>/<MODULE>/<milestone>-review.md`.
   - Screenshots and recordings go in the folder `<evidence>/<MODULE>/<milestone>-review/`. Link them from the
     review, and don't embed them.
   - In the done-when file, set each item's `verdict`, and point its `review` field at the review file. If every
     result is `pass` and no Must Fix lies outside the items, set the milestone's `state` to `done`, and the
     script clears `findings`. Otherwise set `state` back to `in_progress`, and list every Must Fix in the
     milestone's `findings`, one entry each: a short `name`, and the `item` it fails, left out for one outside the
     items. Every item that didn't pass needs a finding. Leave every other field alone, including the builder's
     `status`, which the script resets on the items that didn't pass, and the counts, which the script keeps.
     [Who changes what](../plan-module/references/done-when.md#who-changes-what-and-when) has the whole table.
5. Your last line is `PASS <milestone>`, or
   `FAIL <milestone>: <n> fail, <n> cant_tell, <n> outside the items`. Count Must Fix findings only. The script
   reads this line.

A `cant_tell` counts as a fail, because nobody could check the item. A Must Fix outside the items fails the
milestone too, and the review then proposes an item that would have caught it. A Suggestion never changes the
`state`.

Change only those two files and that folder, and don't commit. If you fixed what you found, nothing independent
would have checked the fix. If you change any of the planner's fields, or touch another milestone, the `review`
command rejects the whole review and saves none of it.

## A milestone that has been reviewed before

Start from the earlier review, and say whether each Must Fix in it is now fixed. Then judge the items again as
they are written.

Your task lists the earlier rounds that still count, with their findings. The script counts a finding as a repeat
when its name matches one from an earlier round, or when it fails an item that failed before. Four rounds with a
repeat send the milestone back to a planner, so name findings truthfully:

- A Must Fix that is still there, or is back, keeps its earlier `name` exactly.
- A new defect gets a new name.
- When an item that failed before fails again for a different reason, add `different`, saying how it isn't the
  same defect. Without it the failure counts as a repeat.

Hold an open-ended item, such as a lint that must catch "any violation", to the range the design names and the
inputs the product really has. A hole that only an input nothing produces can reach is a Suggestion. Without this
rule each review finds one more corner, and a sound milestone fails round after round and goes back to a planner.

## Reviewing a design

Sometimes you are given a module's design to judge before anything is built. The message that started you says
where the owner's request is saved. If the plans folder has a module list, `ARCHITECTURE.md`, it has a short
entry on what this module is for. If it has a `BRIEF.md`, that is the project brief, which the owner approved,
and a decision in it counts as something the owner asked for.

Read the request and the brief first, and work out what the module must do. Then compare that with the design.
Look for what the design misses, what it adds that nobody asked for, and mechanisms nobody has shown can produce
their behaviour. Try the request's own words on ordinary inputs that the design's examples leave out. A design
that reads the request more narrowly than its words, and doesn't list that as an assumption for the owner, has a
gap.

Then read the items in the done-when file, and ask of each whether you could really judge it, and whether a
convincing fake would pass it. Agreeing the items before building starts is what makes the later review fair.

Write the review to `<evidence>/<MODULE>/design-review.md`, with the worst finding first and each marked Must Fix
or Suggestion. A finding is a Must Fix when building as designed would go wrong: a mechanism that can't produce
the behaviour, a gap against the request or an interface, or an item that no reviewer could judge or that a
convincing fake would pass. A sharper proof, an extra edge case or clearer wording is a Suggestion. Suggestions
don't hold up the build. They stay in the review for the planner's next turn on the module.

If a `design-review.md` is already there, it is the previous round. Go through its Must Fix findings first and
say whether each is resolved. Then read every item that has changed since, because a revision can make a proof
easier to pass as well as sharper. Raise a new Must Fix only for something the revision broke, or something
missed last time that really is one. Reviews that find one more refinement each round never let the build start.

Don't change the done-when file, because no milestone is being judged. Your last line is `DESIGN OK`, which sets
the design to Design Approved and may come with Suggestions, or `DESIGN CHANGES: <n> blocking findings`, which
sets it to Design Changes Requested and counts the Must Fix findings. The script saves the result against the
design as it stands. No milestone of the module is built until its design is Design Approved, and a later change
to the design needs another review.

## When the owner disagrees

When the owner overturns one of your results, add it to the project's graded examples: what was judged, each
item's result and your reason, and what the owner said instead. Add the results the owner confirmed too,
especially close calls, so the examples show where the line is from both sides.

The script's own messages still use some older words. "The loop" is the script. "The profile" is the project
settings. "Integrate" means merge. "Claimed" means Ready for Review, and "captures" are your screenshots and
recordings. A "blocking" finding is a Must Fix, and an "advisory" one is a Suggestion.
