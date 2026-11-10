# Anthropic guidance on multi-agent harnesses and long-running work (as of 2026-11-09)

Method note: all pages were fetched through WebFetch, which returns a small-model summary of the page, not raw text. The two prompting-guide pages (Fable 5.2, Fable 5, Opus 5) and the agent-teams/costs docs came back near-verbatim; the engineering blog posts came back as summaries, so numbers there are as relayed and a few should be spot-checked against the page. Evidence type: M = measurement reported by Anthropic, O = opinion or design judgment, A = anecdote or single case study. Anthropic engineering index URLs appear as /research/... in the index and /engineering/... in links; both forms were seen.

## 1. Harness design for long-running work: decomposition, roles, resets vs compaction, state, verification, removing components

### Takeaway
The current Anthropic position (Mar-Nov 2026) is: use a planner / generator / separate evaluator only where measurement shows headroom, write state to files, prefer fresh-context verification for hard or subjective work, and treat every harness component as an assumption about model weakness to be removed one at a time as models improve. Context resets and sprint decomposition were both dropped as models improved (Opus 4.5, then 4.6).

### Cited Findings
- Harness design post, 2026-03-24, Prithvi Rajasekaran (Labs). Generator/evaluator loop for frontend design, extended to planner + generator + evaluator for full-stack builds, on the Claude Agent SDK. [M/A: a few runs, author judgment] — https://www.anthropic.com/engineering/harness-design-long-running-apps
  - Self-evaluation failure: agents "praise their own mediocre work", especially on subjective tasks. A separate evaluator is easier to tune sceptical, but is still an LLM and lenient out of the box. Out-of-box evaluator "found issues, then talked itself into approving them" and tested superficially; the author tuned it by reading its judgments against his own.
  - Planner: expands 1-4 sentences into a full spec, kept high-level on technical detail so spec errors do not cascade. Removing it made the generator under-scope (kept in the later, simpler harness).
  - Sprint contracts: before coding, generator proposes what "done" means and how it will be verified; evaluator reviews until agreed; communication through files. Sprint 3 alone had 27 criteria.
  - Evaluator drives the live app with Playwright MCP (UI, API, DB state) and grades four criteria, each with a hard threshold; failing any one fails the sprint.
  - Cost/latency (Opus 4.5, retro game maker): solo 20 min / $9, game non-functional; full harness 6 hr / $200 (over 20x), playable but rough, AI-made levels had unwinnable obstacles.
  - Opus 4.6 simplification: radical cut did not match performance, so components were removed one at a time. Sprint construct removed; evaluator moved to a single end-of-run pass; planner kept; evaluator kept because it "still added value on tasks at the edge of the model's solo ability". DAW run: 3 hr 50 min, $124.70 (planner $0.46; build rounds $71.08/$36.89/$5.88; QA rounds $3.24/$3.09/$4.06). QA was about 5% of cost.
  - Principle quoted: "every component in a harness encodes an assumption about what the model can't do on its own"; stress-test as models improve. Also: "the space of interesting harness combinations doesn't shrink as models improve", it moves.
  - Context: Sonnet 4.5 showed "context anxiety" (wrapping up early near its believed limit), so resets were essential; Opus 4.5 largely removed it and the author ran one continuous session with automatic compaction. Resets cost orchestration complexity, tokens, latency; compaction keeps continuity but does not clear anxiety.
  - Limit stated: Claude cannot hear, so QA of musical taste was weak (applies to any modality the evaluator cannot perceive).
- Effective harnesses for long-running agents, 2025-11-26 (older), Justin Young. [A/O, claude.ai-clone case] — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - Initializer agent (first session only: init script, progress log, first git commit) then a coding agent per session doing one feature and leaving clean state. Same system prompt and tools; only the first user prompt differs.
  - Feature list as JSON (200+ features, each with steps and a `passes` flag). Coding agents may only flip `passes`; JSON chosen over Markdown because models overwrite it less. Instruction: "It is unacceptable to remove or edit tests".
  - Progress file plus git history let a fresh agent orient. Startup routine: pwd, read git log and progress, pick top unfinished feature, run init script and a basic end-to-end check.
  - Browser automation (Puppeteer MCP) end-to-end testing "noticeably improved results" over unit tests and curl alone; it cannot see native browser alert modals.
  - Failure modes: declares done too early, marks features passing prematurely, leaves undocumented bugs, wastes time starting the app.
  - Open questions it left: would separate testing/QA/cleanup agents beat one general coding agent? (Answered partly by the March post above.)
