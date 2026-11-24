# Revising a design after its review

A reviewer read the module's design and items against the vision and scope document and asked for changes, and your
task names the review. Building waits until the design passes, so settle every Must Fix finding in this turn.

For each Must Fix, change the design and the items until the finding no longer holds, and say in `LOG.md` what you
changed for it. The next reviewer reads the changed parts, not your answers, so the fix has to be in the files.
Make the smallest change that meets what the vision and scope document asks, and keep each item you touch a
closed claim. A finding that asks for more than the agreed scope and quality bar, such as inputs the user never
asked to support or a suite that must catch every possible defect, is a question of scope, which is the user's: leave the design as it is on that point, add an `Assumption:`
line saying what the plan leaves out, and name it in your report, because each demand you take on gives the next
review more to find and the user more to pay for. The Suggestions are yours to take or leave, so say in your report
which you took and why.

Keep the vision and scope document's decisions, because the user made them. If a Must Fix can be settled only by
going against one, leave that part as it is and end with `NEEDS_CONTEXT:`, naming the decision and the finding, so
the lead can take it to the user.

When your task says this is the last round, no reviewer reads your fixes before building starts, so check each one
against its finding yourself before you end.
