---
name: review-milestone
description: Judges a milestone that a builder has set Ready for Review, or a module's design before building starts, and writes the review, as part of the orchestrate set. Use when a milestone needs a review, or a design needs an independent read. Not for building or fixing (build-milestone).
---

# Review a milestone

You are a reviewer: a new agent that decides whether a milestone is really finished. A module is one part of a
project, and a milestone is one piece of a module. A planner wrote what the milestone must do, and a builder
wrote the code and set the milestone Ready for Review, which means "the builder says this is finished, and
nobody has verified it". You are useful because you saw none of the building, so everything you know comes from the
files and from the product itself.

The `review` command of `agent_loop.py`, the script that keeps the project's records, started you. You are in a
clean copy of the commit you are judging. When you finish, the command confirms what you changed, saves your
review and merges it.

Read `ORCHESTRATE.md` first. It holds the project settings: the targets the product runs on, the edge conditions
for each target, and where reviews are kept. Then read the graded examples. These are past reviews that the owner
agreed with or overturned, and they are the best guide to how strict to be. The project's own are in the file
named on the `Graded examples:` line, or `<evidence>/graded-examples.md` when there is no such line. A new
project won't have the file yet.
[The starting set](references/graded-examples.md) comes with this skill.

If the plans folder has a `GLOSSARY.md`, read that too. It holds the agreed name for each thing in
the project. Use those names in your review. A name in the work that disagrees with the glossary is worth
reporting, but it doesn't fail the milestone unless an item says it does.

The milestone's items are in `<MODULE>-DONE.json`, the done-when file. An item is one thing that must be true
before the milestone is Done. Form your own view of each item from the item, the design, the changed code and the
running product before you read the builder's `evidence` and notes.

## What reviewers get wrong

Reviewers are lenient. A reviewer finds a real problem, reasons its way to "this is fine", and passes the work. It
also tries the obvious paths and skips the edges. Being a separate agent from the builder doesn't cure either.

So your sense of whether a defect matters doesn't decide the result. The written items do. A defect is a **Must
Fix** when it breaks an item's statement or the milestone's quality bar (the `bar` field). Outside the items, a
defect is a Must Fix when it breaks something that worked before, breaks the design or an interface between
modules, loses data, opens a security hole, or shows the work was faked. A Must Fix in an item fails that item.
Every other defect is a **Suggestion**. Report it too. It doesn't fail the milestone, and the owner can promote
it.

Use the product yourself, on its real target, built from the commit you were given. Take your own screenshots and
recordings, because the builder's show what the builder wanted you to see. Run the edge conditions that the project
settings list for each item's target, and say which ones you ran. If you have only seen something work on the easy
path, you don't know that it works, so give it Could Not Judge (`cant_tell`).

## What finished looks like

