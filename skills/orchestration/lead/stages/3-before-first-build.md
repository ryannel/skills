# Before the first build

This stage runs once the project is planned, while the settings' `Builders:` line has no count.

Before any builder starts, get the user's agreement to what the plan will deliver and to every choice made in their
name. This is the cheapest moment to correct any of it: no design has been reviewed and nothing is built, so a
misread brief costs one message now rather than days of building later.

What they need to see is what the plan will give them, in a few plain lines (the modules in build order, what they
can try after the first milestones, and what finishes the goal), and what the planner chose for them, from the end
of the plan's `report`. That means each assumption, the reference each inspection is judged against and why, with
its images where the planner saved them, and the names it proposed for the glossary, each with its meaning. A
reference sets how good subjective work has to be, so the user should agree it before builders aim at it. The first
plan names most of the project's concepts, so this is also when the user can most cheaply say "we call that a
hold", before the names spread into code.

Take the `Proposed:` mark off each name the user agrees. Give everything else they change or answer to one change
planner in their words, because only a planner changes the plan files. Once they agree, save the number of builders
they give with `settings --set`.

A build runs for days, and the more a session holds, the sooner and more often it is compacted. The conversation so
far is saved in the brief and the plan, so tell the user that, and recommend they clear it (`/clear` in Claude Code,
`/new` in Codex) and ask for the lead again, which picks up from the project's files, or compact it (`/compact`) if
they'd rather keep it. Then go on to [build](4-build.md).
