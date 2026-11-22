# Reviewing a design

A planner has written or changed a module's design and items, and no builder starts until a reviewer approves them.
Agreeing the items before building is what makes the later milestone reviews fair.

## What to read

Work out what the module must do from the project brief, the module list's entry for it, and the tasks the planners
were given, where your prompt names them. A decision in the brief counts as something the user asked for.

Compare that with the design. Look for mechanisms nobody has shown can produce their behaviour, and try the task's
own words on ordinary inputs the design's examples leave out. A design that reads the task more narrowly than its
words, without listing that as an assumption for the user, has a gap.

For each item in the done-when file, ask whether you could really judge it when its milestone ends, with only the
milestones before it built, and whether a convincing fake would pass it. For an `inspect`, check that its reference
matches what the user asked for, at the level they asked for, and that each checklist line comes from what the
reference shows. A milestone of options for the user to choose from is the exception: its bar is the minimum
requirements and being different in kind, because the user will turn most of them down. For an `ask`, check that it is
about a part the architecture depends on.

Check the design's names against the glossary, as the `domain-language` skill describes, because a design is where a
new concept first gets a name.

## What counts as a Must Fix

A finding is a Must Fix when building as designed would go wrong: a mechanism that can't produce the behaviour, a gap
against the request or an interface, a reference below what the user asked for, two modules that would read an
interface differently, or an item that no reviewer could judge, that its milestone can't prove, that a convincing fake
would pass, or that work meeting the quality bar would fail, such as a cheaper method that looks the same. A sharper
proof, an extra edge case, clearer wording or a name that drifts is a Suggestion, which the planner reads on its next
turn.

A proof that scripts step by step how the builder must test is a Suggestion to shorten it, not to add more steps. An
item says what has to be true and how it is shown, and leaves the route to the builder, because an item that grows
prohibitions turns into a procedure each builder has to untangle.

## A design reviewed before

When your prompt names a previous review of this design, say first whether each of its Must Fix findings is
resolved. Then read every item that has changed since, because a revision can make a proof easier to pass as well as
sharper. Raise a new Must Fix only for something the revision broke, or something missed last time that really is
one. What is left of an earlier Must Fix, when it changes nothing the user would see and nothing another module
relies on, is a Suggestion, because reviews that each find one more refinement never let the build start.

## Finishing

Write the review where your prompt says, and leave the done-when file as it is. Your last line is `DESIGN OK`, which
approves the design and may come with Suggestions, or `DESIGN CHANGES: <n> must_fix findings`, which sends it back
to the planner. The script saves the result against the design as it stands, and a later change to the design needs
another review. Put every Must Fix you find in this review, because after a set number of reviews in a row that ask
for changes, the script approves the planner's revision without another one, and your prompt says when this is the
last.
