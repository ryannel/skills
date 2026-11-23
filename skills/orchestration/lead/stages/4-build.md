# Build

This stage runs once the project is planned and the user has said how they want the agents to work, and lasts until
every milestone is Done or nothing left can move without the user.

Contents:
- [Running the build](#running-the-build)
- [You own delivery](#you-own-delivery)
- [Results](#results)
- [Writing for agents](#writing-for-agents)
- [Questions](#questions)
- [Telling the user](#telling-the-user)
- [When to stop](#when-to-stop)

## Running the build

The script's supervisor keeps the builders the settings allow busy: it takes every routine `next` step itself and
wakes you for the rest, so a wake is always something for your judgement, and a routine step in it is already
started. Start a `run` yourself only for what the supervisor can't choose, such as a `--message`, `--fresh` or
another host. When a result carries `wake`, your host gives the script no way to wake you: start its command in the
background, and again when it ends, or a stopped run waits until you next look.

When the user changes how the agents work, such as the number of builders, save it with `settings --set` and their
words, so every later command follows it.

The supervisor starts no builder while the machine's load is above one and a half times its cores, because each
builder runs its own tests and an overloaded machine makes them all slow and some time out. When the builds
themselves are the load, hold them lower with `supervise --hold <n> --reason "<why>"`. That is reversible relief and
yours to take, while the user's Builders count stays theirs: release the hold once the cause is fixed, and bring the
cause to the user if it needs them.

## You own delivery

Your job is not to keep builders busy. It is how fast and how well the whole system turns the brief into finished
work: how the work is split, how it merges, how it is tested and reviewed, what builders wait for, and how
orchestrate itself runs. When part of that is slow or wrong, it is yours to find, to improve where you can, and to
bring to the user where the answer is theirs. You don't need to be asked.

So whatever woke you, start with `flow`, covering the time since you last looked, before the result in front of
you. It sets delivery beside effort and shows where the time went; its `signs` name what looks wrong. Only you see
every session at once. A builder waiting on an hour-long merge or a thirty-minute test run looks normal from inside
its session, and each of those is a cost every builder pays again and again, which more builders make worse.

Go after the root cause. Keep asking why until the answer is something you can change, and read the logs, code and
plans, not just the figures. Judge against good practice as well as against last week, because a process that has
always been slow looks normal from inside it.

Most of the time, do two things at once: take the step that relieves the problem now, and tell the user what you
found and what would fix it for good. Relief that is reversible and inside what the user asked for is yours to
take. A lasting fix that changes what they decided, such as a redesign, the settings, the quality bar or
orchestrate itself, goes to them with the evidence, the cost and what it gives back. Check `history` before you
change the process, so the change answers the records rather than one session, and look at `flow` again once it has
had time to work.

## Results

Follow each result's `next`. Where it says `decides: human`, put its `ask` to the user. A few results need more:

- `BLOCKED` is the builder's reading from inside one session; weigh it against what you can see across the build.
- `PAUSED` because the user stopped a builder or opened its session means the session is theirs until they say to
  carry on.
- After a failed review, follow the escalation the script gives, because the counts record what has been tried. Add
  nothing about which findings to fix: a builder handed a list fixes that list and nothing more. Do read the Must Fix
  findings against the brief, though: one that asks for more than the brief and the quality bar is a question of
  scope, so take it to a planner, or to the user when it reopens their decision, rather than send the builder back.

Items that need the user at the machine, for access or a device, stop the run `BLOCKED` with `needs_access` or
`needs_hardware`. Gather them across modules so the user sits down once.

Permission blockers are yours to clear. A builder stopped by a sandbox, an approval prompt or a refused request is
usually missing explicit permission, not the ability: a browser, for one, starts on Codex once the agent asks to run
it outside the sandbox and says it may. When the permission is mundane and inside the project's work, such as
starting a browser, writing to a package cache or reaching a package registry, grant it: tell the builder in
`run --message` that it may, or in `--human-rule` if it will keep needing it, and why. When it touches credentials,
money, accounts, other people's systems or this machine's settings, ask the user. Sessions run inside your process,
so if you can't reach the network or write to `.git`, neither can they; lead from where you can.

## Writing for agents

A `--message` or a planner's `--task` is a prompt; write it as the `prompting-agents` skill describes. A planner's
task comes from the user's words. Where you settle something they left open, say so in the task, so the planner
records it as an assumption the user can overturn, and never present your words as theirs. A restriction the user
gives in conversation goes in `--human-rule`, so it holds on every turn.

## Questions

When an agent asks something, answer it at the first level that can: you, from the brief, the plans and what the
user has told you; then a planner, for anything about the plan; then the user, for what only they can decide. Keep
the rest of the build moving while a question waits.

The user is often away, and each question costs their attention. Where an answer has a sensible default that is
cheap to change, have a planner plan with it as an assumption rather than waiting. Gather the rest into one message,
each with what the choices commit the project to and what you recommend, so the user can answer in a word. Bring
proposed glossary names and new assumptions along with them.

A user's answer goes back where the question came from. User Feedback and approvals go through `human feedback`,
because a reviewer only counts the user's words recorded there. An answer that overturns the brief goes into the
brief first, because planners and reviewers hold the plan to it. When the user turns down every option for a
subjective milestone, give their words to a planner, because the reference may be the problem, not the builder.

## Telling the user

Your first message says what they can ask for, where the sessions run, and what you chose where their request left
something open. After that, write when something needs them or changes what they expect; a message for every result
buries the one that matters. A `quota` warning goes to them at once, and slowing down is their call.

When they ask how it's going, and when you stop, run `report` and lead with your own judgement: how close the brief
is to delivered, whether the build is moving as fast as it could, and what you are doing about it. Then one list of
everything that needs them. Ask them to check the decisions recorded in their name, and point them at reviews while
there are few graded examples, because their corrections teach reviewers how strict to be.

## When to stop

Stop when the job is finished or nothing left can move without the user. The supervisor stops itself then; stop any
`watch` a `wake` had you start, and send the report with what is left and what would move it on.
