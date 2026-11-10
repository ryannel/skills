# Claude Code docs: Extend Claude with skills (second reading, for a skill author)

- URL: https://code.claude.com/docs/en/skills
- Read in Chrome on 2026-11-10. Paraphrased. Version numbers are Claude Code's.
- The first reading is [prompting-agents note 05](../../prompting-agents/references/05-claude-code-skills.md). It
  covers how a skill is loaded, kept and dropped. This note adds the parts that matter when you build, test and
  ship a skill. Fifteen sections were read: creating a first skill, synced skills, editing during a session,
  types of content, the frontmatter reference, supporting files, dynamic context, unused skills, evaluating, and
  the six troubleshooting entries.

## Mistakes that fail without an error

- Claude Code reads the frontmatter only when `---` is the first line of the file. Otherwise the whole file is
  treated as the body.
- If the YAML doesn't parse, the skill loads with no fields. Typing `/skill-name` still works, but the model has
  no description to match, so it never picks the skill. `claude plugin validate <skills folder>` finds these
  (2.1.233 or later). `claude --debug` shows the parse error.
- A field name Claude Code doesn't recognise is ignored, with no warning.
- `<` and `>` in a description are shown to the model as `&lt;` and `&gt;`. Write `[branch]`, not `<branch>`.
- A skill named `anthropic-skills`, or with a name in that namespace, does not load. The name is reserved for
  skills synced from claude.ai.
- A name with an invisible character, two spaces in a row, or `<` or `>` is refused.

## What works only in Claude Code

- The portable frontmatter fields are `name`, `description`, `license`, `compatibility`, `metadata` and
  `allowed-tools`. Uploading to claude.ai or the Skills API, or packaging with `package_skill.py`, fails with a
  hard error on any other field ("Unexpected key(s) in SKILL.md frontmatter").
- A personal skill enabled for a claude.ai account (to use it in Cowork, cloud sessions or scheduled tasks) is
  uploaded, so the same six-field rule applies.
- Body features that only Claude Code runs: a line starting with `` !`command` `` (the command's output replaces
  the line before the model sees the skill), `@file` references, and placeholders such as `$ARGUMENTS`,
  `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PROJECT_DIR}`. In claude.ai chat and the API these arrive as literal text.
  For a skill synced from claude.ai into a terminal session, Claude Code does not run `!` commands either.
- If an injected `!` command fails, the whole skill invocation is aborted and the model never sees the skill.
  Append `|| true` to a command that may exit non-zero.
- `allowed-tools` approves tools for the turn that invokes the skill. The grant ends at the user's next message.
  Using `${CLAUDE_SKILL_DIR}` both in the body's command and in an `allowed-tools` rule lets a bundled script run
  without a permission prompt.
- `hooks` in frontmatter are registered when the skill is invoked and stay for the rest of the session. This is
  how a rule that must hold every time can travel with the skill.
- `when_to_use` is appended to the description in the listing. The two together are cut at 1,536 characters.
- `paths` limits automatic loading to work on matching files inside the working folder.

## Two kinds of content

- Reference content: conventions, patterns, domain knowledge. It runs beside the conversation and the model
  applies it to the work in hand.
- Task content: instructions for one action, such as a deployment. Often invoked by name, and often marked
  `disable-model-invocation: true` so the model can't start it by itself.
- The page's advice for both: keep the body concise, because every line is paid for on every later turn. "State
  what to do rather than narrating how or why."

## The cost of the listing

- Every skill's name is always listed. Descriptions share a budget of 1% of the model's context window. When
  they don't fit, Claude Code drops descriptions, starting with the skills invoked least.
- `/skill-doctor` (2.1.252 or later) reports what each skill costs in context and how often it is used, and flags
  skills never invoked. `/doctor` estimates the listing's total cost.

## While you are working on a skill

- Claude Code watches the skills folders. An edit to `SKILL.md` takes effect in the running session. A new
  top-level skills folder needs `/reload-skills`.
- So a draft kept inside a skills folder is live in every session on the machine, including sessions meant to
  run without it.

## Testing, as this page puts it

- Measure two things separately: does the model load the skill on the prompts it should, and is the output right
  when it does. "Seeing a skill trigger tells you Claude found it, not that it did what you intended."
- Both use the same comparison: a few realistic prompts, each run in a fresh session with the skill and again
  with it off. A fresh session matters "because leftover context from authoring the skill will mask gaps in the
  written instructions".
- Turning it off: `skillOverrides` set to `"off"` for a personal or project skill. That setting does not apply to
  a plugin's skill; use `claude plugin eval`, which repeats each run with no plugin loaded.
- To measure triggering for a plugin's skill across many prompts, write cases with a `tool_used: Skill` grader.

## When the model stops following a skill

1. It skipped a rule that must hold every time: move the rule into a hook.
2. It skipped guidance meant for the whole task: reword it to cover the whole task ("after every edit").
3. The conversation was compacted: invoke the skill again. Only the start of the skill is kept.
