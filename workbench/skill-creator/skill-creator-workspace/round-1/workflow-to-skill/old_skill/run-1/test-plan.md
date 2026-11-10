# Test plan for tidepool-release (nothing here has been run)

These are the test prompts I'd use and what a good result has to contain. I wrote the statements before any run
exists, so they can't drift towards an output I like. Please correct the prompts first, because bad prompts test the
wrong thing.

## Where the runs must happen

Never in the real tidepool repository. A real run uploads to TestPyPI and can push a tag, and the tag publishes to
PyPI. Each run gets its own throwaway copy with:

- a small stand-in repository (`pyproject.toml`, `src/tidepool/__init__.py`, `CHANGELOG.md`, a `Makefile` with
  `check`) whose `origin` is a local bare repository, so pushes go nowhere
- a stand-in `uv` that records `uv publish` calls and prints "success" either way
- a stand-in for the TestPyPI lookups, which can be set to "this version is already there"
- a stand-in for the CI status, which says "running" for the first few checks and "passed" after that
- a time zone chosen when the run starts so that the local date differs from the UTC date, otherwise the date rule
  can't fail

I can't build the CI stand-in faithfully until I know what CI tidepool uses (question 1 in reply.md).

Each prompt runs once with the skill and once without it, in fresh agents, as a smoke test. Because Priya uses
Codex, the same cases should also run there, since a skill that works on one model can misfire on another.

## Case 1: a full release

> ok lets ship tidepool 0.9.1. changelog should mention the --depth flag fix and the 3.14 wheels. go

A good result:

1. `pyproject.toml` and `src/tidepool/__init__.py` both say 0.9.1.
2. The 0.9.1 heading in `CHANGELOG.md` carries the UTC date, not the local one.
3. The stand-in remote received the tag `v0.9.1` only after the CI stand-in first answered "passed" for the release
   commit (compare the two logs' timestamps).
4. The agent pushed the tag without asking the person for permission.
5. The agent looked up the version on TestPyPI after uploading, instead of taking "success" as proof.
6. The final message doesn't call the release finished unless `tidepool --version` printed 0.9.1 in a new
   environment.

## Case 2: picking up a half-done release

> priya started the 0.9.1 release yesterday and got pulled onto something else, can you finish it? i think the
> version bump is already committed

The stand-in repository has 0.9.1 in `pyproject.toml` only, a changelog heading with yesterday's date, and a TestPyPI
stand-in that already lists 0.9.1.

A good result:

1. `src/tidepool/__init__.py` ends up at 0.9.1 too.
2. The changelog heading is changed to today's UTC date before any tag is made.
3. The agent tells the person that TestPyPI already has 0.9.1, and doesn't report the rehearsal as passed.
4. No tag is pushed before the CI stand-in answers "passed" for the commit that holds these fixes.

## Case 3: one step only

> can you bump tidepool to 0.10.0 and write the changelog entry, i'll do the rest tomorrow

A good result:

1. Both version files say 0.10.0.
2. Nothing is built, uploaded, tagged or pushed.
3. The reply says the heading date has to match the UTC date on the day the tag is made, so it will need changing
   if the tag is made tomorrow.

## Not done yet

- No runs, with or without the skill.
- No test of whether the description makes the skill load. That needs about twenty prompts in real sessions with
  the skill installed, half that should load it and half near misses ("release the lock file", "what changed in
  tidepool 0.9.0?").
