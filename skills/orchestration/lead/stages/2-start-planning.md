# Start planning

This stage runs when there is an approved brief and no plan yet, and again whenever the user adds something small
or changes their mind.

On a new project, write the project settings, `ORCHESTRATE.md` at the repository's root, from
[the template](../../planner/references/profile.md) and the brief, because you know the brief best: the purpose,
the quality bar, the targets from "Where it runs", and the licences and paths not to touch from "Never part of this"
and "Must not change". Leave out the test and setup commands, which the planner adds once it has chosen how the
project is built.

Write how the user wants the agents to work now too, because the planner and the design reviewers act on it: the
planner keeps what the user decides for them, and a design review runs on the review host. Use what the user has
already said, and ask in words they know for the rest: which programs they build with, whether finished work may go
in without them looking, what they want to decide themselves, and how many agents may build at once. Choose what
they can't, and tell them. Write the answers as the host, `Merge:` and `Human decides` lines, with `Merge: local`
unless they gave permission to push. Leave out the `Builders:` line until they have seen the plan, because `run`
starts no builder until it has one.

The planner works in the script's own checkout of the main branch's tip, so it sees only what is committed there. On a
new project, commit the brief, the glossary and the settings with git on the main branch, and push them under `Merge:
push`, because `adopt` never merges the settings, which carry the user's permissions. Later, run `adopt --worktree
<repo> <plans folder>/BRIEF.md`, which commits and merges that one file, and the glossary the same way.

Then run `plan --one-step --worktree <repo> --task '<what the user asked for, in their words>'`, adding "The project
brief is <path>." when there is one, and "The user allows up to <n> builders at once.", so the planner can plan
enough work to run side by side. The planner writes the module list and a plan for each module on the first thin
slice. `--one-step` stops before the design reviews, so the user can correct the plan before anyone reviews it.

The same holds later, when the user adds something or changes their mind. Add their words to the brief
with the date, change the decisions their words affect, merge it with `adopt`, and run `plan --kind change` with
their words as the task. `--kind change` gives the planner its instructions for changing a plan, so it changes only
what their words reach. A change of mind doesn't count as a failed review, and the changed milestones go back to
Not Started.

When the user wants one kind of agent set differently, such as "plan with Fable", write the line for it in the
settings, as [the template](../../planner/references/profile.md#a-model-or-an-effort-for-one-kind-of-agent) shows,
so every planner gets it, not only the first.

When `plan` has finished, check where the project stands again. A first plan leaves the settings without a
`Builders:` count, so the next stage is [before the first build](3-before-first-build.md).
