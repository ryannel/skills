# Holistic review: instructing-agents, skill-creator and orchestrate on `integrate`

Reviewer: Claude Fable 5.1, 9 November 2026. Read-only; this file is the only thing written. Branch `integrate` at
0b484b2 in `~/Workspace/skill-factory-integrate`. Paths below are relative to that checkout unless they start with `~`.

What I did: read all three skill sets, `install.py`, the marketplace manifest, the root and orchestration READMEs,
`agent_loop.py` (templates, host commands, `binding`, `launch_record`, `preflight`, `cmd_run`, `one_session`,
`cmd_review`, `cmd_plan`), the fold-learnings plan and results, rethink.md, REBUILD.md and both earlier reviews. Ran
the unit tests (121 pass, 101 s), `check_skill.py` on all six skills (ok; PyYAML is absent so it was the strict scan)
and `claude plugin validate .` (passes). Exercised `handoff_nudge.py` with synthetic PreToolUse payloads in a scratch
state folder. Re-checked the host facts that the findings rest on against the live Claude Code docs (skills, hooks,
sub-agents, marketplace reference, host-marketplace) and the OpenAI plugins page. Looked at the owner's current
`~/.claude` and `~/.codex` state because the install has to land there. No model runs were launched. I didn't read the
parallel review.

## Verdict

Close, not there. The three sets now say the same thing about what a brief carries, where a rule has to live to
survive a long run, and that done rests on evidence a loop checks. The always-loaded footprint is what the owner asked
for: five visible descriptions of 316–457 characters, `build` hidden from the model, one line in Codex's global
AGENTS.md, and a one-line refusal once per context. The loop's binding restatement, launch records with an `observed`
field, fresh reviewers and planners, and the loop owning acceptance are the right mechanisms for unattended runs, and
the tests cover them.

Four things stop me calling it ready to install for the owner's builders:

1. The three orchestrate skills carry `model`/`effort` frontmatter that overrides the loop's launch pin for the turn,
   so "every launch names model and effort" isn't true for Claude builders and the loop can't see it (finding 1).
2. On the owner's own machine the single install produces two hooks and two copies of every skill, one of them the
   old instructing-agents with the facts both reviews corrected (finding 2).
3. The Codex path the README recommends (plugins) isn't the path the loop's preflight or the skill text expects
   (finding 3).
4. The loop's prompts still put model and effort inside the Codex goal objective, which the instructing-agents skill
   itself says not to do (finding 6).

Fix 1, 2, 3 and 6 and I'd merge and install. The rest can follow.

## Findings, ranked by consequence

