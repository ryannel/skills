# Orchestration

These skills let AI agents plan and build a software project while you stay in a chat. They work in Claude Code and
in Codex. They suit web apps, native apps, command-line tools, libraries and engines. They also suit work judged by
taste, such as a game's look or a set of icons, where you pick the look before the build starts.

You talk to one agent. It starts the others, and it comes back to you when a decision is yours.

The set's own names, such as milestone, item and Ready for Review, are listed with what they mean in the
[glossary](GLOSSARY.md).

## Who and what is involved

An agent is one AI session working in your repository. It runs in a host, which is Claude Code or Codex.

There are four kinds of agent. The lead is the agent you chat with, and it never writes or judges code. A planner
writes the plan. A builder writes the code. A reviewer judges a plan or some code, and it is always a new session,
so it has seen none of the work it judges.

There is also one script, `build/scripts/agent_loop.py`. It is not an agent. It is a set of commands, and the lead
runs them the way you would run `git commit`. The commands start the other agents, run the tests and keep the
records.

Each kind of agent has a skill that tells it how to do its job:

| Skill | Who reads it | Default model and effort | What it covers |
|---|---|---|---|
| [`interview-me`](interview-me/) | the lead | the lead's | Talking with you to find out what you want and why, and writing the project brief |
| [`domain-language`](domain-language/) | the lead, or any agent asked to sort out the project's names | that agent's | Agreeing one name for each thing in the project, and keeping the glossary |
| [`plan-module`](plan-module/) | the planner | Opus 5.5, high | Splitting a project into modules, and writing each module's design, milestones and done-when file |
| [`build-milestone`](build-milestone/) | a builder | Codex `gpt-6.1-sol` or Opus 5.5, medium | Building one milestone, proving it, and merging it |
| [`review-milestone`](review-milestone/) | a reviewer | Opus 5.5, medium | Judging a design, or a milestone that is Ready for Review |
| [`build`](build/) | the lead | Opus 5.5, medium (either host can lead) | Running the whole build: which commands to run, and when to come to you |

## How a project runs

The example is a small money-tracking tool. It reads a file of transactions and prints account balances.

### Saying what you want

1. You tell the lead what you want.
2. The lead reads the repository first, so it doesn't ask you for anything it could look up. Then it asks about
   the things only you can decide, one question at a time. It asks why you want this before it offers choices,
   and when it does offer them, it says which it recommends. It doesn't ask about anything that wouldn't change
   what gets built.
3. As names for things come up, the lead settles each one with you and writes it into the project's glossary, a
   file that holds the agreed name for each thing. Here, you call the lines of the file "transactions" and the
   lead had been saying "entries", so the glossary says Transaction and lists "entry" as a name to avoid.
4. The lead writes the project brief: your request word for word, the reason, what is left out, how you will
   judge the result, and a numbered list of decisions, each marked as yours or the lead's. It shows you the brief
   in the chat, and you approve or correct it. No planner starts before that, unless you say to skip this
   conversation.

### Planning

5. The lead runs the `plan` command with your words and the brief. The command starts a planner and waits for it.
   A planner can't ask you anything, which is why the brief comes first.
6. The planner splits the project into modules. A module is a part of the project that one builder can work on
   without touching the others. Here there are two: `core` reads the transaction file and adds up the accounts,
   and `report` prints the balances.
7. The planner writes two files for the whole project. The project settings, in `ORCHESTRATE.md`, hold facts about
   the project, such as the command that runs the tests and whether agents may push. Every agent reads them first,
   so the skills need to know nothing about your project in advance. The module list names each module and what it
   provides to the others: here, `core` provides a function that returns the balances, and `report` calls it.
8. The planner writes three files for each module. The design says what the module must do for the people who use
   it. The plan file lists its milestones, each a piece small enough for one builder to finish in one session:
   `core` has one, and `report` has two, "print balances from made-up numbers" and then "print balances from a real
   file". The done-when file lists, for each milestone, the items that must be true before it is Done, such as "a
   file with an unbalanced transaction is refused".
