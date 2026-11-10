# LOGSIFT plan
Reviews: design review owed: run `agent_loop.py review --module LOGSIFT --milestone design --worktree .` before M1 starts
Milestone: M1 Merge large files by timestamp to NDJSON in bounded memory
Now: plan written, waiting on the design review (since 2026-11-09)
Next: M1, once the design review passes
Blocked: none

## M1 Merge large files by timestamp to NDJSON in bounded memory: open
The riskiest promise comes first: 5 GiB in the memory of 50 MiB. Batch mode only.
- [ ] CLI skeleton taking `FILE...` and the flags in the design (follow and query may be rejected as not yet
      supported until M2 and M3)
- [ ] Per-line parsing of JSON, logfmt and raw lines; timestamp and level extraction and normalisation
- [ ] Streaming reader per file with the `--max-line` cap and lossy UTF-8
- [ ] k-way merge with the (timestamp, argument position, line number) key
- [ ] NDJSON writer with `_ts`, `_src`, `_truncated`; quiet exit on a closed stdout
- [ ] Deterministic 5 GiB fixture generator and the peak-RSS comparison test
- [ ] Evidence page with RSS and throughput baselines

## M2 Follow live files through rotation, in timestamp order: open
- [ ] `-f` follow loop with `--poll`, `--start`
- [ ] Watermark merge with `--window` and the 100,000-line buffer cap
- [ ] Rotation by (device, inode) change with the old-handle drain and grace period
- [ ] Missing-path wait, truncation restart, partial-line holding
- [ ] Ctrl-C flush and exit 130
- [ ] Writer-driven tests for each rotation case, with generous timing margins so they don't flake

## M3 Filter with the query language: open
- [ ] Recursive-descent parser with caret errors
- [ ] Evaluator with level ranks, time, numeric and text comparisons, and the missing-field rule
- [ ] Filtering wired into batch and follow
- [ ] `--help` that states the merge contract (`sort -m`), the missing-field rule and the supported rotation range

## Log
- 2026-11-09 Planned from the owner's request. One module, as the owner suggested: there is one piece of state and one
  pipeline. Milestones ordered by risk: bounded memory on 5 GiB first (everything else stands on the reader), then
  follow and rotation (the subtlest timing), then the query language (well understood, least risky). The owner was
  unreachable, so nine decisions were taken on their behalf; they are listed at the end of LOGSIFT.md. No cost target
  exists, so memory is proved as a property (5 GiB vs 50 MiB) and throughput is only recorded. Design review not yet
  run: this planning turn could not start one.
