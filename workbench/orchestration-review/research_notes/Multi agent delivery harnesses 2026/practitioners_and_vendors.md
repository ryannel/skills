# Practitioners and vendors (non-Anthropic, non-OpenAI) on multi-agent delivery harnesses, as of 2026-11-09

Method note: about 19 tool calls. Pages I fetched in full (primary): Cursor x3 posts, Böckeler/Fowler, Maggie Appleton, Cohere, Vals AI, the yage.ai synthesis. Everything else is from search snippets or secondary summaries and is marked "secondary". Not covered adequately (no product-specific evidence found): Google Jules/ADK, Sourcegraph Amp, Factory, Replit, GitHub Copilot agent, BMAD, 12-factor agents, Kiro/Spec Kit primary docs. Model names in the Cohere/Vals pages (GPT 6 Sol, Claude Opus 5.5, Terra, Luna) are as the fetch tool reported them; I did not verify them independently.

## 1. What architectures do teams running agents at scale report?

### Takeaway
Cursor and Cognition both converged on hierarchy with narrow roles and single-writer or isolated-worker discipline. Cursor's flat self-coordination, locks, integrator and judge were each tried and removed. Cognition reversed its 2025 "don't build multi-agents" stance to a narrow form: extra agents add intelligence (review, advice), not parallel writes.