9. For each item, the planner writes how it will be proved. An Automated Check is a shell command that passes or
   fails. A Reviewer Inspection means a reviewer runs the product and looks at it. A Reviewer Question is a
   question a reviewer answers by reading the code. The planner also records when a milestone depends on one in
   another module: the second `report` milestone depends on the `core` milestone, because it needs real balances.
10. The `plan` command confirms the planner changed no record of finished work, merges the plan into your main
    branch, and prints one line saying what happened and which command to run next. The `run` and `review`
    commands end the same way.

### Reviewing the designs

11. The lead runs the `review` command on each module's design. Each run starts a new reviewer, which reads your
    request and the design and writes a review. The command saves it and sets the design to Design Approved or
    Design Changes Requested.
12. After Design Changes Requested, the lead runs `plan` again with the review, a planner fixes the design, and it
    is reviewed again. No builder starts on a module until its design is Design Approved. If the lead runs `run` on
    a module whose design has had no review, `run` does that review first.

### Building

13. The lead makes one worktree for each module: a second working copy of the repository, so two builders can work
    at once without overwriting each other's files.
14. The lead runs the `run` command once for each module. Each run starts a builder on the module's first
    milestone, which becomes In Progress. Here, two builders start, one on `core` and one on `report`.
15. Each builder writes the code and runs the Automated Checks. In the done-when file it marks each item as passed
    and notes where the evidence is saved: a screenshot, say, or a test log. It merges its work into the main
    branch and sets the milestone to Ready for Review, which means the builder says it is finished and nobody has
    verified it yet. If a builder stops before that, `run` sends it a message to continue, until it sets Ready for
    Review or reports that it can't go on.
16. The `run` command then tests the work itself. In a clean copy of the main branch it runs the project's test
    command and every Automated Check. If one fails, it sends the builder the failure, and the builder carries on.
17. A milestone needs a reviewer if any of its items is a Reviewer Inspection or a Reviewer Question, or if it is
    the module's last milestone. If it needs none, `run` sets it to Done in the module's record file. Otherwise it
    stays Ready for Review.

### Reviewing a milestone

18. The lead runs the `review` command on the milestone, which starts a new reviewer. The reviewer runs the tool,
    tries it on its own files, reads the changed code, and gives each item a Pass, a Fail or a Could Not Judge.
19. The command confirms the reviewer changed no code and saves the review. If every item passed, it sets the
    milestone to Done.
20. If the review failed, the milestone goes back to In Progress, and the lead runs the command the script printed.
    That depends on how many reviews the milestone has failed, and how many of those repeated a finding an earlier
    review had raised:

    | Failed reviews | What the lead runs | What happens |
    |---|---|---|
    | 1 or 2 | `run`, with the review | The same builder fixes what the reviewer found. |
    | 3 | `run`, with a new builder | A builder with no memory of the first attempts starts from the files and the review. |
    | 4 with a repeated finding | `plan` | The milestone is Awaiting Replan, and a planner rewrites it, because the plan may be the problem. |
    | 6, mostly on new findings | `plan` | The milestone is Awaiting Diagnosis. A planner reads every review and either rewrites it or names who has to act: the builder, the reviewer or you. |
    | either again, after that | nothing | The milestone is set to Too Many Failed Reviews. The lead asks you, with what failed in each review, whether to accept it, change its scope or try again. |

### The next milestone

21. The lead runs `run` again for the module, and the command starts a builder on the next milestone. A milestone
    that depends on another module doesn't start early: if the lead runs `run` for `report` before the `core`
    milestone is Done, the command prints that the milestone is Waiting on Dependency and starts nothing.
22. Steps 14 to 21 repeat until every milestone in every module is Done.

### When it needs you

23. Some items need a person. Suppose `report` has the item "the owner confirms the layout is readable". The
    planner marked it as needing human feedback. The builder does everything else, then stops and reports it, and
    `run` sets the milestone to Needs Human Feedback and prints the question.
24. The lead asks you in the chat and shows you the output, and you answer.
25. The lead runs the `owner answer` command with your words, which saves them in the record file. Then it runs
    `run` again, and the builder reads your answer and carries on.

A milestone can also stop because something it needs is missing, such as a login the builder doesn't have. It is
then Blocked, and the command prints what would unblock it.

