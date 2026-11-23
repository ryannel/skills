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
so it has seen none of the work it judges. Each has a skill, in a folder named for it:

| Skill | What it covers |
|---|---|
| [`lead`](lead/) | Leading the project: interviewing you for the brief, having it planned, running the build, and coming to you when a decision is yours |
| [`planner`](planner/) | Splitting a project into modules, and writing each module's design, milestones and done-when file |
| [`builder`](builder/) | Building one milestone, proving it, and merging it |
| [`reviewer`](reviewer/) | Judging a design, or a milestone that is Ready for Review |

There is also one script, `lead/scripts/agent_loop.py`. It is not an agent. It is a set of commands, and the lead
runs them the way you would run `git commit`. The commands start the other agents, run the tests and keep the
records. It is standard-library Python, and runs on macOS and Linux.

The skills say what each command is for and when to reach for it. How a command works is written once, in the
script, where it can't drift from what the code does. That includes the numbers the script holds, such as how many
failed reviews bring a diagnosis and which models it uses by default, so this README leaves them to the help:

- `agent_loop.py --help` lists the commands and the rules every result keeps. Each command ends by printing one JSON
  line, its result. When a command stops short, the result's `next` gives the command for the next step, who should
  run it and why. A `next` marked `decides: human` is a decision only you may make, and carries the question, `ask`,
  that the lead puts to you.
- `<command> --help` says what that command does, every result it can print and what each field means.
- `settings` prints the project settings as every command reads them: each setting and whether it was left at its
  default, the model and effort each kind of agent gets on each host and where that came from, and every file and
  folder the script uses, as an absolute path. `settings --template` prints a new settings file with what each line
  does, and `settings --set` changes one line on the main branch, in a commit that keeps your words.

## How a project runs

The example is a small money-tracking tool. It reads a file of transactions and prints account balances.

### Saying what you want

1. You tell the lead what you want.
2. The lead reads the repository and looks up how projects like yours are usually built, so it doesn't ask you for
   anything it could find out. It asks what you want and why before it offers any choices. Then it asks about the
   things only you can decide, a few numbered questions at a time, each with what the choice would commit the
   project to and the answer it recommends.
3. As names for things come up, the lead settles each one with you and writes it into the project's glossary. Here,
   you call the lines of the file "transactions" and the lead had been saying "entries", so the glossary says
   Transaction and lists "entry" as a name to avoid.
4. The lead writes the project brief: your request word for word, the reason, what is left out, how you will judge
   the result, and the decisions so far, each marked as yours or the lead's. You approve or correct it in the chat.
   No planner starts before that, unless you say to skip the conversation.

### Planning

5. The lead writes the project settings, `ORCHESTRATE.md`, from the template: what the project is for, how good the
   work has to be, where it runs. Every agent reads them first, so the skills need to know nothing about your
   project in advance. Then the lead runs `plan` with your words and the brief, which starts a planner.
6. The planner splits the project into modules, each a part one builder can work on without touching the others.
   Here there are two: `core` reads the file and adds up the accounts, and `report` prints the balances. The module
   list names each in build order with what it provides to the others: `core` provides a function that returns the
   balances, and `report` calls it.
7. For each module the planner writes a design, saying what the module must do for the people who use it; a plan
   file, listing its milestones, each small enough for one builder session; and a done-when file, listing for each
   milestone the items that must be true before it is Done, such as "a file with an unbalanced transaction is
   refused". On a big module it writes items for the next stretch of one or two milestones only, and a planner
   writes the rest as the module gets close to them.
8. Each item says how it will be proved. An Automated Check is a shell command that passes or fails. A Reviewer
   Inspection means a reviewer runs the product and looks at it. A Reviewer Question is a question a reviewer
   answers by reading the code. A milestone can also depend on one in another module: the second `report` milestone
   needs the `core` milestone, because it needs real balances.
9. `plan` confirms the planner changed no record of finished work, and merges the plan into your main branch. A
   question the planner couldn't answer comes back to you through the lead.

### Reviewing the designs

