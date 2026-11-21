# Before the first build

This stage runs once the project is planned, while the settings' `Builders:` line has no count. `run` starts no
builder until it has one.

The planner leaves out how the user wants the agents to work, so ask before the first build, in words they know:
how many agents may build at once, whether finished work may go in without them looking, and what they want to
decide themselves. Choose what they can't, and tell them. Write the answers as the host, `Builders:`, `Merge:` and
`Human decides` lines, and commit them as [changing the settings](../references/settings.md) says.

This is also the moment to make room for the build. A build runs for days, and the more a session holds, the
sooner and more often it is compacted, losing part of the lead skill each time. Tell the user that the
conversation so far is saved in the brief and the plan. Recommend that they clear it (`/clear` in Claude Code,
`/new` in Codex) and ask for the lead again, which picks up from the project's files, or compact it (`/compact`) if
they'd rather keep it.

Then go on to [build](4-build.md).