- Claude prompting best practices (living doc, current as of this fetch), long-horizon section. [O, with some internal tests] — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - Multi-context-window workflow: first window sets up framework (tests, setup scripts), later windows iterate a todo list; tests in structured format (e.g. tests.json); an init.sh; "starting fresh" can beat compaction because the models "are extremely effective at discovering state from the local filesystem"; be prescriptive on startup ("Review progress.txt, tests.json, and the git logs").
  - Unstructured text for progress notes, structured files for test status, git for state ("especially well" at using git across sessions); give verification tools (computer use, browser use) as autonomous tasks lengthen.
  - If the harness compacts, tell the model so it does not wrap up near the limit.
- Prompting Claude Fable 5 (current model page). [O + some internal testing] — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
  - "Make self-verification explicit in long-run prompts. Separate, fresh-context verifier subagents tend to outperform self-critique." Suggested prompt: establish a check every [X] interval, "verifying your work with subagents against the specification". No number given.
  - "Ground progress claims": audit each claim against a tool result from this session; in Anthropic's testing this "nearly eliminated fabricated status reports". [M, no figure]
  - "Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality. Review and consider removing older instructions."
  - Avoid showing the model a remaining-token countdown (triggers suggestions to start a new session). Memory: one lesson per file, one-line summary at top.
  - Longer turns by default; consider checking on runs asynchronously (scheduled jobs) rather than blocking.
