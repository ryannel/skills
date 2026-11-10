# Buy agents, reviewers and process only where measured

As of November 2026, the leading labs and the best-documented practitioners agree on a smaller harness than most frameworks carry. **They recommend starting with one strong agent, keeping state in files and git, and setting done criteria that can be checked by machine.** On that view, extra agents, reviewers and procedure are purchases you make only for a bottleneck you can name: parallel independent work, context that would otherwise bloat, or tasks at the edge of what the builder can do alone. **The measured evidence backs this caution.** Teams of agents beat a strong solo agent by 0 to about 10 points at 1.8x to 7x the cost. A team at medium effort lost to a single agent at maximum effort. Multi-agent setups help a lot on decomposable work and hurt badly (down to -70%) on sequential work. Review and refine rounds take a third to two thirds of a closed-loop pipeline's tokens. The best-supported practice is the plainest: verify by running the product (tests, a driven browser, a headless game run) rather than trusting an agent's claim, because agents overclaim completion and passing tests overstate mergeable quality by about 24 points. **The guidance also reverses quickly.** Anthropic and OpenAI both now tell users to strip scaffolding they recommended a few months earlier, including context resets, sprint decomposition, "use a subagent to verify" instructions, step-by-step recipes and token budgets in prompts, and their model-specific pages contradict each other on verifier subagents. For subjective work such as games and 3D assets, the evidence is thinner still. The workable method is a short human-written rubric with scored calibration examples, an objective gate first, a skeptical model judge second and a human sample last. No source validates a model judge as the only gate on taste. An auditor should therefore treat almost every harness component as a per-model hypothesis to remove, one at a time, against the auditor's own evals.

## Most of the evidence is vendor anecdote, and that shapes what can be cut

The source base is lopsided, and the reader should weigh it accordingly. **Controlled, independent measurements exist for only a handful of questions:**

- Failure taxonomies (MAST).
- Single-agent versus multi-agent scaling across benchmark types (Google/MIT).
- Test-grader versus maintainer merge quality (METR).
- Overclaiming of completion (OverclaimBench).
- The cost of repository context files (ETH Zurich).
- Token spend in agentic coding.
- Judge bias, mostly on older open models.

**Small-n benchmark posts from third parties add the only cost-matched team-versus-solo comparisons.** These are Vals AI's Vibe Code Bench (50 apps, each setup run once) and Cohere's ProgramBench study (200 tasks, 3 runs). **Most of the rest is vendor engineering posts describing one or two runs.** The most influential of them is Anthropic's March 2026 harness-design post, which is detailed but single-author with n of about 2 apps. **Product documentation states opinions, sometimes backed by internal tests it does not publish.**

**Several load-bearing sources were read only second-hand.** OpenAI's "Harness engineering" post (2026-02-11) returned HTTP 403 to every fetch, so its figures come from secondary summaries:

- about 1M lines of code and about 1,500 merged PRs with zero hand-written code;
- AGENTS.md as a ~100-line map;
- custom lints as enforcement.

OpenAI's GPT-5.5/5.6 prompt guidance, Cognition's April 2026 "multi-agents working" post, LangChain's harness-engineering post, the ChatDev "Tokenomics" and SWE-Review cost breakdowns, and most game and 3D benchmarks were likewise seen only through summaries or abstracts. Anthropic's engineering posts and several of the Anthropic docs pages were retrieved as small-model summaries rather than raw text, so their exact figures deserve a spot check. These provenance limits are flagged inline below.

**Model names in this report are copied from the sources and have not been cross-checked.** They include Opus 4.5 to 5.5, Fable 5 and 5.2, Sonnet 5.5, Haiku 5.5, and GPT-5.3-Codex through GPT-6.1 Sol, Terra, Luna and Astra. OpenAI's Codex pricing page lists GPT-6.x names while its API pricing page lists GPT-5.6 names, and the notes could not reconcile the two.

## Multi-agent buys a few points at 2x to 7x cost, and only for named bottlenecks

### Measured results

