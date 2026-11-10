# Claude Code docs: Extend Claude with skills

- URL: https://code.claude.com/docs/en/skills
- Read in Chrome on 2026-11-10. Paraphrased. Version numbers are Claude Code's.
- This is the host's own account of how a skill is loaded, kept and dropped. It is the newest Anthropic page on
  skills that I read, and it disagrees with the older "best practices" page in one place (see "Voice" below).

## When to make a skill

- When you keep pasting the same instructions, checklist or procedure into chat, or when a part of CLAUDE.md has
  grown from a fact into a procedure. A skill's body loads only when used, so long reference material costs almost
  nothing until then.
- Two kinds of content. Reference content (conventions, style, domain knowledge) runs inline beside the
  conversation. Task content (deploy, commit) is step-by-step and often invoked by name.

## What is loaded, and when

- Every skill's name and description sit in context so the model can choose. The body loads when the skill is
  invoked. Supporting files load when read. Scripts are executed, not loaded.
- The listing of descriptions has a budget of 1% of the model's context window. When it overflows, descriptions are
  dropped, starting with the least-used skills. The names stay.
- `description` plus `when_to_use` is cut at 1,536 characters in the listing. Put the main use case first.
  (The Agent Skills spec limit for `description` is 1,024.)
- If `description` is missing, the first non-empty line of the body is used.
- If the frontmatter YAML does not parse, the skill still loads, with no description, so it never triggers by
  itself. `claude plugin validate <dir>` finds these.

## What happens after it loads (the lifecycle)

- The rendered SKILL.md enters the conversation as one message and stays. Claude Code does not re-read the file on
  later turns. So write guidance that must hold all task as a standing instruction ("run the tests after every
  edit"), not a one-time step ("run the tests").
- After auto-compaction, the most recent invocation of each skill is re-attached, but only its first 5,000 tokens,
  within a shared 25,000-token budget filled from the most recent skill backwards. So the most important
  instructions go near the top of SKILL.md.
- "Once a skill loads, its content stays in context across turns, so every line is a recurring token cost."

## Voice (a disagreement worth recording)

- This page: "State what to do rather than narrating how or why", and apply the CLAUDE.md conciseness test.
- Anthropic's prompting pages and its skill-creator: give the reason with the rule, because the model generalises
  from the reason.
- These fit together if the reason is one clause that changes what the reader does, and narration (history, how
  the author got there) is cut.

## When the model stops following a skill

1. A rule that must hold every time: move it into a hook. A hook runs on its event whether or not the model is
   following the skill. A skill can define hooks in its own frontmatter.
2. Guidance to apply with judgement: word it to cover the whole task.
3. After compaction: invoke the skill again.

## Frontmatter

- Portable fields (the Agent Skills spec; accepted by claude.ai uploads and the Skills API): `name`, `description`,
  `license`, `compatibility`, `metadata`, `allowed-tools`. Any other field makes an upload fail with a hard error.
- Claude Code only: `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`,
  `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell`.
- `disable-model-invocation: true` is for workflows with side effects (deploy, send a message). Its description is
  then not in context at all.
- `model` and `effort` in frontmatter apply for the rest of the turn. With `context: fork` they set the subagent's.
- Unknown field names are ignored without an error.

## Supporting files

- Keep SKILL.md under 500 lines. Link each supporting file from SKILL.md and say what it holds and when to load it.

## Skills in a subagent (`context: fork`)

- The skill body becomes the subagent's whole task. The subagent does not see the conversation, so the body must
  stand alone. A body that is only guidelines gives the subagent nothing to do.
- The built-in Explore and Plan agents start without CLAUDE.md.
- The other direction: a custom subagent can list skills to preload; then their full content is injected at start.

## Testing

- Seeing a skill trigger shows the model found it, not that it did what you meant. Measure two things separately:
  does it trigger on the prompts it should, and is the output right when it does.
- Both use a baseline comparison: a few realistic prompts, each run in a fresh session with the skill and again
  with it off. A fresh session matters because context left over from writing the skill hides gaps in it.
- Turn a personal or project skill off with `skillOverrides: "off"`. For a plugin skill use `claude plugin eval`,
  which repeats each run with no plugin loaded.
- skill-creator automates the loop: test cases, isolated runs with token and time counts, grading with evidence,
  a benchmark, a blind A/B between versions, description tuning from should-trigger and should-not-trigger prompts,
  and a review viewer.

## Triggering problems

- Not triggering: the description lacks the words users say; or the YAML is broken; or `paths` excludes the files.
- Triggering too often: make the description more specific, or make it manual-only.

## Also

- `/doctor prompt-audit` and `/claude-api prompt-audit` flag instructions written for older models in prompts,
  skills and tool descriptions.
- Claude Code follows the Agent Skills open standard (agentskills.io), which other tools also read.