- Prompting Claude Fable 5.2 (newest page seen). [M for the figures quoted] — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2
  - Start effort at `high`; `medium` for interactive work; `xhigh` only where you have measured a gain (slightly higher scores, many more tokens on internal coding evals); `low` for high-volume "fast, intelligent subagents". Most capability gain already at `high`; rerun your own effort sweep per model.
  - Early stopping at low/medium effort; an anti-stopping prompt halved sessions ending with doable work left but raised output tokens about 30%.
  - Harness items to review when migrating: a token budget written into the prompt (removing a large one lowered cost at equal performance on coding tasks); harness code that edits earlier turns (breaks preserved thinking; keep history append-only except compaction/context editing); accumulated cautious notes and "never" rules (retry rate fell from nearly all to about four in ten with stale "never retry" notes in context; a reviewer's "stop at first error" made 5.2 not retry about a third of the time).
  - Code ownership sentence ("This codebase is yours...") raised merging of repeated code from under a tenth to about half of tries at about 1.5x output tokens, with unrequested changes; review the diff, not the summary.
- Prompting Claude Opus 5. [O/M mixed] — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5
  - "Claude Opus 5 verifies its own work without being told to. If your prompt contains explicit verification instructions ('use a subagent to verify') remove them: ... over-verification ... removing them reduces wasted tokens with no loss in quality. The same applies to legacy harness scaffolding that adds separate verification steps."
  - Review prompts: "only report high-severity" is followed literally and reports less; ask for everything and filter in a separate pass.
- Scaling Managed Agents, 2026-04-08, Lance Martin, Gabe Cemaj, Michael Cohen. [O/architecture, plus one latency figure] — https://www.anthropic.com/engineering/managed-agents
  - Splits Session (append-only event log outside harness and sandbox), Harness (loop), Sandbox. Durable session means a crashed harness resumes from the last event. Restates that context resets helped Sonnet 4.5 and became unnecessary with Opus 4.5. Lazy container provisioning reportedly cut p50 time-to-first-token about 60%, p95 over 90%.
- Agent Harness Design: 3 Patterns, 2026-04-02, Lance Martin (Claude Platform). [M for benchmark numbers] — https://claude.com/blog/harnessing-claudes-intelligence
  - Patterns: lean on what the model already does well (bash, text editor), strip the harness down, set boundaries carefully (caching, declarative tools for gated actions). Context resets for Sonnet 4.5 became "dead weight" with Opus 4.5.
  - BrowseComp: letting Opus 4.6 filter its own tool outputs via code raised accuracy 45.3% to 61.6%; subagents improved BrowseComp by 2.8% over best single-agent Opus 4.6 runs; Sonnet 4.5 flat at 43% regardless of compaction budget while Opus 4.5 reached 68% and Opus 4.6 84%; a memory folder lifted Sonnet 4.5 on BrowseComp-Plus from 60.4% to 67.2%. Cached tokens cost about a tenth of base input.
- Effective context engineering, 2025-09-29 (older), Rajasekaran et al. [O] — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - "Smallest possible set of high-signal tokens"; compaction (tune for recall then precision; clearing old tool results as the light first step), structured note-taking, sub-agent architectures returning condensed summaries, just-in-time retrieval; "do the simplest thing that works".
- The components of agent memory, 2026-11-06 (newest), Lance Martin. [M] — https://www.anthropic.com/research/components-of-agent-memory
  - Tell the model what memory is for, not how to use it; over-recording hurts (Sonnet 3.7 wrote 413 memory files in Pokemon vs Fable 5's 10, with one badge vs four); keep the injected layer small (Claude Code loads first 200 lines or 25 KB of the memory index); parallel agents should get separate pages, since one shared file gets overwritten; "dreaming" (offline memory reorganisation) shown to correct wrong notes. Records only-failures rule lowered gains. Compaction is treated as separate from memory.
- Building a C compiler with parallel Claudes, 2026-02-05, Nicholas Carlini (Safeguards). [A: one extreme project, author skeptical] — https://www.anthropic.com/engineering/building-c-compiler
  - 16 parallel Opus 4.6 instances, about 2,000 sessions over about two weeks, about 2B input / 140M output tokens, about $20,000, about 100k lines of Rust that builds Linux 6.9 (x86, ARM, RISC-V). No orchestrator agent: each agent picks "the next most obvious" problem; tasks claimed by lock files in `current_tasks/` resolved through git; some agents specialised (dedupe, performance, design review, docs).
  - Test harness lessons: tests must be nearly perfect "because an autonomous agent will otherwise solve the wrong problem"; keep output short, log to files, grep-able error tags, precomputed summaries; "time blindness" so a `--fast` sampled mode; CI added late because new features kept breaking old ones; maintained READMEs and progress files; known-good oracle (GCC) to split failures when all agents hit the same kernel bug (parallelism collapsed there).
  - Self-reported limits: "nearly reached the limits of Opus's abilities"; not a drop-in; author "uneasy" that passing tests can be mistaken for done and unverified code could ship.

### Inferences
- The framework's planner / builder / fresh-context reviewer shape matches the March post, but Anthropic's evidence for the evaluator is "worth it at the edge of solo ability", not "always"; for tasks within the builder's ability it dropped per-sprint evaluation to one end pass.
- Sprint-contract style "done" criteria (agree criteria before building) is a measured-by-anecdote practice from one author, and was itself dropped at Opus 4.6 for the sprint split but the criteria idea is not shown to be retired; the post does not say contracts failed, only that the sprint decomposition became unnecessary.
- Tension to flag: Fable 5 page recommends fresh-context verifier subagents; Opus 5 page says remove "use a subagent to verify" and legacy verification scaffolding. Both are model-specific and neither gives a head-to-head number. A framework should make reviewer depth a per-model, measured setting.

### Gaps
- No Anthropic figure found for how much a fresh-context verifier beats self-critique (Fable 5 page asserts it without a number).
- Did not read the full text of the harness-design post, only a summary; the exact evaluator-skepticism tuning procedure and the per-criterion thresholds were not captured.
- Did not fetch Skills / skill-creator material, auto-mode post, or the April 23 Claude Code quality postmortem.
- A search snippet claimed the harness post is indexed under 2026-10-13; the engineering index fetch showed 2026-03-24 (October 13 is "Redesigning source control"). I treat 2026-03-24 as correct.

## 2. When multi-agent pays for itself and what it costs

### Takeaway
Anthropic's stable line since 2025 is: start single-agent; multi-agent costs roughly 3-15x tokens, pays off for parallel, breadth-heavy, context-overflowing or specialised work, and is a poor fit for tightly coupled work such as most coding. 2026 material tightens this (Oct 2026: fold subagents back in; skills in one loop often beat subagents) while newer models make delegation easier and more eager.

### Cited Findings
- Multi-agent research system, 2025-06-13 (older), Anthropic engineering. [M on internal research eval] — https://www.anthropic.com/engineering/multi-agent-research-system
  - Agents use about 4x chat tokens; multi-agent about 15x. Pays off for high-value, parallelisable, wider-than-one-context, many-tool tasks; "most coding" with shared context or heavy dependencies is a poor fit.
  - Opus 4 lead + Sonnet 4 subagents beat single Opus 4 by 90.2% on the internal research eval.
  - Effort scaling baked into prompts: simple fact-finding 1 agent / 3-10 calls; comparisons 2-4 subagents / 10-15 calls each; complex research 10+ subagents.
  - Failure modes: 50 subagents for simple queries, endless search for nonexistent sources, distracting updates, duplicated work from vague briefs.
- Building multi-agent systems: when and how, 2026-01-23, Cara Phillips et al., claude.com. [O, with cost range] — https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them
  - Three justified cases: context protection, parallelisation ("primary benefit is thoroughness, not speed"), specialisation (too many tools or conflicting behaviours).
  - "typically use 3-10x more tokens than single-agent approaches for equivalent tasks" from duplicated context, coordination messages, handoff summaries.
  - Verification subagent named; failure called "the early victory problem" (verifier runs a few tests, sees pass, declares success); mitigations: concrete criteria, comprehensive and negative tests, instruct to run the full suite. Advice: simplest approach first; better prompting of one agent sometimes matches elaborate designs. Message bus / swarms deferred.
- When to fold subagents into the main loop, 2026-10-22, Diane Sarkis, claude.com. [M-ish: enterprise comparisons, small samples] — https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop
  - "a single agent with skills frequently outperformed both the one-prompt-for-everything design and the subagent design on quality". One customer saw about 2x faster runtime with a single loop. Anthropic cut Claude Code's system prompt by over 80% for advanced models via progressive disclosure.
  - Keep subagents when: measurable context-bloat degradation, true parallelism with disposable context, tool-selection trouble (degrades past about 30-50 tool definitions) or conflicting instructions, a subagent must talk to the user. Fold in when specialists chain on each other, share data, or were split "by org chart rather than by problem".
  - Method: small end-to-end eval first (10 golden examples is enough to start), fold in one subagent at a time, run each task more than once (a folded subagent broke a process in one of two runs).
- Claude Code docs, agent teams (experimental, disabled by default) and costs. [Product docs; the 7x is a stated approximation] — https://code.claude.com/docs/en/agent-teams ; https://code.claude.com/docs/en/costs
  - Agent teams: "coordination overhead and use significantly more tokens"; best for research/review, new modules with separate ownership, competing-hypothesis debugging, cross-layer work; sequential tasks, same-file edits, many dependencies are better in one session or subagents. Costs page: teams use "approximately 7x more tokens than standard sessions when teammates run in plan mode"; use Sonnet for teammates; keep teams small; shut idle teammates down.
  - Team size: start with 3-5; 5-6 tasks per teammate; "Three focused teammates often outperform five scattered ones"; avoid two teammates editing the same file; start with research/review before parallel implementation; do not leave a team unattended too long. Known limits: no session resumption for in-process teammates, task status lag, no nested teams, one team per session, lead can stop early.
- Harness-design post cost figures above: evaluator rounds were about 5% of total spend; whole harness over 20x solo cost for a qualitatively different (working) outcome. C compiler: about $20,000. [M/A]
- Opus 5 / Fable guides: Opus 5 coordinates teams well "with effective writer-verifier patterns and few cases of agents overwriting each other's work"; Fable 5 "significantly more dependable at dispatching and sustaining parallel subagents". Fable 5.2: "subagents can account for a large part of what a session costs". [O with testing] — prompting pages in section 1.

### Inferences
- Cost multiples are not consistent across sources (3-10x, 4x/15x, 7x in plan mode, 20x for harness vs solo); each measures a different thing. A framework audit should not quote one number; it should measure its own per-milestone token ratio.
- Anthropic's own repeated tests of "does decomposition help" all favour decomposition only when tasks are independent or the single agent is demonstrably degrading; the Oct 2026 article is the most recent and the most sceptical of subagent proliferation.

### Gaps
- No Anthropic number for coding-specific multi-agent uplift beyond the C compiler anecdote and the 2.8% BrowseComp subagent gain.
- Cost page 7x claim is unqualified for non-plan-mode teams.

## 3. Delegation, briefing, orchestrator/worker, agent teams, model and effort per role

### Takeaway
Briefs must be self-contained because subagents see none of the lead's context; newer models over-delegate unless told when it is and is not worth it, with cost stated first; route cheap or high-volume work to smaller models or lower effort, and cap depth, concurrency and spend deterministically.

### Cited Findings
- Briefing: a research subagent needs objective, output format, tool/source guidance, clear boundaries; vague briefs caused duplication ([2025-06-13 post](https://www.anthropic.com/engineering/multi-agent-research-system)). Claude Code: non-fork subagent "does not see your conversation history, previously invoked skills, or files already read"; gets only the delegation message, its system prompt, CLAUDE.md (Explore/Plan skip it) and git status, so "restate any rule it must follow" ([sub-agents docs](https://code.claude.com/docs/en/sub-agents)). Teammates likewise get the spawn prompt but not the lead's history; "include task-specific details" ([agent teams](https://code.claude.com/docs/en/agent-teams)). Fable 5: stating the reason behind a request improves performance for long-running agents ([Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)).
- Over-delegation control: Opus 4.6 "strong tendency" to spawn subagents where grep suffices ([best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)); Opus 5 delegates "more readily", "multiplies cost and time when applied to small tasks"; sample guidance: delegate only for large, genuinely independent, parallelisable work; "do not use subagents to verify or double-check your own work"; deterministic caps via `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, SDK `max_budget_usd` ([Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)). Fable 5.2: a tool description that states cost first, says when delegation is and is not worth it, and how to brief cut delegation about a third on short tasks with the same success [M]; early testers liked 5.2 as planner/orchestrator for other models; Fable 5.2 used subagents to review its own work at `xhigh`/`max` unprompted ([Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)). Fable 5: prefer asynchronous orchestrator-subagent communication, long-lived subagents that keep context "save time and cost through cache reads".
- Claude Code subagent mechanics: nesting up to three layers by default; concurrency cap 20; subagent `model` options `sonnet`/`opus`/`haiku`/`fable`/inherit; "Routing routine work to Haiku via `model` is the main lever for controlling cost"; subagent requests count against the same usage limits ([sub-agents docs](https://code.claude.com/docs/en/sub-agents), [costs](https://code.claude.com/docs/en/costs)). Teammates inherit lead effort when on the lead's model; cannot set per-teammate permission modes at spawn; hooks `TeammateIdle`, `TaskCreated`, `TaskCompleted` can exit 2 to block completion (quality gates) ([agent teams](https://code.claude.com/docs/en/agent-teams)).
- Plan-before-implement for teammates exists, but a teammate plan is auto-approved by default unless you change its mode; the lead only reviews if the teammate was put in plan mode manually ([agent teams](https://code.claude.com/docs/en/agent-teams)).
- Orchestrator-workers and evaluator-optimizer as named patterns: Building Effective Agents, 2024-12-19 (older; page now carries a note that tooling has changed) ([post](https://www.anthropic.com/research/building-effective-agents)). Evaluator-optimizer "works best with clear evaluation criteria".
- Model/effort per role: Fable 5.2 says low effort for "fast, intelligent subagents", medium interactive, high for long unattended; "plan and iterate at medium, then raise effort for the long unattended part" with a per-message effort change (beta) to keep the cache. Opus 5: use `low`/`medium` "liberally as your primary control for token cost"; accuracy of review holds at lower effort, "fast pass at review time and a more thorough pass later". Research system (older): stronger lead, cheaper subagents. Always "test each change against your own evals" ([Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2), [Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)).
- Caution accumulation across agents: notes, instruction files and reviewer messages that say "never" or "stop at first error" can make Fable 5.2 hold back routine work in multi-agent setups; name steps that need no approval; write the exception into the rule ([Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)). [M, simulated tasks]

### Inferences
- A fresh-context reviewer gets only what the brief and files give it; the review brief should restate criteria and how to run checks. A reviewer's "stop at first error" style output can propagate caution into builders if it is stored in shared notes.
- Review depth and effort could be set per role and per model generation; Anthropic's only stated rule is to sweep effort on your own evals, no universal reviewer setting.

### Gaps
- No Anthropic guidance found on a lead model vs subagent model split beyond the 2025 research post (Opus lead, Sonnet workers) and "use Sonnet for teammates" / "Haiku for simple subagents".
- Skills and skill-creator material, and talks, not covered.

## 4. Evaluating subjective output and judge reliability

### Takeaway
Anthropic's workable method for subjective work is criteria-based LLM grading calibrated with few-shot score breakdowns, run against the live artifact with browser tooling, with weighted criteria and hard thresholds, and tuned by reading the evaluator's traces against the human's judgment; it concedes evaluators are lenient and blind in modalities they cannot perceive.

### Cited Findings
- Frontend design (Mar 2026 harness post) [A/M-ish; one author] — https://www.anthropic.com/engineering/harness-design-long-running-apps
  - Four criteria: design quality, originality, craft, functionality; design and originality weighted more because Claude already did craft/functionality well. Originality penalised template defaults and "AI slop" (e.g. purple gradients over white cards). Few-shot examples with detailed score breakdowns reduced score drift. Evaluator navigated the live page with Playwright MCP, screenshotted, scored each criterion, wrote a critique. 5-15 iterations, runs up to four hours; generator chose refine vs pivot after each critique.
  - Observations: scores rose then plateaued; progress non-linear; author sometimes preferred a middle iteration; criterion wording steered output ("museum quality" pushed toward a visual convergence); even first iteration beat a no-prompt baseline.
  - Full-stack evaluator criteria: product depth, functionality, visual design, code quality, each with hard threshold.
  - Limitation: cannot judge audio quality; QA on taste was weak.
- Demystifying evals for AI agents, 2026-01-09, Grace, Hadfield, Olivares, De Jonghe. [O, practice guidance] — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  - Code graders fast/objective but brittle; model graders flexible but non-deterministic, costlier, need calibration against human experts; humans for calibration.
  - Give the judge an "Unknown" escape hatch; grade each dimension with a separate isolated judge against a structured rubric; grade outcomes not paths; partial credit.
  - pass@k vs pass^k (75% per trial over 3 trials gives roughly 42% all-pass); isolate trials from clean state; a good task is one where two domain experts independently reach the same verdict; a reference solution proves solvability; 0% over many trials usually means a broken task or grader.
- Quantifying infrastructure noise, 2026-02-05, Gian Segato. [M] — https://www.anthropic.com/engineering/infrastructure-noise
  - Terminal-Bench 2.0: 6 percentage points between most- and least-resourced setups (p<0.01); infra error rate 5.8% at 1x vs 0.5% uncapped; score flat 1x to 3x; skepticism for leaderboard gaps under about 3 points. Guaranteed allocation plus a separate kill threshold; treat resources as a controlled variable.
- Verification-subagent failure mode "early victory problem" ([multi-agent systems post](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them), 2026-01-23); test quality as ceiling: nearly perfect tests needed ([C compiler](https://www.anthropic.com/engineering/building-c-compiler)).
- Anthropic's own frontend skill is referenced for design defaults ([best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)); Sonnet 5 / Opus 4.8 pages mention "design and frontend defaults" (not read in full).
- Vision: Opus 5 is strong on UI and frontend visual replication, best "when the model has tools to iteratively analyze, crop, and visually verify" ([Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)).
- Not-yet-fetched but listed: Eval awareness in Opus 4.6's BrowseComp performance (2026-03-06), Designing AI-resistant technical evaluations (2026-01-21) — https://www.anthropic.com/engineering

### Inferences
- For games and 3D assets, the nearest Anthropic evidence is "evaluator plays the running app through browser/computer tooling" plus rubric weighting; there is no Anthropic measurement of judge reliability on 3D or game feel. Perceptual gaps (audio, possibly animation timing and physics feel) are the stated weak spot.
- Calibration against the owner's own judgments is the only evaluator-reliability method Anthropic describes working, and it is manual.

### Gaps
- No human-vs-LLM agreement statistics for design grading found. No Anthropic guidance specific to games or 3D found.
- Eval-awareness and AI-resistant-evals posts not read.

## 5. What changed in 2026 versus 2024-2025

### Takeaway
2024-25 guidance said: simplest solution, five workflow patterns, orchestrator-workers, multi-agent about 15x tokens, resets plus initializer/coder pattern. 2026 guidance adds: planner/generator/evaluator with the evaluator justified only at the model's capability edge; explicit pruning of harness parts as models improve (resets, sprints, verification steps, delegation instructions, token budgets); stronger and more eager native subagent use that now needs throttling; and a late-2026 swing towards folding subagents into skills-equipped single loops.

### Cited Findings (dated change log)
- 2024-12-19 Building Effective Agents: workflows vs agents, five patterns, "simplest solution possible" — https://www.anthropic.com/research/building-effective-agents. Page now notes the tooling changed and points to Managed Agents. Principle (simplicity, evaluator-optimizer needs clear criteria) not retracted.
- 2025-06-13 multi-agent research system: 15x tokens, 90.2% gain, coding a poor fit — still cited; softened by Jan 2026 post (3-10x) and Oct 2026 post (fold in).
- 2025-09-29 context engineering: compaction, notes, sub-agents. Updated by Mar 2026 findings: compaction value depends on model (Sonnet 4.5 flat, Opus 4.6 84% on BrowseComp), and Nov 2026 memory post says compaction is separate from memory.
- 2025-11-26 initializer/coder, JSON feature list, progress file, per-session reset. Changed by 2026-03-24 (resets dropped for Opus 4.5+, sprints dropped for Opus 4.6; evaluator added) and by the prompting guide ("starting fresh can beat compaction" retained as an option).
- 2026-01-23 multi-agent systems: 3-10x tokens, three justified cases.
- 2026-02-05 C compiler: parallel agents with no orchestrator, lock files; tests as the control surface.
- 2026-03-24 / 04-02 / 04-08: harness-as-assumptions principle stated three times (harness-design post, harnessing-intelligence post, Managed Agents post).
- 2026-10-22 fold subagents back in; skills over subagents.
- Model-page drift: Opus 4.6 over-uses subagents and over-engineers; Opus 5 verifies itself, so remove "use a subagent to verify"; Fable 5 recommends fresh-context verifier subagents; Fable 5.2 says delegation is eager, cost-first tool descriptions cut it about a third, token budgets in prompts raise cost, remove stale "never" notes. Sources: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2 and linked pages above.
- Agent teams in Claude Code: still marked experimental and disabled by default in the docs fetched on 2026-11-09 (https://code.claude.com/docs/en/agent-teams).
- Not found: any explicit Anthropic statement that the March 2026 planner/generator/evaluator pattern was superseded. The harness-design post remains current guidance with a revision made inside it (Opus 4.6 simplification).

### Inferences
- Items likely safe to cut by Anthropic's own logic: fixed per-sprint review gates, forced context resets, always-on verification subagents, delegation instructions that push work out, token-budget text in prompts, and long accumulated "never" rules, each only after a one-at-a-time ablation on your own tasks.
- Items Anthropic still supports with evidence: a planner that sets scope, an independent evaluator for work near the builder's ceiling, file-based state with git, end-to-end tests against the running product, grounding progress claims in tool output, effort chosen by measurement.

### Gaps
- Skills/skill-creator guidance, auto mode post, Claude Code quality postmortem (2026-04-23), Managed Agents multi-brain details not read. No talk transcripts reviewed.
