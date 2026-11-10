# Writing a skill

A skill's description and body are prompts: text an agent will act on with no chance to ask what you meant. This
file shows each writing point from `SKILL.md` at work.

Contents: [The description](#the-description) · [What the body carries](#what-the-body-carries) ·
[How strict to be](#how-strict-to-be) · [What the body leaves out](#what-the-body-leaves-out) ·
[The wording](#the-wording) · [Before and after](#before-and-after)

## The description

The description has one job: to let the reader decide, from one or two sentences, whether this task needs the
skill.

> Too vague: "Helps with PDFs."
>
> Too wide: "Use for anything involving documents, files, forms, reports, text extraction or data."
>
> Right: "Extracts text and tables from PDF files, fills PDF forms and merges PDFs. Use when the task reads or
> changes a PDF file."

A person who wants a dashboard may say "chart", "metrics" or "KPI page" and never say "dashboard". Name what the
person is trying to do in the words a person uses for it. Leave the skill's inner workings out of the
description.

The reader usually loads a skill only for a task it couldn't do well alone. A one-step request such as "read this
PDF" may not load even a perfectly matched skill, and that is not a fault in the description.

The limit is 1,024 characters, and most good descriptions are well under half of it. `scripts/check_skill.py`
checks the limit and the characters that break a description.

## What the body carries

**The purpose** goes in the first lines.

> "This skill reviews a database migration before it is merged. The aim is that no migration locks a large table
> during business hours."

With that, a reader that meets a case the skill didn't name (a migration that rebuilds an index) can still decide
what to do.

**What finished looks like, and the check.**

> "The review is finished when you have run `make migrate-dry-run` against the staging copy and reported its
> lock time for each table. Give the command's output, not a summary of it."

If finishing includes running the result and fixing what fails, say so. Some models return after a first
version.

**The boundaries.** A boundary is something the reader must not do, or must get a go-ahead for.

> Weak: "NEVER touch production. Be very careful with the database. Do not run migrations. (Approved migrations
> are fine.)"
>
> Better: "Get the person's go-ahead before you run a migration against any database other than the staging
> copy, because the others hold customer data. Reading schemas, writing migration files and running
> `make migrate-dry-run` need no approval; the dry run changes nothing."

The better version states the rule once. It names the exact action. The exception is inside the rule, where the
reader can't miss it. The reason lets the reader place a database the rule didn't name. And it says what needs no
approval, so the reader doesn't stop to ask about every command.

A skill supports the task the person asked for. Don't write one that widens the task, changes settings the task
didn't mention, or tells the reader to disregard other instructions. Guidance that conflicts with what the
person asked can make the reader stop and ask which to follow.

**The facts the reader couldn't guess.** These are what make a skill worth loading.

> "The `orders` table marks a deleted row by setting `deleted_at`. It does not remove the row, so every count
> needs `WHERE deleted_at IS NULL`."
>
> "The `/health` endpoint answers 200 while the database is down. Use `/health/db`."

Keep them in `SKILL.md`, not in a reference, because the reader won't know the moment to go and look one up.
Each correction the person had to make while doing the task is a candidate.

**The format of the output.** A template is more reliable than a description of a format. Say whether it is
exact.

> "A program reads this file, so keep these four headings exactly as written."
>
> "A sensible default for the report is: summary, findings, open questions. Change it if the findings call for
> something else."

**The other files.** Name each one and say when to read it or run it.

> "Read `references/api-errors.md` if the API returns a status other than 200."

"See the references folder" tells the reader nothing about when.

## How strict to be

Match each part of the skill to how fragile that part of the work is.

| The work | What to write | Example |
|---|---|---|
| Several approaches would do | What to aim for, and why | "Keep each chart readable in grey-scale, because the report is printed" |
| There is a preferred pattern | A template or one worked example, marked as a default | An example commit message, with "follow this shape" |
| It breaks if done differently, or the order is the point | The exact command or numbered steps, and a line saying not to change them | "Run `python3 scripts/migrate.py --verify --backup`. Don't add flags" |

Both vendors use the same picture. An open field needs only a direction. A narrow bridge with a drop on each
side needs exact instructions.

## What the body leaves out

**The recipe.** A skill written as a fixed sequence of steps holds a current model to the steps its author
thought of. Give the outcome and the facts, and keep fixed steps for the third row of the table above.

**What the reader knows.** Before keeping an explanation, ask whether a capable engineer new to this project
would need it. That engineer knows what a migration is. They don't know your staging copy is refreshed at 02:00.

**Emphasis.** If you find yourself writing "ALWAYS" or "NEVER" in capitals, give the reason instead. "Never use
ellipses" works less well than "the text is read aloud by a speech engine that can't pronounce ellipses". With
the reason, the reader also handles the cases you didn't list. If a plainly worded rule is still missed, more
emphasis won't fix it. The rule belongs in a hook, as the table in `SKILL.md` says.

**Reminders.** "Always run the tests", "double-check your work", "keep going until done", "use subagents for
speed". GPT-6 Astra and Claude Opus 5 test and check unprompted, and do too much of both when told to. Say what
check this kind of change needs, and when a subagent is worth its cost.

**A rule made from one case.** One failure, one example or one person's preference is not a rule for every task.
Write the narrow correction: "For tables over a million rows, …".

**Model and effort.** "Use the most capable model" or "think at high effort" in a body does nothing, because the
reader can't change what it is. Where a host has a setting for this, it is a frontmatter field.

**Facts that will expire, undated.** "The new API" is wrong within a year. Give the version or the date.

## The wording

**Name who does each thing.** A skill is read by an agent that has to work out which actions are its own.

> Unclear: "The build is verified and results are reported."
>
> Clear: "Run `make build`. Tell the person which targets failed."

**A script is not an agent.** An agent runs a command, and the command does something. "Tell the build script to
skip the cache" sends the reader looking for something to talk to. Write "run `build.sh --no-cache`".

**One word for one thing.** If the skill says "module" in one sentence and "component" in the next, the reader
has to decide whether those are two things. Define the few words the skill depends on, such as "finished" or
"blocked", where they first appear. Use a thing's existing name; don't coin a label for it.

**Whole sentences.** The packed style looks efficient and is hard to act on:

> "**Verify on target.** Capture from exact build; cover edge conditions; label proxies; no unevidenced claims."

The plain version is longer, and each sentence does one job:

> "Look at the output yourself, on the exact build and on the device it is for. Passing tests show the code does
> what the tests say. They don't show that it looks right. If you used a stand-in, such as a Mac standing in for
> an iPhone, say so."

Be efficient by covering each point once. Don't say a thing three ways, or back one point with several examples
that show the same thing.

**Exact things in exact forms.** Whole sentences are for explanation. A list of allowed values, a table of who
changes which field, or steps where the order matters should keep the form that holds them exactly.

## Before and after

A skill body written for an earlier model:

> "## When to use this skill
> Use this skill whenever the user mentions reports!
>
> ## Instructions
> IMPORTANT: You MUST follow these steps EXACTLY.
> 1. First, carefully read the user's request.
> 2. Think hard about what data is needed.
> 3. Query the database. Be careful!
> 4. Write the report. Make sure it is high quality and comprehensive.
> 5. ALWAYS double-check your work before finishing."

The same skill for a current one:

> "This skill writes the weekly sales report that the regional managers read on Monday.
>
> The figures come from the `sales_weekly` view, which is rebuilt every Sunday at 23:00 UTC. If its
> `refreshed_at` is more than a day old, tell the person and stop, because the report would repeat last week's
> numbers. Returns are stored as negative rows in the same view, so a region's total is the plain sum.
>
> The report is finished when each region's total matches `python3 scripts/check_totals.py`, which prints one
> line for each region. Use `assets/report-template.md`. The managers compare weeks side by side, so keep its
> headings in the same order."

The second version has no steps, because the reader knows how to query a view and write a report. Every sentence
in it is something the reader could not have known. The "when to use" line has moved to the description, where it
is read in time to matter.