Each is marked verified (I read the text or ran it) or suspected (an inference I didn't reproduce). A finding can be
verified as to the text and suspected as to the behaviour; I say which.

### 1. Skill frontmatter overrides the loop's effort pin on Claude, and nothing detects it

**Verified for the text and the documented semantics; the runtime effect wasn't run.**
`skills/orchestration/build-milestone/SKILL.md:4-5`, `review-milestone/SKILL.md:4-5` and `plan-module/SKILL.md:4-5`
set `model: claude-opus-5-5` and `effort: medium` (`high` for plan-module). The loop launches
`claude -p ... --model M --effort E` (`agent_loop.py:1259`) and its prompt says "Use the build-milestone skill", so the
skill loads and its frontmatter applies. The Claude Code skills page says the `effort` field "Overrides the session
effort level" and `model` "applies for the rest of the current turn". So `LOOP run --effort high` on Claude runs the
first turn at high until the skill loads, then at medium; a `--model` other than Opus flips back to Opus when the skill
loads. `pin_check` (`agent_loop.py:1384-1394`) reads only the model from Claude's stream, so the effort change is
invisible, and the launch record's `observed` field correctly never claims the effort. The README's host table says
"the effort isn't [checked]" and ROUND-TWO-CHANGES deferred this as Astra 12, an owner decision. It needs deciding
before publish, because it contradicts the house rule in `skills/orchestration/README.md:56-57` and
`instructing-agents/SKILL.md:52-54`, and because it makes the `Model {model}, effort {effort}` line in the review and
plan templates (finding 6) untrue for Claude. Codex is unaffected: `$skill` has no such fields and the rollout shows
both. Suggested: remove `model` and `effort` from the three skills. The loop, the agent files
(`build/agents/claude/*.md`) and the profile already set them, and a person running `/build-milestone` in a chat is
on the model they chose. If the owner wants them kept for chat use, say in the README that they win over the loop's
flag on Claude, and have `instruction_warnings` or `preflight` say so when `--effort` differs from the skill's.

### 2. The install leaves the owner with two hooks and two of every skill, one of them the old instructing-agents

**Verified.** The owner's `~/.claude/settings.json` has a PreToolUse hook running `~/.claude/hooks/instructing-agents-gate.py`
(the same logic as the plugin's); `~/.claude/skills/` holds `build`, `build-milestone`, `instructing-agents`,
`plan-module`, `review-milestone` and `skill-creator`, with `~/.agents/skills/` symlinking to them; and
`~/.claude/skills/instructing-agents/references/` still has `goals-and-briefs.md` and `models.md`, the pre-rebuild
version with the facts both reviews corrected (subagents at `xhigh`, the fixed "harness already says" inventory).
`install.py` only prints "note: … is a standalone copy; remove it" (`install.py:69-80`) and says nothing about the
settings hook. After `python3 install.py`, every Claude session on this machine would carry two descriptions per
skill, two instructing-agents bodies competing when either is loaded, and two refusals per context (the hand gate
denies, the agent resends, the plugin hook denies, the agent resends). The gate also fired on one of my own Bash
calls during this review. RESULT-D lists the cleanup as "what stays manual", which is honest, but the brief's
requirement was a single install with no hand-configuration, and this is the one machine the install is for.
Suggested: an `--replace-standalone` flag (or a prompt) that deletes the listed standalone folders and symlinks and
removes the settings-hook entry whose command names `instructing-agents-gate.py`, after showing what it will remove.
Failing that, `install.py` should exit non-zero when duplicates exist, so the double load can't happen silently.

### 3. The Codex plugin install isn't what the loop or the skill text expects

**Verified for the code and text; suspected for `$name` resolution.** The README and `install.py` put Codex skills in
`$CODEX_HOME/plugins/cache/...` as namespaced `orchestrate:review-milestone` (RESULT-D item 11). Three places don't
know that:
- `skill_warnings` (`agent_loop.py:1488-1510`) looks for Codex skills in `~/.agents/skills`, `/etc/codex/skills` and
  `.agents/skills` up the tree, and flags `~/.codex/skills`, but never looks in the plugin cache. After the recommended
  install, every `LOOP run/review/plan` on Codex warns that the skill "isn't installed where codex finds skills by
  name", and `build/SKILL.md:88-89` tells the lead to report that warning to the owner. For Claude the same function
  does check `CLAUDE_HOME/plugins/**` (line 1499), so the asymmetry is an oversight, not a design.
- `skill_note` (`agent_loop.py:1224-1228`) writes `$review-milestone in Codex`. Whether a bare `$name` reaches a plugin
  skill registered as `orchestrate:review-milestone` wasn't checked by anyone (RESULT-D only lists the names). The
  prompt also gives the file path, so the agent can still read it, which is the saving grace.
- `skill-creator/references/writing.md:143-157` ("Where skills live") describes only `~/.claude/skills`,
  `~/.agents/skills` and `npx skills add`, with no mention of plugins, while the README now says to install these
  skills as plugins because that's what carries the hook. `skill-creator/SKILL.md:79` sends the reader there. The
  section is dated 8 November with "host versions weren't recorded".
Suggested: add `CODEX_HOME/plugins/cache/**/skills/<name>/SKILL.md` (or wherever `codex plugin add` lands skills) to
`skill_warnings`; add a dated paragraph on plugin installs to writing.md; and confirm `$name` versus
`$plugin:name` once with a Codex turn when quota allows, then make `skill_note` match.

### 4. Under the plugin install the loop never uses the orchestrate agent files on Claude

**Verified by code; the plugin-side observation is RESULT-D's.** `agent_installed` (`agent_loop.py:1219-1221`) checks
`~/.claude/agents/<name>.md` and `<worktree>/.claude/agents/<name>.md` only. `install.py` runs `install_agents.sh`
with `--codex-only` (`install.py:127`), relying on the marketplace entry's `agents` list for Claude, and RESULT-D
reports `claude plugin details orchestrate` showing `Agents (0)`, uninvestigated. So on Claude the review and plan
turns run without `--agent`, which means without the agent's `skills:` preload and its `disallowedTools`. The loop
still passes `--disallowedTools Agent` itself (line 1263), and the prompt names the skill, so the result is a slower
start rather than a broken one. The sub-agents page confirms a plugin agent can be addressed by its bare name when
unambiguous, so if the plugin's agents do load, `agent_installed` could ask `claude agents` (or glob
`CLAUDE_HOME/plugins/**/agents/`) instead of two fixed paths. The README host table ("plus the orchestrate agent files
when installed") should say that the plugin install doesn't install them for the loop until this is fixed.

### 5. The README's update rule is version-dependent, and the manifest layout has a latent trap

**Suspected for the first; verified doc rule for the second.** `README.md:150-152` and `install.py:97` say Claude Code
re-copies a plugin only when its `version` changes, so bump it on each change. The current host-marketplace page says
the opposite for exactly this install path: "A plugin that users load in place from a marketplace they added from a
local path isn't controlled by `version`. It loads your current files at every session start". RESULT-D saw a cache
copy on 2.1.239, so the behaviour has probably changed between 2.1.239 and the current docs; the README should say
which it observed and on what version, or `install.py` should check for the in-place case. Second, all four
marketplace entries use `source: "./"` with `strict: false` and declare `skills`, `agents` or `hooks`. The marketplace
reference says that with `strict: false`, if the fetched plugin has a `plugin.json`, "an entry that declares any
component field is a conflict, and the plugin fails to load". There is no root `.claude-plugin/plugin.json` today, so
the entries are the manifests and this works, but the first person who adds one (the skill-creator testing reference
at `testing.md:218` tells people to add a `plugin.json` for `claude plugin eval`) breaks all four plugins at once. A
one-line comment in `marketplace.json` isn't possible, so put the warning in the root README's setup section.

### 6. Model and effort are still inside the Codex goal objective, and open every other template

**Verified.** `BUILD_TEMPLATE` (`agent_loop.py:158-175`) begins with `GOAL_LINE` ("Call your create_goal tool with this
objective") and ends with "(Launched on {model} at {effort} effort.)", so the builder's objective text carries the
line. `instructing-agents/SKILL.md:52-54` says: "Don't put them inside a `/goal` objective: the receiver can't make
that text true, and Codex may audit it as a requirement", and `kinds.md:51` repeats it. RESULT-B moved the line from
the head to the tail, and the test (`test_item6_the_build_prompt_no_longer_opens_with_the_model`) checks only that.
`REVIEW_TEMPLATE`, `DESIGN_REVIEW_TEMPLATE` and `PLAN_TEMPLATE` (lines 177-192) still open with "Model {model},
effort {effort}." RESULT-B says the plan named only the build template. The launch record (`launch_record`, line
1419) already holds the requested and observed values, which is the place the skill says they belong. Drop the line
from all four templates. On Claude, finding 1 makes the review and plan lines untrue in any case.

### 7. A resumed Claude turn restates the rules but not the objective

**Verified text; suspected consequence.** On Codex, an active goal re-sends the objective each turn, so the loop's
restatement carries only the binding rules, and only when no goal is active (`agent_loop.py:2063-2068`). On Claude
and generic hosts every resumed turn gets "Continue the objective." plus `binding()` (lines 1426-1447), about 60
words naming the milestone, the done-when path, `land`, the Check and the profile's bounds. After a compaction that
summarised away the first prompt, "the objective" has nothing to point at except what the summary kept. The
instructing-agents skill's own rule ("A rule that must hold through a long run belongs somewhere it gets re-read",
`SKILL.md:88-96`) argues for one more sentence: what claimed means for this milestone. The first sentence of
`BUILD_TEMPLATE` is about 40 words and already parameterised; appending it to the Claude restatement costs little and
makes the two hosts equivalent. The alternative the README rules out, Claude `/goal` under `-p`, would do the same
job if it works there; the README says the loop doesn't use it, without saying why.

### 8. The hook's launch pattern misfires both ways

**Verified by running it.** `handoff_nudge.py:16` treats `;`, `&`, `|` and `(` as shell separators without regard to
quoting, so `git commit -m "note: run tests && codex exec later"` is refused (I ran it), and the owner's identical
gate refused one of my Bash calls this session whose only `codex exec` was inside a quoted JSON string. The same
pattern misses `timeout 600 claude -p …` and `CLAUDE_CONFIG_DIR=/x claude -p …` (both pass), because the launch token
must come first or after a separator. The cost of a false positive is one refusal per context landing on an
unrelated command; the cost of a miss is the original failure mode. The heredoc case (a body line starting with
`codex exec`) correctly passes. Also, the docstring at line 9 says the hook ships "(hooks/hooks.json next to this
file)"; it ships inline in `marketplace.json`, as RESULT-D explains and as the marketplace reference requires. Low
effort fixes: strip single- and double-quoted spans before matching, and allow a leading `env`, `timeout N`,
`nohup` or `NAME=value` tokens.

