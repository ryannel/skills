---
name: models
description: Keeps orchestrate's model catalogue and a project's Agents table current, as part of the orchestrate set. Researches the models Codex, Claude Code and Antigravity offer from each vendor's own pages, updates models.json with their IDs, efforts, context, list prices, plans and retirement dates, and proposes changes to the table with reasons. Use when a model launches or retires, when the models command flags a cell, or when asked whether the project's models are current. Not for writing prompts for a new model (prompting-agents).
---

# Models

Orchestrate's script, `agent_loop.py`, starts each kind of agent (planner, builder, reviewer, design reviewer) on the
model and effort that the project's Agents table names for that host, and routes work across hosts by quota. The
model catalogue, `models.json`, says what each model the table can name is for, which efforts it takes, its list
price and when it retires. Vendors launch and retire models every few weeks, so both go out of date. Your job is to
bring the catalogue up to date from the vendors' own pages, then propose what the table should change, for the user
to agree.

The script is `scripts/agent_loop.py` in the lead skill's folder, a sibling of this one
([lead](../lead/SKILL.md)). The shipped catalogue is `scripts/models.json` beside it. The user's own copy,
`~/.config/orchestrate/models.json`, overrides an entry with the same host and ID and adds new ones; it works from any
project and survives a plugin update, so that is the one to write unless you are working in the repository that
publishes the plugin.

## Start from what the script sees

Run `agent_loop.py models --worktree <project>` first. It prints the catalogue with its checked date, and each table
cell that names a model the catalogue doesn't know, one retired or retiring within two weeks, or an effort the model
doesn't take. Those cells are where to begin. `agent_loop.py quota --worktree <project>` shows each host's windows,
plan and banked resets, which matter when a change would move work between hosts.

## Research from the vendors' pages

Read each vendor's own model and pricing pages, because a model's ID, its efforts and its price are facts only the
vendor can settle, and third-party write-ups lag and disagree. The pages that have held these facts:

- **Claude:** the models overview and pricing pages on platform.claude.com, and Claude Code's model configuration
  page on code.claude.com, which gives Claude Code's default effort and which plans include each model.
- **Codex:** OpenAI's Codex models page (learn.chatgpt.com/docs/models) and its pricing pages.
- **Antigravity:** the models page at antigravity.google/docs/models, Google's model guides on
  docs.cloud.google.com, and the Gemini pricing page.

When a page has moved, search the vendor's site for the new one. Where a vendor's pages are silent, say so in the
entry (leave `efforts` empty, or `context` null) rather than filling the gap from a blog post; a wrong effort or ID
makes a run fail, and an empty one only makes the script pass no setting. If you do use a developer report, put it
in the summary to the user, labelled as reported, and keep it out of the file.

What to collect for each model the hosts offer for agent work:

| Field | What it holds |
|---|---|
| `host`, `id`, `name` | the host the model runs on (`codex`, `claude`, `antigravity`), the ID that host's CLI takes, and the display name |
| `for` | one sentence on what the vendor says the model is for, and how it compares on price with its siblings |
| `roles` | the kinds of agent it suits (`plan`, `build`, `review`, `design`), from the vendor's positioning: deep, long-horizon models for planning and design reviews, and coding models for building and reviewing |
| `efforts`, `default_effort` | the efforts the host's CLI accepts for it, and the CLI's default, which can differ from the API's |
| `context` | the context window the host gives by default, in tokens |
| `price`, `price_changes` | the API list price per million tokens (`input`, `cached`, `output`), and any announced change as `{"from": "YYYY-MM-DD", ...}` |
| `plans` | the subscription plans that include it |
| `retires` | the announced retirement date, or null |
| `sources` | the pages you read |

Set `checked` at the top of the file to today. Keep retired models in the file until their date has passed, so the
`models` command can still warn about a table that names them.

List prices are there to compare hosts, for instance when the dashboard puts runs on different hosts side by side.
A subscription is charged by its plan's quota, so never present a list price as what a run cost the user.

## Propose changes to the table

Once the catalogue is current, look at the project's Agents table (`agent_loop.py settings --worktree <project>`
prints it) and work out what should change: a cell naming a retired model, a new model that does a role's job
better or for less quota, or an effort the model no longer takes. Bring each change to the user in chat with its
reason and what it costs: the role and host, the model and effort now and proposed, why, the list-price difference,
and anything the change does to quota on that host. A proposal is the user's to agree, change or turn down, because
the table spends their plans.

When the user agrees, the lead writes each cell with `agent_loop.py settings --worktree <project> --set 'Agents
<Role> <Host>' '<model> <effort>' --said '<their words>'`, so the record shows who decided. A blank or `-` cell keeps
that kind of agent off the host.

When a new model family arrives, the prompts the script and the lead write to it need guidance too. Say so, and
point to the prompting-agents skill, which holds a reference per model family.

## In the repository that publishes orchestrate

If you are working in the skills repository itself, update the shipped `scripts/models.json` as well as, or instead
of, the user's copy, and bump that skill's entry in the repository's `freshness.json` so its last-checked date
matches.
