# Holistic review synthesis

9 November 2026. Sources: `astra-REVIEW.md` (A1–A13) and `fable-REVIEW.md` (F1–F10). Both find the direction sound and the always-loaded footprint within the owner's limit. Both say the problems are at the seams between the skills, the loop and the installer.

## Decisions

### Loop and orchestrate skills (owner: `skills/orchestration/**`, loop tests)
1. **Planner success needs a result** (A1). A progress report isn't completion. The planner turn is accepted only when its files exist and validate.
2. **Owner restrictions survive retries** (A2). A restriction passed with `--message` is stored with the milestone's loop state. It's restated on every later turn, including after `--fresh`, until the owner clears it.
3. **Cap on progress-only continuations** (A3). After two or three continuations with no item changed and no blocker stated, the loop stops the builder with a stated result, as instructing-agents advises.
4. **Remove `model` and `effort` frontmatter** from build-milestone, review-milestone and plan-module (F1). The loop's launch settings decide them, and the frontmatter silently overrides those on Claude.
5. **Model and effort live only in the launch record** (F6). Take them out of every template's text and out of the Codex goal objective. The test checks that they're absent.
6. **Resumed Claude turns restate the objective** (F7), in one sentence, alongside the binding rules.
7. **Find plugin-installed skills and agents** (F3, F4, A6). This covers the Codex plugin cache, namespaced skill names (`orchestrate:review-milestone`), and Claude plugin agents.
8. **The reviewer fails only on material defects** (A5). Immaterial ones are reported but don't fail the milestone. This must agree with `kinds.md`.
9. **Effort defaults** (A13, F9). Orchestrate keeps medium as the default, and the owner's choice stands. instructing-agents says medium is the default and to raise effort where a run has been seen falling short. That matches the vendor advice to set effort explicitly and measure.

### Install, hook and shared skills (owner: `install.py`, root README, `.claude-plugin/`, `skills/instructing-agents/**`, `skills/skill-creator/**`, `freshness.json`)
10. **Install from this checkout** (A4). When the marketplace is already registered under another source, the installer updates the source or says so loudly.
11. **Migration** (A8, F2). `install.py --replace-standalone` removes standalone copies of these skills from `~/.claude/skills` and `~/.agents/skills` and removes the old settings hook entry, showing exactly what it will remove before it acts. Without the flag, it detects the duplicates and fails clearly rather than printing notes.
12. **Repo setup** (A7). What it reports matches what it checked.
13. **Hook matching** (A9, F8):
    - ignore separators inside quotes;
    - catch `VAR=x`, `timeout N` and `env` prefixes;
    - fix the docstring.

    The loop's own launches carry templates the loop owns, which these decisions cover, so the hook doesn't need to see them.
14. **Plugin facts** (F5). Re-copying depends on version: state it with the host version. Warn that a root `.claude-plugin/plugin.json` breaks `strict: false` entries, and fix the `plugin eval` advice in `testing.md` that would add one.
15. **Claims match evidence** (A10). Publication notes and results say what's verified, what's owed, and by whom.
16. **Wording** (A12, A11, F10):
    - soften "only fragile steps" to match the evidence and skill-creator;
    - say where skills live, including plugins;
    - update the stale values (`autoCompactWindow`, `freshness.json`);
    - give one install route in the root README.

## Owed after the fixes (not code)
- A live loop claim with a resumed Claude turn. This needs a signed-in `claude` CLI, so it's the owner's step.
- A post-compaction handoff with the plugin hook installed and the hand-installed hook removed, run in the desktop app after install.
- The trigger trial: does the description alone suffice?
