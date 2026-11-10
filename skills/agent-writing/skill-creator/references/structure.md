# The structure of a skill

What a skill's folder holds, what each host does with it, and the mistakes that fail without an error. A host is
the program that runs the model and gives it skills, such as Claude Code or Codex. Facts about hosts change
between releases. Those below were checked on 10 November 2026 unless a line gives another date.

Contents: [The folder](#the-folder) · [How a skill is loaded](#how-a-skill-is-loaded) ·
[The frontmatter](#the-frontmatter) · [Mistakes that fail without an error](#mistakes-that-fail-without-an-error) ·
[References](#references) · [Scripts](#scripts) · [Rules that must hold every time](#rules-that-must-hold-every-time) ·
[What a skill's code can do on each host](#what-a-skills-code-can-do-on-each-host) ·
[Where skills live](#where-skills-live)

## The folder

```
skill-name/
├── SKILL.md       required: frontmatter, then the instructions
├── references/    files the reader opens when SKILL.md says to
├── scripts/       code the reader runs
└── assets/        files that go into the output, such as templates
```

Create only the parts the skill uses. A skill with one job and little detail is a single `SKILL.md`.

Leave out a README, a changelog, an installation guide and notes on how the skill was made. The folder is for
the reader doing the job, and every extra file is something it may open and act on.

Claude Code, Codex, claude.ai and both vendors' APIs read this same format, which is defined at agentskills.io.

## How a skill is loaded

1. At the start of a session, the host shows the reader the name and description of every installed skill. This
   costs about 100 tokens a skill.
2. When the reader decides a task matches a description, it loads that skill's `SKILL.md`. No host matches
   keywords; the model decides.
3. The reader opens another file in the folder when `SKILL.md` tells it to. A script's code is never loaded;
   only what the script prints is.

What follows for the author:

- Once loaded, `SKILL.md` stays in the conversation and takes some of the reader's attention on every later
  turn. The reader does not open it again.
- Files the reader never opens cost nothing, so a skill can carry large references.
- Some hosts hand the reader the body without the frontmatter. Don't put an instruction in the frontmatter and
  expect the reader to see it after loading.

| | Claude Code | Codex |
|---|---|---|
| Space for all descriptions together | 1% of the model's context window | 2% of it |
| When they don't fit | Drops descriptions, least-used skills first. Names stay | Shortens descriptions, then leaves skills out with a warning |
| Longest description shown | 1,536 characters, together with `when_to_use` | Shortened as needed |
| After a long conversation is compacted | Keeps the first 5,000 tokens of the latest load of each skill, within 25,000 tokens shared by all of them, newest first | Not documented |

So put the main use first in the description, and the most important instructions first in `SKILL.md`.

## The frontmatter

The frontmatter is the block between two `---` lines at the top of `SKILL.md`. Six fields are in the format's
specification, and every host accepts them:

| Field | Rule |
|---|---|
| `name` | Required. 1 to 64 characters: lowercase letters, digits and hyphens, with no hyphen at either end and no two in a row. The same as the folder's name. Anthropic's products refuse a name containing "anthropic" or "claude" |
| `description` | Required. 1 to 1,024 characters. What the skill does and when to use it |
| `license` | A licence name, or the name of a licence file in the folder |
| `compatibility` | At most 500 characters on what the skill needs: a product, installed programs, network access. Most skills don't need it |
| `metadata` | A map of text keys to text values, such as `author` and `version` |
| `allowed-tools` | Tools approved in advance, such as `Bash(git:*) Read`. Every host accepts the field; not every host acts on it |

Use only these six unless the skill is for one host. Uploading a skill to claude.ai or to Anthropic's Skills API
fails with an error on any other field.

Claude Code reads more fields and ignores any it doesn't recognise, without a warning. The useful ones:

- `disable-model-invocation: true` makes the skill run only when the person asks for it by name. Set it when
  the person wants that. For a skill with side effects, such as a deployment, the other way is to leave the
  skill discoverable and have its body require a go-ahead right before the action. OpenAI's own skill-creator
  prefers that way.
- `user-invocable: false` hides the skill from the person's menu, for knowledge only the reader uses.
- `model` and `effort` change the model and how much it thinks for the rest of the turn in which the skill
  loads. This is the place for such a choice; a sentence in the body can't make it.
- `context: fork` runs the skill in a subagent that can't see the conversation, so the body must stand alone.
- `hooks` registers hooks when the skill loads. They stay for the rest of the session.
- `paths` limits automatic loading to work on files that match a pattern.

Codex reads its extra settings from `agents/openai.yaml` in the skill's folder: a display name, and
`policy.allow_implicit_invocation: false`, which is Codex's form of `disable-model-invocation`.

## Mistakes that fail without an error

`scripts/check_skill.py` reports the first six.

1. The frontmatter doesn't start on line 1. Claude Code then treats the whole file as the body.
2. The frontmatter isn't valid YAML. Claude Code loads such a skill with no description, so the reader never
   picks it. Some hosts drop the skill. The usual cause is an unquoted description with a colon and a space in
   it, such as `description: Use this when: the user asks about PDFs`. Claude Code 2.1.319 reads that one
   correctly, and a strict YAML parser does not, so quote it.
3. The name doesn't match the folder, or breaks the naming rule.
4. The description contains `<` or `>`. Claude Code shows them to the reader as `&lt;` and `&gt;`.
5. A link in `SKILL.md` points at a file or heading that isn't there.
6. A field that isn't one of the portable six. It is ignored on one host and refused on another.
7. The same skill is installed twice, once as a plain folder and once in a plugin. Both copies load.
8. Two installed skills give opposite instructions. The reader may stop to ask which to follow.

## References

A reference holds detail that only some tasks need.

- Link each reference from `SKILL.md` and say when to read it. Don't link from one reference on to another,
  because a file reached at second hand may be only skimmed.
- Where a skill covers several variants, give each one a file (`aws.md`, `gcp.md`), so the reader loads one.
- Keep each fact in one place: in `SKILL.md` or in a reference, not both.
- Give a reference over 100 lines a list of contents at the top, so a partial read still shows what it holds.

## Scripts

Bundle a script when every run would otherwise write the same code, or when a step has to be done exactly the
same way each time. In `SKILL.md`, say what the script does and whether the reader should run it or read it. Run
every script you add before you hand the skill over.

When an existing tool does the job, name the command and skip the script. Pin the version, as in
`npx eslint@9.0.0`, so the command does the same thing next year, and state what must already be installed.

The reader decides what to do next from what a script prints. So a script an agent will run should:

1. Never wait for typed input. An agent's shell can't answer a prompt, and the script hangs. Take every input as
   a flag, an environment variable or standard input.
2. Print a short usage message for `--help`, with one or two examples.
3. Make each error say what was wrong, what was expected and what to try: "`--format` must be one of json, csv,
   table. Received: xml".
4. Print data as JSON or CSV on standard output, and progress and warnings on standard error.
5. Be safe to run twice, because agents retry.
6. Offer `--dry-run` for anything destructive.
7. Keep its output short by default. Many hosts cut tool output off at 10,000 to 30,000 characters. Offer a flag
   for more, or write to a file.

Refer to a script by its path from the skill's folder (`scripts/extract.py`). In Claude Code, `${CLAUDE_SKILL_DIR}`
in the body is replaced with the folder's full path. Other hosts don't replace it.

A Python script can list its own dependencies at the top (the PEP 723 block) and be run with
`uv run scripts/extract.py`, with no install step.

## Rules that must hold every time

The reader weighs a skill's text against everything else it has read. A rule with no exceptions belongs in
something the host runs whatever the reader decides: a hook, a permission rule, a test, or a script that checks
the result.

Ship that mechanism with the skill, so installing the skill installs it. A hook the person added to their own
settings by hand doesn't reach the next machine.

- In Claude Code, a skill's `hooks` frontmatter registers hooks when the skill loads.
- A Claude Code plugin can carry a `hooks/hooks.json` that calls a bundled script through
  `${CLAUDE_PLUGIN_ROOT}`. When several marketplace entries share one folder as their source, put the hook
  inline in that plugin's marketplace entry instead; a file there would load with every entry (Claude Code
  2.1.239, checked 9 November 2026).
- Where a host can't install the mechanism from the package, bundle a setup script, and say in `SKILL.md` what
  it does and what stays manual.

## What a skill's code can do on each host

| Host | Network | Installing packages |
|---|---|---|
| Claude Code, Codex on the person's machine | The same as any program there, within the host's sandbox | Possible. Install into the project, not system-wide |
| claude.ai | Depends on the person's or administrator's settings | Depends on the same settings |
| Anthropic's API | None | Not possible. Only what is pre-installed |

A skill uploaded to one of Anthropic's products is not copied to the others.

A skill is instructions and code from someone else, and people are told to read one before installing it. Its
contents should match what its description says it is for. It should not fetch its instructions from the
network, because fetched text can change after the skill was reviewed.

## Where skills live

| Host | Project folder | Personal folder |
|---|---|---|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/`, in the working folder and each parent up to the repository root | `~/.agents/skills/` and `~/.codex/skills/` |
| Many other agents | `.agents/skills/` | `~/.agents/skills/` |

- When two skills share a name, Claude Code uses the personal one over the project one, and Codex lists both.
  Give a skill a name that won't collide.
- Claude Code watches these folders, so an added or edited skill shows up in a running session. A skills folder
  created after the session started needs `/reload-skills`.
- To share one copy between hosts, keep one real folder and symlink it into the other host's folder. Both
  Claude Code and Codex follow symlinks.
- `npx skills add <owner/repo> --skill <name> -g` installs a published skill for every agent at once.
- A plugin carries skills together with hooks and agents. Claude Code and Codex both install plugins from a
  marketplace file (`.claude-plugin/marketplace.json`) and list a plugin's skill as `plugin:skill`.
- claude.ai takes a skill as a zip file with the skill's folder at its top level, uploaded in the person's
  settings. Leave `evals/` out of the zip.
- Claude Code downloads skills enabled on the person's claude.ai account into `~/.claude/skills/synced/`. An
  edit made there is overwritten by the next sync. Change such a skill on claude.ai.
