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

Judge the design against the brief and the module's scope, meaning what its entry in the module list gives it to do.
A finding is a Must Fix when building as designed would miss what the brief asks of the module: a mechanism that
can't produce the behaviour across the range the brief covers, a gap against the request or an interface, a reference
below what the user asked for, two modules that would read an interface differently, or an item that no reviewer
could judge, that its milestone can't prove, that a convincing fake would pass, that work meeting the quality bar
would fail, such as a cheaper method that looks the same, or that is open-ended enough that no work could be shown to
meet it, such as a suite that must fail "when any behaviour is broken". A convincing fake skips what the item claims
on inputs the brief covers, such as output that is right only for the example in the check; a version that differs
only on an input the brief never mentions isn't one.

Growth beyond that scope is a Suggestion, however real: a wider range of input than the brief names, a proof stronger
than its claim needs, an extra edge case, clearer wording or a name that drifts. The range the brief names is the one
"How it will be judged" and its examples describe, not every value a type allows: a brief that reads numbers with
`float()` asks for ordinary numbers, not overflow to infinity. A finding that goes against an assumption or decision
the user agreed is a Suggestion too, with the case for changing it, because only the user can reopen their own
decision. The planner reads Suggestions on its
next turn, and the user can ask for more, because the user, not the review, decides how much quality the project is
worth, and a design that grows with each review never lets the build start.

A proof that scripts step by step how the builder must test is a Suggestion to shorten it, not to add more steps. An
item says what has to be true and how it is shown, and leaves the route to the builder, because an item that grows
prohibitions turns into a procedure each builder has to untangle.

## A design reviewed before

When your prompt names a previous review of this design, judge what has changed since and what those changes touch, not
the whole design again. The rest was judged last time, and a review that reads it all afresh finds new refinements each
round, so even a small wording change would restart the design's reviews. Your prompt lists what changed, or, when the
script couldn't compare, where to start. Say first whether each Must Fix of the previous review is resolved. Then read
each changed part, and the parts that rely on it, because a revision can make a proof easier to pass as well as sharper.
Raise a new Must Fix only for something the change broke. What is left of an earlier Must Fix, when it changes nothing
the user would see and nothing another module relies on, is a Suggestion, and so is anything you notice in a part
nothing changed, unless building it would miss the brief outright.

## Finishing

Write the review where your prompt says, and leave the done-when file as it is. Your last line is `DESIGN OK`, which
approves the design and may come with Suggestions, or `DESIGN CHANGES: <n> must_fix findings`, which sends it back
to the planner. The script saves the result against the design as it stands, and a later change to the design needs
another review. Put every Must Fix you find in this review, because after a set number of reviews in a row that ask
for changes, the script approves the planner's revision without another one, and your prompt says when this is the
last.
