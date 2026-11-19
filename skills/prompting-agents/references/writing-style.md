# Writing style

The style to copy is Randall Munroe's in "What If?": start from what the reader knows, take one step at a time,
and use the exact detail when you have it. Leave out the jokes, meaning the asides, the playful examples and the
clever last line. A prompt should end on its last useful fact.

## The habits at work

**Put the main thing first.** A prompt that opens with "I've been looking at the sync code, and there's some
history here you should know about" makes the reader hold every detail until it finds out what they are for.
Open with the task instead: "Find out why `sync` retries forever when the server returns a 429." The history
can follow, and now the reader knows what to look for in it.

**Use ordinary words.** While you work, you invent short names for things: "the fallback path", "phase two",
"the big refactor". The reader wasn't there when you named them. Write the plain description instead, such as
"the code that runs when the cache is empty".

**Define a term once, then keep to that word.** The reader can't ask what "the ledger" is, so say it once: "The
ledger is the file `state/ledger.json`, which lists every job and its status." After that, always call it the
ledger. If a later paragraph says "the state file", the reader has to work out whether that is a second file.

**Explain a new fact next to the ordinary case.** "`/export` streams CSV" is easy to miss on its own. "Most
endpoints in this service return JSON, but `/export` streams CSV, so don't parse its body as JSON" tells the
reader exactly where its usual assumption breaks.

**Make it clear whose job each action is, and in what order.** "The branch should be rebased before review"
doesn't say who rebases it. "Rebase the branch before you ask for review" does. When the job belongs to someone
else, name them and say why: "Ask Priya before you deploy. She owns the release calendar." When several steps
happen in sequence, tell them in that sequence: "Run the migration on the staging copy, check that the row counts
match, then open the pull request."

**Be concrete.** "The test suite is slow" gives the reader nothing to act on. "The suite takes 11 minutes, and
the 63 resolver tests take 9 of them" tells it where to look.

**Write whole sentences.** "Auth: review. Spec: `docs/auth.md`. No style." is short, but the reader has to guess
how the three parts connect. "Review the auth change against `docs/auth.md`, and leave style alone" is only a few
words longer, and leaves nothing to guess.

In longer text, one more habit matters: give one example, then go back to the plain statement. Three similar
examples make the reader copy whatever the three happen to share.

## Two prompts, before and after

A brief for a subagent:

> Before: "Investigate the flaky tests. IMPORTANT: be thorough and check all possible causes. First read the CI
> config, then read the test files, then look at recent commits, then form hypotheses. Report back with a
> detailed analysis including root cause, contributing factors, and recommendations."
>
> After: "Three tests in `tests/sync/` fail about one run in five on CI and never on a laptop. The failing runs
> are linked in `notes/flaky.md`. Find out why, and fix it if the fix stays inside `tests/sync/` and
> `src/sync/`. A fix counts when the three tests pass 20 times in a row with `make test-sync-loop`. If the cause
> is outside those folders, stop and tell me what you found. Say which parts you confirmed by running something
> and which you only suspect."

The second version drops the capitals and the reading order, because the subagent can plan its own
investigation. What it adds are the facts the subagent had no way to find: how often the tests fail, where the
evidence is, how far it may go, and what counts as fixed.

A line in an instruction file:

> Before: "NEVER touch the generated code!!!"
>
> After: "`src/gen/` is written by `make codegen` from `api/schema.yaml`. To change it, edit the schema and run
> `make codegen`."

The first version only forbids, so a reader that needs a change in `src/gen/` is stuck. The second says why the
files shouldn't be edited by hand and what to do instead.
