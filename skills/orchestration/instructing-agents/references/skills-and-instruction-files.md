# Skills and standing instruction files

## Skills

How to write, package and test a skill, including its description, layout, frontmatter and where it's installed,
belongs to `skill-creator`. Use that skill for those. Two points from this skill still apply to what goes inside one.

A shared skill steers every agent that loads it, whichever model that is. So keep corrections for one model out of
it, and put them in that model's goal or brief instead.

A rule that must hold goes in a hook, a permission rule or a sandbox. Prose in a skill is context. It doesn't enforce
anything.

## AGENTS.md and CLAUDE.md

These files load into every session. So every line costs attention on every task, whether it's relevant or not.

Stick to stable norms the agent can't work out for itself. That means commands, conventions, boundaries, where things
live, and what needs a human. Move procedures into skills, which load only when needed. Leave out architecture the
agent can read for itself.

Point to files by when to use them, not as a mandate. Write "Use X.md when Y". Don't write "read X.md, Y.md and Z.md
before every edit".

Drop old pushes. Encouragement like "run the tests" makes Astra test too much. Lines like "keep going" make current
Claude models work too much. Give standing permission for the safe test loop instead.

Look again at "ask first" language. Strong wording that was written to stop older models over-reaching makes Astra
stop work it should continue. State the real boundaries accurately. Those are things that are irreversible,
destructive, outward-facing, cost money, or are in other people's areas.

Say which instructions win. The user's instructions win over a skill's guidance.

Layer the files by directory. Codex joins them together from the root down, and closer files win. It stops at 32 KiB
by default. So put overrides next to the work they govern.

Prune regularly. For each line, ask whether removing it would cause a mistake you've actually seen. If a line keeps
being ignored, that usually means the file is too long. More emphasis won't help.

There's a cheap way to test a line you suspect. Replay one real session prompt twice from the same snapshot, once with
the line and once without it. Then compare quality, tool calls, tokens and time.