### 9. The two skills give different default efforts for the same work

**Verified text.** `instructing-agents/references/hosts-and-models.md:163-164`: "medium for routine work and high for
hard debugging, subtle audits and long unattended runs". `orchestration/README.md:9-12` and the three skills run
builders in long unattended runs and reviewers (a subtle audit of a possible fake) at medium; the planner at high.
Both are defensible, and the owner's pacing prefers medium, but the two sets will be read together and should either
agree or say why the loop's default is lower (the owner sets the pace; reviewers are calibrated by graded examples).
One sentence in either place.

### 10. Small things

- `skill-creator/references/testing.md:196-197` says the auto-compact window "on one machine in November 2026 was
  350,000 tokens"; the owner's `~/.claude/settings.json` now has `autoCompactWindow: 500000`. Verified. Fine as a
  dated observation; worth updating since the sentence tells people when to expect compaction.
- `BUILD_TEMPLATE` line 172: "If you're blocked (probed directly) or missing context" is unclear in the one prompt
  every builder reads. Verified.
- `freshness.json` top-level `updated` is `2026-09-09` while the instructing-agents entry says `last_checked`
  `2026-11-09`. Verified; cosmetic.
- Root `README.md:60` still gives `npx skills add` as the orchestrate install, and line 112 the `/plugin install`
  route, beside the new `install.py` section. Three routes for one set, with the hook only on one of them. Say which
  is the default and when the others are fine. Verified.
