# Anthropic: testing plugins with evals, and the Agent Skills overview

- URLs: https://code.claude.com/docs/en/plugin-evals and
  https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- Read in Chrome on 2026-11-10. Paraphrased. The last 7,500 characters of the plugin-evals page (the end of its
  troubleshooting section) were cut off and not read.

## `claude plugin eval` (Claude Code 2.1.269 or later)

**What it is.** A shell command that runs a plugin, or a folder of skills, against test cases and scores the
results. Each case is a realistic prompt and one or more graders. A grader is a pass or fail check on what the
model produced.

**What one run is.** Claude Code starts a fresh `claude -p` session in an empty temporary folder with only the
plugin under test loaded. The user's settings, hooks, `CLAUDE.md` files, memory, other plugins and other skills
are all absent. The session can't read the `evals/` folder, so it can't see its own graders. Each case runs three
times by default, because one run of a model "tells you little".

**The baseline.** Each case is run again with no plugin. The report shows the score with, the score without, and
the difference. The page's own warning: a case that scores 1.0 both ways shows the plugin "isn't what made it
pass".

**Cost.** Every run and every judge grader is a real model call on the user's plan or API bill. A suite makes
about cases × runs × 2 agent runs, plus three short judge calls per `llm` grader per run.
`--max-cost-usd` sets a ceiling. `--ablation none` skips the baseline and halves the cost.

**The files.**

```
my-plugin/evals/
├── first-case/
│   ├── prompt.md        settings in frontmatter, then the prompt as a user would type it
│   ├── graders/         one check per file
│   └── case.yaml        optional; needed only for the context.* fields
└── results/             written by each run
```

- `prompt.md` frontmatter: `max_turns` (default 10), `timeout_seconds` (default 300), `runs` (default 3),
  `model`, `tags`, `allowed_tools`, and a few more. An unknown key is an error.
- `allowed_tools` grants only read-only tools (`Read`, `Glob`, `Grep`, `Skill`, `Agent` and the task tools).
  `Bash`, `Write`, `Edit`, `WebFetch` and `WebSearch` must be granted on the command line with `--allow-tools`.
  A tool that isn't granted is removed from the session.
- `case.yaml` needs `schema_version: "1.1"` and `name`. It adds `context.scaffold_script` (a Bash script that
  fills the empty folder; runs only with `--scaffold`), `context.add_dirs` (folders the run may read) and
  `context.history_file` (an earlier conversation to continue).
- A case with no grader does not load.

**Grader types.** `regex`, `tool_used`, `tool_order` and `file_exists` are computed and cost nothing. `llm` and
`baseline` call a judge model. There are no graders that run custom code.

- A grader looks at the final message (the default), the transcript (`trace`), the list of files created
  (`files`), the contents of one file (`{ source: file, path: … }`), or the calls to mocked tools.
- An `llm` judge shown the transcript sees only its first 12 and last 12 messages.
- An `llm` grader passes on two of three judge votes. Write its rubric as concrete PASS and FAIL conditions.

**Their advice on stable grading.**

1. Grade long output, such as a generated file, with a `regex` over the file. Keep `llm` graders for short output.
2. Give each case one grader on the result and one on the steps (`tool_used`), so you learn whether the answer was
   right and whether the plugin produced it.
3. If the skill was used and the difference is negative, suspect the judge first. A small judge model can fail a
   correct answer for its formatting.
4. To check that a build or test passed inside a run, have the prompt ask for the outcome in a file, grade the
   file, and check with `tool_used` that the command ran.

**Did the skill load?** A `tool_used` grader with `tool: Skill` and an `input_match` on the skill's name passes
when the skill was invoked. In a with-and-without run this grader is reported but not scored, because it can
never pass without the plugin. A "must not load" case uses `min: 0`, `max: 0` and `arm: both`. The page calls the
most common first finding "a Δ near zero" with this grader failing: the model isn't choosing the skill on natural
phrasing, so the description needs work.

**Other points.**

- `claude plugin eval init` interviews the author, proposes prompts that should and shouldn't trigger the plugin,
  designs graders, tries them once and writes the files.
- `claude plugin validate` checks a plugin's files for syntax and schema errors. It does not test behaviour.
- The page says the skill-creator plugin has its own `evals/evals.json` format and that neither tool reads the
  other's files. The skill-creator synced from claude.ai on 10 November 2026 writes case folders in the layout
  above, and keeps reading an old `evals.json` if one exists. So the page is behind the skill on this point.
- For CI: pin `--model` and `--judge-model`, pass `--trust-plugin`, and fail on the exit code. `--threshold`
  defaults to 1.0.

## Agent Skills overview (Claude API, claude.ai, Claude Code)

- The same three loading levels as everywhere else: name and description always (about 100 tokens a skill),
  `SKILL.md` body when triggered (under 5,000 tokens), other files when read. A script's code never enters the
  context; only its output does. Files that aren't read cost nothing, so a skill can bundle a lot.
- On the API and claude.ai, the model reads `SKILL.md` with a shell command from a virtual machine's file system.
- `name` may not contain the words "anthropic" or "claude", or XML tags. `description` may not contain XML tags.
- **Custom skills do not sync between products.** A skill uploaded to claude.ai is not on the API, and neither
  is in Claude Code, which reads folders on disk.
- **What a skill's code can do depends on where it runs.**

| Where | Network | Installing packages |
|---|---|---|
| Claude API | None | Not possible; only pre-installed packages |
| claude.ai | Depends on the user's or administrator's settings | Depends |
| Claude Code | Same as any program on the user's computer | Possible; install locally, not globally |

- **Security.** A skill is instructions plus code, so installing one is like installing software. Their advice to
  users: read every file, and be wary of a skill that fetches content from an outside address, because the
  fetched content can carry instructions and can change later. For an author this means a skill should not fetch
  its instructions from the network, and its contents should match its stated purpose.
