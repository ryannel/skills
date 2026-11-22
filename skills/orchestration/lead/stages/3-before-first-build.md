# Before the first build

This stage runs once the project is planned, while the settings' `Builders:` line has no count. `run` starts no
builder until it has one.

First, show the user what the plan will give them, in a few plain lines: the modules in build order, what they'll
be able to try after the first milestones, and what finishes the goal. Ask whether that is what they meant, because a
misread brief costs one message here and days of building later.

In the same message, show what the planner chose for them, from the end of the plan's `report`: each `Assumption:`
line, the reference each inspection is judged against and why the planner chose it, with its images when the
planner saved them in the folder the settings' `References:` line names, and the names it proposed in the glossary,
each with its one-line meaning. A reference sets how good subjective work has to be, so the user should agree it
before builders aim at it. The first plan names most of the project's concepts, so this is when the user can most
cheaply say "we call that a hold", before the names spread into code. No design has been reviewed yet, so a
correction now costs one planner turn and no review.

Remove the `Proposed:` line from each name the user agrees, and `adopt` the glossary. Give everything else they
change or answer to a planner as one `plan --kind change --one-step` task in their words, because only a planner
changes the plan files.

Once they agree, write the `Builders:` line with the number they gave, and commit it as
[changing the settings](../references/settings.md) says.

This is also the moment to make room for the build. A build runs for days, and the more a session holds, the
sooner and more often it is compacted. Tell the user that the conversation so far is saved in the brief and the
plan. Recommend that they clear it (`/clear` in Claude Code, `/new` in Codex) and ask for the lead again, which picks
up from the project's files, or compact it (`/compact`) if they'd rather keep it.

Then go on to [build](4-build.md). `run` starts each module's design review before its first builder.
