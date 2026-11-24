# Start planning

This stage runs when there is an approved vision and scope document and no plan yet, and again whenever the user
adds something small or changes their mind.

## The project settings

On a new project, you write the project settings, `ORCHESTRATE.md` at the repository's root, before the first plan.
You write them rather than the planner because you know the vision and scope document best: its purpose, its
quality bar, where it runs, and what is out of bounds. `settings --template` gives every line with a note on what
it does. Your judgement is in which of those choices to bring to the user, and in what words.

Most lines are yours to fill from the vision and scope document or leave at the template's value. Bring the user
only the choices that are theirs: which programs they build with, whether finished work may merge without them
looking, what they want to decide themselves, and how many agents may build at once. Ask in words they know, choose
what they can't, and tell them what you chose. Leave out any host or model line they named nothing for, so the
script's own defaults apply; `settings` shows what each kind of agent gets.

A few lines carry the user's permission, so only their words can fill them. `Merge: push` is standing permission to
push verified work to the main branch, so write `Merge: local` unless they allowed pushing. If the project's
`AGENTS.md` or `CLAUDE.md` says not to push without authorisation, say in the line's note that this line is that
authorisation, so an agent reading both knows which wins. Write the `Human decides` line in their words.

Leave the test and setup commands to the planner, which chooses them once it has chosen how the project is built.
Leave out the `Builders:` line until the user has seen the plan, so nothing builds before they agree to what it will
deliver.

## The first plan

You want a first plan the user can correct before anyone reviews it, so start it with `plan --one-step`, which stops
before the design reviews. Give the task in the user's words, and say how many builders they expect at once, because
there is no `Builders:` line yet and the planner needs the number to plan enough work to run side by side.

## Later changes

When the user adds something or changes their mind, add their words to the vision and scope document with the date, change the
decisions their words affect, and run `plan --kind change` with their words as the task. A change planner changes
only what their words reach. A change of mind doesn't count as a failed review.

When the user wants one kind of agent set differently from now on, such as planning on a larger model or reviewing
at a higher effort, that is a settings line, so save it with `settings --set` and every later agent of that kind
gets it.

When `plan` has finished, check where the project stands again.
