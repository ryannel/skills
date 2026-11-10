# Orchestration

These skills let AI agents plan and build a software project while you stay in a chat. They work in Claude Code and
in Codex. They suit web apps, native apps, command-line tools, libraries and engines. They also suit work judged by
taste, such as a game's look or a set of icons, where you pick the look before the build starts.

You talk to one agent. It starts the others, and it comes back to you when a decision is yours.

## Who and what is involved

An **agent** is one AI session, in Claude Code or Codex, working in your repository. Claude Code and Codex are
called **hosts** below.

There are four kinds of agent:

- The **lead** is the agent you chat with. It never writes code and never judges code.
- A **planner** writes the plan.
- A **builder** writes the code.
- A **reviewer** judges a plan or some code. A reviewer is always a new session, so it has seen none of the work it
  judges.

There is also one **script**, `build/scripts/agent_loop.py`. It is not an agent. It is a set of commands, and the
lead runs them the way you would run `git commit`. The commands start the other agents, run the tests and keep the
records. Some files call the script "the loop", because its `run` command keeps a builder going until the builder
has finished.

Each kind of agent has a skill that tells it how to do its job:

| Skill | Who reads it | Default model and effort | What it covers |
|---|---|---|---|
| [`plan-module`](plan-module/) | the planner | Opus 5.5, high | Splitting a project into modules, and writing each module's design, milestones and done-when file |
| [`build-milestone`](build-milestone/) | a builder | Codex `gpt-6.1-sol` or Opus 5.5, medium | Building one milestone, proving it, and merging it |
| [`review-milestone`](review-milestone/) | a reviewer | Opus 5.5, medium | Judging a design, or a milestone that is Ready for Review |
| [`build`](build/) | the lead | Opus 5.5, medium (either host can lead) | Running the whole build: which commands to run, and when to come to you |

## How a project runs

The example is a small money-tracking tool. It reads a file of transactions and prints account balances.

### Planning

1. You tell the lead what you want.

2. The lead runs the `plan` command and passes it your words. The command starts a planner and waits for it to
   finish.

3. The planner splits the project into modules. A **module** is a part of the project that one builder can work on
   without touching the other parts. Here there are two: `core` reads the transaction file and adds up the accounts,
   and `report` prints the balances.

4. The planner writes two files for the whole project:
   - The **project settings**, in a file called `ORCHESTRATE.md`. It holds facts about the project, such as the
     command that runs the tests and whether agents may push. Every agent reads it first, so the skills need to
     know nothing about your project in advance.
   - The **module list**. It names each module and says what each one provides to the others. Here, `core` provides
     a function that returns the balances, and `report` calls it.

5. The planner writes three files for each module:
   - A **design**. It says what the module must do for the people who use it.
   - A list of **milestones**. A milestone is a piece of the module small enough for one builder to finish in one
     session. `core` has one. `report` has two: "print balances from made-up numbers", then "print balances from a
     real file".
   - A **done-when file**. For each milestone, it lists the things that must be true before the milestone is Done.
     Each of those things is an **item**. "A file with an unbalanced transaction is refused" is an item.

6. For each item, the planner writes how it will be proved. There are three ways:
   - An **Automated Check** is a shell command that passes or fails.
   - A **Reviewer Inspection** means a reviewer runs the product and looks at it.
   - A **Reviewer Question** is a question a reviewer answers by reading the code.

   The planner also writes down when a milestone **depends on** a milestone in another module. Here, the second
   `report` milestone depends on the `core` milestone, because it needs the real balances.

7. The `plan` command finishes. It confirms the planner wrote only plan files. It merges them into the main branch
   of your repository. Then it prints one line that says what happened and which command to run next. Every command
   below ends the same way.

### Reviewing the designs

8. The lead runs the `review` command on each module's design. Each run starts a new reviewer. The reviewer reads
   your request and that module's design, and writes a review. The command saves the review in the repository and
   sets the design's status to **Design Approved** or **Design Changes Requested**.

9. If the status is Design Changes Requested, the lead runs `plan` again and passes it the review. A planner fixes
   the design, and the lead runs `review` on it again. No builder starts on a module until its design is Design
   Approved. If the lead runs `run` on a module whose design has had no review, the `run` command runs that review
   first.

### Building

10. The lead makes one **worktree** for each module. A worktree is a second working copy of the repository, so two
    builders can work at once without overwriting each other's files.