- `hosts-and-models.md:13` dates its checks to Claude Code 2.1.317 (the desktop app) while the loop and `install.py`
  run the PATH `claude` 2.1.239, which the fold-d work was tested on. Both are stated; a reader has to notice they
  differ. Verified.
- RESULT-D's Codex facts (Codex reads `.claude-plugin/marketplace.json`, plugin hooks need approval, skills are
  namespaced) rest on empirical checks with the app's bundled CLI; the OpenAI plugins page I fetched confirms hooks
  must be reviewed before they run and that a Codex plugin can carry hooks, but doesn't document the Claude-format
  marketplace read or the model-facing skill name. The README states these as checked on 0.167.0-alpha.3.2, which is
  the right way to state them. Nothing to change; noted so nobody reads them as a contract.

## What holds together, and what I checked that holds

- **Thesis and mutual exclusion.** instructing-agents (what a brief carries, where a rule lives), skill-creator (what a
  skill body carries, receiver-side runs, hooks shipped in the package) and orchestrate (done by evidence the loop
  checks) say the same thing from three directions. Each description ends with a "Not for … (other skill)" line that
  names the right neighbour, and `build` is explicit-only on both hosts.
- **Always-loaded weight.** Descriptions: instructing-agents 432, skill-creator 324, build-milestone 316, review-milestone
  423, plan-module 457 characters; `build` 416 but hidden by `disable-model-invocation` (the skills page confirms the
  description leaves the model's context) and `allow_implicit_invocation: false` on Codex. Codex gets one AGENTS.md
  line. The hook adds one line, once per context, again after `compact_boundary` or 400 KB. This meets the owner's
  constraint. The only weight nobody needs is the duplicates in finding 2.
- **Long unattended runs.** Durable state in files (plan, done-when, `-ACCEPTED.json`), rules re-read on resumed
  turns, checks run by the loop in a clean tree, fresh reviewers on another host, a text-only ending treated as a
  report and re-prompted, progress-based budget rather than a timer, and launch records that separate requested from
  observed. This matches Anthropic's harness posts, the Opus 5.5 unattended guidance (the loop is the loop, so the
  paragraph isn't needed in prompts) and OpenAI's spec/plan/status advice. Finding 7 is the one gap I'd close.
- **Host facts re-checked today and holding:** PreToolUse `permissionDecision: deny` blocks the call and shows the
  reason to the model; hook input carries `session_id`, `transcript_path`, `cwd`, and `agent_id` inside subagents;
  `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` are exported to hook processes; entry `hooks` must be an inline
  object and the file-path form fails only at load time (exactly what RESULT-D found and writing.md now says); loaded
  skill content isn't re-read and re-attaches at 5,000 tokens each within 25,000 after compaction; the listing cuts
  descriptions at 1,536 characters; plugin skills are `plugin:skill` with the bare form working when unambiguous;
  subagent `skills:` preloads full content; `omitClaudeMd` needs 2.1.271; Explore and Plan skip CLAUDE.md.
- **Checks.** 121 loop tests pass; `check_skill.py` ok on all six skills; `claude plugin validate .` passes; the hook
  nudges once, passes the resend, ignores `agent_loop.py run`, and re-nudges after a `compact_boundary` (all run).

## What I'd do before merging to main and installing

1. Decide finding 1 and apply it (I'd remove `model`/`effort` from the three skills).
2. Make `install.py` remove or refuse the owner's standalone copies and hand hook (finding 2), then run it.
3. Teach `skill_warnings` the Codex plugin cache and document plugin installs in writing.md (finding 3).
4. Drop model and effort from the four loop templates (finding 6); add the objective sentence to the Claude
   restatement (finding 7).
5. Quote-strip and prefix-allow in the hook pattern; fix its docstring (finding 8).
6. Fix the README's update sentence and add the `plugin.json` warning (finding 5); the small items as time allows.
7. Then the two behavioural checks the plan still owes: a live loop claim with a resumed Claude turn (which also
   shows whether the skill's `effort` frontmatter changes the turn), and one post-compaction handoff in a real session
   with the plugin hook installed and the hand hook removed.
