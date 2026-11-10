# agentskills.io: the specification, and using scripts in skills

- URLs: https://agentskills.io/specification and https://agentskills.io/skill-creation/using-scripts
- Read in Chrome on 2026-11-10. Paraphrased.
- agentskills.io is the home of the Agent Skills format, which Claude Code, Codex and other agents all read.

## The specification

A skill is a folder holding at least a `SKILL.md` file. `SKILL.md` is YAML frontmatter followed by Markdown.

| Field | Required | Rule |
|---|---|---|
| `name` | Yes | 1 to 64 characters. Lowercase letters, digits and hyphens. No hyphen at the start or end, and no two hyphens in a row. Must match the folder's name |
| `description` | Yes | 1 to 1,024 characters. Says what the skill does and when to use it, with the words that identify a matching task |
| `license` | No | A licence name, or the name of a licence file in the folder |
| `compatibility` | No | At most 500 characters. What the skill needs from its environment: the intended product, system packages, network access. "Most skills do not need" it |
| `metadata` | No | A map from text keys to text values, for anything the specification doesn't define, such as author and version |
| `allowed-tools` | No | A space-separated list of tools approved in advance, such as `Bash(git:*) Read`. Marked experimental; support varies between agents |

- The body has no required format. The page notes that the agent loads the whole file once it decides to use the
  skill, and suggests moving long content into other files.
- Suggested sizes: about 100 tokens for the name and description; under 5,000 tokens and under 500 lines for the
  body.
- Refer to other files by a path relative to the skill's folder. Keep references one level deep from `SKILL.md`.
- `skills-ref validate ./my-skill` checks the frontmatter and the naming rules.

## Using scripts

**One-off commands.** When an existing package does the job, name the command in `SKILL.md` and skip the
`scripts/` folder. Runners such as `uvx`, `pipx`, `npx`, `bunx`, `deno run` and `go run` fetch the package when
the command runs.

- Pin the version (`npx eslint@9.0.0`), so the command does the same thing next year.
- State what must be installed ("Requires Node.js 18+"). For a requirement on the runtime itself, use the
  `compatibility` field.
- When a command gets hard to type correctly the first time, move it into a tested script.

**Bundled scripts.** List each script in `SKILL.md` with one line on what it does, then tell the agent when to
run it. Paths are relative to the skill's folder. A script can declare its own dependencies at the top of the
file (Python's PEP 723 block, run with `uv run scripts/extract.py`), so it needs no install step.

**Designing a script an agent will run.** The agent reads what the script prints and decides what to do next.

1. Never prompt for input. An agent's shell cannot answer a prompt, so the script hangs. Take every input as a
   flag, an environment variable or standard input.
2. Give `--help` a short description, the flags and one or two examples. This is how the agent learns the
   interface. Keep it short, because the output lands in the agent's context.
3. Make each error say what was wrong, what was expected and what to try: "`--format` must be one of: json, csv,
   table. Received: xml".
4. Print data in a structured format (JSON, CSV), to standard output. Print progress and warnings to standard
   error.
5. Make it safe to run twice, because agents retry.
6. Reject ambiguous input with a clear error. Don't guess.
7. Give a destructive operation a `--dry-run` flag, and consider requiring a `--confirm` flag.
8. Use a different exit code for each kind of failure, and list them in `--help`.
9. Keep the output size predictable. Many harnesses cut tool output off at 10,000 to 30,000 characters. Print a
   summary by default and offer a flag such as `--offset` for more, or require an `--output` file.
