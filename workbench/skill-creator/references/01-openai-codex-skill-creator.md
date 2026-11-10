# OpenAI: the skill-creator that ships with Codex

- Source: `~/.codex/skills/.system/skill-creator/SKILL.md` on this machine, 229 lines, file dated 6 November 2026.
  It ships inside the Codex CLI. Its folder also holds `scripts/init_skill.py`, `scripts/quick_validate.py`,
  `scripts/generate_openai_yaml.py` and `references/openai_yaml.md`.
- Read on 2026-11-10. Paraphrased; short quoted phrases are marked.
- This is the rewrite OpenAI's Astra post said it had made. The copy on GitHub that the earlier research read
  ([prompting-agents note 12](../../prompting-agents/references/12-openai-prompt-engineering-and-skill-creator.md))
  was the older 368-line version. The new one is 40% shorter and drops most of the old version's fixed process.

## Its five principles

1. **Assume the model is already capable.** Include only what "changes its decisions or improves its work". Remove
   generic advice, repeated instructions, speculative edge cases, and examples that don't make the task clearer.
2. **Preserve the user's intent and scope.** A skill supports the task the user asked for. It should not replace
   the product the user chose, widen the assignment, change unrelated configuration, or imply permission for more
   outside actions. A single example, one past failure or a personal preference should not become a rule for every
   task. Approval to do a task does not widen what the task covers. A workflow that retries, or that changes
   something outside the machine, gets a stopping condition in proportion to the risk.
3. **Match how specific you are to the risk.** Leave room where several approaches are reasonable. Use detailed
   steps, a script, or absolute wording only where correctness, safety, permissions or a fragile workflow needs it.
   Open-ended work gets the outcome and the criteria for deciding. Work with a preferred shape gets an example or a
   configurable script. A fixed sequence is for operations where a deviation "would cause a concrete problem".
   Keep the facts about how the system works that the model could not guess. Say which lines are requirements and
   which are recommendations or local habits. Don't restate a policy that is already enforced somewhere else.
4. **Keep discovery cheap and precise.** The name and description are read before the skill loads. Describe the
   real capability and when it applies. Add an exclusion only when it prevents a likely wrong match. No long lists
   of capabilities, and no catch-all wording that attracts unrelated requests. Keep a skill self-contained: point
   to another skill or tool only when the workflow needs it and it will be there. A specialised review or audit
   skill should apply when asked for or needed, not because ordinary work touches the same subject.
5. **Disclose detail in stages.** `SKILL.md` holds the shared purpose, the essential constraints and the routing.
   Substantial guidance for one mode, schemas, examples and procedures go in references, read only when relevant.
   "A simple self-contained skill does not need a router or extra files."

## Structure

- The folder: `SKILL.md`, and optionally `agents/openai.yaml`, `scripts/`, `references/`, `assets/`. Don't create
  folders, placeholders, examples or extra documents with no clear use.
- Three stages of loading: name and description at selection; body when the skill applies; other files when the
  task needs them.
- The entry file should be "as short as the task permits" while keeping important constraints. A large upper
  limit "is not a target". Move conditional detail out when that helps, without waiting for the file to get
  unwieldy.
- Scripts: for logic that would otherwise be rewritten each time, or where deterministic execution makes the work
  more reliable. Run every new or changed script to check it.
- References: link each one from `SKILL.md` and say when to read it. Keep each fact in one place. No copied
  manuals, exhaustive catalogues or generic tutorials. Before removing an existing file, check what uses it. For a
  large reference, add search terms or a short contents list.
- Assets: files that go into the output. They are not loaded as instructions.
- No README, installation guide, changelog or duplicated quick reference in the folder.
- Routing examples: one reference per cloud provider, read only the one chosen; or a short skill that handles
  ordinary work directly and links out for two advanced operations. These "illustrate options, not a required
  structure".

## Creating or updating

- Fit the work to the request. A narrow update may need one edit and a validation run.
- Ask a clarifying question only when the missing fact matters and can't be inferred. If the user explained the
  task clearly, don't ask for more examples.
- Automatic selection stays on unless the user asks for an explicit-only skill
  (`policy.allow_implicit_invocation: false` in `agents/openai.yaml`). Don't infer explicit-only from a sensitive
  operation: keep the skill discoverable and require authorisation "immediately before the actual mutation".
- Names: lowercase letters, digits and hyphens, under 64 characters, short and action-oriented, same as the folder.
- The description says briefly what the skill does and when it applies, with a boundary where similar requests
  should not activate it. Their example is one sentence: create or edit Word documents when formatting, tracked
  changes or comments need document-specific handling. Workflows, tool choices and modes go in the body.
- The body: "only the instructions needed for another Codex instance to perform the task well". The outcome, the
  context that isn't obvious, the real constraints, the relevant references and tools. Don't prescribe a fixed
  structure, process or number of steps when the task doesn't need one.

## Validating and testing

- `scripts/quick_validate.py <folder>` checks frontmatter, naming and leftover placeholders. It "does not prove
  that the skill makes good decisions".
- When a test is warranted, check observable behaviour or a meaningful invariant. Don't write tests that only
  match generated wording, headings or regex patterns.
- Improve from real use or a demonstrated failure. Prefer a narrow correction to piling up universal rules.
- Forward-testing with an independent subagent is for a skill complex or risky enough that a realistic run adds
  confidence. Ordinary creation and small edits don't need it.
- Give the evaluating agent a realistic request, the skill and the minimum raw material. Don't give it the
  intended answer, the suspected bug, the proposed fix or earlier conclusions.
- Use an isolated temporary folder so test output doesn't enter the working tree or a later test. Ask before a
  test that needs more authorisation, touches a live system, or costs a lot of time or money. Then change only
  what the observed behaviour supports.

## What changed from the older version

| Older copy (GitHub, read earlier) | Shipped copy (6 November 2026) |
|---|---|
| Description "clear and comprehensive", with a long example | One sentence: the capability and when it applies |
| A fixed six-step creation process | "Adapt the work to the request" |
| Always ask for concrete examples | Ask only when the fact matters and can't be inferred |
| Write in the imperative | Not stated; "avoid prescribing a fixed structure, process, or number of steps" |
| Not stated | Preserve user intent and scope; a skill must not widen permissions |
| Not stated | Don't turn one example or one failure into a universal rule |
| Not stated | Tests check behaviour, never wording or headings |
