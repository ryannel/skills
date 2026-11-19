# Writing a skill

Examples of the points in `SKILL.md` that are particular to skills. How to write any prompt, a skill's body
included, is in the `prompting-agents` skill.

Contents: [The description](#the-description) · [What the body carries](#what-the-body-carries) ·
[How strict to be](#how-strict-to-be) · [Before and after](#before-and-after)

## The description

The description has one job: to let the reader decide, from a sentence or two, whether this task needs the skill.

> Too vague: "Helps with PDFs."
>
> Too wide: "Use for anything involving documents, files, forms, reports, text extraction or data."
>
> Right: "Extracts text and tables from PDF files, fills PDF forms and merges PDFs. Use when the task reads or
> changes a PDF file."

Leave the skill's inner workings out of the description. The reader is matching a task against it, and the task
is described in the person's words, not the skill's.

The reader usually loads a skill only for a task it couldn't do well alone. A one-step request such as "read this
PDF" may not load even a perfectly matched skill, and that is not a fault in the description.

The limit is 1,024 characters, and most good descriptions use well under half of it. `scripts/check_skill.py`
checks the limit and the characters that break a description.

## What the body carries

The purpose goes in the first lines, so the reader can decide the cases the skill didn't name:

> "This skill reviews a database migration before it is merged. The aim is that no migration locks a large table
> during business hours."

With that, a reader that meets a migration that rebuilds an index can still work out what matters.

What finished looks like, with a check the reader can run:

> "The review is finished when you have run `make migrate-dry-run` against the staging copy and reported its
> lock time for each table. Give the command's output, not a summary of it."

The facts the reader couldn't guess:

> "The `orders` table marks a deleted row by setting `deleted_at`. It does not remove the row, so every count
> needs `WHERE deleted_at IS NULL`."
>
> "The `/health` endpoint answers 200 while the database is down. Use `/health/db`."

The format of the output, saying whether it is exact:

> "A program reads this file, so keep these four headings exactly as written."
>
> "A sensible default for the report is: summary, findings, open questions. Change it if the findings call for
> something else."

Each other file, with when to open it:

> "Read `references/api-errors.md` if the API returns a status other than 200."

## How strict to be

Match each part of the skill to how fragile that part of the work is. An open field needs only a direction. A
narrow bridge with a drop on each side needs exact instructions.

| The work | What to write | Example |
|---|---|---|
| Several approaches would do | What to aim for, and why | "Keep each chart readable in grey-scale, because the report is printed" |
| There is a preferred pattern | A template or one worked example, marked as a default | An example commit message, with "follow this shape" |
| It breaks if done differently, or the order is the point | The exact command or numbered steps, and a line saying not to change them | "Run `python3 scripts/migrate.py --verify --backup`. Don't add flags" |

Model and effort belong in the frontmatter, where a host has a field for them. A line in the body such as "think
at high effort" does nothing, because the reader can't change how it was started.

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
