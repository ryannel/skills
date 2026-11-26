# Before the first build

This stage runs once the project is planned, while the settings have no `Builders:` line.

Before any builder starts, get the user's agreement to what the plan will deliver and to every choice made in their
name. This is the cheapest moment to correct any of it: no design has been reviewed and nothing is built, so a
misread vision and scope document costs one message now rather than days of building later.

What they need to see is what the plan will give them, in a few plain lines (the modules in build order, what they
can try after the first work packages, and what they can do in the first release), and what the planner chose for
them, from the end of the plan's `report`. That means each assumption, the reference each inspection is judged
against and why, with its images where the planner saved them, and the names it proposed for the glossary, each
with its meaning. A reference sets how good subjective work has to be, so the user should agree it before builders
aim at it. The first plan names most of the project's concepts, so this is also when the user can most cheaply say
"we call that a hold", before the names spread into code.

Delete the `Proposed:` line from each name the user agrees. Give everything else they change or answer to one change
planner in their words, because only a planner changes the plan files.

Then agree which models do the work. The settings' Agents table gives, for each kind of agent, the model and effort
it runs on each host the user has: Codex, Claude Code, Antigravity. Every filled cell in a row is a choice the user
agrees to in advance, so the script can send each work package to whichever host would otherwise lose the most quota
at its next reset, rather than leaving one plan's quota unspent while another's runs out. Run `models` for what each
model is for and what it costs, and `quota` for where each host stands, then propose a table: a strong model for
planners and design reviewers, where a mistake costs the most, and a cheaper one for builders and reviewers. Leave a
host's column out when the user doesn't want work there. Save each cell they agree with `settings --set 'Agents
<Role> <Host>' '<model> <effort>'`. If `quota` shows a banked reset, mention it now, with when it expires, because
the plan for it can change how the build is set up.

Once they agree, save how they want the agents to work with `settings --set`: the programs, and the most builders at
once if they want a limit, or no limit, which can be per host ("two Codex, one Antigravity"). The supervisor starts
the build from that line, so no `run` is needed.

A build runs for days, and the more a session holds, the sooner and more often it is compacted. The conversation so
far is saved in the vision and scope document and the plan, so tell the user that, and recommend they clear it (`/clear` in Claude Code,
`/new` in Codex) and ask for the lead again, which picks up from the project's files, or compact it (`/compact`) if
they'd rather keep it. Then go on to [build](4-build.md).
