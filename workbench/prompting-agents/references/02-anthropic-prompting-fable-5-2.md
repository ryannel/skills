# Anthropic: Prompting Claude Fable 5.2

- URL: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2
- Read in Chrome on 2026-11-10. Paraphrased. Numbers are Anthropic's own testing unless marked.
- Applies to Fable 5.2 and Mythos 5.2. Organised by symptom: find what you observe, apply that section.

## Effort

- Start at `high` (the API default). Sweep again on this model; do not carry over a level tuned on Fable 5.1 or
  Opus 5.5, because the thinking behind each level differs between models.
- `low`: quick exchanges, well-specified tasks, high-volume subagents. `medium`: interactive coding, chat, everyday
  work. `high`: hard coding, research, long unattended runs. `xhigh`: only where you measured a gain (small score
  rise, many more tokens). `max`: measuring the ceiling.
- Most capability is already there at `high`. Above it, gains are uneven.
- Stops early more often at `low` and `medium`.
- At `high` and above it thinks before almost every reply. An instruction to answer without deliberating did not
  stop that at `medium` and above. Lower the effort instead.
- Effort barely changes reply length. Use the prompt for length and tone.

## Finishing the whole task

- Symptom: a turn ends with a list of what remains, an offer to continue, or a stop at an ordinary obstacle.
- Fix: a "finishing work" block that separates two kinds of obstacle. Ordinary ones (errors, timeouts, failing
  tools) are diagnosed and worked through. Deliberate ones (a file marked not to touch, withheld access, a
  guardrail) are left alone and reported.
- Measured on replayed coding sessions at `medium`: about half as many sessions ended with doable work left. Output
  tokens rose about 30%. It removed endings that ask permission; it did not remove endings that list what's left.
- Keep your own confirmation step for risky actions, because the model asks less with this text.

## Approvals

- Say what you want, not a bare "continue": "Yes, run the migration on the staging database".
- Approval rules are applied as written. Name the exact actions. A rule that listed "sending messages to people
  outside this conversation" made the model hold back about half its routine requests to colleagues.

## Who owns the code

- With no word on ownership, or code presented as someone else's, it adds to the existing structure and reports
  nearby problems without fixing them.
- With "this codebase is yours", it merged duplicated code in about half the tries, against under a tenth without.
  It also used about 1.5x the output tokens and made unasked changes (tests, docs); it changed existing behaviour in
  one try in six to ten. Its summary named large changes and often omitted small ones: read the diff.
- A scope rule elsewhere ("no drive-by refactors") did not cancel the ownership sentence.

## Progress updates

- It can run long stretches of tool calls with little user-facing text.
- Updates come back as progress-update thinking blocks, empty at the default display setting. Check the client
  shows them before changing the prompt.
- Harness option: after several silent steps, append a short turn-scoped reminder. Roughly halved the longest
  silent stretch, no noticeable cost.
- Prompt option: ask for a line before starting, brief updates, and a recap that stands alone. About 20% more
  output tokens. Simpler: "every few tool calls, give the user a one-line update".

## Subagents

- How much it delegates depends on the harness. With a plain tool it rarely delegates; where prompts invite
  delegation it delegates readily.
- First review lines in system prompts, skills and agent files that tell it to delegate. Only then change the tool
  description. A good description states what a subagent costs, when delegation is and isn't worth it, and how to
  brief one. That cut delegation by about a third with the same task success.
- At `xhigh` and `max` it used subagents to review its own work unprompted. Early testers had good results with it
  as planner and orchestrator for other models.
- Check which model the harness runs subagents on by default.

## Caution that builds up

- Cautions pile up wherever context carries over: memory, notes, instruction files, messages between agents. This
  model follows them closely, so it asks for approvals it doesn't need or holds back routine work.
- Remove notes you no longer need. One stale "never retry" note among a dozen cut retries from nearly all tries to
  about four in ten.
- Name the steps that need no approval. A general "act more freely" changed nothing; a line listing retries among
  steps needing no approval raised retries from almost none to about half.
- Check what reviewer agents attach. A reviewer's "stop at the first error" stopped it retrying in a third of tries.
- Write the exception into the rule itself. Under a "never" rule, an approved step was taken one try in ten. A
  separate line saying approved steps may proceed barely helped. The rule saying "get a go-ahead first" gave nine
  in ten.

## Instructions written for earlier models: review before reusing

- Standing instructions to delegate: remove what the tasks don't need.
- A token budget written into the prompt changes how much it spends. Removing a large budget lowered cost with the
  same performance.
- Harness code that edits earlier turns invalidates the thinking after that point. Keep history append-only.
- The Opus 5.5 "treat that answer as done" lines made it far less likely to point out its own earlier mistakes.
- "Answer directly without deliberating": no effect at `medium` and above. Lower effort.
- Hard style limits ("one instruction per sentence, in 20 words or fewer") make its prose choppy. It follows style
  rules closely. Remove ones you no longer need.
- Built-up rules, notes and memories: delete cautions whose reason no longer holds, and rewrite absolute rules so
  they state their scope and reason.

## Final reports

- Readers of a final report have not seen the tool calls or files. The report must stand alone.
- Their block: write for an intelligent, low-context reader; key points first; no reference in line 1 that only
  makes sense at line 12; plain words; full sentences; no terms or abbreviations made up during the work; mostly
  the style of ASD-STE100 Simplified Technical English (short sentences, one idea each, active voice, the same word
  for the same thing); prose where ideas connect, bullets for separate items.
- Effect: reports were less dense, with fewer semicolons and shorter sentences.

## Refusals

- Asking the model to write its reasoning into the response can be declined (`reasoning_extraction`). Remove such
  instructions from prompts, skills and tool descriptions. Read the thinking summaries instead.

## Migration order

1. Set effort to `high` explicitly; also run `medium` and `xhigh`.
2. Read everything you carry over (system prompts, skills, agent files, memory, notes, harness text) and remove or
   test the instructions above.
3. Run the longest tasks; note early stops, needless approvals, silence, over-delegation, code added where it should
   have been restructured.
4. Apply one fix at a time and measure its effect and token cost.

## Also

- Make prompt changes in new conversations only; changing the system prompt mid-conversation can fail the request.
  To change instructions partway, put them in the newest turn.