11. The lead runs the `run` command once for each module. Each run starts a builder on that module's first
    milestone, which becomes **In Progress**. Here, two builders start: one on `core`, one on `report`.

12. Each builder builds its milestone. It writes the code and runs the Automated Checks. In the done-when file, it
    marks each item as passed and notes where the **evidence** is saved. Evidence is saved proof, such as a
    screenshot or a test log. The builder merges its work into the main branch. Last, it sets the milestone to
    **Ready for Review**, which means "the builder says this is finished, and nobody has verified it".

    If a builder stops before that, the `run` command sends it a message to continue. This repeats until the builder
    sets Ready for Review or reports that it can't go on.

13. The `run` command tests the builder's work. It makes a clean copy of the main branch, and runs the project's
    test command and every Automated Check there. If one fails, the command sends the builder the failure, and the
    builder continues working.

14. The `run` command finishes. A milestone needs a reviewer if any of its items is a Reviewer Inspection or a
    Reviewer Question, or if it is the module's last milestone. If it needs no reviewer, the command sets it to
    **Done** in a record file. Otherwise it stays Ready for Review.

### Reviewing a milestone

15. The lead runs the `review` command on the milestone. The command starts a new reviewer. The reviewer runs the
    tool, tries it on its own files, and reads the changed code. It writes a review that gives each item a Pass, a
    Fail or a Could Not Judge.

16. The `review` command finishes. It confirms the reviewer changed no code, and saves the review. If every item
    got a Pass, it sets the milestone to Done.

17. If the review failed, the milestone goes back to In Progress, and the lead runs the command the script printed.
    Which command that is depends on how many reviews the milestone has failed:

    | Failed reviews | What the lead runs | What happens |
    |---|---|---|
    | 1 or 2 | `run`, with the review | The same builder fixes what the reviewer found. |
    | 3 | `run`, with a new builder | A builder with no memory of the first attempts starts from the files and the review. |
    | 4 | `plan` | The milestone is **Awaiting Replan**, and a planner rewrites it, because the plan may be the problem. |
    | 4 more, after the rewrite | nothing | The milestone is set to **Too Many Failed Reviews** and waits for you. |

### The next milestone

18. The lead runs `run` again for the module. The command starts the builder on the module's next milestone.

    A milestone that depends on another module does not start early. If the lead runs `run` for `report` before the
    `core` milestone is Done, the command prints that the milestone is **Waiting on Dependency** and starts nothing.

19. Steps 11 to 18 repeat until every milestone in every module is Done.

### When it needs you

20. Some items need a person. Suppose `report` has the item "the owner confirms the layout is readable". The
    planner marked that item as needing human feedback when it wrote it. The builder does everything else, then
    stops and reports it. The `run` command sets the milestone to **Needs Human Feedback** and prints the question.

21. The lead asks you in the chat, and shows you the output. You answer.

22. The lead runs the `owner answer` command with your words. The command saves them in the record file. The lead
    runs `run` again, and the builder reads your answer and continues.

A milestone can also stop because something it needs is missing, such as a login the builder doesn't have. That
milestone is **Blocked**, and the command prints what would unblock it.

### The report

23. The lead runs the `report` command. It prints what is Done, what each review said, what waits for you, every
    decision saved in your name, and what the build cost. The lead sends you that, with its own notes.

## Milestone statuses

| Status | Means | Extra information |
|---|---|---|
| Not Started | No builder has worked on it yet. | |
| Waiting on Dependency | It can't start until another module's milestone is Done. | which milestone |
| In Progress | A builder is working on it. | how many reviews it has failed, and which lead started it |
| Ready for Review | The builder has finished, and no review has run yet. | |
| Needs Human Feedback | It stopped on something only a person can decide. | the question |
| Blocked | It stopped because something it needs is missing. | what would unblock it |
| Awaiting Replan | It failed four reviews, so a planner has to rewrite it. | |
| Too Many Failed Reviews | It failed four more reviews after the rewrite, and waits for you. | |
| Done | Every check and review has passed. | |

A module's design has three statuses of its own: Design Ready for Review, Design Changes Requested and Design
Approved.

The files and the script's output use older, shorter names for some of these. You will see them if you open a
done-when file or read a command's output:

