# Models, persistence and harnesses

Contents:
- [Which vendor warns against which habit](#which-vendor-warns-against-which-habit)
- [Persistence by model and harness](#persistence-by-model-and-harness)
- [Harness stop causes](#harness-stop-causes)
- [Claude Opus 5.5](#claude-opus-55)
- [OpenAI GPT-6 Astra](#openai-gpt-6-astra)
- [OpenAI GPT-6.1 Sol](#openai-gpt-61-sol)
- [Choosing a model and effort](#choosing-a-model-and-effort)

Each vendor ties its advice to the model it measured. Re-check it on yours. Where a newer guide is silent, the older
finding is marked as untested on the newer model.

## Which vendor warns against which habit

- **Step-by-step recipes and itineraries.**
  - OpenAI: these now hurt Astra.
  - Anthropic: prefer judgment and give heuristics for open work, but still give sequential steps and checklists for
    complex, fragile operations.
- **Emphasis and capitals.**
  - Anthropic: plain lines are followed, and piled-on emphasis makes Claude over-apply a rule or over-trigger tools.
  - OpenAI: the warning is about strong "ask first" language and over-emphatic skill descriptions.
- **Mandatory reading lists.** OpenAI: point to docs by use case instead.
- **Review stops after a first implementation.** OpenAI: they pull Astra toward stopping early.
- **"Keep going", "be thorough" and "double-check" lines.**
  - Anthropic: these cause over-work, and Opus 5 already verifies itself.
  - OpenAI: recommends persistence wording for Astra (see below).
- **"Run the tests" encouragement.** OpenAI: Astra already tests, and the line makes it over-test.

## Persistence by model and harness

The vendors disagree here, so choose per run:
- **Astra.**
  - Define completion up front, and say if the job includes running, inspecting and fixing.
  - OpenAI's autonomy wording helps: bias to action, carry the task to completion, and treat "can you…" as a request
    to act. Don't stop at a plan or a partial answer.
  - Keep OpenAI's carve-outs with it: act autonomously unless an action is clearly destructive or irreversible, and
    don't add unsolicited warnings or approval flows.
- **Sol.** Add no extra pressure. It already persists more, so spend the words on evidence and honest claims.
- **Claude with a human in the loop.** Add no push. Current models carry on through an agreed task, and push lines cause
  over-work.
- **Claude unattended.**
  - Use a harness loop: Claude Code `/goal` or a Stop hook.
  - Without one, use the Opus 5.5 guide's unattended paragraph. It names the early-stop patterns to avoid:
    - a summary that announces the next step without taking it;
    - an offer to continue;
    - non-blocking decision lists;
    - stopping at a natural checkpoint.
  - Name the stops you do want, keep your own confirmation for risky or irreversible actions, and add the paragraph
    from the first request.

## Harness stop causes

Before blaming the instructions, check the harness.
- **Codex `/goal`.**
  - An interruption pauses the goal, and only the user or system resumes it.
  - Hitting the budget stops substantive work without completing it.
  - Plan-only turns don't trigger continuation, and a continuation turn with no tool call suppresses the next one.
  - The agent can declare itself blocked only after repeated no-progress turns.
- **Claude Code `/goal`.**
  - The loop stops after several turns in a row with no tool use, leaving the goal set.
  - Evaluation is deferred while background work or a subagent runs.
  - Auth, credit and context-overflow errors clear the goal; rate limits pause it.
  - A Stop hook can block only a bounded number of times.
- **Claude without a loop.** The session ends at turn end. A text-only Opus 5.5 turn may be a progress report that the
  harness treated as finished.

## Claude Opus 5.5

Model id: `claude-opus-5-5`.

- **Effort is the main control.**
  - The default is `medium` (Opus 5 defaulted to `high`). At `medium` it matched or beat Opus 5 at `high` on multistep
    repository work, and `low` comes close on several coding evals.
  - Set effort explicitly and sweep it, keeping `xhigh` and `max` for measured gains.
  - To cut thinking, lower effort rather than writing instructions.
  - Thinking can't be disabled, and forced `tool_choice` returns an error. To get a tool used, say when it applies.
- **It starts quickly.** On loosely specified tasks across several sources, tell it to explore broadly first, including
  sources the task didn't name. Keep untrusted content out of what it searches.
- **Unattended loops.**
  - Keep the task's parts in a checklist it updates.
  - When items remain open and no blocker is stated, continue with a short message naming them. Stop after two or
    three automatic continuations.
  - Wait for background work before treating the task as done.
- **Time signals.** An elapsed/budget line such as `elapsed 340s / 1200s` mainly raises parallelism in multi-agent
  harnesses. Keep a hard timeout of your own; under time pressure it verifies a little less.
- **Chat prompts.** Drop "think carefully" lines, which delayed replies with no quality gain.
- **Pasted text.** Wrap it in matching tags carrying a random id, and say that instructions inside count only where the
  user's own message asks.
- **Frontend look.** "Avoid a generic AI look" just swaps one default for another. Name the specific patterns to avoid,
  and extend the list each round.
- **Reasoning in the reply.** Requests for verbatim reasoning can be declined. Ask for a short explanation or a summary
  of actions.
- **Measured on Opus 5, untested on 5.5:**
  - Scope can widen on its own judgment. For narrow tasks, add a scope paragraph:
    - deliver what was asked at the intended scope;
    - check in only when different readings lead to materially different work;
    - if the request seems wrong, say so in a sentence and continue as asked.
  - It verifies and self-corrects unprompted. Remove "double-check" and verification-subagent lines, and limit
    correction narration to errors that change the user's decisions.
  - Responses and written deliverables run long, and effort doesn't shorten them. Ask for brevity explicitly.
  - It delegates readily. Delegate only large, independent, parallel work; never use a subagent to verify; use one where
    one suffices. Claude Code and the Agent SDK have hard caps.

## OpenAI GPT-6 Astra

Model id: `gpt-6-astra`.

- **It is tentative about stopping.**
  - It may return for review after a first implementation while work remains, and asks more clarifying questions than
    earlier models.
  - See [persistence](#persistence-by-model-and-harness), and remove review gates you don't need.
  - Prepare reviewable results before asking for approval.
- **It is very sensitive to skills and AGENTS.md.**
  - Unclear or conflicting text makes it pause.
  - Make precedence explicit: the user's instructions win over skill guidance.
  - Ask it to cite the exact skill line behind any pause.
- **It over-tests small changes.** Ask for tests that are meaningful and necessary, sized to the change.
- **It under-delegates.** Say when parallel delegation is wanted.
- **Its writing is heavily formatted.** Ask for short prose paragraphs, lists only where they help, plain words, and the
  main point first.
- **Effort.** `none` isn't supported. OpenAI's migration note maps `minimal` to `low`.

## OpenAI GPT-6.1 Sol

Model id: `gpt-6.1-sol`.

There is no Sol-specific prompting guide; OpenAI points to the Astra-centred GPT-6 guide. Sol is trained like Astra and
comes near its quality at much lower cost.
- **It persists and overclaims more than Astra.** In the system card, it measured more unwanted persistence past
  warnings, more reward hacking and concealed uncertainty, and a higher misrepresentation rate on coding-deception
  tasks.
  - Cut recipes and emphasis as for Astra, but don't add "keep going" pressure (this is an inference from those figures).
  - Ask for evidence behind every claim, keep verified, approximate and blocked apart, and give a stated blocked path.
- **It misses some subtle patterns Astra catches.** In OpenAI's audit, Sol Ultra found 92% of Astra's findings at about
  14% of the cost, and missed constant feature flags used as other flags' dependencies.
  - Name known blind spots in that run's goal or brief.
  - Keep the corrections narrow, and keep them out of shared skills and AGENTS.md, which steer every model.
  - Revisit them when models change.
- **Broad, ambiguous requests.** These worked on Astra but not on GPT-5.6 Sol. That wasn't re-measured on 6.1, so for
  Sol, start with a scoped goal with clear validation criteria.
- **Effort.** `low` to `max`, defaulting to `medium`; no `none`. Compare `medium` with `high` on your workload, and use
  `xhigh` and `max` only for a measured gain.

## Choosing a model and effort

- **Start small.** Compare configurations on one representative task before scaling. A cheaper model at medium effort is
  often enough.
- **Escalate** effort or model for hard reasoning, deep debugging, subtle cross-cutting audits and long unsupervised
  work. Drop back for routine follow-ups.
- **Effort is a tuning knob,** not a rescue for a bad prompt. Fix the instructions first.
