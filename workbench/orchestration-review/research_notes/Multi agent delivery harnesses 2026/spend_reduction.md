# Reducing spend in autonomous coding-agent harnesses (Claude Code, Codex, comparable hosts), read 2026-11-09

Reading notes: "Primary" = vendor docs/engineering posts fetched on 2026-11-09. "Secondary" = blogs/aggregators surfaced by search only (snippets, not fetched). Measured = the source reports an experiment; Asserted = advice/anecdote without a method. Dates on vendor docs are read-dates; most doc pages carry no publication date. Model names (Fable, Mythos, Opus 5.5, Sonnet 5.5, Haiku 5.5, GPT-5.6/6.x) are as printed on the pages; I did not cross-check them against other sources.

## 1. Where does spend concentrate?

### Takeaway
Input tokens (re-read context on every turn, across every agent) dominate agent cost, not output. Multi-agent fan-out multiplies this (Anthropic: ~15x chat; Claude Code agent teams ~7x). Measured studies put iterative review/refine rounds at 33-66% of a closed-loop pipeline's tokens, and show 30x run-to-run variance on the same task. Idle sessions, scheduled loops, cross-session messages and goal check-ins also spend full-context turns.

### Cited Findings
- Agents use ~4x the tokens of chat; multi-agent systems ~15x. Token usage alone explained 80% of BrowseComp variance (tokens + tool calls + model choice = 95%). Measured on Anthropic's internal research eval, 2025. Early versions overspent (e.g. spawning 50 subagents for a simple query). Also: most coding has fewer parallelisable subtasks than research, and shared-context/dependent domains are a poor fit. — [Anthropic, multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (primary, read 2026-11-09)
- "How Do AI Agents Spend Your Money?" (SWE-bench Verified, 8 frontier models; NeurIPS 2026 listing): agentic coding uses ~1000x the tokens of code reasoning/chat; input tokens drive most cost; same task can differ up to 30x in total tokens between runs; more tokens do not reliably mean higher accuracy (accuracy often peaks at intermediate cost then flattens); models predict their own token use poorly (correlation up to 0.39) and underestimate. Measured. Abstract only; paper did not report cache tokens on the page I read. — [Hugging Face paper page 2604.22750](https://huggingface.co/papers/2604.22750) (abstract level, read 2026-11-09); [NeurIPS listing](https://neurips.cc/virtual/2026/170688)
- ChatDev "Tokenomics" (30 tasks, GPT-5 reasoning model): the iterative Code Review stage was 59.4% of tokens on average; authors conclude cost sits in refinement/verification, not initial generation. Measured, small sample, a different framework from ours. — search-result summary only, [fugumt mirror of arXiv 2601.14470](https://fugumt.com/fugumt/paper_check/2601.14470v1) (secondary; not fetched)
- SWE-Review (closed-loop generate/review/revise on SWE-bench-style issues): with a strong generator each phase is ~1/3 of budget; with weaker generators review share rises 36%->66%. Preprint, measured. — [arXiv 2607.06065](https://arxiv.org/pdf/2607.06065) (search summary only, not fetched)
- Claude Code docs list why long sessions climb: full conversation resent every request (cache-read rate); cache misses after idle beyond TTL; session-scoped scheduled tasks fire while idle sending full context each time; cross-session messages delivered as new turns on idle sessions; goal check-ins on idle sessions (max 3 per goal since v2.1.246, `CLAUDE_CODE_GOAL_CHECKIN_MINUTES=0` disables); every subagent/workflow agent sends its own requests; teammates keep consuming until shut down; `/compact` is itself a large request (most expensive when resuming an old session with a cold cache). Asserted by vendor docs (no numbers). — [Claude Code, Manage costs](https://code.claude.com/docs/en/costs) (primary)
- `/usage` on plan accounts shows attribution of recent usage to skills, subagents, plugins and individual MCP servers, plus loop rows (heaviest `/loop` tasks, tokens per run) and recommendations like "Trim CLAUDE.md · 49k tokens per request". — same page.
- Enterprise averages: ~$13 per developer per active day, $150-250/month, <$30/day for 90% of users (interactive developer use, not unattended multi-agent). — same page (primary).
- Subagent economics, practitioner numbers (anecdotal): one analysis reports a task at 121k tokens direct became 513k fanned to two subagents; a different post says subagents save context not tokens; Agent Teams $150 in 3 hours (single user). — [MindStudio](https://www.mindstudio.ai/blog/claude-code-subagents-cost-tokens), [Hora de Codar](https://horadecodar.com.br/subagentes-claude-code/), [Towards AI](https://pub.towardsai.net/i-burned-150-in-3-hours-using-claude-code-agent-teams-232811baaa24) (secondary, search snippets, unverified)

### Inferences
- For a planner/lead/builders/fresh-context-reviewers design, the likely top three cost lines are (a) every builder and reviewer re-reading its own context each turn, (b) review rounds repeated per milestone (reviewers start cold, so each round pays orientation again), (c) lead context growth if the lead holds builder results in its window. Evidence for (b) is from other frameworks (ChatDev, SWE-Review), not from a Claude/Codex harness like this one.
- The 30x variance means a per-task budget cap and early abort on runaway runs probably saves more than shaving average cost.

### Gaps
- No primary, measured breakdown for a Claude Code/Codex lead+builders+reviewers harness (share by role). Nobody I found published one.
- Idle-polling cost has doc-level description only; no measured share.

## 2. Model tier and effort per role; advisor/escalation/cascades; current lineups, prices, plan limits, headless quota

### Takeaway
Anthropic's own harness advice: Sonnet for teammates, Haiku for simple subagents, Opus/Fable only for hard planning, lower effort for simple work, and the advisor pattern (cheap executor + stronger advisor consulted at decision points) with vendor-reported modest gains (+2.7pp score, -12% cost). Cascades/routing research exists but evidence for agentic coding is thin and partly negative. Prices have fallen steeply for the mid tier; subscription headless/quota treatment is NOT confirmed from a primary page.

### Cited Findings
**Anthropic price list (per MTok: input / 5m write / 1h write / cache read / output), read 2026-11-09, [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) (primary):**
- Fable 5.2 and Mythos 5.2 (limited availability): $8 / $10 / $16 / $0.20 / $40. Fable 5.1 / Mythos 5.1: $10 / 12.50 / 20 / 0.25 / $50.
- Opus 5.5: $4 / $5 / $8 / $0.20 / $20. Opus 5 and Opus 4.5-4.8: $5 / 6.25 / 10 / 0.50 / $25.
- Sonnet 5.5: $2 / $2.50 / $4 / $0.10 / $10. Sonnet 5: $2 / ... / $0.20 / $10. Sonnet 4.6/4.5: $3 / ... / $0.30 / $15.
- Haiku 5.5: $0.10 / $0.125 / $0.20 / $0.01 / $0.50 for prompts <=100k tokens; $0.50 / $0.625 / $1 / $0.05 / $2.50 above 100k (per request, cache tokens count). Haiku 4.5: $1 / $5.
- Batch API 50% off input and output; not available with fast mode. US-only inference geo is a 1.1x multiplier. Fast mode is premium-priced for Fable 5.2, Opus 5.5, Opus 5, Opus 4.8 (multiplier not extracted).
- Cache read is 10% of base input on most models (Opus 5.5: $0.20 vs $4 = 5%; Sonnet 5.5: $0.10 vs $2 = 5%; Haiku 5.5: 10%).

**OpenAI API prices (per MTok: input / cached / output), [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) (primary, read 2026-11-09):** gpt-5.6-sol $4 / $0.40 / $20 (promo pricing through 2026-11-30); gpt-5.6-terra $2 / $0.20 / $12; gpt-5.6-luna $0.20 / $0.02 / $1.20; gpt-5.5 $5 / $0.50 / $30; gpt-5.4 $2.50 / $0.25 / $15; gpt-5.4-mini $0.75 / $4.50; gpt-5.4-nano $0.20 / $1.25; gpt-5.3-codex $1.75 / $0.175 / $14. Batch/Flex 50% of standard; Fast (formerly Priority) 2x (2.5x for gpt-5.5). Cached input is 10% of input.

**Codex subscription (read 2026-11-09, [ChatGPT/Codex pricing page, redirected from developers.openai.com/codex/pricing](https://learn.chatgpt.com/docs/pricing); page undated, extracted via a small model so figures are lightly verified):**
- Plans: Free $0, Go $8, Plus $20, Pro from $100 ($100/$200/$500 tiers), Business $20-25/user, Enterprise. Plus/Standard Business local-message ranges per 5-hour window: GPT-6 Astra 5-45, GPT-6.1 Sol 15-160, GPT-6.1 Terra 35-285, GPT-6 Sol 15-150, GPT-6 Luna 350-3,000. Pro "currently has no five-hour limit"; weekly limits "may also apply" with no numbers.
- Credit rate card (credits per MTok input/cached/output): GPT-6.1 Sol 50/2.5/250; GPT-6.1 Terra 25/1.25/125; GPT-6 Luna 2.5/0.25/12.5; GPT-6 Astra 250/25/1,250; GPT-5.6 Sol 100/10/500. "A typical GPT-5.6 Sol task may use 2-15 credits." Fast = 2.5x included usage (2x purchased credits); Ultrafast 8x.
- Local messages and cloud chats share one allowance; CLI and SDK are listed as plan-included surfaces; API-key sessions bill at API rates. The page does NOT explicitly say `codex exec` draws from the plan allowance. Subagents have no cost notes.
- CONFLICT: the Codex page lists GPT-6.x names while the API page lists GPT-5.6/5.5 names; they may be different product tiers or one page is ahead of the other. Do not treat the two lineups as the same list. A secondary source says GPT-5.5 retires from Codex with ChatGPT sign-in on 2026-10-14 ([CloudZero](https://www.cloudzero.com/blog/openai-codex-pricing/), [uibakery](https://uibakery.io/blog/openai-codex-pricing), secondary); the Codex page itself repeats that date.
- Secondary: on 2026-04-02 OpenAI moved Codex metering from per-message to credits tracking API tokens ([CloudZero](https://www.cloudzero.com/blog/openai-codex-pricing/), secondary, unverified).

**Claude plans and headless:**
- Claude Code usage on Team/Enterprise draws a per-seat allowance on a rolling 5-hour window plus a weekly window, shared with chat and Cowork; "hit your session/weekly limit" is shared across models, but a model-specific "Opus limit" can be escaped by switching family. Usage credits extend past the limit; `/usage-credits`. Claude Code v2.1.234+ can wait and auto-continue after a limit reset. — [Claude Code costs](https://code.claude.com/docs/en/costs) (primary)
- Workflows (dynamic multi-agent scripts) pause rather than fail on a usage limit only in interactive subscription sessions; NOT in `claude -p`, Agent SDK, background sessions or agent-team teammates, where the affected agent fails. Cap: 16 concurrent agents default, 1,000 agents per run; "Large workflow" warning above 25 agents or 1.5M projected tokens. — [Claude Code workflows](https://code.claude.com/docs/en/workflows) (primary)
- `claude --bare -p` does not use subscription login (needs ANTHROPIC_API_KEY); `--bare` is recommended for scripted calls and skips CLAUDE.md, skills, hooks, MCP, auto-memory discovery. `--output-format json` gives `total_cost_usd` (client-side estimate). `--max-budget-usd` caps a run. — [Claude Code headless](https://code.claude.com/docs/en/headless) (primary)
- Secondary and UNVERIFIED: one DEV post says from 2026-06-15 `claude -p`, Agent SDK and GitHub Actions move off the subscription bucket into a separate monthly credit ($20 Pro / $100 Max 5x / $200 Max 20x). I could not find this on a primary Anthropic page. — [DEV Community](https://dev.to/jovan_chan_9500711396d4e6/claude-code-agentic-api-rate-limits-in-june-2026-what-the-new-credit-separation-means-for-solo-1kal) (secondary). Another secondary says 5-hour limits were doubled on 2026-05-06 ([Neowin](https://www.neowin.net/amp/claude-code-gets-throttled-as-anthropic-rolls-out-fresh-usage-caps/) title only; unverified).

**Role guidance from vendors:**
- Claude Code: Sonnet for most coding, Opus for complex architecture/multi-step reasoning, `model: haiku` for simple subagents; subagents inherit the session model by default (switching to Opus before delegating runs the subagents on Opus too); `CLAUDE_CODE_SUBAGENT_MODEL` can force one; agent teams: "Use Sonnet for teammates", keep teams small. — [costs](https://code.claude.com/docs/en/costs), [model-config](https://code.claude.com/docs/en/model-config) (primary)
- Effort: default `medium` on Fable 5.2, Opus 5.5, Sonnet 5.5, Haiku 5.5. Docs say Opus 5.5 at `medium` matches or exceeds Opus 5 at `high` on Anthropic's coding and knowledge-work evals (vendor-asserted, no token figures). `low` = quick reviewed exchanges; `high` = verification matters/edge cases; `max` = unsupervised hard problems with warnings of overthinking and diminishing returns. `effort` can be set in subagent/skill frontmatter. `opusplan` = Opus in plan mode, Sonnet for execution (but each toggle is a model switch = cache miss). — [model-config](https://code.claude.com/docs/en/model-config) (primary; page truncated at 100k chars, advisor section unread)
- Thinking cannot be turned off on Opus 5.5, Sonnet 5.5, Haiku 5.5 or Fable; only effort lowers it. Thinking tokens bill as output. — [costs](https://code.claude.com/docs/en/costs)
- Third-party measurement: Artificial Analysis found Sonnet 5 at max effort used ~40% more output tokens per Intelligence Index task than Sonnet 4.6, i.e. newer models can cost more per task despite per-token price parity. — [Artificial Analysis search summary](https://artificialanalysis.ai/es/articles/claude-sonnet-5-5) and [SoftwareSeni](https://www.softwareseni.com/why-claude-sonnet-5-costs-more-than-its-per-token-price-suggests) (secondary, snippets only)

**Advisor / escalation:**
- Advisor tool (`advisor_20260301`, beta header `advisor-tool-2026-03-01`): executor calls a stronger advisor mid-task inside one request; advisor reads the full transcript, no tools, typical output 400-700 text tokens (1,400-1,800 with thinking); billed at advisor model rates; each advisor call re-reads the whole transcript (not cached in Claude Code; API `caching` option breaks even at roughly 3 advisor calls per conversation). Best practice: call early after orientation and again before finishing; cap with `max_tokens: 2048` (cut mean advisor output from ~4,200-5,900 to 630-840 tokens, ~0% truncation, n=40) and a soft "under 80 words" instruction. Poor fit: single-turn Q&A, tasks where every turn needs the top model. Anthropic-internal tests: Haiku nudge to call the advisor ~+7pp pass rate, but a low-effort executor that stops consulting underperforms; Sonnet at medium effort + Opus advisor matched Sonnet at default effort at lower cost. Measured, vendor-internal, not reproducible. — [Anthropic advisor tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool) (primary; last ~24k chars unread); [Claude Code advisor docs](https://code.claude.com/docs/en/advisor) (primary): experimental, Anthropic API only (not Bedrock/Vertex/Foundry), counts toward plan limits on subscriptions (Fable advisor bills to usage credits on some plans), `/advisor` also works in `-p`; subagents inherit the configured advisor.
- Headline numbers (secondary summaries of Anthropic's launch, vendor-reported): Sonnet 4.6 + Opus advisor on SWE-bench Multilingual 74.8% vs 72.1% solo, $0.96 vs $1.09 per task (-11.9%); Haiku + Opus advisor on BrowseComp 41.2% vs 19.7% solo, at 85% less than Sonnet solo. The 370-task coding set is Anthropic-internal; I found no independent replication. — [BestHub summaries](https://www.besthub.dev/articles/can-opus-sonnet-advisor-cut-costs-while-raising-ai-benchmark-scores-90ad42470c8f), [Developers Digest](https://www.developersdigest.tech/blog/claude-advisor-tool-vs-bigger-model-2026) (secondary); primary blog is linked from docs: [claude.com/blog/the-advisor-strategy](https://claude.com/blog/the-advisor-strategy) (not fetched)
- Multi-agent research system used Opus lead + Sonnet subagents, beating single-agent Opus by 90.2% on its internal eval; also "upgrading to Sonnet 4 gave a larger gain than doubling the token budget on Sonnet 3.7". — [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system) (primary)

**Cascades/routing literature:**
- Survey of dynamic model routing and cascading (Mar 2026). — [arXiv 2603.04445](https://arxiv.org/pdf/2603.04445) (search listing)
- Cascading for code: routing AUC 0.780 on SWE-bench Verified (+15.3 over prompt-only baseline), per a Stanford-hosted review citing Son et al. 2026; SWE-Router reads the cheap model's first turns to decide to continue/escalate; the same review notes cascades can hurt in agentic workloads because escalation latency compounds. — [Stanford review post](https://web.stanford.edu/~shuhuiq/blog/review-routing-cascades.html) (secondary summary)
- Triage (Apr 2026): routes SE tasks to cheaper tiers using code-quality signals. — [arXiv 2604.07494](https://arxiv.org/html/2604.07494) (listing only, results not read)
- A practitioner page cites "CASTER" (ETH) at 40-60% cost reduction with <2% quality loss; I could not confirm it. Do not rely on it.

### Inferences
- Claude-side default for a harness: planner/reviewer-of-design on the top tier at medium-high effort; builders on Sonnet 5.5; mechanical subagents (log filtering, file search) on Haiku 5.5; reviewers need independence more than raw tier, so choice should be by miss-rate on your own seeded defects, which nobody has published.
- Haiku 5.5's long-prompt pricing step (>100k prompt, 5x) means cheap-tier subagents should be kept under 100k context or the saving shrinks.
- Because subagents inherit the lead's model, a lead on Opus silently runs all unspecified subagents/workflow agents on Opus. Pin models explicitly.
- Effort changes keep the cache on the 5.x models, so per-role effort can be changed without a cache penalty; model changes cannot.
- Cascade "cheap first, escalate on failure" evidence for agentic coding is weak; the advisor pattern (escalate for advice, not for the whole task) is better evidenced but only by the vendor.

### Gaps
- Whether `codex exec` and subagents draw from plan allowance on the Codex page; weekly-limit numbers for Codex.
- Primary confirmation (or denial) of the claim that Claude `-p`/Agent SDK usage moved to a separate credit pool.
- Independent replication of advisor-tool gains; the end of the advisor tool doc and model-config page were not read.
- Reconciling GPT-6.x (Codex page) vs GPT-5.6 (API page).

## 3. Caching, context editing, compaction, tool-result trimming, skills, code-execution tool use

### Takeaway
Caching is the largest built-in lever (cache reads are 5-10% of input price) and most harness waste comes from breaking it: model switches, MCP/tool changes, compaction, idle gaps beyond TTL, and subagents that cannot share the parent's prefix. Anthropic reports large savings from tool-result clearing (84% tokens on a 100-turn eval) and code-execution-style tool use (98.7% on one example), both vendor-measured on their own cases.

### Cited Findings
- Claude Code prompt caching mechanics: exact-prefix match; layers are system prompt, project context (CLAUDE.md), conversation. Cache is per model and, on most models, per effort level (effort changes keep the cache on Fable 5.1+, Opus 5.5, Sonnet 5.5, Haiku 5.5). Invalidators: model switch (including `opusplan` toggles and skill frontmatter `model`), fast-mode toggle, MCP/tool definition changes when not deferred, compaction, many images, Claude Code upgrade. Keepers: editing files, CLAUDE.md edits (not applied until restart), permission mode, skills/commands, `/rewind`, plugin skills/agents/hooks. — [Claude Code prompt caching](https://code.claude.com/docs/en/prompt-caching) (primary)
- TTL: main conversation (interactive, `-p`, SDK turns) gets 1 hour only on a Claude subscription within plan usage, otherwise 5 minutes; subagents, workflows, teammates, forks, compaction get 5 minutes by default even on a subscription. `promptCacheTtl`/`subagentPromptCacheTtl` (v2.1.242+), `CLAUDE_CODE_PROMPT_CACHE_TTL`, `ENABLE_PROMPT_CACHING_1H`. 1h writes cost more (Sonnet 5.5: $4 vs $2.50 per MTok). — same page, plus [pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- Subagent cache: a subagent's first request cannot read the parent's cache (different prefix); a fork inherits the parent's exact prefix and does read it; parallel agents in the same directory can read each other's cache; workflow fan-outs hold all but the first agent up to 5s so siblings read the first one's prefix (`CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS`); same model/effort/agent type/tools/schema/cwd required. Cache scope is per machine+directory. — same page and [workflows](https://code.claude.com/docs/en/workflows)
- `/usage` shows `Prompt cache (main)` line: hit share, misses with likely cause, expected rebuilds; covers main conversation only, not subagents (v2.1.251+). Also `usage.cache_creation` in `claude -p --output-format json`. — [costs](https://code.claude.com/docs/en/costs)
- Context management (Anthropic, Sep/Oct 2025): context editing (auto clearing of stale tool calls/results) improved an internal agentic-search eval by 29%; with the memory tool 39%; and in a 100-turn web-search eval cut token consumption 84% while letting runs finish that would otherwise exhaust context. Vendor-internal measured. — [Anthropic, context management](https://www.anthropic.com/news/context-management) (found via search; the page itself not fetched, attribution of 84% is to context editing per Anthropic's page per the search summary; The Decoder attributes it to the combined setup)
- Advisor tool interaction: `clear_thinking` with `keep` other than `all` breaks advisor-side cache (cost only). — [advisor docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)
- Code-execution-style tool use: exposing MCP tools as code APIs, discovering on demand and filtering in a sandbox reduced a 150,000-token workflow to 2,000 tokens (98.7%), Anthropic's own worked example, 2025-11-04; caveat of sandbox/monitoring overhead. — [Anthropic, code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) (primary)
- Tool-result trimming in Claude Code: MCP tool definitions deferred by default (tool search); prefer CLIs (`gh`, `aws`) over MCP; a PreToolUse hook that greps test/log output to failures can cut tens of thousands of tokens to hundreds (vendor-asserted, no measured rate); code-intelligence (LSP) plugins replace grep+multi-file reads; skills load on demand while CLAUDE.md loads every session (keep CLAUDE.md under 200 lines; the doc's example row shows a 49k-token CLAUDE.md costing tokens on every request). — [costs](https://code.claude.com/docs/en/costs) (primary)
- Skills progressive disclosure: skill bodies are appended at invocation as messages (keeps cache). Specific per-skill token savings: no primary measured figure found. A secondary claim that Claude Code uses ~33,000 tokens before the first prompt vs a competitor is a vendor-comparison blog snippet, unverified ([aitoolly](https://aitoolly.com/en/ai-news/article/2026-07-13-claude-code-vs-opencode-token-efficiency-analysis-why-claude-code-uses-33000-tokens-before-your-firs)).
- Background spend knobs: session recap, idle compaction (`idleCompaction`, v2.1.290+), prompt suggestions each make requests while idle. — [costs](https://code.claude.com/docs/en/costs)
- Batch API (50%) is incompatible with interactive harness loops but available for non-urgent bulk steps (e.g. nightly review sweeps); stacks with caching. — [pricing](https://platform.claude.com/docs/en/about-claude/pricing)

### Inferences
- For a lead keeping several builders busy: spawn builders as forks or with identical prefixes where the host supports it, keep tool sets and model identical across builders, and do not toggle model/MCP mid-run; otherwise each builder pays a full uncached first request (5m TTL default means idle builders go cold quickly).
- Reviewers with fresh context necessarily start cold; the cost to minimise is their orientation (give them a compact diff + done-criteria, not repo-wide reading).
- On subscription plans, the one-hour TTL applies to the main conversation only; subagent-heavy designs lose that, so setting `subagentPromptCacheTtl` to `1h` is worth testing for long builder tasks but write cost is higher.

### Gaps
- No primary measured saving for skills with progressive disclosure vs inline instructions.
- No measured cache-hit rates for subagent-heavy sessions (the Claude Code stat line excludes subagents).
- I did not fetch the Anthropic context-management page directly; figures come via search summary.
- Codex-side caching specifics (TTL, what breaks cache) not researched here beyond cached-input prices.

## 4. Instruction length and process overhead

### Takeaway
The best measured evidence says repo context files raise cost ~19-23% and do not reliably raise success; LLM-generated ones can hurt. Length itself did not correlate with success or cost in that study; content redundancy with existing docs did. Claude Code docs advise keeping CLAUDE.md small and moving workflow-specific text into on-demand skills.

### Cited Findings
- ETH Zurich, "Evaluating AGENTS.md" (Feb 2026; Claude Code + Sonnet-4.5, Codex + GPT-5.2/5.1-mini, Qwen Code): LLM-generated context files changed success by about -0.5% (SWE-bench) and -2% (AGENTbench/CTX) (not significant), raised cost ~20% and ~23% and steps +2.45/+3.92 (significant). Developer-written files: +2.4% success (not significant), cost up to +19%, +3.34 steps. Developer files beat LLM-generated by ~7% (p=0.038). Context file length did not correlate with success or cost. Authors: omit LLM-generated files; developer files should contain only what is not already in README/docs; evaluate before adopting. Measured. — [arXiv 2602.11988](https://arxiv.org/html/2602.11988) (primary, read 2026-11-09)
- Counter-evidence: when existing docs were stripped from repos, LLM-generated context files helped. A secondary source cites a separate study where AGENTS.md reduced median runtime 28.64% and output tokens 16.58%; I could not identify that study, treat as unverified. — [search summary of the ETH paper and coverage](https://arxiv.org/pdf/2602.11988)
- Claude Code docs: CLAUDE.md is loaded every session so move workflow-specific instructions to skills; aim for under 200 lines; "Specific prompts" and verification targets avoid broad scanning and rework; plan mode before implementation prevents expensive re-work (all vendor-asserted). — [costs](https://code.claude.com/docs/en/costs) (primary)
- Agent team spawn prompts add to every teammate's context from the start; teammates auto-load CLAUDE.md, MCP servers and skills. — [costs](https://code.claude.com/docs/en/costs)
- `--bare` skips CLAUDE.md/skills/hooks/MCP/auto-memory in scripted runs and is recommended for SDK/scripted calls; this is a direct route to run a builder or reviewer with only the instructions you pass. — [headless](https://code.claude.com/docs/en/headless)

### Inferences
- A process skill that every builder and reviewer loads in full is paid in input tokens on every request of every agent (at cache-read price after the first). A 10k-token skill read by 20 agent-sessions of 50 turns each is 10M cached-read tokens; at Sonnet 5.5's $0.10/MTok that is about $1, so the dollar cost is small when caching works, but it is large against subscription quota if quota counts cache reads (not confirmed) and it costs context room and attention. My arithmetic, not a source.
- Evidence supports "shorter, non-redundant, discoverable-only instructions" as cost-neutral-or-better; it does not show shorter instructions raise quality. No study found on mandatory ceremonies (e.g. required self-review steps) specifically.

### Gaps
- No study found isolating long skills / mandatory process steps vs terse ones in a multi-agent harness.
- No measured evidence on skill length vs adherence for Claude/Codex.

## 5. Scaling review effort with risk

### Takeaway
I found no primary evidence that sampling reviews or skipping review on trivial changes preserves quality in a multi-agent coding harness. What exists: vendor advice to give agents machine-checkable verification targets, hook-based deterministic filtering, and measured data that review/refine loops are a large cost share (so gating them matters).

### Cited Findings
- Review/refine rounds: 59.4% of tokens in ChatDev (see Q1); 33-66% in SWE-Review depending on generator strength (stronger generator = lower review share). — see Q1 sources
- Claude Code docs: "give verification targets" (tests, expected output) so Claude self-catches; test incrementally; deterministic hooks (e.g. language-server type errors reported automatically after edits) replace some model judgement. — [costs](https://code.claude.com/docs/en/costs) (primary, vendor-asserted)
- Claude workflows can run independent agents adversarially reviewing each other's findings, and loop "fix until check passes or two rounds make no progress" as a stop rule; the bundled deep-research workflow votes on claims. Quality pattern asserted, no cost/quality numbers. — [workflows](https://code.claude.com/docs/en/workflows) (primary)
- Advisor docs recommend a final advisor call after writes and tests, and a "Hard rule" checkpoint raised under-calling tasks by 7-10pp but was flat on mixed workloads: i.e. mandatory checkpoints help only where the executor under-escalates. — [advisor docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool) (primary, vendor-internal)
- Multi-agent paper: coordination yields diminishing or negative returns once a single-agent baseline exceeds ~45% (β≈-0.40); error amplification 17.2x independent, 7.8x decentralized, 4.4x centralized, 5.1x hybrid (centralised verification contains errors best). Measured on the authors' benchmarks, not coding-specific; the "45% rule" is a heuristic. — [Kim et al., arXiv 2512.08296](https://huggingface.co/papers/2512.08296) (search summary only)

### Inferences
- Defensible tiering (not evidenced as a policy): deterministic checks (tests, types, lint, done-criteria scripts) first, model review only when they pass; stop rules on no-progress rounds; review model tier/effort scaled to blast radius. Each part is supported by general evidence, the combination is untested here.
- Because review share is higher when the generator is weaker, spending more on the builder tier may lower total spend via fewer review rounds (SWE-Review pattern); that is an inference from one preprint.

### Gaps
- No paper or post found measuring defect-escape vs review-sampling rate for agent-written code.
- No data on review skipped for trivial changes.
- SWE-Review and Tokenomics were read as search summaries only.

## 6. Parallelism: cost and return

### Takeaway
Token cost scales roughly linearly with concurrent agents (Anthropic docs: agent teams ~7x a standard session in plan mode), wall-clock gains are real but accuracy gains are task-dependent, and conflicts/error propagation are the main waste. Anthropic's own guidance is small teams, small self-contained tasks, effort scaled to complexity.

### Cited Findings
- Agent teams use ~7x tokens of a standard session when teammates run in plan mode; token use roughly proportional to team size; keep teams small and tasks self-contained; shut teammates down when done; disabled by default (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`). Vendor-asserted. — [costs](https://code.claude.com/docs/en/costs) (primary)
- Research system: effort scaling rules embedded in prompts — simple fact-finding 1 agent / 3-10 calls; comparisons 2-4 subagents / 10-15 calls each; complex research >10 subagents; parallelisation cut research time up to 90%. Synchronous subagents bottleneck the lead. — [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system) (primary)
- Workflows runtime: default 16 concurrent agents (1-256 configurable), 1,000 agents per run, warning at >25 agents or 1.5M projected tokens; size guideline default `medium` (<10 agents) or `small` (<5) on Pro; transforms done "in an isolated copy" for migrations; failure mid-fan-out reruns already-finished later agents on resume. — [workflows](https://code.claude.com/docs/en/workflows) (primary)
- Claude Code docs: concurrent subagent limit exists and is not enforced under ultracode, and ultracode "uses more tokens and reaches limits sooner". — [workflows](https://code.claude.com/docs/en/workflows)
- Multi-agent scaling paper (Google/MIT): see Q5; independent agents amplify errors 17.2x vs 4.4x with a central coordinator. — [arXiv 2512.08296](https://huggingface.co/papers/2512.08296) (summary)
- Practitioner anecdotes (secondary, unmeasured): subagents give parallelism at 2-3x cost vs 7x for teams when subtasks don't communicate; merge conflicts and error cascades when agents touch the same files; worktrees as mitigation; a self-reported orchestrator repo table shows 43% conflicts parallel vs 0% serial (ambiguous labels). — [search summary of Towards AI post](https://pub.towardsai.net/i-burned-150-in-3-hours-using-claude-code-agent-teams-232811baaa24), [indiekitai/claude-orchestrator](https://github.com/indiekitai/claude-orchestrator)

### Inferences
- No source gives an optimal concurrency number for coding builders. Evidence points to: parallelise only independent milestones/file sets, cap concurrency low (Anthropic's own team guidance, "small"), and measure marginal wall-clock saved per extra agent for your repo.
- For subscription plans the binding constraint is the shared 5-hour/weekly window, so extra parallel builders burn quota faster without extra quota; wall-clock speed-up is the only return.

### Gaps
- No controlled study of coding-agent concurrency vs conflict rate, merge overhead or wasted work.
- No Codex-side data on parallel subagent usage cost.

## 7. Measuring and forecasting spend and quota

### Takeaway
Claude Code exposes per-session/model cost, cache stats, per-subagent/skill/MCP attribution, OpenTelemetry, workspace limits and `--max-budget-usd`; its dollar figures are list-price estimates. Forecasting evidence is thin: models mispredict their own token use and per-task variance is up to 30x.

### Cited Findings
- `/usage`: session token usage by model at list price (estimate, not bill; `modelPricing` managed setting for contracted rates), cache stats, plan usage attribution to skills/subagents/plugins/MCP servers, loops, and recommendations with a fix shortcut; computed locally from session history, excludes other devices. — [costs](https://code.claude.com/docs/en/costs) (primary)
- `claude -p --output-format json` returns `total_cost_usd` and per-model breakdown; `--max-budget-usd` caps a run and stops background work when reached; `--continue`/`--resume` reports cumulative cost. Estimates only. — [headless](https://code.claude.com/docs/en/headless)
- OpenTelemetry export gives per-user token/cost metrics near real time on every setup; Console Cost page, Claude Code Analytics API and workspace spend limits for API orgs; Teams/Enterprise spend report CSV and Enterprise Analytics API; subscription seat usage is not metered in dollars. Rate-limit guidance per user: 200-300k TPM for 1-5 users down to 10-15k TPM for 500+. — [costs](https://code.claude.com/docs/en/costs)
- Statusline scripts can read `current_usage`, `prompt_cache` and cost fields. — [prompt caching](https://code.claude.com/docs/en/prompt-caching), [costs](https://code.claude.com/docs/en/costs)
- Advisor usage reported per iteration in `usage.iterations[]` (`advisor_message` vs `message`); top-level usage counts executor only; advisor tokens not bounded by top-level `max_tokens`; count advisor calls client-side. — [advisor docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)
- Codex: usage page at chatgpt.com/codex/settings/usage for plan limits and credits per a secondary guide ([fast.inference.net](https://fast.inference.net/guides/codex-usage), secondary); the credit rate card lets you convert tokens to credits (see Q2). Tasks in credits: "typical GPT-5.6 Sol task 2-15 credits" (OpenAI page, wide range).
- Forecast difficulty: same-task runs vary up to 30x; self-prediction correlation ≤0.39 (measured, [HF 2604.22750](https://huggingface.co/papers/2604.22750)). Workflows show projected token totals and warn at 1.5M. — [workflows](https://code.claude.com/docs/en/workflows)
- Practitioner guidance (secondary, asserted): run a small slice first to gauge spend (also in the Claude workflows docs as vendor advice). — [workflows](https://code.claude.com/docs/en/workflows)

### Inferences
- A harness can forecast per milestone from its own history (tokens per milestone by role, by model, per retry) with a safety multiple, since public priors are loose; track cache-read share and rework rounds as leading indicators.
- Quota on subscriptions is opaque (percent bars, no token counts, per-window), so forecasting must use proxies (tokens at list price from `total_cost_usd`) calibrated against the observed bar movement; no source documents the conversion.

### Gaps
- No documented conversion from tokens to subscription quota percent for Claude plans, nor weekly numbers for Codex.
- No published forecasting method for multi-agent harness spend beyond per-task statistics above.