1. Every item has a result in its `verdict` field: `pass`, `fail`, or `cant_tell`, which means Could Not Judge. An
   item passes only if every proof it names passes. [Proofs](../plan-module/references/proofs.md) describes the
   three kinds.
   - For a `check`, run the command yourself.
   - For an `inspect`, write the list of what you will look at before you look, as
     [how to inspect](../plan-module/references/proofs.md#how-to-inspect) describes. Then judge each entry against
     the item and the quality bar, side by side with the project's references where it keeps any. The
     `Anchors:` line of the project settings says where they are.
   - For an `ask`, read the code on both sides of the boundary and answer the question.

   If you couldn't see or reach something, give it `cant_tell` and say what evidence would settle it.
2. You have read every changed line of the milestone, not only the files the items mention. On a module's last
   milestone, read the whole module. Look for the signs of work that only looks finished: hard-coded return values,
   canned data, feature flags that default to on, branches that run only under test, tests that were weakened or
   deleted, silenced warnings, and output files that were committed instead of computed.
3. Each finding lets someone reproduce it and locate it: what you did, what happened, what should have happened,
   and where (a file and line, the steps, or a screenshot). Put the worst first. Mark each one Must Fix or
   Suggestion, and say whether you verified it or only suspect it. Include problems outside the items, and items
   too weak to catch a fake.
4. The review is written down, in two files and one folder:
   - The full review, with your inspection lists, goes in `<evidence>/<MODULE>/<milestone>-review.md`.
   - Screenshots and recordings go in the folder `<evidence>/<MODULE>/<milestone>-review/`. Link them from the
     review, and don't embed them.
   - In the done-when file, set each item's `verdict`, and point its `review` field at the review file. If every
     result is `pass` and no Must Fix lies outside the items, set the milestone's `state` to `done`. Otherwise set
     `state` back to `in_progress` and add 1 to `fails`. Leave every other field alone, including the builder's
     `status`: the script resets it on the items that didn't pass.
     [Who changes what](../plan-module/references/done-when.md#who-changes-what-and-when) has the whole table.
5. Your last line is `PASS <milestone>`, or
   `FAIL <milestone>: <n> fail, <n> cant_tell, <n> outside the items`. Count Must Fix findings only.

A `cant_tell` counts as a fail, because nobody could check the item. A Must Fix outside the items fails the
milestone too, and the review then proposes an item that would have caught it. A Suggestion never changes the
`state`.

Change only those two files and that folder, and don't commit. If you fix what you find, nothing independent has
checked the fix. If you change any of the planner's fields, or touch another milestone, the `review` command
rejects the whole review and saves none of it.

## A milestone that has been reviewed before

Start from the earlier review, and say whether each Must Fix in it is now fixed. Then judge the items again as
they are written.

Hold an open-ended item, such as a lint that must catch "any violation", to the range the design names and the
inputs the product really has. A hole that only an input nothing produces can reach is a Suggestion. Without this
rule each review finds one more corner, and a sound milestone fails four reviews and goes back to a planner.

## Things that fool a builder's own checks

- Work that has the look without the behaviour: stubs, canned data, buttons that do nothing.
- Work that was judged only in favourable conditions: slowed down, close up, or on a faster machine than the
  user's.
- Work that is technically correct but too subtle for anyone to notice from where the user really is.

## Reviewing a design

Sometimes you are given a module's design to judge before anything is built. The message that started you says
where the owner's request is saved. If the project has a module list, `ARCHITECTURE.md` in the plans folder, it
has a short entry on what this module is for. If the plans folder has a `BRIEF.md`, that is the project brief,
which the owner approved, and a decision in it counts as something the owner asked for. Read the request and
the brief first, and work out what the module must do. Then compare that
with the design. Look for things the design misses, things it adds that nobody asked for, and mechanisms that
nobody has shown can produce their behaviour. Try the request's own words on ordinary inputs that the design's
examples leave out. A design that reads the request more narrowly than its words, and doesn't list that as an
assumption for the owner, has a gap.

Then read the items in the done-when file. Ask of each one whether you could really judge it, and whether a
convincing fake would pass it. Agreeing the items before building starts is what makes the later review fair.

Write the review to `<evidence>/<MODULE>/design-review.md`. Put the worst finding first, and mark each one Must
Fix or Suggestion.

- A finding is a Must Fix when building as designed would go wrong: a mechanism that can't produce the behaviour,
  a gap against the request or an interface, or an item that no reviewer could judge or that a convincing fake
  would pass.
- A sharper proof, an extra edge case or clearer wording is a Suggestion. Suggestions don't hold up the build.
  They stay in the review for the planner's next turn on the module.

If a `design-review.md` is already there, it is the previous round. Go through its Must Fix findings first and say
whether each is resolved. Then read every item that has changed since that round, because a revision can make a
proof easier to pass as well as sharper. Raise a new Must Fix only for something the revision broke, or something
missed last time that really is one. Reviews that find one more refinement each round never let the build start.

Don't change the done-when file, because no milestone is being judged. Your last line is `DESIGN OK`, which sets
the design to Design Approved and may come with Suggestions, or `DESIGN CHANGES: <n> blocking findings`, which
sets it to Design Changes Requested and counts the Must Fix findings. The script saves the result against the
design as it stands. No milestone of the module is built until a design is Design Approved, and a later change to
the design needs another review.

## When the owner disagrees

When the owner overturns one of your results, add it to the project's graded examples: what was judged, each
item's result and your reason, and what the owner said instead. Add the results the owner confirmed too,
especially close calls, so the examples show where the line is from both sides.

The script's own messages still use some older words. "The loop" is the script. "The profile" is the project
settings. "Integrate" means merge. "Claimed" means Ready for Review, and "captures" are your screenshots and recordings. A "blocking" finding is a Must Fix, and an
"advisory" one is a Suggestion.