| Status | Older name |
|---|---|
| Not Started | `open` |
| Waiting on Dependency | `waiting` |
| In Progress | `in_progress`, or `taken` when another lead started it |
| Ready for Review | `claimed` |
| Needs Human Feedback | `blocked`, on an item marked `attended` |
| Awaiting Replan | `replan_owed` |
| Too Many Failed Reviews | `parked` |
| Done | `done`, or "accepted" |
| Automated Check, Reviewer Inspection, Reviewer Question | `check`, `inspect`, `ask` |
| Could Not Judge | `cant_tell` |

## Why it is built this way

The short version: agents often say work is finished when it isn't. So nothing in this process depends on an agent
saying so. Most of the design follows from that.

Each choice below says what it rests on. Some choices rest on measurements. Some rest on one company's report of
what worked for them. Some are our own practice, kept because it fixed a problem we saw. Most published advice in
this area is of the second kind, and the text says so where it matters.

### What "done" means is written before building, and the builder can't change it

The planner writes the items before any code exists. A builder may mark an item as passed. If a builder changes
the wording of an item, the `run` command rejects the builder's work.

The reason is that an agent that writes its own tests tends to write tests its code already passes.

- A study called TDFlow gave agents tests written by people, and they solved 94.3% of a standard set of tasks. The
  figure reported for agents that wrote their own tests is about 69.8%. We have that second number only from a
  summary. ([TDFlow](https://arxiv.org/abs/2510.23761))
- A study of six models found that the tests agents wrote for themselves made no measurable difference to their
  results, and were mostly print statements. ([arXiv 2602.07900](https://arxiv.org/abs/2602.07900))
- Anthropic's harness for long-running work keeps its list of features in a JSON file that the builder is told not
  to edit, for the same reason.
  ([Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents))

### A script verifies the work

When a builder says a milestone is finished, the `run` command runs every Automated Check itself, in a clean copy
of the main branch. Only the script writes the record of what is Done.

The reason is that an agent's own report is often wrong, and wrong in a confident voice.

- OverclaimBench gave twelve models review tasks with planted defects. In 67.9% of runs the agent did not read
  every file. Of those incomplete runs, 80.4% gave a misleading account of what they had covered.
  ([OverclaimBench](https://arxiv.org/abs/2609.20812))
- METR had four maintainers review 296 changes that had passed an automated grader. The share they would merge
  was about 24 points lower than the grader's pass rate. Passing tests is not the same as being finished.
  ([METR](https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/))

Both of these are measurements.

### A script starts the agents, and the lead does not use subagents

A **subagent** is a helper agent that an agent starts from inside its own session. Both hosts have them. The lead
could start its builders and reviewers that way, and the first version of these skills partly did. On 8 November
2026 the lead had to be a Claude session. It used the script only to start Codex builders, and it started planners
and reviewers as subagents.

Over the next two days we moved all of it into the script, for these reasons:

1. A subagent reports back to the lead in its own words. The lead would have to believe that report, which is the
   problem described above. A script command can look at what changed instead. It rejects a builder that edited an
   item, a reviewer that edited code, and a planner that marked something as passed.
2. A subagent runs on the lead's host. A Claude lead gets Claude subagents. The script can start a session on
   either host, so a milestone built by Codex can be reviewed by Claude. A reviewer from a different company shares
   fewer of the builder's blind spots. The support for that is modest: Cognition reports gains from mixing models
   on its hardest cases, and nobody has measured it for code review.
3. A build runs for hours or days, which is longer than one chat stays useful. The host saves every session the
   script starts. The `run` command can resume the same builder later, even after the lead's own conversation has
   been shortened or replaced by a new one.
4. "A new session" means different things on the two hosts. A Claude Code subagent starts with none of the lead's
   conversation. A Codex subagent starts with a copy of all of it unless told otherwise. A reviewer must not have
   seen the building. The script starts every reviewer the same way: a new session, in a clean copy of the commit
   it is judging. ([Claude Code subagents](https://code.claude.com/docs/en/sub-agents),
   [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md))
5. A subagent uses the lead's model unless something sets another. The script names the model and effort on the
   command line for every session, and saves what was used.
   ([Claude Code model configuration](https://code.claude.com/docs/en/model-config))
6. You can watch a session the script starts in the Codex app or in Claude desktop, and step in.

This choice has a cost. The script is about 6,100 lines, and it depends on how each host's command line behaves,
which changes between releases.

There is also advice that points the other way. Both companies say to start with one agent and add more only for a
problem you can name. Anthropic reported in October 2026 that a single agent with skills often did better than a
design built from subagents.
([When to fold subagents into your main agent loop](https://claude.com/blog/building-agents-when-to-fold-subagents-into-your-main-agent-loop))
OpenAI's documentation says subagents use more tokens than one agent doing the same work. That is why these skills
also work in a single chat with no lead, and why a small job should be done that way.

### A reviewer is a new session, and it uses the product

A reviewer has seen none of the building. It runs the product and looks at it, and does not judge from the code or
from the builder's screenshots alone.

- Anthropic's reviewer drove the running application in a browser and caught concrete bugs. The same post found a
  model lenient when it judged its own work.
  ([Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps))
- Cognition reports that a writer with a separate reviewer that shares none of its context is the pattern that
  worked best for them in production. Their reviewer found about two bugs in each change, and more than half were
  serious. ([Cognition](https://cognition.ai/blog/multi-agents-working))

These are two companies' reports, not measurements. Nobody has published a test of a new-session reviewer against
a builder reviewing its own work. Anthropic's own guides disagree from one model to the next: the guide for Fable
5 recommends separate reviewers, and the guide for Opus 5 says to remove them.

That same Anthropic post also had the reviewer agree what "done" meant before work started. The design review
here keeps that, once for each module, because a reviewer who agreed the items up front judges them more fairly
later.

### The planner says what to build, and the builder decides how

An item says what will be observed when the work is right. It does not say how to arrange that. Anthropic kept
its planner when it removed almost everything else from its harness, and it kept the planner at that level.

Our own first project showed why. Long items that scripted their own proof were rewritten up to four times before
any review had failed.

### One builder works on each module, and only a few builders run

Two agents writing to the same files overwrite each other, so each module has one builder, in its own worktree.

- Cognition keeps all writing to one agent at a time, and calls loose groups of agents "mostly a distraction".
- Cohere measured teams of agents on 200 tasks. Teams cost three to seven times as much as one agent. More than
  two to four builders made the results worse.
  ([Cohere](https://cohere.com/blog/lessons-from-scaling-teams-of-frontier-coding-agents))
- Cursor found that locks became the bottleneck at twenty agents.
  ([Cursor](https://cursor.com/blog/scaling-agents)) Here one lock covers a whole merge, including the project's
  test command, so a slow test command limits how fast builders can merge. That is a deliberate trade for two or
  three builders.
- Anthropic's C compiler project used automated checks as the judge, and locks so that agents working at once did
  not collide. ([Building a C compiler](https://www.anthropic.com/engineering/building-c-compiler))

### Everything is kept in files and in git

The plan, the items, the reviews and the record of what is Done are all files in your repository. No agent has to
remember anything. A new lead, on either host, can read the files and carry on.

Anthropic and OpenAI both recommend this for long work, because a long session loses track of its early
instructions.
([Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents),
[Run long horizon tasks with Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex))

### How agents are given their instructions

The script writes the message that starts each agent. The lead writes messages too, when it passes on a review or
your words. Both follow the same rules.

1. The message says what must be true at the end, and which skill to read. It does not list steps. The method is
   in the skill. Both companies' guides say that a capable model does better with the goal and the reason than
   with a procedure.
   ([Anthropic's prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices),
   [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra))
2. The message says what the agent may change, and what happens if it changes anything else. A builder is told it
   may change only the status and evidence of its own items.
3. The message says how to end: with `DONE`, or with `BLOCKED` and what would unblock it. The script reads that
   last line.
4. The lead passes on file paths and your own words. It does not add its summary or its opinion. A reviewer that
   is handed a conclusion tends to agree with it, and then the review is no longer independent. Claude Code's own
   guidance for starting subagents says the same.
5. Your request goes to the planner word for word. In one test run, a plan read "accents" more narrowly than the
   owner meant, and the finished tool dropped the letter `Ø`.
6. Nothing is written in capitals for emphasis. Current models apply a shouted rule too widely. The effort setting
   is the control for how hard a model works.
   ([Claude Code best practices](https://code.claude.com/docs/en/best-practices))
7. Rules that must hold for a whole session are sent again when a session is resumed. A model attends less to its
   early instructions as a session grows.
   ([Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents))
8. Reviewers and planners are started with the ability to start other agents turned off. A reviewer that hands its
   reading to a helper has not read the work.

The fuller write-up of these rules, with every source, is the
[`instructing-agents`](https://github.com/ryannel/skills/tree/main/skills/instructing-agents) skill in the same
repository.

### Our own practice

Nothing published supports these. Each is here because it fixed something we saw:

- The escalation steps after a failed review: the same builder, then a new builder, then a rewritten plan, then
  stopping for you. Each step exists because the one before it has already been tried.
- A milestone proved only by Automated Checks is Done without a reviewer, unless it is the module's last
  milestone. The last milestone's review reads the whole module. Anthropic's rule for when a reviewer is worth its
  cost was how hard the task is for the model, not how the work is proved, so this is a trade-off to revisit.
- Subjective work is judged against a quality bar written in words and, where the project keeps them, references:
  the option you chose, or a set of reference images. It is never judged against one target image, because agents
  told to match an image copy its accidents too.
- Subjective work starts with options you choose from. Builders get a fresh opinion on their work and improve it
  before they set Ready for Review. They keep the best round, not the last, because Anthropic's design runs
  sometimes peaked in the middle.
- Every agent is started with its model and effort named on the command line, because defaults change between
  releases. The skills and the Claude agent files name neither, because Claude lets those files override the
  command line.
- Builders and reviewers run at medium effort, and planners at high. Raise it where a run has been seen to fall
  short.
- You set the pace by choosing how many builders run. The script forecasts the usage limit, and never slows down
  on its own.

### What our own runs showed

One real project, an engine, has been built with these skills since 9 November 2026. In its first day, four milestones went from Ready for Review to Done. A reviewer failed one of them twice before passing
it, so reviewers do fail work. Most of the time went on planning and design reviews, not on building. Nobody has
yet graded whether those reviews were right.

Nine test runs on small made-up projects are described under [Known limits](#how-much-this-has-been-tested). They
are where most of the wording in the skills was corrected.

The research behind this section, an assessment of these skills against it, and the records of every test run are
in the skills repository, under `workbench/orchestration-review/`.

## Installing

The four skills link to each other's files, so install them together.

For an interactive install, run `npx @ryannel/orchestrate` and choose the hosts and where to install. Claude Code
can install for one project or for all of them. Codex installs for all of them.

From a clone of the skills repository, `python3 install.py --plugins orchestrate` installs the `orchestrate` plugin
in both hosts. In Claude Code that is the skills plus the agent files for the planner and the reviewer. In Codex it
is the skills plus the reviewer's agent file, which `build/scripts/install_agents.sh --global --codex-only` installs.

Add `--repo <repo>` to prepare one repository as well. It adds a `CLAUDE.md` that holds `@AGENTS.md`, for older
versions of Claude Code that would otherwise not read `AGENTS.md`. It also checks `ORCHESTRATE.md`, once a planner
has written it.

`npx skills add` still works if you want the skills alone.

## Starting a project

You do all of this by talking to the lead. You never need a terminal. The smallest project is one module in an
empty repository with one commit.

1. Say what you want and ask for a plan, or run `/plan-module`. Say which hosts you build with, whether agents may
   push, and how the project is tested. A planner takes the safest reading of anything you leave out, and lists
   what it assumed.
2. The lead has a reviewer read each design. Until a design is Design Approved, the plan can be revised freely.
   After that, a milestone's items change only when a planner rewrites them or when you change the scope. This
   stops anyone from quietly making a requirement easier to meet.
3. Say "build it", or run `/build`, and say how many builders to run and on which hosts, such as "two Claude
   builders and one Codex". The lead keeps builders and reviewers going, and tells you when a milestone is Done or
   needs you.

You can also work in one chat with no lead. Run `/plan-module`, then `/build-milestone`, in either host. You can
switch hosts partway, because everything the next agent needs is in the files.

Some decisions are yours: choosing between options, judging an item no agent can, accepting a milestone that
reviewers keep failing, changing the scope. The lead asks you in the chat and saves your answer in your own words.
The report lists every decision saved in your name, so you can spot one you didn't make.

| Ask the lead | It runs |
|---|---|
| what is planned, what is next, and what is running in this repository | `status` |
| what is running on this machine, in every repository | `loops` |
| to stop cleanly and carry on later | `pause`, then `run` again |
| what the build has cost, for each milestone, split into planning, building and reviewing | `cost` |
| whether the Codex weekly usage limit will last | `quota` |
| for a report | `report` |
| to save a decision of yours | `owner answer`, `accept`, `rereview`, `unpark` or `scope` |

Each of these is a command of `python3 <where the skills are installed>/build/scripts/agent_loop.py`. You can run
them yourself if you would rather.

## What the script verifies

The script does not rely on what an agent says it did. Each command verifies the agent's work before it saves
anything. Only the script can set a milestone to Done.

It keeps a **record file**, `<MODULE>-ACCEPTED.json`, beside each done-when file. The record file holds the approved
items, the commit that was tested, the reviews, your decisions, and whether each milestone is Done. Only the
script's own commits write to it.

### After a builder

Before the `run` command treats a milestone as Ready for Review, all of these must be true:

- The done-when file is still valid, the builder changed only the fields that are its to change, and the items are
  the approved ones. A builder can't reword an item to make it easier.
- The work is committed, with no stray files, and merged into the main branch.
- The project's test command and every Automated Check pass when the script runs them itself, in a clean copy of
  the main branch.

A builder saying "done" is never enough. If a builder goes three turns in a row without changing anything or
reporting anything, the command stops it.

### After a reviewer

A reviewer works in a clean copy of the commit it is judging. The `review` command confirms that the reviewer
changed only its review, its folder of screenshots, and its own fields in the done-when file. It confirms that the
result for each item agrees with the review's last line, and that a failed review added one to the count of failed
reviews. Then the command merges the review itself. If any of that is wrong, nothing is saved.

### After a planner

The `plan` command accepts a planner's work only if the planner ends with `PLANNED:` and the files it names, those
files exist and have changed, and each done-when file has a design beside it. A planner that stops with only a
progress note is sent a message naming what is missing. The command rejects a plan that marks
any item as already passed, or that touches a record file. It merges the rest and saves the new items as the
approved ones.

A planner leaves its files uncommitted, and the command commits them. A planner or reviewer that made a commit of
its own is rejected. So is one that ran while some other commit changed a record file on the main branch.

### Which milestone can start

One rule decides this for every command. A milestone can start only when the milestones before it in its module are
Done, and the milestones it depends on in other modules are Done.

When a lead starts a milestone, the script marks it In Progress in a way that every copy of the repository can see.
A second lead that runs `run` on it is told it is already In Progress.

A plan counts only once it is merged. If plan files are uncommitted or not yet merged, the commands name them, and
the `adopt` command merges just those files.

A new module has to go through a design review. Until its design is Design Approved, and while nothing is built,
`adopt` also approves revised items, and the design review judges them. After that, only a planner run or
`owner scope` changes the items.

### Your decisions

The lead asks you in the chat and runs the `owner` command with your words. The script saves them, and `report`
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
write a file because of a sandbox stops and names the file. It does not retry.

A browser won't start inside Codex's default `workspace-write` sandbox. A Codex agent can run one only by asking to
run that command outside the sandbox. The script starts Codex with `approvals_reviewer=auto_review`, which grants
or refuses each request, and builders, reviewers and planners all get the same setting. In test runs, reviewers
that asked were granted it, and a builder that never asked ended up Blocked on four items. When a Codex build plainly
needs a browser, the script warns once. For dependable browser work, set `Codex sandbox: danger-full-access` in the
project settings, or give that module to a Claude builder. Claude sessions are not sandboxed this way.

The script runs Automated Checks with the lead's own permissions, outside any sandbox. The text of each check is
fixed once approved, but a script that a check calls can still be changed by the builder. Read new check scripts.
Proper isolation would need a container.

### What protects the record file

The record file is protected by rules and by detection, not by cryptography.

The script detects three things. A planner that leaves a changed record file is rejected. A planner, reviewer or
builder is rejected if a commit that the script didn't make changed a record file on the main branch while it ran.
A planner or reviewer that commits anything is rejected.

It does not detect a record file edited between runs, by hand or by a session working on the side. It does not
stop a session that deliberately forges the script's commit marker. The check for commits reads git's reflog, so it
misses a session that merges from a different working copy, one that commits in a way that leaves no reflog entry,
and any session in a repository with reflogs turned off. What remains in those cases is the main rule: nothing is Done unless the
script's checks, a reviewer or you made it so, against the approved items.

One special case covers a project that starts using these skills with work already built. In a repository that has
never had a record file, each module is taken as it stands, and its finished milestones count as Done. The script's
first commit writes a record file for every such module. After that, a module without a record file is new and has
nothing Done. A module merged just before that first commit is also taken as it stands, so on the first day, read
what the first planner run merged.

The detection looks for record files in the plans folder named in the project settings. A commit that changes that
folder's location hides the old record files. Every module then disappears from `status`, which is the sign.

### Your decisions depend on an honest lead

You work in the chat, so the lead runs the `owner` commands. The script can't tell a decision you made from one a
lead invented. What it does is save the words given with each decision, and list every one in `report`. Read that
list.

The `owner` commands refuse to run where the `ORCHESTRATE_ROLE` environment variable is set, which the script sets
in every session it starts. That stops a builder, reviewer or planner from accepting its own work. The variable is
confirmed in background Codex and Claude sessions, and unconfirmed in sessions the Codex app runs. The commands also
refuse while a `run`, `review` or `plan` is working on the same module. A session building a different module is
not stopped by that. When sessions run in the app, such a session can also use `adopt` to revise the items of
another module whose design is not yet approved. The design review still judges those items before anything is
built.

These stop mistakes and casual shortcuts. They do not stop a determined agent, which could unset the variable.

### Claude's sign-in

Claude sessions are meant to use your signed-in plan. So the script removes every `ANTHROPIC_*` and `CLAUDE*`
environment variable from them, except `CLAUDE_CONFIG_DIR` and `CLAUDE_CODE_OAUTH_TOKEN`. That also removes any
provider settings you keep in those variables. A credential helper you have set up could still supply other
credentials.

Anthropic has said `--bare` will become the default for `claude -p`. Bare mode reads only API-key sign-ins and does
not look for skills or agent files, so Claude builders will need a change then. Tested with Claude Code 2.1.239 and
Codex 0.167.

### The reviewer is the least proven part

The `review-milestone` skill makes a reviewer use the product itself, read every changed line, write down what it
will look at before it looks, and fail what it finds. It comes with five example reviews that a person has graded.
You tune it by reading its early reviews and saying where it was wrong.

Nobody has measured how often this reviewer catches a fake, or wrongly fails sound work. In the test runs below,
reviewers did fail real defects, but no person graded their results.

### Sessions in the apps

Showing sessions in the Codex app and in Claude desktop depends on parts of those apps that are not public
interfaces, and that can change with an update. They were proven with the Codex app 26.1103 and Claude desktop
4.23118.0. Each command's output says whether its session ran in the app or in the background. Setting
`ORCHESTRATE_HEADLESS=1` makes every session run in the background.

A new Codex thread opens in the app's window, which brings the app to the front, and it starts with a one-line
setup turn. A Claude session runs in the script's own copy of the Claude CLI, so the CLI must be signed in.

### Smaller limits

- `loops` sees one machine. It keeps its notes under `~/.local/state/orchestrate/loops`, and setting
  `ORCHESTRATE_LOOPS_DIR` moves them. A session that can't write there, or that an older copy of the script
  started, is still listed, but without its tokens.
- The script runs on macOS and Linux only.
- Some of the rules for stopping a Codex builder read Codex's local goal database. Whether `codex exec` writes to
  that database is not confirmed. Where it doesn't, those rules are skipped.
- With two builders, planners still run one at a time. Two modules that both need a revised plan wait in line.

### How much this has been tested

One engine project has run full milestones under version 1.5, with sessions in the app.

Before this version, nine test runs took five small made-up projects from an empty repository to the end, with
every session in the background. They used Claude, Codex, and the two mixed. The projects were a text tool (three
runs), the two-module money tool above with two builders at once (two runs), an icon set judged by taste (three
runs), and a browser game (one run).

Seven runs ended with every milestone Done and a product that did what was asked. One produced a tool that dropped
the letter `Ø`, which the planning skill now guards against. The game stopped at its first milestone, for reasons
that have been fixed but not run again.

Those runs were short. The longest took 97 minutes. Each was run once, no person graded a review, and in each one
the lead also played the owner. Only the last run had the lead save an owner's decisions the way it does now.
Accepting a milestone by hand, asking for a new review, and editing the scope are covered by automated tests only.

## Left out for now

The rule is to start small, and to add something only when its absence has caused a problem. So these are not here
yet:

- merging through pull requests;
- agents dedicated to research;
- a second agent that confirms each finding;
- running Automated Checks in a container.