### Cited Findings
- Cursor, "Scaling long-running autonomous coding" (Wilson Lin, 14 Jan 2026): phase 1 equal agents coordinating via a shared file with locks; 20 agents slowed to the throughput of two or three. Phase 2 optimistic concurrency. Phase 3 planners (explore, create tasks, spawn sub-planners) and workers (take one task, finish, push). Flat structure made agents risk-averse and they churned on small safe changes. Production report with named runs: browser from scratch about a week, 1M+ lines; Solid-to-React migration 3+ weeks (+266K/-193K) "still needs careful review"; video rendering 25x faster, merged. No dollar cost, only "trillions of tokens". Says "prompts matter more" than harness and model. Open issues: planners not waking, agents running too long, need for periodic fresh starts. — [Cursor](https://cursor.com/blog/scaling-agents)
- Cursor, "Towards self-driving codebases" (Wilson Lin, 5 Feb 2026): root planner does no coding; recursive subplanners; workers get their own repo copy, complete one task and return a handoff (notes, concerns, findings) to the requesting planner; workers do not talk to each other. Removed or replaced: shared-state-file coordination; the planner/executor/workers/judge pipeline (judge removed once agents were reliable enough, so the final design has no dedicated judge); a continuous executor that was overloaded and skipped planning and claimed premature completion; the integrator (central quality gate, became a bottleneck). Demanding 100% correctness before every commit caused serialisation, so they accepted a small steady error rate and let work "converge". Disk I/O from hundreds of compiling agents was the main hotspot. Vague instructions produced an architecture that could not evolve. Peak about 1,000 commits/hour, about 10M tool calls in a week, several hundred agents. Switched to OpenAI models for instruction-following. Judge-less end state is described as expected self-healing, with a "green branch plus fixup pass" proposed but not implemented. Production report, no cost figures. — [Cursor](https://cursor.com/blog/self-driving-codebases)
- Cursor Long-running agents (12 Feb 2026, product launch, weaker evidence): agent proposes a plan and waits for approval before execution; "multiple different agents checking each other's work"; PRs larger, "merge rates comparable to other agents" (numbers only in a chart I could not read); examples 25 to 52 hours, one 151k-line PR. No cost stated. Marketing-grade. — [Cursor](https://cursor.com/blog/long-running-agents)
- Cognition April 2026 post "multi-agents working" (via ZenML summary; I did not open the primary at cognition.ai/blog/multi-agents-working): (1) writer plus clean-context reviewer (Devin Review) reported at about 2 bugs per PR, about 58% severe; (2) "smart friend": small fast model escalates to a larger one, weak point is the small model's judgment of when to escalate, cross-frontier routing works; (3) manager Devin spawns child Devins over internal MCP, live on week-long multi-PR work, with open problems (over-prescriptive managers, wrongly assumed shared state, children not reporting back). Rejects unstructured swarms as "mostly a distraction". Principle: keep writes single-threaded. Production report, Cognition's own numbers. — [ZenML summary](https://www.zenml.io/llmops-database/multi-agent-systems-in-production-code-generation-and-review-at-scale)
- Cognition's reversal as quoted from their social post ("10 months ago... argued not to build multi-agent... Today the landscape is different") — secondary: [echai summary](https://echai.ventures/how-founders-use-ai/r/walden-yan-a-year-later-what-changed--943), [Latent Space wiki](https://latent.space/wiki/walden-yan-7c572c23/). Original essay June 2025 (older source, not re-read).
- LangChain, "Improving Deep Agents with harness engineering": deepagents-cli moved 52.8 to 66.5 on Terminal Bench 2.0 by changing only the harness (system prompt, tools, middleware such as local-context mapping, time-budget warnings pushing toward verify-then-finish), model fixed. Measured, but vendor's own and not independently reproduced; secondary coverage only. — [LangChain](https://blog.langchain.com/improving-deep-agents-with-harness-engineering)
- Terminal-agent paper (arXiv, March 2026): subagents get isolated context, filtered tools and their own iteration budgets; early versions gave subagents the same tools as the main agent and this was changed; todo management kept with the main agent. Snippet only. — [arXiv 2603.05344](https://arxiv.org/pdf/2603.05344)

### Inferences
- The two best-documented large-scale systems both found that a central gate (Cursor's integrator and judge) was the bottleneck. This weighs against heavy always-on review roles in a long-running swarm, but Cursor's workloads are objectively checkable (CI, browser tests); it does not follow that a subjective-work pipeline can drop its reviewer.
- Cursor ended with no judge and accepted a nonzero error rate; Cognition ended with a clean-context reviewer as its most successful pattern. These are different positions on review and the evidence for each is a production report, not a controlled comparison.

### Gaps
- No primary material found for Jules/ADK, Amp, Factory, Replit or GitHub Copilot agent architectures. Cohere cites a Factory three-role system at 14x cost and 13x time on GDAL (secondary claim inside the Cohere post; not verified).
- Cursor gives no dollar cost for any run.

## 2. Single versus multi-agent in 2026

### Takeaway
Where measured, teams give modest and conditional gains at 1.8x to 7x cost; the gain depends on the lead model and on a named bottleneck. Writes stay single-threaded or isolated; parallel reads, review and verification are where extra agents pay off. Not settled: the evidence is a handful of 2026 benchmark posts with small n.

### Cited Findings
- Vals AI Vibe Code Bench (10 Sep 2026 per page "10/09/2026", ambiguous format; 50 apps, each setup run once): team versus single agent: Sol medium 77.6 to 84.9 (+7.3, p=0.005, only significant result); Sol max +1.4; Opus medium -0.3; Opus max +3.4 (n.s.). Cost 1.8x to 5.1x (Opus max $23.77 to $122). Raising one model's effort from medium to max beat a team at medium. Biggest team gains (20+ points on nine apps) were where single agents had claimed tests passed but features were missing; the lead drove a headless browser in 46/50 runs. Opus leads wrote a shared contract (schema, routes, file ownership) first. Measured, small n. — [Vals AI](https://www.vals.ai/blogs/multi-agent-vibe-code-bench)
- Cohere (14 Oct 2026, ProgramBench 200 tasks, 3 runs): solo 52.1 vs blocking team 61.8; with a plan-implement-verify prompt solo 57.7 vs team 63.1. Cost 3x to 7x ($510 all-stage async team, $249 planning-only, $155 strong lead with 16 cheap planners at 61.8). A weak lead with cheap workers (51.6) lost to a strong solo agent (57.7). More than 2 to 4 implementers got worse. Worker-to-worker messaging hurt cheap models. Some models (Opus 4.7, Haiku 4.5, Flash) barely delegated or gained nothing. Planning delegation helped most when the program had to be discovered by running it. No merge-conflict discussion (shared workspace). Measured. — [Cohere](https://cohere.com/blog/lessons-from-scaling-teams-of-frontier-coding-agents)
- Synthesis (yage.ai, 21 Oct 2026, a blog, not primary) citing: Anthropic's June 2025 numbers (multi-agent about 15x tokens; token use explained about 80% of BrowseComp variance); Microsoft Research Fork-and-Flush (0.78 vs 0.47 at equal compute, arXiv 2610.07447); Agentless (32% SWE-bench Lite at $0.70/issue with a fixed pipeline); MAST failure taxonomy (arXiv 2503.13657); Noam Brown on Dwarkesh (Sept 2026): four parallel agents roughly halve time at double price. Its bottom line: for hard single-step reasoning or tightly coupled edits, raise one agent's effort; add agents only for a nameable payoff (wall-clock, coverage, search diversity, context isolation). I did not verify the cited papers themselves. — [yage.ai](https://yage.ai/share/multi-agent-what-it-buys-en-20261021.html)

### Where practitioners disagree
- Cursor: hundreds of parallel writers pushing to one branch with minimal conflicts works for them. Cognition: writes single-threaded. Vals and Cohere: gains are real but cost 2x to 7x and vanish with a weaker lead or more effort on a single agent.
- Cursor says judge/integrator removed; Cognition and Vals say a verifier or reviewer with clean context catches features the author claimed done.

### Inferences
- What "settled" it, as far as it is settled: cost-matched comparisons (Vals effort-vs-team, Cohere cheap-worker teams) and the writer/reviewer asymmetry. A spend-minimising framework should treat multi-agent as a per-task purchase, not a default.

### Gaps
- No independent replication of any of these; Vals ran each setup once.

## 3. Loop-and-spec approaches

### Takeaway
Spec-driven tooling is criticised as heavy ceremony for small work by the best-documented critic; Ralph-style loops rest on a strong exit check and have no rigorous evaluation I could find; Gas Town is reported as costly and idiosyncratic though its persistence idea is widely borrowed.

### Cited Findings
- Birgitta Böckeler (Thoughtworks), Martin Fowler site, 15 Oct 2025 (older than 2026; tools tested Sept 2025 and fast-changing): Kiro turned a small bug into 4 user stories and 16 acceptance criteria ("sledgehammer to crack a nut"); Spec Kit felt like overkill for a 3-5 point feature, produced eight verbose markdown files for one spec, ignored research notes and created duplicate classes; she would rather review code than specs; spec-as-source (Tessl) risks model-driven-development rigidity plus LLM non-determinism, and regenerating from the same spec gave different code. Hands-on opinion with concrete examples, not a measured study. — [Fowler](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- Maggie Appleton on Gas Town (written after mid-Jan 2026, undated page): "entirely vibecoded", built in about 17 days by Yegge's own account, too many overlapping ad hoc concepts, "burning through thousands of dollars a month" in API costs; but valuable patterns: specialised roles, persistent tasks with ephemeral sessions, continuous work queues. Argues design and planning, not coding, become the bottleneck and humans supply taste. Opinion. — [Appleton](https://maggieappleton.com/gastown)
- Gas Town/Beads facts (secondary): Beads released Oct 2025; Gas Town open-sourced 1 Jan 2026; Beads stores issues as JSONL in git with a SQLite cache and hash IDs to avoid merge conflicts; one practitioner keeps beads, worktrees, tmux and strips "polecats, molecules, deacons, refineries" as ceremony. No independent benchmark found. — [Software Engineering Daily, 12 Feb 2026](https://softwareengineeringdaily.com/2026/02/12/gas-town-beads-and-the-rise-of-agentic-development-with-steve-yegge/), [DEV post](https://dev.to/kiwibreaksme/what-i-learned-from-steve-yegges-gas-town-and-a-small-tool-for-solo-developers-2me2)
- Ralph loop (Huntley, mid-2025 origin; January 2026 coverage, all secondary): bash loop re-feeding a prompt; explicit exit condition (tests pass, checker returns 0); specs and plan files first; "back pressure" from tests, lints, build. Critique: only as good as the scorecard under it, otherwise "you pay for the difference". Stuck-loop advice in community write-ups: after the same error three times, document the blocker and skip; vague specs are the usual root cause; Huntley reportedly favours driving it by hand during the spec phase. Cursed language project (3 months running) is the headline demo, unverified. — [Ralph Wiggum Loop Isn't a Strategy](https://piperstreetsoftware.pages.dev/articles/ralph-loop-isnt-a-strategy.html), [Ralph Playbook](https://claytonfarr.github.io/ralph-playbook), [Driving Ralph by Hand](https://blog-9h2.pages.dev/ai/driving-ralph-by-hand-what-geoff-huntley-really-sa)
- A June 2026 blog argues spec-driven development "becomes tax" when applied uniformly — weak source, snippet only. — [ainexusdaily](https://ainexusdaily.vercel.app/article/2026-06-01-spec-driven-development-when-structure-helps-and-when-it-becomes-tax)

### Inferences
- Both the spec critique (Böckeler) and Vals' finding (Opus leads write a contract and ownership doc first) point the same way: a short contract that prevents integration mismatch earns its cost; per-task multi-file spec ceremony for small changes does not. Sizing the process to the change is the common thread.

### Gaps
- No primary read of Spec Kit, Kiro, BMAD, 12-factor agents, or Huntley's own posts; no measured comparison of spec-driven versus plain prompting found.

## 4. Planning granularity, dependencies, parallelism, merge conflicts, review, recovery

### Takeaway
Evidence favours coarse-to-fine recursive planning by a non-coding planner, one task per worker with a handoff, isolated repo copies, and clean-context review; sub-failure recovery is the least documented area.

### Cited Findings
- Planner owns scope and does not code; subplanners own narrow slices; workers hand off notes and concerns upward — [Cursor Feb 2026](https://cursor.com/blog/self-driving-codebases)
- Merge conflicts: Cursor first used a central integrator (removed as bottleneck), then tolerated transient breakage and convergence; Beads uses hash IDs to avoid ID collisions; Vals Opus leads assigned file ownership up front; Cohere shared one workspace and had the lead consolidate — sources as above.
- Dependencies: Cohere found asynchronous minimal-prompt leads delegated less and gained little, while a structured plan-implement-verify prompt helped both solo and team. — [Cohere](https://cohere.com/blog/lessons-from-scaling-teams-of-frontier-coding-agents)
- Review: Cognition clean-context reviewer (about 2 bugs/PR, 58% severe); Vals verification-by-driving-the-running-app caught claimed-but-missing features. LangChain's time-budget nudges push agents to verify before finishing.
- Recovery: Ralph community rule "same error 3x, document and skip"; Cursor periodic fresh starts and the executor's premature-completion failure. No vendor source gave a principled escalation or re-plan policy.

### Inferences
- Premature "done" claims appear in Cursor (executor), Vals (single agents reporting tests passed) and Ralph critiques; this supports machine-checkable done criteria plus a verifier that runs the product, but none of these sources address subjective output (games, 3D).

### Gaps
- Nothing found on judging subjective quality in these harnesses.
- Nothing found on re-planning after repeated failure beyond Ralph folklore.

## 5. Cost and how much process is too much

### Takeaway
Reported multipliers are 1.8x to 7x for teams over a strong solo agent, with gains of 0 to about 10 points; vendors running swarms publish no dollar costs, and a critic reports Gas Town at thousands of dollars per month.

### Cited Findings
- Vals: 1.8x to 5.1x; most extra spend is cached input re-sent by each subagent — [Vals AI](https://www.vals.ai/blogs/multi-agent-vibe-code-bench)
- Cohere: 3x to 7x; cheap planners under a strong lead cut cost (to $155) at similar score (61.8) — [Cohere](https://cohere.com/blog/lessons-from-scaling-teams-of-frontier-coding-agents)
- Cohere cites Factory's three-role system at 14x cost, 13x time on GDAL (secondary) — same page.
- Anthropic's 15x token figure for multi-agent, cited via [yage.ai](https://yage.ai/share/multi-agent-what-it-buys-en-20261021.html) (Anthropic is out of scope; included only as a number others cite).
- Cursor: "spends some extra tokens" on synchronisation, no figures; accepted error rate to avoid serialisation — [Cursor](https://cursor.com/blog/self-driving-codebases)
- Böckeler: spec ceremony is excessive for small changes — [Fowler](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)

### Inferences
- Cheapest-evidence-supported moves: strong lead with cheap planners or workers for read-heavy phases; a single reviewer with clean context; a short contract; reasoning effort tuned before adding agents. Anything not in a measured source (integrators, per-task spec bundles, role proliferation) lacks support here.

### Gaps
- No cost-per-merged-milestone data from any vendor; no measurement of process overhead as a share of spend.
