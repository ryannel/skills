# Revising a design after its review

A reviewer read the module's design and items against the brief and asked for changes, and your task names the
review. Building waits until the design passes, so settle every Must Fix finding in this turn.

For each Must Fix, change the design and the items until the finding no longer holds, and say in `LOG.md` what you
changed for it. The next reviewer reads the design afresh, not your answers, so the fix has to be in the files. The
Suggestions are yours to take or leave, so say in your report which you took and why.

Keep the brief's decisions, because the user made them. If a Must Fix can be settled only by going against one,
leave that part as it is and end with `NEEDS_CONTEXT:`, naming the decision and the finding, so the lead can take
it to the user.

When your task says this is the last round, no reviewer reads your fixes before building starts, so check each one
against its finding yourself before you end.