10. Each module's design is reviewed by a new reviewer before anything is built. The script saves the review and
    sets the design to Design Approved or Design Changes Requested. After Design Changes Requested, a planner revises
    the design and it is reviewed again. After a set number of reviews in a row have asked for changes, the planner
    revises once more and the script approves that revision without another review, so a design can't go round
    forever on ever-smaller refinements. No builder starts on a module until its design is Design Approved.

### Building

11. Before the first build, the lead shows you what the plan will give you and what the planner assumed for you, and
    asks how many builders may run at once, on which hosts. It saves your answer in the settings' `Builders:` line,
    and `run` starts no builder until that line has a count.
12. The lead runs `run` once for each module. With the settings' `Worktrees:` line, which the template has, the
    script builds each module in a worktree of its own on a `build/<module>` branch, so two builders never overwrite
    each other's files, and removes it once the module is finished and merged. Each run starts a builder on the
    module's first milestone, which becomes In Progress.
13. Each builder writes the code and runs the Automated Checks. In the done-when file it marks each item as passed
    and notes where the evidence is saved, such as a screenshot or a test log. It merges its work into the main
    branch, with the milestone still In Progress, and says it has finished.
14. `run` then tests the work itself, in a clean copy of the main branch and in its own process rather than the
    builder's sandbox. It checks that the builder changed only its own fields and left the items as approved, so a
    builder can't reword an item to make it easier. Then it runs the test command and every Automated Check. A check
    that already passed on exactly the same files isn't run again. If one fails, the builder gets the failure and
    carries on.
15. If every check passes, `run` sets the milestone to Ready for Review: the builder has finished and the script's
    checks passed, but no reviewer has judged it yet. Only the script sets this status.

A milestone needs a reviewer when any of its items is a Reviewer Inspection or a Reviewer Question, when it is the
module's last milestone, whose review reads the whole module, or when it ends a stretch a planner wrote, so each
stretch is read once before the next is built on it. Your pick between options is reviewed too, because a planner
always ends its stretch at the pick. Any other milestone is Done as soon as its checks pass.

Merges take turns. Branches that ask to merge while one is running merge together as a batch, with one run of the
test command, and a failing batch is split to find the branch that broke it.

### Reviewing a milestone

16. `run` goes on to the review, with a new reviewer, in a clean copy of the commit it judges. The reviewer runs the
    tool, tries it on its own files, reads the changed code, and gives each item a Pass, a Fail or a Could Not Judge,
    which counts as a fail, because a milestone nobody could check is not Done.
17. The script confirms the reviewer changed only its review and its own fields, and saves the review. If every item
    passed, it sets the milestone to Done. If not, the milestone goes back to In Progress.

### When a review fails

The script keeps two counts on each milestone: every failed review, and the failed reviews that failed an item an
earlier review had failed, or repeated an earlier finding. The second means the milestone isn't making progress on
that item, whether its fixes aren't holding or each fix meets a new defect. After each failed review, the first row that applies
is the next step. `next --help` gives the counts at which each row applies.

| After | What happens |
|---|---|
| A finding only a planner can settle, such as an item its proof can't prove; or either count reaching its higher limit | The milestone is Waiting: For Diagnosis. A planner reads every review and decides why it keeps failing. It either changes the items, a Re-plan, or keeps the plan and names who has to act: the builder, the reviewer or you. |
| Either count reaching its lower limit | A new builder session starts, with no memory of the first attempts, from the files and the review. |
| Any other failed review | The same builder carries on in the same session, with the review. |
| The same counts again, after the diagnosis | The milestone is Blocked: Too Many Failed Reviews. The lead asks you, with what failed in each review, whether to accept it, change its scope or reopen it for another try. |

A milestone gets one diagnosis, so one that keeps failing reaches you after one planner turn. The counts start again
after a diagnosis, after a planner changes the milestone's items, and after you change the milestone's scope or
reopen it. An item that fails again brings the diagnosis sooner than failures spread over different items do,
because a milestone can fail review on something new in each item while nothing is wrong with its plan, but an item
that keeps failing on new defects usually asks for more than the brief does.

