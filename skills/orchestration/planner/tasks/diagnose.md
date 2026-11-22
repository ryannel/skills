# Diagnosing a milestone

A milestone that keeps failing review is Waiting: For Diagnosis, and no builder works on it until you find out why.
Your task says how it got here:

- The same finding keeps coming back, so the fixes aren't holding.
- Each review finds something new, so each fix held and the milestone came no closer to passing.
- A reviewer marked a finding as one only a planner can settle, such as an item whose proof can't show what it
  claims, or two items that contradict each other.

Read every review your task lists and the code, and decide why the milestone keeps failing.

## Where the fault is

The fault may be in the plan. The milestone may be too big for one session and need splitting. It may depend on
something outside this module. Its mechanism may be unable to produce the behaviour, and need a new design. Its
items may be too broad, or impossible to meet as written.

The fault may also be outside the plan. A builder may fix the one place each review names while the same defect
stays where no reviewer has looked yet, or a reviewer's findings may go beyond what the items ask. A new plan cures
neither, and it costs a design review and a rebuild.

## When the plan is at fault

Change what is at fault, whether that is the items, the split into milestones or the design. Write the reason, and
each changed item's history, in `LOG.md`, and end with `PLANNED`.

When the fix belongs in another module, plan it as a milestone of that module and add it to the diagnosed
milestone's `depends_on`, because otherwise the script starts the diagnosed milestone's builder at once, before the
fix exists, and it fails the same way.

Give each milestone you split off a `diagnoses` count one higher than the one it came from shows, because the script
adds one to that milestone when your turn merges, and can't tell which new milestone came from which. Leave the other
counts and `findings` alone, because the script puts back any change a plan makes to them.

## When the plan is sound

Change no file, and make your last line `KEEP <MODULE> <milestone>: builder|reviewer|human: <why>`, naming who has
to act:

- `builder`, when a builder keeps breaking something. The script starts a new builder session with your reasons.
- `reviewer`, when the findings go beyond the items. A new builder session proves the items, and the script tells
  the next reviewer to judge them as written.
- `human`, when only the user can decide. The script blocks the milestone as Too Many Failed Reviews, with your
  reasons, for the lead to take to the user.

When your turn merges, the script records the diagnosis and resets the review counts itself. A milestone gets one
diagnosis, so if it keeps failing review after that, the script blocks it for the user. The one exception is a
later finding only a planner can settle, after a diagnosis for something else, which gets a diagnosis of its own.