### The report

26. The lead runs the `report` command. It prints what is Done, what each review said, what waits for you, every
    decision saved in your name, and what the build cost. The lead sends you that with its own notes.

### Where things stand

Every project keeps its plans in the same place, `docs/plans/`, with one folder per module. The page to open is
`docs/plans/STATUS.md`. The script writes it after every change it records, so it is never out of date and nobody
edits it. It opens with an overview: how many modules are done, what is waiting on you, what is happening now and
next, and what was recently done. Below that it lists every module in build order, finished and still to come,
with what each is for and how far along it is.

```
docs/plans/
  STATUS.md  BRIEF.md  GLOSSARY.md  ARCHITECTURE.md
  <MODULE>/  DESIGN.md  PLAN.md  LOG.md  DONE.json  ACCEPTED.json
```

The files agents read for detail sit in each module's folder. `PLAN.md` holds only what is left to build, and the
module's history goes in `LOG.md`, so the plan stays short enough to read. A project in the older layout, with files
such as `<MODULE>-PLAN.md`, moves with the script's `migrate` command.

## Milestone statuses

The walkthrough above meets every status a milestone can have, and the [glossary](GLOSSARY.md#statuses) lists them
in one table, with the shorter names the files and the script's output use for them, such as `claimed` for Ready
for Review. When `status` shows a milestone, it adds what you need to act on: which milestone it is waiting on,
how many reviews it has failed and which lead started it, the question for you, or what would unblock it.

## Why it is built this way

Agents often say work is finished when it isn't. So nothing in this process depends on an agent saying so, and
most of the design follows from that.

Each choice below says what it rests on: a measurement, one company's report of what worked for them, or our own
practice, kept because it fixed a problem we saw. Most published advice in this area is the second kind. The
figures and sources are in this repository: the research, and an assessment of the set against it, in
`workbench/orchestration-review/` (the report is `reports/Multi agent delivery harnesses 2026.md`), and the surveys
of other skill libraries in `workbench/intent-conversation/` and `workbench/domain-language/`.

### The lead finds out what you want before anyone plans

A planner can't ask you anything, so it settles whatever is unclear in your request with a guess, and the guess is
then built and reviewed as if you had asked for it. Our test runs showed both ways this goes wrong: a plan that read
"accents" too narrowly, and a plan that added an 80-column limit nobody wanted. So the lead talks to you first.

The conversation's rules come from fourteen other skill libraries, and lean on the three that measured their own
conversation skill: [Superpowers](https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md),
[Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/solutions/skill-design/confirmations-filter-by-salience-not-length-caps.md)
and [Matt Pocock's skills](https://github.com/mattpocock/skills). Asking only questions whose answer would change
the build roughly halved filler questions in Superpowers' blind-graded tests, and asking why before offering
choices is what kept the reason in the conversation. Those numbers grade the conversation. Nobody, us included, has
measured whether the result ends up closer to what the owner wanted. Some parts of the brief are our own: how the
result will be judged, which judgements only you can make, your request kept word for word, and the difference
between "I don't know", "I don't mind" and "you decide".

### Each thing has one name, kept in a glossary

Each agent starts new and knows only the files, so a name that isn't written down gets invented again, slightly
differently, by the next agent. This set went through that itself: by 10 November 2026 its files said "claimed",
"the loop", "the ladder" and "parked", and its owner couldn't tell what they meant. Going through them one by one
produced the set's own glossary and the rules in `domain-language`. The rules for keeping a glossary from going
wrong, such as holding names and nothing else, and removing entries as well as adding them, come from Matt Pocock's
and Compound Engineering's reports. Nobody has measured whether agents do better work with a glossary. We keep it
because the owner couldn't follow the build without it.

### What "done" means is written before building, and the builder can't change it

The planner writes the items before any code exists, and if a builder changes an item's wording, the `run` command
rejects its work. An agent that writes its own tests tends to write tests its code already passes. Two studies
measured this, [TDFlow](https://arxiv.org/abs/2510.23761) and [arXiv 2602.07900](https://arxiv.org/abs/2602.07900),
and Anthropic's harness for long-running work keeps its feature list in a file the builder may not edit for the
same reason.

### A script verifies the work

The `run` command runs every Automated Check itself, in a clean copy of the main branch, and only the script writes
the record of what is Done. This rests on measurements: [OverclaimBench](https://arxiv.org/abs/2609.20812) found
agents misreporting what they had covered in most runs where they skipped files, and
[METR](https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/) found
maintainers would merge far fewer changes than an automated grader passed.

### A script starts the agents, and the lead does not use subagents

A subagent is a helper agent that an agent starts from inside its own session. On 8 November 2026 the lead had to
be a Claude session, and it started planners and reviewers that way. Over the next two days all of it moved into
the script, because:

1. A subagent reports back in its own words, and the lead would have to believe it. A script command looks at what
   changed instead, and rejects a builder that edited an item, a reviewer that edited code, or a planner that
   marked something as passed.
2. The script can start a session on either host, so a milestone built by Codex can be reviewed by Claude. A
   reviewer from another company should share fewer of the builder's blind spots, though nobody has measured that
   for code review.
3. A build runs for hours or days, longer than one chat stays useful. The host saves every session the script
   starts, and `run` can resume the same builder after the lead's own conversation has been shortened or replaced.
4. A Claude Code subagent starts with none of the lead's conversation, while a Codex subagent starts with a copy of
   all of it. The script starts every reviewer the same way: a new session, in a clean copy of the commit it judges.
5. The script names the model and effort for every session on the command line, and saves what was used.
6. You can watch a session the script starts in the Codex app or in Claude desktop, and step in.

The cost is a script of about 6,100 lines that depends on how each host's command line behaves, which changes
between releases. And both companies advise starting with one agent and adding more only for a problem you can
name, so these skills also work in a single chat with no lead, and a small job should be done that way.

### A reviewer is a new session, and it uses the product

A reviewer has seen none of the building, and runs the product rather than judging from the code or the builder's
screenshots alone. This rests on two companies' reports, Anthropic's and Cognition's, not on measurements, and
Anthropic's own guides disagree between models about separate reviewers. The design review, once for each module,
comes from the same Anthropic report: a reviewer that agreed what "done" meant up front judges it more fairly later.

### The planner says what to build, and the builder decides how

An item says what will be observed when the work is right, not how to arrange it. Anthropic kept its planner at
that level when it removed almost everything else from its harness. In our first project, long items that scripted
their own proof were rewritten up to four times before any review had failed.

### One builder works on each module, and only a few builders run

Two agents writing to the same files overwrite each other, so each module has one builder, in its own worktree.
Cognition, Cohere, Cursor and Anthropic all report that more agents writing at once cost more and helped less;
Cohere measured results getting worse beyond two to four builders. Here one lock covers a whole merge, including the
test command, so a slow test command limits how fast builders can merge. That is a deliberate trade for two or three
builders.

### Everything is kept in files and in git

The plan, the items, the reviews and the record of what is Done are all files in your repository, so no agent has
to remember anything, and a new lead on either host can read them and carry on. Anthropic and OpenAI both
recommend this for long work, because a long session loses track of its early instructions.

### How agents are given their instructions

Each message that starts an agent says what must be true at the end, which skill to read, what the agent may
change, and how to end, because the script reads the last line. It gives no steps. The lead passes on file paths
and your own words, without its summary or opinion, because a reviewer handed a conclusion tends to agree with it.
Your request reaches the planner word for word: in one test run a plan read "accents" more narrowly than the owner
meant, and the finished tool dropped the letter `Ø`. Rules that must hold for a whole session are sent again when
it is resumed, and reviewers and planners are started unable to start other agents, because a reviewer that hands
its reading to a helper hasn't read the work. The
[`prompting-agents`](https://github.com/ryannel/skills/tree/main/skills/agent-writing/prompting-agents) skill
explains these rules and their sources.

### Our own practice

Nothing published supports these. Each is here because it fixed something we saw.

- After a failed review, the steps run from the same builder, to a new builder, to a rewritten plan or a planner's
  diagnosis, to stopping for you. Each step exists because the one before it has been tried. Only a repeated
  finding counts toward a rewrite, because one project's milestone failed eight reviews, each on something new
  that the builder then fixed, and stopped for its owner with nothing wrong in its plan.
- A milestone proved only by Automated Checks is Done without a reviewer, unless it is the module's last
  milestone, whose review reads the whole module. Anthropic's rule for when a reviewer is worth its cost was how
  hard the task is for the model, not how the work is proved, so this is a trade-off to revisit.
- Subjective work is judged against a quality bar in words and, where the project keeps them, references: the
  option you chose, or a set of reference images. It is never judged against one target image, because agents told
  to match an image copy its accidents too.
- Subjective work starts with options you choose from. Builders get a fresh opinion on their work and improve it
  before Ready for Review, and keep the best round rather than the last, because Anthropic's design runs sometimes
  peaked in the middle.
- Every agent is started with its model and effort named on the command line, because defaults change between
  releases. The skills and the Claude agent files name neither, because Claude lets those files override the
  command line.
- Builders and reviewers run at medium effort, and planners at high. Raise it where a run has been seen to fall
  short.
- The project settings name one model for each host and one effort. A line can set either for one kind of agent:
  `Claude planner: claude-fable-5-2 high` plans with a larger model on Claude Code, and `Reviewer: high` raises
  every reviewer's effort. A line that names a model names its host and applies only there, so the same settings
  still work when a planner runs on Codex or another company's agent. Say "plan with Fable" to the lead, and it
  adds the line.

### What our own runs showed

One real project, an engine, has been built with these skills since 9 November 2026. In its first day, four
milestones went from Ready for Review to Done, and a reviewer failed one of them twice before passing it, so
reviewers do fail work. Most of the time went on planning and design reviews, not building. Nobody has yet graded
whether those reviews were right. The earlier test runs, where most of the skills' wording was corrected, are
described under [How much this has been tested](#how-much-this-has-been-tested).

## Installing

The six skills link to each other's files, so install them together.

For an interactive install, run `npx @ryannel/orchestrate` and choose the hosts and where to install. Claude Code
can install for one project or for all of them, and Codex installs for all of them.

From a clone of the skills repository, `python3 install.py --plugins orchestrate` installs the `orchestrate` plugin
in both hosts. In Claude Code that is the skills plus the agent files for the planner and the reviewer. In Codex it
is the skills plus the reviewer's agent file, which `build/scripts/install_agents.sh --global --codex-only`
installs. Add `--repo <repo>` to prepare one repository as well: it adds a `CLAUDE.md` holding `@AGENTS.md`, for
older versions of Claude Code that wouldn't otherwise read `AGENTS.md`, and checks `ORCHESTRATE.md` once a planner
has written it.

`npx skills add` still works if you want the skills alone.

## Starting a project

You do all of this by talking to the lead, and never need a terminal. The smallest project is one module in an
empty repository with one commit.

1. Say what you want, or run `/interview-me`. The lead asks what it can't look up, including which hosts you build
   with and whether agents may push, and shows you the project brief to approve. To skip the conversation, say
   "just plan it" or run `/plan-module`. A planner then takes the safest reading of anything you left out, and
   lists what it assumed.
2. The lead has a reviewer read each design. Until a design is Design Approved, the plan can be revised freely.
   After that, a milestone's items change only when a planner rewrites them or you change the scope, so nobody can
   quietly make a requirement easier to meet.
3. Say "build it", or run `/build`, and say how many builders to run and on which hosts, such as "two Claude
   builders and one Codex". The lead keeps builders and reviewers going, and tells you when a milestone is Done or
   needs you.

You can also work in one chat with no lead: run `/interview-me`, `/plan-module`, then `/build-milestone`, in
either host. You can switch hosts partway, because everything the next agent needs is in the files.

Some decisions are yours: choosing between options, judging an item no agent can, accepting a milestone that
reviewers keep failing, changing the scope. The lead asks you in the chat and saves your answer in your own words,
and the report lists every decision saved in your name, so you can spot one you didn't make.

| Ask the lead | It runs |
|---|---|
| what is planned, what is next, and what is running in this repository | `status` |
| what is running on this machine, in every repository | `loops` |
| to stop cleanly and carry on later | `pause`, then `run` again |
| what the build has cost, for each milestone, split into planning, building and reviewing | `cost` |
| whether the Codex weekly usage limit will last | `quota` |
| for a report | `report` |
| to save a decision of yours | `owner answer`, `accept`, `rereview`, `unpark` or `scope` |

Each of these is a command of `python3 <where the skills are installed>/build/scripts/agent_loop.py`, and you can
run them yourself if you would rather.

## What the script verifies

Each command verifies an agent's work before it saves anything, and only the script can set a milestone to Done.
It keeps a record file, `ACCEPTED.json`, beside each done-when file, holding the approved items, the
commit that was tested, the reviews, your decisions, and whether each milestone is Done. Only the script's own
commits write to it.

### After a builder

Before the `run` command treats a milestone as Ready for Review, three things must hold. The done-when file is
still valid, the builder changed only its own fields, and the items are the approved ones, so a builder can't
reword an item to make it easier. The work is committed, with no stray files, and merged into the main branch. And
the test command and every Automated Check pass when the script runs them itself, in a clean copy of the main
branch. If a builder goes three turns in a row without changing or reporting anything, the command stops it.

### After a reviewer

A reviewer works in a clean copy of the commit it judges. The `review` command confirms that the reviewer changed
only its review, its folder of screenshots and its own fields in the done-when file, that each item's result agrees
with the review's last line, and that a failed review lists its findings. It counts the review itself. Then it merges the
review itself. If any of that is wrong, nothing is saved.

### After a planner

The `plan` command accepts a planner's work only if the planner ends with `PLANNED:` and the files it names, those
files exist and have changed, and each done-when file has a design beside it. A planner that stops with only a
progress note is sent a message naming what is missing. The command rejects a plan that marks any item as already
passed or touches a record file, merges the rest, and saves the new items as the approved ones.

A planner leaves its files uncommitted, and the command commits them. A planner or reviewer that made a commit of
its own is rejected, and so is one that ran while some other commit changed a record file on the main branch.

### Which milestone can start

One rule decides this for every command: a milestone can start only when the milestones before it in its module,
and those it depends on in other modules, are Done. When a lead starts a milestone, the script marks it In
Progress in a way every copy of the repository can see, so a second lead that runs `run` on it is told so.

A plan counts only once it is merged. If plan files are uncommitted or not yet merged, the commands name them, and
the `adopt` command merges just those files. A new module goes through a design review. Until its design is Design
Approved, and while nothing is built, `adopt` also approves revised items, which the design review then judges.
After that, only a planner run or `owner scope` changes the items.

### Your decisions

The lead asks you in the chat and runs an `owner` command with your words, the script saves them, and `report`
lists them. The `owner` commands refuse to run inside any session the script started, so a builder, reviewer or
planner can't save a decision for you. [Known limits](#known-limits) says what this does and doesn't stop.

## Claude Code and Codex

| | Codex | Claude Code | Another command-line agent |
|---|---|---|---|
| How a session starts | On a Mac with the Codex app running, as a thread the app lists under the project and runs itself. Otherwise with `codex exec --json`. Either way it can be resumed. | With `claude -p`, and it can be resumed. On a Mac with Claude desktop running and the CLI signed in, the session also appears in the Code tab. | With the `Host <name>:` command from the project settings, as one new process for each turn. |
| What you can do in the app | Watch it, type to steer it, and press Stop. After Stop the script reports the session as paused and leaves it to you. Running `run` again hands it back. | Watch the transcript. If you open the session to work in it, the script pauses and does not write to it at the same time. | Nothing. |
| Model and effort | Set when the session starts, and checked each turn from the session file. | Set when the session starts. The model is checked. The effort can't be. | Set in the command, and not checked. |
| What the record file keeps about the session | The model and effort asked for, the CLI version, and what the session file showed was used. | The same, but only the model can be shown as used. | The model and effort asked for. |
| Resumed sessions | With an active Codex goal, only the rules you gave are sent again. Without one, all the rules are. | The rules are sent again on every resumed turn. | Every turn after the first carries them. |
| Stopping reviewers and planners from starting agents | `-c features.multi_agent=false` | `--disallowedTools Agent`, plus the agent files when they are installed | Only the prompt says so. |
| Goals and the usage limit | Goal status, and a forecast of the weekly usage limit, from Codex's local files. | Neither. The script does not use Claude's `/goal`. | Neither. |
| Tokens used | Saved from `codex exec`'s output. A turn that ran in the app reports none, so use `quota` for those. | Saved, with Claude's list-price estimate, which is not what a plan is charged. A turn that was stopped early counts only the messages it finished. | None. |
| How an agent finds its skill | By name, as `orchestrate:<skill>` from the plugin. The prompt also gives the file path. | By name. The prompt also gives the file path. | The prompt gives the file path. |

A command's output shows the tokens for a whole session so far. Use `cost` to add things up.

## Known limits

### Sandboxes and permissions

Every session the script starts in the background runs inside the lead's process, with the lead's sandbox and
operating-system permissions. If the lead can't use the network or write to `.git`, its builders can't merge. A
builder that needs screen recording or a camera needs it granted to the app the lead runs in. A command that can't
write a file because of a sandbox stops and names the file, without retrying.

A browser won't start inside Codex's default `workspace-write` sandbox, so a Codex agent can run one only by asking
to run that command outside the sandbox. The script starts Codex with `approvals_reviewer=auto_review`, which
grants or refuses each request, and every kind of agent gets the same setting. In test runs, reviewers that asked
were granted it, and a builder that never asked ended up Blocked on four items. When a Codex build plainly needs a
browser, the script warns once. For dependable browser work, set `Codex sandbox: danger-full-access` in the
project settings, or give that module to a Claude builder. Claude sessions are not sandboxed this way.

The script runs Automated Checks with the lead's own permissions, outside any sandbox. The text of each check is
fixed once approved, but a builder can still change a script that a check calls, so read new check scripts. Proper
isolation would need a container.

### What protects the record file

The record file is protected by rules and by detection, not by cryptography. The script rejects a planner that
leaves a changed record file, a planner or reviewer that commits anything, and any planner, reviewer or builder
during whose run a commit the script didn't make changed a record file on the main branch.

It doesn't detect a record file edited between runs, by hand or by a session working on the side, and it doesn't
stop a session that deliberately forges the script's commit marker. The check for commits reads git's reflog, so it
misses a session that merges from a different working copy, one that commits without leaving a reflog entry, and
any session in a repository with reflogs turned off. What remains in those cases is the main rule: nothing is Done
unless the script's checks, a reviewer or you made it so, against the approved items.

A project that starts using these skills with work already built is a special case. In a repository that has never
had a record file, each module is taken as it stands, and its finished milestones count as Done. The script's first
commit writes a record file for every such module, and after that a module without one is new and has nothing Done.
A module merged just before that first commit is also taken as it stands, so on the first day, read what the first
planner run merged.

The script looks for record files in the plans folder named in the project settings. A commit that moves that
folder by hand hides the old record files, and every module then disappears from `status`, which is the sign. Move
it with the `migrate` command instead, which moves the files and the `Plans:` line together.

### Your decisions depend on an honest lead

You work in the chat, so the lead runs the `owner` commands, and the script can't tell a decision you made from one
a lead invented. What it does is save the words given with each decision and list every one in `report`. Read that
list.

The `owner` commands refuse to run where the `ORCHESTRATE_ROLE` environment variable is set, which the script sets
in every session it starts, so a builder, reviewer or planner can't accept its own work. The variable is confirmed
in background Codex and Claude sessions, and unconfirmed in sessions the Codex app runs. The commands also refuse
while a `run`, `review` or `plan` is working on the same module, though that doesn't stop a session building a
different module. When sessions run in the app, such a session can also use `adopt` to revise the items of another
module whose design isn't yet approved, which the design review still judges before anything is built. These stop
mistakes and casual shortcuts, not a determined agent, which could unset the variable.

### Claude's sign-in

Claude sessions are meant to use your signed-in plan, so the script removes every `ANTHROPIC_*` and `CLAUDE*`
environment variable from them except `CLAUDE_CONFIG_DIR` and `CLAUDE_CODE_OAUTH_TOKEN`. That also removes any
provider settings you keep in those variables. A credential helper you have set up could still supply other
credentials.

Anthropic has said `--bare` will become the default for `claude -p`. Bare mode reads only API-key sign-ins and
doesn't look for skills or agent files, so Claude builders will need a change then. Tested with Claude Code 2.1.239
and Codex 0.167.

### The reviewer is the least proven part

The `review-milestone` skill makes a reviewer use the product itself, read every changed line, write down what it
will look at before it looks, and fail what it finds. It comes with five example reviews that a person has graded.
You tune it by reading its early reviews and saying where it was wrong. Nobody has measured how often this reviewer
catches a fake or wrongly fails sound work. In the test runs below, reviewers did fail real defects, but no person
graded their results.

### Sessions in the apps

Showing sessions in the Codex app and in Claude desktop depends on parts of those apps that are not public
interfaces and can change with an update. They were proven with the Codex app 26.1103 and Claude desktop
4.23118.0. Each command's output says whether its session ran in the app or in the background, and setting
`ORCHESTRATE_HEADLESS=1` makes every session run in the background.

A new Codex thread opens in the app's window, which brings the app to the front, and starts with a one-line setup
turn. A Claude session runs in the script's own copy of the Claude CLI, so the CLI must be signed in.

### Smaller limits

- `loops` sees one machine. It keeps its notes under `~/.local/state/orchestrate/loops`, and setting
  `ORCHESTRATE_LOOPS_DIR` moves them. A session that can't write there, or that an older copy of the script
  started, is still listed, but without its tokens.
- The script runs on macOS and Linux only.
- Some of the rules for stopping a Codex builder read Codex's local goal database. Whether `codex exec` writes to
  it is not confirmed, and where it doesn't, those rules are skipped.
- With two builders, planners still run one at a time, so two modules that both need a revised plan wait in line.

### How much this has been tested

One engine project has run full milestones under version 1.5, with sessions in the app.

Before that, nine test runs took five small made-up projects from an empty repository to the end, with every
session in the background, using Claude, Codex, and the two mixed. The projects were a text tool (three runs), the
two-module money tool above with two builders at once (two runs), an icon set judged by taste (three runs), and a
browser game (one run). Seven ended with every milestone Done and a product that did what was asked. One produced a
tool that dropped the letter `Ø`, which the planning skill now guards against. The game stopped at its first
milestone, for reasons that have been fixed but not run again.

Those runs were short; the longest took 97 minutes. Each was run once, no person graded a review, and in each the
lead also played the owner. Only the last had the lead save an owner's decisions the way it does now. Accepting a
milestone by hand, asking for a new review and editing the scope are covered by automated tests only.

The `interview-me` and `domain-language` skills were added after those runs. Each was tested on three requests,
with a second agent playing the owner, against a run of the same request with no skill, graded blind against checks
written beforehand. With the skill, the agent asked why before offering choices, kept the owner's words apart from
its own decisions, and planned nothing before the owner approved. Without it, one agent built a whole app after two
replies, and another wrote a brief without asking a single question. The first round showed two gaps in the
skills, which were fixed and run again. No conversation has been run with a real
person, and each request was run once or twice, so this is a first reading. The record is in
`workbench/orchestration-review/polish-workspace/results.md`.

## Left out for now

The rule is to start small, and add something only when its absence has caused a problem. So these are not here
yet:

- merging through pull requests;
- agents dedicated to research;
- a second agent that confirms each finding;
- running Automated Checks in a container.

Some things were considered after a real failure and left out on purpose, because a smaller change already
covers that failure:

- a check for free disk space before a build: the script now removes a finished module's checkout instead;
- a check that rejects status written into plan files: `STATUS.md` is generated, and the skills say not to write
  status anywhere else;
- letting the owner's approval of a design survive an edit to its header: status no longer belongs in the header,
  so there is nothing to edit there;
- one planner lock per module: a second planner now waits for the first instead of being turned away.