A builder told about a failed review is also told that a review shows what one reviewer tried, and the next reviewer
starts again from the items. So the milestone is finished when every item is true as written, not when the review's
findings are cleared.

### The next milestone

18. After a pass, `run` starts a builder on the module's next milestone. One that depends on another module waits:
    if `report` reaches its second milestone before the `core` milestone is Done, it is Waiting: On Dependency. When
    every planned milestone is Done and the plan names more, the module is Waiting: For Planning, and a planner
    writes the next stretch.
19. These steps repeat until every milestone is Done, and the lead isn't needed for any of them. It is woken when a
    command stops at something that needs judgement, and by the script's supervisor at the lead check-in the
    settings give, and sooner on a warning sign such as a builder that has stopped making progress. The supervisor
    also starts the builders on work whose next step is routine, so the build doesn't wait for the lead. Each time, the lead looks
    at whether the work is moving as fast as it could, and steers: it sends a builder a message, starts a planner on a
    re-plan, changes the order of the work, or asks you.

### When it needs you

20. Suppose `report` has the item "the layout is readable in a terminal", which no agent can judge, so the planner
    marked it as needing user feedback. The builder does everything else and stops, and the milestone is Blocked:
    Needs User Feedback, with the question.
21. The lead asks you in the chat and shows you the output, and you reply, such as "looks good to me". It saves your
    words with `human feedback`, and runs `run` again. The builder reads your reply and carries on.

An item can also need a permission approved, such as screen recording, or a device connected, such as a phone. The
lead runs that milestone in a session you can see, at a time you are at the machine, and approving the prompt is all
you do. A milestone missing something else, such as a login, is Blocked with a reason, and the result says what
would unblock it.

### Reports

22. When you ask how it's going, and when it stops, the lead runs `report`. It prints what waits for you, every
    decision saved in your name, what is Done, what each review said, what has slowed down and what the build cost.
    The lead adds its own reading on top: how close the brief is to delivered, whether the build is moving as fast
    as it could, and what it is doing about anything that isn't.
23. `dashboard --open` gives the longer view: what each kind of agent and each model cost per day, the costliest
    milestones, every failed turn and review, how each version of the script compared with the last, and a retro.

## Statuses and who changes what

