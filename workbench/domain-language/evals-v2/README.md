# Single-turn cases for domain-language 1.0.0

Written 20 November 2026, before any run, for the rewrite that puts the field's established terms first. Each case
is one request. The agent under test works in a copy of `files/` (a git repository with one commit), and where it
would next message the human it writes that message to `REPLY.md` and stops. So these cases test the first round
only: what it found, what it recommended, and how it explained it. They don't test a whole conversation; the
two-agent cases in `evals/` do that, and their checks assume the older rule that the human's word wins.

Each case is run twice in fresh subagents, with the skill (a copy outside every folder a host scans) and without
it, and graded against `checks.md`.