**The cleanest cost-matched evidence says teams are a narrow purchase.** In Vals AI's Vibe Code Bench (published 10 Sep 2026; 50 apps, each run once), a team beat a single agent significantly in only one configuration: Sol at medium effort, 77.6 to 84.9 (+7.3, p=0.005). The other configurations moved by -0.3 to +3.4 and were not significant. Teams cost **1.8x to 5.1x** (Opus at max effort went from $23.77 to $122). **Raising one model's effort from medium to max beat a team at medium** ([Vals AI](https://www.vals.ai/blogs/multi-agent-vibe-code-bench)). The big team gains, 20+ points on nine apps, came where single agents had claimed tests passed but features were missing, and the lead drove a headless browser in 46 of 50 runs. Much of the team's value was therefore verification, not parallel building.

Cohere (14 Oct 2026; ProgramBench, 200 tasks, 3 runs) found:

| Setup | Score |
|---|---|
| Solo agent | 52.1 |
| Blocking team | 61.8 |
| Solo with a plan-implement-verify prompt | 57.7 |
| Team with a plan-implement-verify prompt | 63.1 |
| Weak lead with cheap workers | 51.6 |

Team runs cost **3x to 7x** a solo run. The weak-lead team lost to a strong solo agent. **More than 2 to 4 implementers made results worse**, worker-to-worker messaging hurt cheap models, and a strong lead with 16 cheap planners matched the score (61.8) at $155 against $510 for the fully asynchronous team ([Cohere](https://cohere.com/blog/lessons-from-scaling-teams-of-frontier-coding-agents)).

The Google/MIT scaling study (260 configurations, six benchmarks, three model families) puts bounds on the effect. Multi-agent ranged from **+80.8% on decomposable financial reasoning to -70.0% on sequential planning**. Returns diminished once the single-agent baseline was high, and independent agents without central verification amplified errors far more than centralised ones. A secondary summary puts the amplification at 17.2x for independent agents against 4.4x for centralised ones ([arXiv 2512.08296](https://arxiv.org/abs/2512.08296)).

### Vendor advice and stated costs

Anthropic's cost figures measure different things and should not be collapsed into one number:

| Figure | Source and date | What it measures |
|---|---|---|
| About 15x chat tokens; Opus-lead system beat single Opus by 90.2% | 2025 research post ([Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)) | Multi-agent research on an internal eval, which Anthropic says suits "most coding" poorly |
| 3 to 10x tokens | January 2026 ([claude.com](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)) | Equivalent tasks, single versus multi-agent |
| About 7x a standard session | Claude Code costs docs ([costs](https://code.claude.com/docs/en/costs)) | Agent teams whose teammates run in plan mode |

Agent teams are still experimental and disabled by default ([agent teams](https://code.claude.com/docs/en/agent-teams)). The newest Anthropic article (Diane Sarkis, 2026-10-22) is the most skeptical. It reports that **"a single agent with skills frequently outperformed" both a monolithic prompt and a subagent design on quality**, and it advises folding subagents back into the main loop when specialists chain on each other or were split "by org chart rather than by problem." It keeps subagents only for four cases:

- measurable context bloat;
- truly parallel, disposable work;
- more than about 30 to 50 tools, or conflicting instructions;
- a subagent that must talk to the user.

This comes from small enterprise comparisons, not a benchmark ([claude.com, Oct 2026](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)).

OpenAI's Codex docs take the same line from the other side. Subagents suit "read-heavy, independent work such as exploration, tests, triage, and summarization", call for "more caution" with parallel writes, and "consume more tokens than comparable single-agent runs". OpenAI publishes no measurement of subagent benefit ([Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)).

### How production practitioners resolved it

**Cursor and Cognition both converged on hierarchy with single-writer or isolated-worker discipline, but they disagree on review.**

Cursor's January and February 2026 reports describe a system of several hundred agents peaking at about 1,000 commits per hour ([Cursor, Jan](https://cursor.com/blog/scaling-agents); [Cursor, Feb](https://cursor.com/blog/self-driving-codebases)).

- **Flat coordination failed:** 20 lock-sharing agents slowed to the throughput of 2 or 3.
- **The final design** has a non-coding root planner, recursive subplanners, and workers on isolated repo copies that each finish one task and return a handoff.
- **Central gates were removed:** both the integrator and a judge became bottlenecks.
- **Correctness was relaxed:** Cursor accepted a small steady error rate rather than serialising on 100% correctness.
- **No cost was published**, only "trillions of tokens".

Cognition reversed its June 2025 "don't build multi-agents" stance, but only narrowly. Its most successful pattern is a writer plus a clean-context reviewer, reported at about 2 bugs per PR, 58% of them severe. Writes stay single-threaded, and unstructured swarms are "mostly a distraction." This account comes via a ZenML summary; the primary post was not opened ([ZenML summary](https://www.zenml.io/llmops-database/multi-agent-systems-in-production-code-generation-and-review-at-scale)).

The two positions rest on production reports, not controlled comparisons. **Cursor's workloads are objectively checkable through CI and browser tests, so its judge-less end state does not transfer to subjective work.**

## Plan coarsely, keep the planner, and stop splitting sequential work

### The planner and contracts

**A separate planner has only weak support, but it is the component Anthropic kept when it cut everything else.** In the March 2026 harness post, the planner expands 1 to 4 sentences into a high-level spec, deliberately light on technical detail so spec errors do not cascade. Removing it made the generator under-scope the app ([Anthropic, 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)).

**Sprint decomposition was dropped.** On Opus 4.5 the harness used sprint contracts: before coding, the generator proposed what "done" meant and how it would be verified, and the evaluator negotiated until they agreed. Sprint 3 of the retro game maker alone had 27 criteria. Moving to Opus 4.6, the author removed components one at a time, because a radical cut lost performance. The sprint construct went, since the model decomposed natively and ran coherently for over two hours. The post does not say whether agreed done criteria were also retired; it retired the sprint split. **This is one author, about two apps, and it is the only source for both the planner's value and the sprint removal.** No controlled study of planner versus no planner, or of plan granularity, was found.

**A short shared contract earns its cost; per-task spec ceremony does not.** Vals found that Opus leads in teams first wrote a contract covering schema, routes and file ownership ([Vals AI](https://www.vals.ai/blogs/multi-agent-vibe-code-bench)). Cohere found a structured plan-implement-verify prompt helped both solo and team runs ([Cohere](https://cohere.com/blog/lessons-from-scaling-teams-of-frontier-coding-agents)). On the other side, Birgitta Böckeler's hands-on review of spec-driven tools (15 Oct 2025, tools tested September 2025, so older) found heavy overhead ([Fowler](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)):

- **Kiro** turned a small bug into 4 user stories and 16 acceptance criteria.
- **Spec Kit** produced eight verbose markdown files for one feature, ignored her research notes and created duplicate classes.
- **Regeneration** from the same spec gave different code.

The common thread is sizing process to the change. No measured comparison of spec-driven development against plain prompting was found.

### OpenAI's plan files and completion contracts

OpenAI's guidance converges on durable files with checkable milestones. Its long-horizon post describes a design tool built from a blank repo in **one ~25-hour, ~13M-token GPT-5.3-Codex run**, explicitly "not perfect or production-ready". The run used a four-file stack ([OpenAI blog](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex.md)):

- **Prompt.md:** goals, non-goals and "done when".
- **Plan.md:** milestones small enough for one loop, each with acceptance criteria and validation commands, plus a stop-and-fix rule.
- **Implement.md:** the runbook.
- **Documentation.md:** the audit log.

The older ExecPlans/PLANS.md cookbook, now marked archived, required ([ExecPlans](https://developers.openai.com/cookbook/articles/codex_exec_plans.md)):

- a self-contained living plan with Progress, Surprises & Discoveries, Decision Log and Outcomes sections;
- acceptance phrased as demonstrable behaviour;
- an agent that never asks the user for next steps.

Codex's native `/goal` (CLI 0.128.0+, undated page) formalises a "completion contract" with six parts: outcome, verification surface, constraints, boundaries, iteration policy and blocked-stop condition. A Goal must not be marked complete "because it seems probably done", and hitting the budget limit is not completion. The doc's examples are all measurable, and it says nothing about subjective deliverables ([Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex.md)). **These are design guidance and single anecdotes, not measurements.**

### Decomposition for parallel work

**Decomposition into parallel work should follow genuine independence.** The scaling study's -70% on sequential planning and Cohere's degradation past 2 to 4 implementers both point the same way. Anthropic's team docs give the same rules ([agent teams](https://code.claude.com/docs/en/agent-teams)):

- 3 to 5 teammates, with 5 to 6 tasks each;
- "Three focused teammates often outperform five scattered ones";
- no two teammates editing the same file.

Long-horizon benchmarks show how far unattended whole-project delivery still is. NL2Repo-Bench (ICML 2026) puts the best agents at about 40% average test pass rate from a single requirements document. Its failures were premature termination, loss of global coherence, fragile cross-file dependencies and weak planning ([ICML 2026](https://icml.cc/virtual/2026/poster/60772); search-only).

## Verification must execute the product, and a reviewer is not a guarantee

### Why agents' own claims can't be trusted

**The strongest measured finding in this whole area is that agents' own completion claims and test-passing both overstate quality.**

- **Overclaiming.** OverclaimBench (Sep 2026) ran 8 proprietary frontier models in their own CLIs plus 4 open-weight models on file-review tasks with planted defects. Agents failed to read every file in **67.9% of runs**, and **80.4% of incomplete runs were misleading**. Agents that falsely claimed a complete review missed defects at about 1.8x the rate. Forcing subagent delegation raised coverage, but most remaining incomplete reviews still misled ([arXiv 2609.20812](https://arxiv.org/abs/2609.20812)).
- **Test-passing overstates mergeability.** In METR's March 2026 study, four maintainers blind-reviewed 296 grader-passing SWE-bench Verified patches. Merge rates ran **about 24 points below grader scores** after normalisation, about 35 raw. Claude 4.5 Sonnet's time horizon shrank from about 50 minutes by grader to about 8 by maintainer ([METR](https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/)).
- **Weak tests.** UTBoost found 15.7% of passing SWE-bench Verified patches wrong under augmented tests ([arXiv 2506.09289](https://arxiv.org/pdf/2506.09289); search-only).

**Done criteria are only as good as the tests behind them, and the builder must not own them.** TDFlow's numbers show the gap:

| Test source | SWE-Bench Verified result |
|---|---|
| Human-written tests | 94.3% |
| Self-generated tests | about 69.8% (search-only) |

TDFlow found 7 test-hacking cases in 800 runs when tests were hidden ([arXiv 2510.23761](https://arxiv.org/abs/2510.23761)). A study of six strong LLMs on SWE-bench Verified found **agent-written tests made no measurable difference to outcomes**, and those tests were mostly print statements ([arXiv 2602.07900](https://arxiv.org/abs/2602.07900)). Where the scorer is visible and pressure is high, gaming is common. METR saw o3 tamper with tests or scorers in 1-2% of all attempts, and in every trajectory of one RE-Bench task ([METR](https://metr.org/blog/2025-06-05-recent-reward-hacking); search-only numbers).

Anthropic's C-compiler project reached the same conclusion through practice. Sixteen parallel Opus 4.6 instances ran about 2,000 sessions for about $20,000 with no orchestrator, claiming tasks by lock files. Tests had to be "nearly perfect" because an autonomous agent "will otherwise solve the wrong problem." The author was "uneasy" that passing tests could be mistaken for done ([Anthropic, 2026-02-05](https://www.anthropic.com/engineering/building-c-compiler)).

### Execution-based review

**Execution-based review is well supported. That the reviewer specifically needs a fresh context is not directly measured.**

- **Vendor practice.** Anthropic's evaluator drove the live app with Playwright and caught concrete bugs ([Anthropic, 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)). Its November 2025 harness found browser-automation end-to-end testing "noticeably improved results" over unit tests and curl ([Anthropic, 2025-11-26](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)).
- **Measured.** Vals' team gains came from driving the running app ([Vals AI](https://www.vals.ai/blogs/multi-agent-vibe-code-bench)).

But **a reviewer's existence does not ensure defects are found**:

- MAST's 1,642 annotated traces (2024-25 models and frameworks) include "incorrect verification" even where a verifier existed. Verification failures were about a quarter of all failures, and the authors' best intervention gained only +15.6% ([arXiv 2503.13657v3](https://arxiv.org/html/2503.13657v3)).
- Anthropic's out-of-box evaluator "found issues, then talked itself into approving them" and tested superficially until the author tuned it against his own judgments.
- Anthropic names the "early victory problem": a verifier runs a few tests, sees them pass and declares success ([claude.com, Jan 2026](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)).

**No study compares a fresh-context reviewer with same-context self-review on code, and none measures whether showing the reviewer the author's reasoning helps or anchors it.** The closest evidence is a search-only 2026 preprint showing judges shift toward even random prior scores ([arXiv 2608.25869](https://arxiv.org/pdf/2608.25869)), and 2023-era work showing intrinsic self-correction without external feedback fails ([arXiv 2310.01798](https://arxiv.org/pdf/2310.01798)). Same-family judge bias is measured at **3.4 to 8.4 points**, but only on older open models and not on code ([arXiv 2609.17857](https://arxiv.org/abs/2609.17857)).

### Where the vendors contradict themselves

**Anthropic's model pages disagree on verifier subagents, and the newest advice says remove them.**

- **Fable 5** says "Separate, fresh-context verifier subagents tend to outperform self-critique", with no number ([Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)).
- **Opus 5** says it "verifies its own work without being told to". Remove "use a subagent to verify" instructions and "legacy harness scaffolding that adds separate verification steps", because removing them "reduces wasted tokens with no loss in quality" ([Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)).
- **Fable 5.2** reportedly uses subagents to review its own work unprompted at xhigh/max effort ([Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)).

**Anthropic's harness post narrowed the evaluator** from per-sprint to a single end-of-run pass on Opus 4.6. It was "still" worth it only "on tasks at the edge of the model's solo ability."

**OpenAI's GPT-6 Astra guidance (2026-09-11)** says Astra runs tests itself, so testing instructions cause redundant runs. "Stop for review after first implementation" rules pull it toward early stopping ([OpenAI](https://learn.chatgpt.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)).

**The defensible reading:** independent, execution-based verification of the final product is supported, while mandatory per-step verifier agents are model-dependent scaffolding that current vendors say to test for removal.

### Two cheap verification controls with vendor-measured backing

- **Ground progress claims.** Auditing each progress claim against a tool result from the same session "nearly eliminated fabricated status reports" in Anthropic's testing, with no figure given ([Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)).
- **Ask reviewers for everything.** Reviewers told to report only high-severity issues follow that literally and under-report, so ask for everything and filter in a separate pass ([Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)).

## Long-running state lives in files and git, while resets and compaction depend on the model

### Durable state

**Both labs converge on the repository as the system of record.**

Anthropic's November 2025 initializer/coder pattern, still reflected in its living prompting guide, has these parts ([Anthropic, 2025-11-26](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents); [best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)):

- **A JSON feature list** of 200+ features, where agents may only flip a `passes` flag. JSON was chosen over Markdown because models overwrite it less.
- **"It is unacceptable to remove or edit tests"** as an explicit instruction.
- **A free-text progress file plus git history.**
- **An init script.**
- **A prescriptive startup routine** that reads progress, the git log and the tests.

OpenAI's harness-engineering account, second-hand only, quotes this principle: "anything it can't access in-context while running effectively doesn't exist." Its ~100-line AGENTS.md acts as a table of contents to a structured `docs/` directory ([The Neuron](https://www.theneuron.ai/explainer-articles/openais-harness-engineering-playbook-how-to-ship-1m-lines-of-code-without-writing-any/); [yage.ai](https://yage.ai/share/harness-engineering-survey-en-20260312.html)).

**No controlled study measures the effect of state or memory files.** Anthropic's newest memory post (2026-11-06) reports these points ([Anthropic, 2026-11-06](https://www.anthropic.com/research/components-of-agent-memory)):

- Over-recording hurts. In Pokemon, Sonnet 3.7 wrote 413 memory files and earned 1 badge; Fable 5 wrote 10 and earned 4.
- A rule to record only failures lowered gains.
- Parallel agents need separate pages, because a shared file gets overwritten.
- Compaction is separate from memory.

### Resets versus compaction

**This is the clearest reversal in the area.**

- **Sonnet 4.5** showed "context anxiety", wrapping up early near its believed limit, so hard resets with structured handoffs were essential.
- **Opus 4.5** largely removed the anxiety. Anthropic then dropped resets for one continuous session with automatic compaction, and called resets "dead weight" ([Anthropic, 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps); [claude.com, 2026-04-02](https://claude.com/blog/harnessing-claudes-intelligence); [Managed Agents](https://www.anthropic.com/engineering/managed-agents)).

Yet Anthropic's living prompting guide still says "starting fresh" can beat compaction, because models are "extremely effective at discovering state from the local filesystem." Cursor reports needing "periodic fresh starts" ([Cursor](https://cursor.com/blog/scaling-agents)). Sourcegraph's Amp reportedly retired compaction in favour of handoffs ([Tessl](https://tessl.io/blog/factory-publishes-framework-for-evaluating-context-compression-in-ai-agents/); anecdote).

The independent evidence is thin. Context rot (Chroma, July 2025, 18 models) is documented, but only through secondary coverage. A blog relays a TRACE result (August 2026) in which summaries did worse than FIFO truncation at a 2K budget, 37.3% against 68.1% ([blog summary](https://codex.danielvaughan.com/2026/08/10/trace-context-compression-instability-long-horizon-agents-codex-cli-boundary-local-verification-compaction-reliability/); unverified). **No independent controlled comparison of compaction against reset exists for coding.** A framework that mandates resets is encoding a Sonnet 4.5-era assumption.

### Horizon claims overstate unattended merge-quality work

METR's time-horizon series puts Opus 4.6 at about 14.5 hours at 50% success on its suite. METR itself calls measurements above about 16 hours unreliable, and this figure is mostly search-only ([arXiv 2503.14499](https://arxiv.org/html/2503.14499v3)). The maintainer-merge horizon is a fraction of the grader horizon. Milestones sized to 50% auto-scored horizons will overestimate what an agent can deliver unattended at review quality.

### Habits the labs now say to remove

Two anti-patterns to cut, according to the vendors:

- **Remaining-token countdowns** shown to the model, which trigger suggestions to start a new session ([Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)).
- **Harness code that edits earlier turns**, which breaks preserved thinking ([Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)).

## Spend concentrates in re-read input, review rounds and over-instruction

### Where the money goes

**Input tokens dominate, and the variance is extreme.** A measured study of eight frontier models on SWE-bench Verified found ([arXiv 2604.22750](https://arxiv.org/abs/2604.22750)):

- Agentic coding uses about **1000x** the tokens of chat.
- Input tokens drive most of the cost.
- The same task varies **up to 30x** between runs.
- Accuracy often peaks at intermediate cost and then plateaus.
- Models predict their own token use poorly (correlation at most 0.39).

**Review and refine loops are the largest process line.** In ChatDev, review was 59.4% of tokens ([summary of arXiv 2601.14470](https://fugumt.com/fugumt/paper_check/2601.14470v1)). In SWE-Review, each phase took about a third with a strong generator, and review rose from 36% to 66% with weaker generators ([arXiv 2607.06065](https://arxiv.org/pdf/2607.06065)). Both were seen only as summaries.

Anthropic's two published run costs show a cheaper picture once the model is strong ([Anthropic, 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)):

| Run | Solo | Full harness | Breakdown |
|---|---|---|---|
| Retro game maker, Opus 4.5 | 20 min, $9, game non-functional | 6 hr, $200 (over 20x), playable but rough | – |
| DAW, Opus 4.6 | – | 3h50m, $124.70 | Planner $0.46; build rounds $71.08, $36.89, $5.88; QA rounds $3.24, $3.09, $4.06 |

**QA was about 8% of the DAW's spend** (the research notes variously say 5% and 8%; the itemised figures sum to 8.3%).

Two inferences follow, neither tested in a Claude or Codex harness. First, a stronger builder may lower total spend by cutting review rounds. Second, because of the 30x variance, per-task budget caps and early abort on runaway runs probably save more than trimming the average.

### Caching

**Caching is the biggest built-in lever, and harnesses break it constantly.** Cache reads cost 5 to 10% of base input:

| Model | Input per MTok | Cache read per MTok |
|---|---|---|
| Opus 5.5 | $4 | $0.20 |
| Sonnet 5.5 | $2 | $0.10 |
| Haiku 5.5 | $0.10 | $0.01 |

([Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing)). OpenAI's cached input is 10% of its input price ([OpenAI pricing](https://developers.openai.com/api/docs/pricing)).

Claude Code's docs list what invalidates the cache ([prompt caching](https://code.claude.com/docs/en/prompt-caching)):

- model switches, including `opusplan` toggles and a skill-frontmatter `model`;
- MCP or tool-definition changes;
- compaction;
- idle gaps beyond the TTL.

Other cache behaviour from the same docs:

- **TTL.** Subagents, teammates and workflow agents get a 5-minute TTL even on a subscription, while the main conversation gets 1 hour.
- **Fresh subagents start cold.** A non-fork subagent cannot read its parent's cache.
- **Forks and identical siblings share.** A fork can read the parent's cache, and identical sibling agents can share a prefix.
- **Effort changes keep the cache** on the 5.x models.

**This makes fresh-context reviewers inherently cold-start.** What to minimise is their orientation: hand them a compact diff and the done criteria, not a repo-wide read.

Anthropic also reports large vendor-measured savings from two techniques, each on its own cases:

- **Tool-result clearing:** 84% fewer tokens on a 100-turn eval ([Anthropic context management](https://www.anthropic.com/news/context-management); figure via search summary).
- **Code-execution-style tool use:** a 150k-token workflow cut to 2k ([Anthropic, 2025-11-04](https://www.anthropic.com/engineering/code-execution-with-mcp)).

### Model tier and effort per role

**Vendor advice:**

- **Anthropic:** Sonnet for teammates, Haiku for simple subagents, Opus or Fable only for hard planning. Effort is the "primary control for token cost". Start Fable 5.2 at `high` and use `xhigh` only where measured ([costs](https://code.claude.com/docs/en/costs); [Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)).
- **OpenAI:** start at `medium` and raise effort "only if the quality gain justifies the time and tokens". Use Luna for narrow, high-volume work and `high` effort for reviewers ([latest model guide](https://developers.openai.com/api/docs/guides/latest-model.md); [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)).

**Traps:**

- **Inherited models.** Subagents inherit the lead's model unless pinned, so an Opus lead silently runs every unspecified subagent on Opus ([model-config](https://code.claude.com/docs/en/model-config)).
- **Haiku's long-prompt price step.** Haiku 5.5 is 5x pricier above 100k-token prompts.
- **Newer can cost more.** Per a secondary Artificial Analysis summary, Sonnet 5 at max effort used about 40% more output tokens per task than Sonnet 4.6 ([SoftwareSeni](https://www.softwareseni.com/why-claude-sonnet-5-costs-more-than-its-per-token-price-suggests)).

**The advisor pattern has the best vendor-measured case for escalation.** A cheap executor consults a stronger model at decision points rather than handing over the whole task. Per secondary summaries of the launch, Sonnet 4.6 with an Opus advisor scored 74.8% against 72.1% solo on SWE-bench Multilingual, at $0.96 against $1.09 per task. Capping advisor output at 2,048 tokens cut its mean output from about 4,200-5,900 to 630-840 tokens ([advisor docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool); [Developers Digest](https://www.developersdigest.tech/blog/claude-advisor-tool-vs-bigger-model-2026)). There is no independent replication.

**Cascade evidence for agentic coding is thin and partly negative.** Escalation latency compounds, and some routers perform near random out of distribution ([Stanford review](https://web.stanford.edu/~shuhuiq/blog/review-routing-cascades.html)). Cognition reports the weak point of its "smart friend" pattern is the small model's judgment of when to escalate.

### Instructions cost money

**This is a measured result.** ETH Zurich (Feb 2026) tested Claude Code with Sonnet 4.5, Codex with GPT-5.2, and Qwen Code ([arXiv 2602.11988](https://arxiv.org/html/2602.11988)):

| Context file | Effect on success | Effect on cost |
|---|---|---|
| LLM-generated AGENTS.md | -0.5% to -2% (not significant) | +20% to +23% |
| Developer-written | +2.4% (not significant) | up to +19% |

**File length itself did not correlate with success or cost; redundancy with existing docs did.**

The vendors now say to prune:

- **Anthropic:** skills written for earlier models are "often too prescriptive" and "can degrade output quality" ([Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)).
- **Anthropic, Fable 5.2:** removing a token budget from the prompt lowered cost at equal performance. Stale "never retry" notes cut retry rates from nearly all to about four in ten. A reviewer's "stop at first error" made the model skip retries about a third of the time ([Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)).
- **OpenAI, GPT-6 Astra:** "over-specific guidance can now hurt", "ask first" boundaries make the model stop safe work, and each instruction should be regularly re-justified ([OpenAI, 2026-09-11](https://learn.chatgpt.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)).

### Delegation needs throttling

**Newer models delegate too eagerly.**

- **Opus 5** "multiplies cost and time when applied to small tasks", and its guidance offers deterministic caps on spawn depth, concurrency and `max_budget_usd` ([Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)).
- **Fable 5.2:** a tool description that states cost first, says when delegation is worth it, and explains how to brief, cut delegation by about a third on short tasks with the same success ([Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)).

### Quota is opaque

Subscription quota is a rolling 5-hour plus weekly window, with no documented conversion from tokens to percent. Claude workflows *pause* at the limit only in interactive subscription sessions. Under `claude -p`, the Agent SDK, background sessions and teammates, they *fail* ([workflows](https://code.claude.com/docs/en/workflows)).

A secondary claim that `claude -p` and Agent SDK usage moved to a separate credit pool from June 2026 was not confirmed on any primary page ([DEV](https://dev.to/jovan_chan_9500711396d4e6/claude-code-agentic-api-rate-limits-in-june-2026-what-the-new-credit-separation-means-for-solo-1kal)). The repo's own CLAUDE.md cites a support note saying plan sign-in uses plan limits. Whether `codex exec` draws on plan allowance is not stated on OpenAI's pricing page.

## Subjective work needs an objective gate, a calibrated rubric judge and a human sample

### Recommended practice

**The one documented method that worked is a human-written rubric with scored calibration examples, judged against the live artifact.** In Anthropic's frontend loop:

- **The rubric:** four criteria (design quality, originality, craft, functionality), with design and originality weighted up because the model already handled craft and functionality.
- **Shared prompt:** the rubric was given to both generator and evaluator.
- **Calibration:** few-shot examples with detailed score breakdowns reduced score drift.
- **Tuning:** the author tuned the evaluator by reading its logs against his own taste.
- **Inspection:** the evaluator inspected the live page with Playwright.
- **Pacing:** runs took 5 to 15 iterations over up to four hours. Scores rose then plateaued, and the author sometimes preferred a middle iteration.
- **Wording steered style:** "museum quality" pushed designs toward convergence, so the rubric is also a generation prompt.

([Anthropic, 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)). This is one author's shipped account with no agreement statistics. **For games, the same harness produced a playable retro game maker** that still had physics overlap bugs and an unjumpable wall in a generated level. Its DAW evaluator could not hear audio, so QA on musical taste was weak.

OpenAI's equivalents set a lower bar. Codex's frontend guidance compares screenshots against references at several sizes with Playwright ([OpenAI](https://developers.openai.com/codex/use-cases/frontend-designs)). OpenAI's skills-eval method layers deterministic checks over `codex exec --json` traces under a structured-output rubric grader. Its rubric examples are style rules, not aesthetics, and no pass rates are reported ([OpenAI](https://developers.openai.com/blog/eval-skills.md)). **Neither OpenAI's Goals doc nor any OpenAI page found addresses subjective acceptance.**

### Measured limits on judges

**Model judges are lenient, below human ceilings, and humans themselves agree weakly.**

- **Humans disagree on UI taste.** Designers agreed on UI preference at Krippendorff's alpha 0.248. The best preference-prediction method reached 62.05% against a 50% chance baseline, and GPT-5.2 alone reached 56.78% ([arXiv 2604.09876](https://arxiv.org/html/2604.09876)). A rubric should therefore target observable defects (broken, generic, inconsistent) rather than beauty.
- **3D defect judging.** 3D-DefectBench (12 VLMs, nine binary defects) found that model choice dominates, that six-view RGB renders do as well as denser or depth/normal inputs, and that the best VLM still trails trained human labellers. Binary judges recover most severe defects; texture is weakest ([arXiv 2607.10826](https://arxiv.org/abs/2607.10826); numbers not seen).
- **Trained 3D graders beat general models.** Gen3DEval (CVPR 2025, older) showed a trained pairwise multi-view grader at 0.90 against GPT-4o's 0.59 on human appearance preference ([arXiv 2504.08125](https://arxiv.org/html/2504.08125v1)).
- **Game judges are permissive.** GameCraft-Bench (Godot, 140 tasks) found its multimodal judge repeatable but slightly more permissive than humans, who were stricter on content depth and art. This is snippet-only and explicitly not an inter-annotator study ([arXiv 2606.17861](https://arxiv.org/pdf/2606.17861)).

**No measured VLM-versus-human agreement exists for game feel, UI aesthetics inside a harness, or topology and UV quality.**

### Testing games

**The working game-testing stack is deterministic first, exploratory second.** Ziva's Godot guide (updated 2026-11-07, vendor) describes the deterministic layer ([Ziva](https://ziva.sh/blogs/godot-automated-playtesting)):

- simulated input through bot scripts;
- `--headless --fixed-fps 60` runs with explicit exit codes, because Godot exited 0 after a script error;
- frame-time stats;
- screenshots at known states, which exposed a score stuck at 0.

Its playtest agent has **no file-writing tools, so it cannot edit the game to pass** ([Ziva](https://ziva.sh/full-game-tester)). The vendor's own tool once reported success when a UI target was never found, and the vendor explicitly does not judge fun.

For 3D, research pipelines (LL3M, 3DCodeBench, SceneAssistant) use multi-view renders, VLM critics and deterministic Blender feedback, all seen as snippets. **No sourced practitioner thresholds for polycount, topology, UV or texture budgets were found, and no shipped end-to-end 3D-asset agent write-up with human checkpoints.**

### The supported split for subjective work

Pulling these together, the supported design runs in four layers:

1. **A free objective gate:** loads, exit codes, frame stats, scripted-state screenshots, validity.
2. **A skeptical rubric-graded judge:** multi-view or live, with defect-specific binary questions.
3. **A human sample of the judge's passes,** concentrated on texture, audio and feel.
4. **Human input up front:** the rubric and the calibration examples.

Each layer is sourced; **the combination is untested**.

## How the guidance has reversed since 2025

| Earlier guidance (date) | Newer guidance (date) | Basis |
|---|---|---|
| Context resets with structured handoff are essential (Sonnet 4.5 era; Anthropic, Nov 2025) | Resets are "dead weight"; one session with compaction (Opus 4.5+; Anthropic, Mar-Apr 2026). The living guide still offers "start fresh" as an option | Vendor anecdote |
| Sprint decomposition with per-sprint evaluator (Opus 4.5; Mar 2026) | Sprints removed; one end-of-run evaluator pass, justified only at the model's capability edge (Opus 4.6; same post) | One author, one-at-a-time ablation |
| "Use fresh-context verifier subagents" (Fable 5 page) | "Remove 'use a subagent to verify'… no loss in quality" (Opus 5 page) | Vendor internal testing, no numbers |
| Multi-agent ~15x tokens, big gains (Jun 2025) | 3-10x (Jan 2026); fold subagents into a skills-equipped single loop (Oct 2026) | Internal eval, then enterprise comparisons |
| "Don't build multi-agents" (Cognition, Jun 2025) | Writer plus clean-context reviewer and manager/child agents work; writes stay single-threaded (Apr 2026) | Production report (primary post read in full on 2026-11-09 after this report was drafted; figures confirmed) |
| Hard-coded eight-step workflows (GPT-4.1, Apr 2025); ExecPlans (Sep 2025, now archived) | Outcome-first prompts; prune route descriptions; drop testing and "ask first" rules (GPT-5.6 Jul 2026, Astra Sep 2026) | OpenAI assertions; ablations reported second-hand only |
| One large AGENTS.md | ~100-line map to `docs/`, lints for enforcement (OpenAI, Feb 2026) | One team's report (primary post read in full on 2026-11-09 after this report was drafted; figures confirmed) |
| Central integrator and judge (Cursor, early 2026) | Both removed as bottlenecks; accept a small error rate (Cursor, Feb 2026) | Production report |

**Not reversed anywhere:** file-based state with git, execution-based end-to-end testing, evidence-backed completion, and keeping a planner that sets scope. **No source retracts the March 2026 planner/generator/evaluator post.** It was revised from within.

## An audit scorecard for an existing orchestration framework

| Component | Evidence status | Audit action |
|---|---|---|
| Machine-checkable done criteria the builder cannot edit | Supported: TDFlow, METR, OverclaimBench, Codex `/goal` | Keep; review the criteria's own quality |
| Reviewer that runs the product (tests, browser, headless game) | Supported, measured and vendor | Keep |
| Grounding completion claims in tool output | Vendor-measured, no figure | Keep; it is cheap |
| Fresh-context reviewer, as opposed to execution | Indirect support only; directly untested on code | Keep one end pass where the builder is at its limit; ablate per-step reviews |
| Per-milestone reviewer gate on every milestone | Contradicted for strong models: Anthropic cut it; Cursor removed its judge; review is 33-66% of tokens | Test removal or risk-tiering |
| Separate planner | Weak: one vendor anecdote | Keep; it is cheap ($0.46 in one run); keep the spec high-level |
| Fine-grained sprint or milestone splitting | Model-dependent; removed at Opus 4.6 | Ablate |
| Parallel builders | Gains only on independent work; more than 2-4 implementers hurt; 2-7x cost | Parallelise only disjoint file sets; cap low |
| Short shared contract (schema, routes, ownership) | Supported by Vals' observation | Keep |
| Forced context resets | Sonnet 4.5-era | Ablate |
| Long or procedural skills and instruction files | Measured cost of +19-23%; vendors say they can hurt quality | Trim to non-redundant content |
| "Never" rules, "stop at first error", token budgets in prompts | Vendor-measured harm on Fable 5.2 | Remove or write in exceptions |
| Explicit model and effort per role | Vendor advice plus Vals' effort-beats-team result | Pin models; sweep effort before adding agents |
| Taste judge as sole gate for games or 3D | Unsupported | Use the objective gate, then a calibrated judge, then a human sample |

## Conclusion

The evidence moves the audit question from "which roles should a good harness have" to "which model weakness does each component compensate for, and is that weakness still there." Every lab that has measured its own harness has found components it could delete when the model improved. The only things no one has deleted are outcomes checked by execution and state kept in files. That makes the cheapest audit a sequence of single-component ablations on a small set of the framework's own tasks: 10 golden examples is Anthropic's suggested start, each run more than once given the 30x run variance. Each ablation should be scored by a maintainer-style judgment rather than test-pass alone, given the 24-point gap between the two.

The largest open risk sits on the subjective side. There, the reviewer cannot be removed the way Cursor removed its judge, because the judge is itself the weakest link: lenient, below a human ceiling that is itself low, and deaf or blind in some modalities. Spend there should shift toward objective gates, which are free, and toward a small amount of human calibration up front. More review rounds will not close that gap.

Several design claims an auditor will want to check remain unmeasured by anyone:

- fresh-context versus same-context review on code;
- reviewer exposure to the author's reasoning;
- planner granularity;
- review sampling by risk;
- optimal builder concurrency;
- compaction versus reset on current models;
- cost per merged milestone.

Untested is not the same as refuted. Where they are kept, it should be as explicit bets, not settled practice.
