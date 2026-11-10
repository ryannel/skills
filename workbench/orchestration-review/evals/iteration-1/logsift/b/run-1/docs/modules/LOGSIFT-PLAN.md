# LOGSIFT plan
Reviews: design review owed: none run yet (the planner could not start one; the lead runs `agent_loop.py review --module LOGSIFT --milestone design --worktree .`)
Milestone: M1 Batch merge of large files into NDJSON
Now: plan written, waiting for the design review (since 2026-11-09)
Next: build M1 once the design review passes
Blocked: none

## M1 Batch merge of large files into NDJSON: open
- [ ] Records parsed from JSON and timestamp-led text lines, continuations attached
- [ ] Heap merge of several files, sorted and deterministic, every input record written once
- [ ] NDJSON output to the schema in the design, broken pipe exits 0
- [ ] 5 GiB scale test with peak RSS recorded and under the 100 MiB tripwire

## M2 Follow mode through rotation: open
- [ ] Follow from end or from start, with the lag watermark across quiet files
- [ ] Rename-and-recreate rotation drains the old descriptor, then reads the new file from the start
- [ ] Truncation, deletion and late-created files handled without exiting
- [ ] Ctrl-C exits 0 with output flushed

## M3 Query filtering and a finished CLI: open
- [ ] Query parser and evaluator to the grammar in the design, with caret errors
- [ ] Filtering in both modes
- [ ] Help, errors and exit codes as dependable as ripgrep's; whole-module review

## Log
- 2026-11-09 Planned as one module (the owner's suggestion; the per-file reader state is the only state, so no architecture doc). Order puts the riskiest first: flat memory on 5 GiB and merge correctness (M1), then rotation and live merge (M2), then the query language, the lowest-risk part (M3). Owner was unreachable; the assumptions are listed in LOGSIFT.md#assumptions. Design review is owed before M1 starts.
