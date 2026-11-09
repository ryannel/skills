# Part A results: skill-creator deltas

9 November 2026, branch `fold-a`. Line numbers are in the new files under `skills/skill-creator/`. The SKILL.md
description is unchanged; SKILL.md gained no new sentence, only two edited ones. `python3 scripts/check_skill.py .`
passes.

| Item | Already covered | Changed |
|---|---|---|
| 1. Trigger test records context state, leakage, cost; post-compaction needs a resumed real session; one or two trials; don't ask a model | Real sessions with neighbouring skills, three runs, and "don't ask a model which skill it would pick" (testing.md 186–190) | testing.md 193–205: long and post-compaction trials (one or two), the ~350k auto-compact window, `claude --resume` then `/compact`, record cost, check what survived compaction; leakage check for trigger trials, hook-forced loads tested separately. testing.md 167–174: results record must carry leakage checked, context state and token cost per trigger trial. |
| 2. Receiver-side run for skills whose output another agent acts on; criteria from the task | "Grade the thing the skill made" and "statements about the result, not the process" (testing.md 61–62, 130–131) | testing.md 145–159: new subsection on receiver-side runs, criteria from the task not the skill's rules, contracts excepted, written before outputs are seen. testing.md 8: contents entry. testing.md 174: results-record field. SKILL.md 49–50: criteria written before looking at outputs (edited sentence). SKILL.md 54–55: pointer now names receiver-side runs (edited sentence). |
| 3. Ship a needed hook or script inside the package with its setup step | "Must never happen belongs in a hook, permission rule, sandbox or script" (writing.md 73–74) | writing.md 74–79: extend that paragraph; ship it in the package with setup, plugin `hooks/hooks.json` via `${CLAUDE_PLUGIN_ROOT}` (checked against installed plugins, Claude Code 2.1.239), setup script plus a statement of what stays manual where a host can't. |
| 4. Host facts carry a date and version | "Where skills live" dated at section level (writing.md 142) | writing.md 81–83: rule that host facts carry check date and host version. writing.md 142–143: notes versions weren't recorded on 8 November. testing.md 90: date on the `skillOverrides` fact. testing.md 217: date on the 2.1.269 eval minimum. |

Not verified: no model runs were made, so none of these changes has a behavioural result. The Codex host facts were
not re-checked (Codex isn't installed on this machine).
