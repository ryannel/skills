# Planning, verifying and steering agent work whose quality is subjective or partly measurable (as of 2026-11-09)

Research depth note: about 13 tool calls. Primary pages fetched in full: Anthropic harness post, Ziva playtesting page, 3D-DefectBench abstract, Gen3DEval, arXiv 2604.09876. Everything else is from search snippets only and is flagged as such. Evidence type tags: [measured] = reported numbers; [shipped] = a real project write-up; [vendor] = vendor claim; [opinion] = blog or guidance.

## 1. How agent systems define acceptance for subjective output

### Takeaway
The best-documented practice (Anthropic, March 2026) is a short graded rubric, written once by a human, given to both builder and evaluator, with few-shot scored examples to calibrate the evaluator, plus negotiated per-sprint "contract" criteria. Exemplars via screenshots plus Playwright comparison is the OpenAI/Codex pattern. I found no solid evidence for pairwise-against-previous-best or "taste captured once and reused" inside agent harnesses beyond the few-shot calibration and one personalisation paper whose results were weak.

### Cited Findings
- Frontend rubric of four criteria, design quality, originality, craft, functionality, given to both generator and evaluator. Design quality and originality were weighted higher because Claude already did craft and functionality well. The originality criterion penalised template-like "AI slop". Criterion wording steered style (phrases like "museum quality" pushed designs toward a visual convergence). [shipped, author's own account, no agreement statistics] — [Anthropic Engineering, Rajasekaran, 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- Evaluator calibrated with few-shot examples carrying detailed score breakdowns, which aligned it with the author's taste and reduced score drift across iterations. The author tuned the QA prompt by reading evaluator logs and fixing divergences from his own judgement. [shipped] — same source
- Sprint contracts: in the retro-game-maker run, sprint 3 had 27 contract criteria for the level editor, negotiated before building; the evaluator tested the running app against them. [shipped] — same source
- Playwright MCP used by the evaluator to navigate the live page, take screenshots, score each criterion, and write a critique the generator consumes next round; 5 to 15 iterations per generation, runs up to 4 hours; scores improved then plateaued; the author sometimes preferred a middle iteration. [shipped] — same source
- OpenAI Codex use-case guidance: turn screenshots/briefs into UI, compare to references at several screen sizes with Playwright, iterate until it looks right; screenshots are a visual target translated into the project's own tokens. [vendor guidance; no measured reliability] — [OpenAI Codex frontend designs](https://developers.openai.com/codex/use-cases/frontend-designs)
- Third-party skills (unverified against OpenAI's repo): capture desktop and mobile screenshots, a visual lint pass, a loop to "10/10", and taste rules (two typefaces, one accent, write a visual thesis first). [opinion/community; found via search snippet only] — [tessl review of frontend-design skill](https://tessl.io/registry/skills/github/udecode/plate/frontend-design/review), [claudeskills.info](https://claudeskills.info/skills/fcakyon/claude-codex-settings/openai-frontend-design/)
- Taste personalisation research: designers agreed only weakly with each other on UI preference (binary pairwise agreement 0.624, Krippendorff alpha 0.248). Held-out preference prediction: GPT-5.2 direct 56.78%, GPT plus inferred rubric 57.98%, tuned UIClip about 59 to 60%, proposed method 62.05% at 8 onboarding comparisons (chance 50%). 20 participants, single-page mobile UIs. Authors say tacit, screen-dependent preference is hard to capture. [measured, small] — [Peng, Bigham, Wu, arXiv 2604.09876 v2, 2026-09-14](https://arxiv.org/html/2604.09876)

### Inferences
- A rubric plus few-shot-scored examples is the only proven "taste capture" mechanism here; it needs the human once, at rubric and calibration time, not per output.
- Because human designers themselves agree only at alpha about 0.25 on UI preference, a judge cannot be expected to beat that ceiling; a rubric should target observable defects (broken, generic, inconsistent) rather than "is it beautiful".
- Anthropic's finding that wording steers style means the rubric is also a generation prompt; changing it changes output, not only grading.

### Gaps
- No agent-harness source found that uses pairwise comparison against a previous best for acceptance (it exists in 3D evaluation papers, see section 2, but not as a harness gate). No published style-guide-as-gate evidence beyond the community skills.

## 2. Reliability of VLMs as judges (visual, 3D, UI, games)

### Takeaway
VLM judges are usable as cheap defect finders and rankers but are lenient, trail trained humans, and are sensitive to setup; no source I found validates one as the sole gate for taste. 3D judging works best with multi-view renders and pairwise or defect-specific questions.

### Cited Findings
- Leniency in agent QA: out of the box the QA agent found real issues then talked itself into approving; it tested superficially. Self-judgement of own subjective work was too generous, so a separate tuned evaluator was used. [shipped] — [Anthropic 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- 3D-DefectBench: nine binary defects (geometry, texture, prompt adherence), 84 inference designs, 12 VLMs. Model choice is the dominant factor; six-view RGB performs about as well as denser views or depth/normal inputs; best VLM still trails trained human labelers; binary judges recover most defects humans rate severe; texture is weakest, dropping sharply against noisy "silver" labels. No numbers on the abstract page I fetched. [measured] — [arXiv 2607.10826, submitted 2026-07-12, v2 2026-10-06](https://arxiv.org/abs/2607.10826)
- Gen3DEval (CVPR 2025, older): pairwise comparison of rendered views (4 per object, equal-interval 360 degree orbit, RGB or normals) with Elo ranking; trained approach with CLIP encoder 0.90 accuracy on human appearance preference versus GPT-4o 0.59; weak on out-of-domain surface-normal evaluation; Janus-artifact objects judged erratically; human labels themselves noisy. [measured, older, trained model rather than a general agent judge] — [arXiv 2504.08125](https://arxiv.org/html/2504.08125v1)
- Eval3D reports 0.79 to 0.88 correlation with human judgements; I only saw this on an aggregator and did not verify it. [unverified] — [alphaxiv overview](https://alphaxiv.org/overview/2504.18509v1)
- UI-to-code (late 2025): a VLM judge reproduced the human ranking of systems on Design2Code-HARD but gave more conservative margins; that measures code-output comparison, not design taste. [measured, search snippet only] — [arXiv 2511.08195](https://arxiv.org/pdf/2511.08195)
- GameCraft-Bench (Godot, 140 tasks, 15 game families): a multimodal judge (GPT-5.5 per snippet) scores gameplay evidence against a hidden rubric; repeat runs on fixed evidence had small standard deviation; preliminary human calibration on a small subset found the judge broadly aligned but slightly more permissive, humans stricter on content depth and art/presentation; authors say it is not an inter-annotator study. I could not read the PDF body. [measured, thin, snippet only] — [arXiv 2606.17861, 2026-06-17](https://arxiv.org/pdf/2606.17861)
- WebGameBench (111 tasks, 12 coding agents): runtime evaluator reasonably aligned with human playability on a usable-rate criterion; exact three-way label agreement much harder. [measured, snippet only] — same search; paper not opened
- Judge-bias literature (general, not visual): a high self-preference rate may just be general leniency; leniency rises with the examinee's capability; one source finds evaluator uncertainty explains an average 89.6% of measured self-preference; a practitioner rule of thumb asks 85 to 90% judge-vs-expert agreement before gating a release. [mixed: papers via snippet; the 85 to 90% figure is blog opinion] — [alphaxiv 2604.06996](https://www.alphaxiv.org/abs/2604.06996), [MLflow guide](https://mlflow.org/articles/llm-judge-calibration/)

### Inferences
- Leniency is the consistent failure across Anthropic, GameCraft-Bench and the general literature, so judge prompts should be skeptical by default and calibrated on cases a human rejected.
- For 3D, a six-view RGB turntable is the evidence-supported cost-efficient input; defect-specific binary questions plus pairwise comparison are better supported than a single holistic score. Texture quality is where human review should concentrate.
- Same-family builder and judge may inflate scores, but the evidence for that specifically is contested (above); cheaper to test with a human sample than to assume.

### Gaps
- No measured VLM-vs-human agreement for UI aesthetic quality from agent harnesses; no measured agreement on "game feel"; no measured topology/UV quality judging by VLM. 3D-DefectBench numbers were not on the page I read.

## 3. How agents test games and interactive products

### Takeaway
The working stack is: scripted or bot input, fixed-timestep headless runs for objective metrics, MCP-driven screenshots for a model to look at, and an exploratory agent that returns pass/fail/blocked with evidence. Vendors explicitly stop short of judging fun.

### Cited Findings
- Godot practice: `Input.parse_input_event`/`action_press` simulate input; bot autoloads exit 0/1; flags `--headless`, `--fixed-fps 60`, `--quit-after`; Godot exited 0 after a script error so the bot must set exit codes; `--write-movie` needs a rendering display and crashed headless; GdUnit4 counts frames so wait by time; frame metrics (average FPS, 1% low, worst frame) via vendor tool. Scripted tests only check what was scripted; agents explore but cost model time and vary run to run; in one run the vendor tool reported success though a UI target was never found, so its report must be checked; screenshots exposed a score stuck at 0. Vendor states it does not judge whether a game is fun. [vendor, hands-on specifics] — [Ziva, updated 2026-11-07](https://ziva.sh/blogs/godot-automated-playtesting)
- Ziva Full Game Playtest Agent: launches scene, sends keyboard/mouse/gesture input, returns pass/fail/blocked; has no file-writing tools so it cannot edit the game to pass; Godot 4.2+. [vendor] — [ziva.sh/full-game-tester](https://ziva.sh/full-game-tester)
- Other Godot tooling: Godot Agent Loop (author, validate, run, observe, playtest, verify, refine), Open Godot MCP, Beckett (autonomous playtest paid tier), a community skill capturing viewport screenshots about every 2 s. [vendor/community, announcement-level] — [Godot forum Open Godot MCP](https://forum.godotengine.org/t/open-godot-mcp-ai-plays-tests-your-game-not-just-edits-files/141986), [Beckett](https://forum.godotengine.org/t/beckett-zero-sidecar-mcp-server-for-godot-4-2-the-ai-sees-and-optionally-playtests-your-game/141177/1), [godot-agent-loop](https://cdn.jsdelivr.net/gh/beremaran/godot-agent-loop@main/README.md)
- Anthropic retro-game-maker: solo run 20 min, $9, but play mode did not work; full harness 6 hr, $200, playable. Evaluator clicked through the running app and found concrete bugs (fill tool, delete handler, route ordering). Residual gaps: physics overlap bugs, an unjumpable wall in a generated level, a workflow that did not guide sprite-before-level, and for the DAW no audio input so QA could not hear. [shipped] — [Anthropic 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- GameDevBench (132 Godot tutorial-derived tasks): typical agent errors are wrong node hierarchies and missing signal connections. [measured, snippet only] — [summary](https://www.themoonlight.io/review/gamedevbench-evaluating-agentic-capabilities-through-game-development)
- Research on LLM playtest (match-3, 2025): coverage and HP-correlation figures exist on an aggregator but I could not verify them. [unverified] — [Emergent Mind](https://www.emergentmind.com/topics/llm-agents-as-game-testers)

### Inferences
- The cheap, reliable layer is deterministic: exit code, no script errors, fixed-fps frame stats, scripted input to reach states, screenshot at known states. Exploratory playtest agents add coverage of unscripted paths but need their own report verified.
- Giving the playtester no write tools is a design point worth copying (prevents gaming the check).

### Gaps
- No independent measurement of agent playtesters finding real bugs versus false positives; mostly vendor sources. Unity/Unreal/web-engine specifics not found in this pass.

## 4. Published agent-built game and 3D pipelines: process and breakdowns

### Takeaway
Generator-plus-critic loops with rendered feedback are the norm; every source that reports it finds the loop beats a single pass but costs far more, and it fails at subtle gameplay, audio and underspecified workflows.

### Cited Findings
- Anthropic: generator-evaluator loop; planner expands 1 to 4 sentences into a spec and was kept because without it the builder under-scoped; later (Opus 4.6) sprint decomposition and context resets were removed and the evaluator moved to a single end pass, justified only for tasks beyond what the model does reliably alone; DAW run about 3h50m, $124.70, QA pass roughly $3 to $4 each. Components were removed one at a time to test which were load-bearing. [shipped] — [Anthropic 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- LL3M: multi-agent Blender code generation; critic reviews multi-viewpoint renders with a VLM; separate verifier checks fixes were applied. [paper, snippet only] — [arXiv 2508.08821 area / search result](https://arxiv.org/html/2508.08821v1) (the snippet attributed Designer, Coder, Visual Inspector to 2508.08821; LL3M's own link was not given)
- 3DCodeBench / Infinigen-style: geometric validation step plus iterative visual refinement; multi-turn refinement with deterministic Blender feedback improves results; retry loop feeds back traceback; outputs human-verified. [paper, snippet only] — [3DCodeBench via search](https://www.3dcodebench.com/)
- SceneAssistant: VLM gets rendered feedback each step and can judge and prune generated assets. [paper, snippet only] — [arXiv 2603.12238](https://arxiv.org/pdf/2603.12238)
- Planner-Actor-Critic for Blender-MCP 3D modelling. [paper, only title seen] — [arXiv 2601.05016](https://arxiv.org/pdf/2601.05016)
- Blender MCP servers expose viewport capture, turntable/multi-angle renders, and post-operation object-state verification. [vendor listings] — [glama listing](https://glama.ai/mcp/servers/sandraschi/blender-mcp)

### Inferences
- Anthropic's own simplification path implies: keep the planner, and treat evaluator cost as justified only at the model's capability edge; re-test each harness component whenever the model changes.

### Gaps
- No first-hand shipped end-to-end 3D-asset agent write-up with a human-checkpoint and failure account found. A dev.to "AI-orchestrated 3D asset pipeline from JPEG to game-ready GLB" appeared in results but was not opened.

## 5. What can be made objective, and the objective/taste split

### Takeaway
Objective items agents can gate on: loads without error, exit codes, frame-time stats, UI text/score state, API and database state, clicks that produce the specified change. For 3D, geometry validation exists in research pipelines but I found no sourced practitioner guidance on polycount or topology budgets.

### Cited Findings
- Functional/behavioural checks via contract criteria and live clickthrough caught most reported bugs. [shipped] — [Anthropic 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- Frame time, fixed-fps repeatability, crash and runtime-error detection are measurable headlessly; fun is left to humans. [vendor] — [Ziva 2026-11-07](https://ziva.sh/blogs/godot-automated-playtesting)
- Audio: coding agents cannot hear; one tool converts audio to measurements and an annotated spectrogram PNG for agents; text-only models score surprisingly high on a music QA benchmark (56.4%) so audio benchmarks may not test listening; model audio-physical perception near chance on some tasks. [promotional blog plus papers via snippet; unverified] — [earshot blog](https://themenonlab.blog/blog/earshot-giving-coding-agents-ears-for-audio-work/), [arXiv 2504.00369](https://arxiv.org/html/2504.00369v2)
- Anthropic's DAW run: no audio input meant QA could not verify sound. [shipped] — [Anthropic 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)

### Inferences
- A sensible split: objective gate (loads, validity, budgets, frame stats, scripted-state screenshots exist) blocks first and is free; taste gate (rubric-graded VLM review) runs only on items passing it; humans sample the taste gate and own audio and "feel".
- The "budgets" side (polycount, texture size, file validity) is inferred from general practice, not sourced here.

### Gaps
- No sourced practitioner thresholds for polycount, topology, UV or texture budgets; no sourced engine-side frame-time targets for Unity/Unreal.

## 6. Human in the loop and keeping it cheap

### Takeaway
The cheapest sourced human contributions are up-front (rubric, calibration examples, prompt tuning from evaluator logs) and a final play/look. Anthropic's author did both and otherwise let the loop run. Evidence on batching or side-by-side options is generic HCI and tool-marketing, not harness-specific.

### Cited Findings
- Human wrote criteria and calibration examples, tuned QA by reading logs, played outputs and picked iterations; loop was autonomous between. [shipped] — [Anthropic 2026-03-24](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- Co-creation research: parallel mode (AI loop keeps running while the artist refines) studied with 21 participants; a 2026 Figma-based study proposes five user action patterns and a 214-turn dataset; CREA allows optional user interventions to steer direction. [measured/academic, snippet only] — [LACE arXiv 2504.14827](https://arxiv.org/html/2504.14827v1), [arXiv 2603.02050](https://arxiv.org/html/2603.02050v4), [CREA 2504.05306](https://arxiv.org/html/2504.05306v2)
- Practitioner advice: use agents early, define explicit human checkpoints, generate several directions and curate; mood boards generate variants side by side. [opinion/vendor] — [futuramo](https://futuramo.com/blog/?p=18618), [buildaiq](https://www.buildaiq.com/blog/ai-for-designers-amp-creatives-how-to-use-ai-without-replacing-your-creativity), [Krea](https://www.krea.ai/nodes/app/youngposhbullmastiff/mode-board1)

### Inferences
- Approving direction early (a spec, rubric and two or three rendered options) is cheaper than judging output late, but the evidence for it is opinion; Anthropic's counter-evidence is that a planner-written spec plus a once-written rubric ran for hours without human input.
- Given weak human-human agreement (alpha about 0.25 for UI preference), asking the human for a forced choice between two options is likely more reliable than asking for scores; this is inference, not tested in the sources.

### Gaps
- No source measuring human time or decision count saved by batching. No evidence found on OpenAI-side autonomous design agents beyond the Codex use-case page.

## Source quality summary for the report writer
- Strongest primary: Anthropic 2026-03-24 post (shipped, detailed, author-run, no agreement stats). Ziva page (vendor, hands-on).
- Measured but partly unread: GameCraft-Bench, WebGameBench, GameDevBench, Eval3D, 3D-DefectBench numbers, UI2Code^N, all taken from search summaries.
- Older: Gen3DEval (CVPR 2025).
- Nothing found on: UI aesthetic judge agreement from harnesses, game-feel judging, polycount/topology budgets, pairwise-vs-previous-best in a harness, shipped 3D asset agent with human checkpoints.