The [glossary](GLOSSARY.md#statuses) lists every status with its stored name. A milestone is Waiting when its next
step is lined up and needs nobody to step in, and Blocked when it can't move until someone does. A Blocked milestone
moves again when its block is cleared: your reply lifts Needs User Feedback, a run with you at the machine or the
device connected lifts Needs Access and Needs Hardware, the lead supplies the fact for Needs Context, a planner adds
what Needs Dependency was missing, and Too Many Failed Reviews waits for your decision.

Each field of the done-when file has one owner at any time, and the script refuses a change from anyone else:

| Who | What they change |
|---|---|
| Planner | The milestones, their items and how each is proved. The script saves new items as the approved ones and clears the old proof. |
| Builder | The milestone's status from Not Started to In Progress, and each item's result and evidence. |
| Reviewer | Each item's verdict, and the review's findings. |
| The script | Every other status, the counts of failed reviews, the record file and the status page. |
| You, through the lead | The items, with `human scope`. A milestone's status, with `human accept`, `rereview` or `reopen`. Your answers, with `human feedback`. |

A builder leaves Ready for Review and Done to the script, because other builders rebase onto the main branch, and a
status nobody had checked would claim checks that never ran. Planners and reviewers don't commit at all: the script
compares what they changed with this table, and either merges all of it or rejects all of it.

## The record file

Beside each done-when file, the script keeps a record file, `RECORD.json`, written only in the script's own commits.
It is committed, so every worktree, copy of the repository and lead reads the same one. For each milestone it holds a
hash of the approved items, the commit the script tested and the main-branch commit it ran the checks on, every
review, your decisions in your words, the tokens each builder run and review used, and whether the milestone is Done
and what made it so: its checks, a reviewer or you. It also holds the module's design review.

A milestone is Done only when the record file says so, for the items as they are now. A `done` in the done-when file
is not enough, which is what makes the done-when file safe for agents to edit.

A milestone can start only when the milestones before it in its module, and those it depends on, are Done. When a
lead starts one, the script marks it In Progress where every copy of the repository can see it, so a second lead is
told. A plan counts only once it is merged, and `adopt` merges plan files left uncommitted.

## Where things are kept

The plans live in the repository, in `docs/plans` unless the settings name another folder. `settings` prints where
each file is.

```
ORCHESTRATE.md                  the project settings
docs/plans/
  STATUS.md  BRIEF.md  GLOSSARY.md  ARCHITECTURE.md
  <MODULE>/  DESIGN.md  PLAN.md  LOG.md  DONE.json  RECORD.json
```

`PLAN.md` holds only what is left to build, and the history goes in `LOG.md`, so the plan stays short enough to read.
`ARCHITECTURE.md` opens with the module table: every module in build order, with what it's for.

The page to open is `STATUS.md`, the status page. The script writes it after every record it merges, so it is never
out of date and nobody edits it. It opens with a line of progress, then Needs you now, Choices made for you, Now and
next, and Recently done, and lists every module in build order below that.

Git holds what the project needs to build and run: code, plans, and the test data tests read. Everything else stays
on your computer inside the repository's `.git` folder, shared by every worktree, so the repository doesn't grow with
every capture. That is the working folder, which each worktree opens at `.orchestrate/evidence` and which holds
evidence, reviews, handoffs and the graded examples; the script's clean checkouts; and logs and ledgers. Links into
the working folder work on your computer but not in a fresh clone. It all stays until you ask the lead to clear it.
The lead runs `cleanup`, which lists what it would remove and removes it only on your yes. The script removes a
finished module's checkouts itself, and any nobody has been using for a while, sooner when the disk is nearly full;
`cleanup --help` says when.

Claude Code deletes its session files after 30 days, and Codex archives its own. So after every turn the script copies
the figures out of the session's file into the delivery history, under `~/.orchestrate/history/`: tokens, model and
effort, time and how the turn ended, never what was said, plus a copy of each review. `history` and the dashboard
read it. The hosts bill a plan rather than each token, so it keeps three measures and names which it shows: weighted
tokens, which compare a Claude turn with a Codex turn; Codex's share of its weekly limit; and Claude's list price,
which a plan doesn't charge.

## Locks and main-branch checks

A project without these settings lines never meets either. A lock lets runs share something the machine has only so
much of: a simulator one run at a time, or a GPU three runs at once. A command that holds a lock too long is stopped,
so one stuck run can't keep everyone waiting. A main-branch check is a check too slow to run before every merge. It
runs on the main branch's tip after merges, one run covering everything merged since the last, and an item that
depends on it waits for a run that covers its commit. A failure that holds is traced to the first commit that fails,
and the lead starts a planner on a fix or reverts that commit. `lock --help` and `main-check --help` give the rest.

## Changing the settings

Ask the lead, which runs `settings --set` with your words. Every agent is started with its model and effort named on
the command line, because defaults change between releases. With no settings line for a kind of agent, the script
names its own defaults, not the host's, so they change only when the script is updated. The settings name one model
for each host and one effort, and a line can set either for one kind of agent: `Claude planner: <model> high` plans
with a model of your choice on Claude Code, and `Reviewer: high` raises every reviewer's effort. A line that names a
model applies only on its host, so the same settings work when a planner runs on Codex. `settings` shows what each
kind of agent gets and why.

## Older projects

A project planned by an older version of the set stops with a message naming `migrate`, which moves it to the current
layout and names in one commit. It moves plans from the flat layout of before 2.0, with files such as
`<MODULE>-PLAN.md`, into a folder per module. It renames the stored names that 2.0 and 2.2 changed, such as a
milestone's `state` to `status` and `ACCEPTED.json` to `RECORD.json`. And it moves evidence that versions before
2.6.0 committed to git into the working folder, listing any item whose check names the old folder, for a planner to
fix. A worktree with commits from before the migration is moved with `migrate --branch`, because a rebase by hand
conflicts in exactly the files the renames rewrote. `migrate --help` lists every rename.

## Installing

The skills link to each other's files, so install them together. For an interactive install, run
`npx @ryannel/orchestrate` and choose the hosts and where to install. From a clone of the skills repository,
`python3 install.py --plugins orchestrate` installs the plugin in both hosts, with `prompting-agents`, which the
agents use to write for each other, and `domain-language`, which says how to keep a glossary. Add `--repo <repo>` to
add a `CLAUDE.md` holding `@AGENTS.md` to one repository, for older versions of Claude Code that don't read
`AGENTS.md`.

## Working with the lead

You do all of this by talking to the lead, and never need a terminal. Say what you want, or run `/lead`. To skip the
conversation, say "just plan it", and a planner takes the safest reading of anything you left out and lists what it
assumed. Once the plan is approved, say "build it", or name the modules. You can switch hosts partway, because
everything the next agent needs is in the files.

Some decisions are yours: choosing between options, judging an item no agent can, accepting a milestone reviewers
keep failing, changing the scope. The lead asks you in the chat and saves your answer in your own words, and the
report lists every decision saved in your name, so you can spot one you didn't make.

| Ask the lead | It runs |
|---|---|
| what is planned, what is next, and what is running in this repository | `status` and `ready` |
| what is running on this machine, in every repository | `runs` |
| to stop cleanly and carry on later | `pause`, then `run` again |
| what the build has cost, per milestone and kind of agent | `cost` |
| how fast milestones moved, beside commits, lock queueing and failed jobs | `flow` |
| who holds each lock, and who is waiting for it | `locks` |
| whether the Codex weekly usage limit will last | `quota` |
| how the build is going | `report`, with its own reading on top |
| to change a setting, such as the number of builders | `settings --set` |
| to clear what the build keeps on this computer | `cleanup` |
| to save a decision of yours | `human feedback`, `accept`, `rereview`, `reopen` or `scope` |

Each is a command of `python3 <where the skills are installed>/lead/scripts/agent_loop.py`, and you can run them
yourself if you'd rather.

## Why it is built this way

Agents often say work is finished when it isn't. So nothing in this process depends on an agent saying so, and most
of the design follows from that. Each choice below says what it rests on: a measurement, or one company's report of
what worked for them. The research, and an assessment of the set against it, are in `workbench/orchestration-review/`
in this repository (the report is `reports/Multi agent delivery harnesses 2026.md`), with the surveys of other skill
libraries in `workbench/intent-conversation/` and `workbench/domain-language/`.

### The lead finds out what you want before anyone plans

A planner that meets something unclear either guesses, and the guess is built and reviewed as if you had asked for
it, or asks, and the question waits until you're back. Test runs showed guesses going wrong both ways: a plan that
read "accents" too narrowly, so the finished tool dropped the letter `Ø`, and a plan that added an 80-column limit
nobody wanted. So the lead talks to you first, while you're in the chat. The conversation's rules lean on the skill
libraries that measured their own: [Superpowers](https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md),
[Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/solutions/skill-design/confirmations-filter-by-salience-not-length-caps.md)
and [Matt Pocock's skills](https://github.com/mattpocock/skills). Asking only questions whose answer would change the
build roughly halved filler questions in Superpowers' blind-graded tests. Nobody has measured whether the result ends
up closer to what you wanted.

Every question an agent can't answer comes to the lead, which answers it from what it can see, from a planner, or
from you. That keeps one agent responsible for clearing blocks and for your attention, so it can keep other work
moving while a question waits, and gather what's left into one message.

### Each thing has one name, kept in a glossary

Each agent starts new and knows only the files, so a name that isn't written down gets invented again, slightly
differently, by the next agent. So the project's glossary holds the agreed names, and an agent that names something
new adds it as proposed until you agree it. How to choose a name comes from the `domain-language` skill. Nobody has
measured whether agents do better work with a glossary. It is kept because the user couldn't follow the build
without one.

### What "done" means is written before building, and a script checks it

The planner writes the items before any code exists, and `run` rejects a builder that changes one. An agent that
writes its own tests tends to write tests its code already passes: [TDFlow](https://arxiv.org/abs/2510.23761) and
[arXiv 2602.07900](https://arxiv.org/abs/2602.07900) measured this, and Anthropic's harness for long-running work
keeps its feature list where the builder can't edit it for the same reason. The script runs every check itself and
writes the record of what is Done, because [OverclaimBench](https://arxiv.org/abs/2609.20812) found agents
misreporting what they had covered in most runs where they skipped files, and
[METR](https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/) found
maintainers would merge far fewer changes than an automated grader passed.

### A script starts the agents, and the lead does not use subagents

A subagent is a helper agent that an agent starts from inside its own session. The script starts every agent
instead, because:

1. A subagent reports back in its own words, and the lead would have to believe it. A script command looks at what
   changed, and rejects a builder that edited an item, a reviewer that edited code, or a planner that marked
   something as passed.
2. The script can start a session on either host, so a milestone built by Codex can be reviewed by Claude, which
   should share fewer of the builder's blind spots, though nobody has measured that for code review.
3. A build runs for days, longer than one chat stays useful. The host saves every session the script starts, and
   `run` resumes the same builder after the lead's own conversation has been shortened or replaced.
4. A Claude Code subagent starts with none of the lead's conversation, while a Codex subagent starts with all of it.
   The script starts every reviewer the same way: a new session, in a clean copy of the commit it judges.
5. The script names the model and effort on every launch and every turn, and saves what was used.

It never leaves either to a host's default, because the settings are your choice of quality and cost, and a host's
default changes between releases. A run that still ends on another model or effort is run again as set, and the lead
tells you. Only when the same mismatch comes back does the lead ask you, because then something on the host keeps
winning, and you decide whether to change that or the settings.

The cost is a large script that depends on how each host's command line behaves, which changes between releases.
And both companies advise starting with one agent and adding more only for a problem you can name, so these skills
also work in a single chat with no lead, and a small job should be done that way.

### The script runs the routine steps, and the lead watches delivery

Most steps need no judgement: a milestone Ready for Review gets its review, a failed review goes back to its builder,
and a pass moves on. Until 2.4 the script stopped after each, and the lead ran each printed command unchanged. One
36-hour build ran about 170 agent sessions, each costing the lead two turns, and that load got the lead's
conversation shortened four times. So `run` and `plan` now carry on through those steps, and stop at anything that
needs judgement. That frees the lead to see every run at once and notice what no single run can, such as builders
all waiting on the same thing. The warning signs the supervisor looks for are set where a sign would have caught a
stall seen in a real build, not from any measurement.

The steps between runs are routine too, so the script's supervisor takes them: one background process per repository
that the lead's next command starts if it isn't running. It keeps the builders the settings allow busy, and wakes the
lead for anything else: a run that ended, a warning sign, the check-in, a finished build, or a build waiting on you.
It then stops itself. A lead that had to keep a `watch` running could fall idle with nothing set to wake it, and a
host restart ended that `watch` silently. How the supervisor reaches the lead depends on the host:

| Lead's host | How it is woken |
|---|---|
| Claude Code, command line or desktop app | A message on the session's own messaging socket, which starts a turn |
| A Codex app thread | `codex queue --resume`, which starts a turn in the app |
| The Codex command line, Antigravity, or anything else | No push reaches it, so results carry `wake` and the lead keeps `watch` running |
| Any host, by the settings' `Lead wake:` line | A command of your own, given the message |

### A reviewer is a new session, and it uses the product

A reviewer has seen none of the building, and runs the product rather than judging from the code or the builder's
screenshots. This rests on Anthropic's and Cognition's reports, not on measurements. The design review comes from the
same Anthropic report: a reviewer that agreed what "done" meant up front judges it more fairly later. A milestone
proved only by Automated Checks is Done without a reviewer unless it ends a stretch or the module. Anthropic's rule
for when a reviewer is worth its cost was how hard the task is, not how the work is proved, so this is a trade-off to
revisit. Subjective work starts with options you choose from, and is judged against a quality bar in words and the
option you chose, never one target image, because agents told to match an image copy its accidents too.

### The planner says what, and the builder decides how

An item says what will be observed when the work is right, not how to arrange it. Anthropic kept its planner at that
level when it removed almost everything else from its harness. In the first real project, long items that scripted
their own proof were re-planned up to four times before any review had failed.

### The skills say when, and the script says how

The script always knows what kind of task it starts, so it puts that kind's instructions, from the skill's `tasks/`
folder, in the agent's prompt, and the skill keeps only what every kind shares. Paths, defaults, settings and what
each result means live in the script's `--help` and output. Earlier versions copied them into the skills, and every
change to the script left some copy wrong.

### One builder per module, and only a few at once

Two agents writing to the same files overwrite each other, so each module has one builder, in its own worktree.
Cognition, Cohere, Cursor and Anthropic all report that more agents writing at once cost more and helped less, and
Cohere measured results getting worse beyond two to four builders.

### Everything is kept in files and in git

The plan, the items, the reviews and the record of what is Done are all files in your repository, so no agent has to
remember anything, and a new lead on either host can read them and carry on. Anthropic and OpenAI both recommend
this for long work, because a long session loses track of its early instructions.

### How agents are given their instructions

Each message that starts an agent says what must be true at the end, which skill to read, what the agent may change,
and how to end, because the script reads the last line. It gives no steps. The lead passes on file paths and your own
words, without its summary, because a reviewer handed a conclusion tends to agree with it. Reviewers and planners are
started unable to start agents of their own, because a reviewer that hands its reading to a helper hasn't read the
work. The [`prompting-agents`](https://github.com/ryannel/skills/tree/main/skills/prompting-agents) skill explains
these rules and their sources.

## Claude Code and Codex

| | Codex | Claude Code | Another command-line agent |
|---|---|---|---|
| How a session starts | With `codex exec --json`. With `ORCHESTRATE_VISIBLE=1` on a Mac with the Codex app running, as a thread the app runs itself instead, which the app lists under Recents rather than under the project. Either way it can be resumed. | With `claude -p`, and it can be resumed. With `ORCHESTRATE_VISIBLE=1` on a Mac with Claude desktop running and the CLI signed in, the session also appears in the Code tab. | With the `Host <name>:` command from the project settings, as one new process for each turn. The command must take `{prompt}`, `{model}` and `{effort}`, so the script can name the model and effort every time. |
| What you can do in the app (with `ORCHESTRATE_VISIBLE=1`) | Watch it, type to steer it, and press Stop. After Stop the script reports the session as paused and leaves it to you. Running `run` again hands it back. | Watch the transcript. If you open the session to work in it, the script pauses and does not write to it at the same time. | Nothing. |
| Model and effort | Named when the session starts and on every turn, and checked each turn from the session file. | Named when the session starts and on every turn. The model is checked. The effort can't be. | Set in the command, and not checked. |
| Resumed sessions | With an active Codex goal, only the rules you gave are sent again. Without one, all the rules are. | The rules are sent again on every resumed turn. | Every turn after the first carries them. |
| Stopping reviewers and planners from starting agents | `-c features.multi_agent=false` | `--disallowedTools Agent` | Only the prompt says so. |
| Goals and the usage limit | Goal status, and a forecast of the weekly usage limit, from Codex's local files. | Neither. The script does not use Claude's `/goal`. | Neither. |
| Tokens used | Saved from `codex exec`'s output. A turn that ran in the app reports none, so use `quota` for those. | Saved, with Claude's list-price estimate, which is not what a plan is charged. | None. |
| How an agent finds its skill | By name, as `orchestrate:<skill>` from the plugin. The prompt also gives the file path. | By name. The prompt also gives the file path. | The prompt gives the file path. |

## Known limits

### Sandboxes and permissions

Every session the script starts in the background runs inside the lead's process, with the lead's sandbox and
operating-system permissions. If the lead can't use the network or write to `.git`, its builders can't merge. A
builder that needs screen recording or a camera needs it granted to the app the lead runs in.

A browser won't start inside Codex's default `workspace-write` sandbox, so a Codex agent runs one by asking to run
that command outside it, which Codex's auto-review grants or refuses. The Codex prompt tells agents to ask from the
start, and the lead clears a refusal by giving the agent explicit permission, or asks you when the permission
isn't mundane. `settings` and `run` warn when a Codex build plainly needs a browser.

The script runs Automated Checks with the lead's own permissions, outside any sandbox. The text of each check is fixed
once approved, but a builder can still change a script that a check calls, so read new check scripts. Proper
isolation would need a container.

### What protects the record file

The record file is protected by rules and by detection, not by cryptography. The script rejects a planner that leaves
a changed record file, a planner or reviewer that commits anything, and any agent during whose run a commit the
script didn't make changed a record file on the main branch. It doesn't detect a record file edited by hand between
runs, or a session that forges the script's commit marker, and its check for commits reads git's reflog, so it misses
a session that merges from a different working copy. What remains is the main rule: nothing is Done unless the
script's checks, a reviewer or you made it so, against the approved items.

In a repository that has never had a record file, each module is taken as it stands, and its finished milestones
count as Done, so work built before the project used these skills isn't built again. On the first day, read what the
first planner run merged. A commit that moves the plans folder by hand hides the record files, and every module
disappears from `status`. Move it with `migrate --to` instead.

### Your decisions depend on an honest lead

The lead runs the `human` commands for you, and the script can't tell a decision you made from one a lead invented.
It saves the words given with each decision and lists every one in `report`, so read that list. The `human` commands
and `settings --set` refuse to run inside any session the script started, and the `human` commands refuse while a run
holds the module. That stops mistakes and casual shortcuts, not a determined agent.

### Claude's sign-in

Claude sessions are meant to use your signed-in plan, so the script removes every `ANTHROPIC_*` and `CLAUDE*`
environment variable from them except `CLAUDE_CONFIG_DIR` and `CLAUDE_CODE_OAUTH_TOKEN`, which also removes any
provider settings you keep there. Anthropic has said `--bare` will become the default for `claude -p`. Bare mode
reads only API-key sign-ins and doesn't look for skills, so Claude builders will need a change then.

### The reviewer is the least proven part

The `reviewer` skill makes a reviewer use the product, read every changed line, write down what it will look at
before it looks, and fail what it finds. It comes with example reviews a person has graded, and when the settings
name a graded examples file, as the template does, each review you overturn is added to it, so later reviewers learn
how strict you are. Nobody has measured how often this reviewer catches a fake or wrongly fails sound work.

### Sessions in the apps

With `ORCHESTRATE_VISIBLE=1`, sessions show in the Codex app and in Claude desktop instead of running in the
background. That depends on parts of those apps that are not public interfaces, proven with the Codex app 26.1103 and
Claude desktop 4.23118.0, and an update can break it. Each result says where its session ran.

### Smaller limits

- `runs` sees one machine.
- Some of the rules for stopping a Codex builder read Codex's local goal database. Whether `codex exec` writes to it
  is not confirmed, and where it doesn't, those rules are skipped.

## Left out for now

The rule is to start small, and add something only when its absence has caused a problem. So agents dedicated to
research, a second agent that confirms each finding, and running Automated Checks in a container are not here yet.

Four larger ideas came out of the review of a 36-hour build. Each needs a design of its own, so they wait:

- Merging through pull requests. The merge queue and its batches assume the script merges straight into the main
  branch, and a pull request adds a second place where a merge can wait, fail or be changed.
- A spending budget. The token figures aren't charges: Claude's is a list price, and a turn in the Codex app reports
  none, so a budget would stop a build on the wrong numbers. `quota` forecasts Codex's weekly limit meanwhile.
- Starting a module's next milestone while its last is with a reviewer, which would build on work that may fail.
  Instead, a run waiting on a reviewer or planner gives up its builder slot to another module.
- Full support for a Codex lead in the command-line app. The supervisor wakes a lead in Claude Code or in a Codex
  app thread by itself, but a message queued for a CLI thread waits until that thread next takes a turn, so a CLI
  lead still waits on `watch`, and the skill hasn't been worked through for how Codex runs long commands.

A check for free disk space before a build was considered and left out, because the script already removes
checkouts nobody is using, sooner when the disk is low, and the supervisor warns the lead.
