# LOGSIFT design

## Purpose

The owner's request, as typed:

> need a plan for logsift, a rust cli that tails multiple log files, merges them by timestamp, filters with a small
> query language (level>=warn AND svc=api) and outputs ndjson. must handle 5GB files without loading them, and
> rotation (file renamed + recreated mid-tail). repo is just cargo init. one module is fine i think

The current goal is finished when one binary, `logsift`, does all of that on the owner's Mac: it reads several log
files, merges their records into one timestamp-ordered stream, keeps the records a query selects, and writes them as
NDJSON. It does this in flat memory on multi-gigabyte files, and it keeps following through log rotation without
losing or repeating a line.

## Why one module

The owner suggested one module, and the state agrees. The tool has one kind of long-lived state: for each input file,
its open descriptor, read offset, identity (device and inode) and partial-line buffer, plus the merge's pending
records. Every part of the pipeline exists to move records through that state, and none of it is shared with another
program. Splitting reader, merge and query into modules would add contracts and design reviews without separating any
state, so there is no `ARCHITECTURE.md`. Inside the crate, the reader, the record parser, the merge, the query and the
output are separate Rust modules with narrow interfaces, which is a detail left to the builder.

## What the user gets

```
logsift [OPTIONS] <FILE>... [-q <QUERY>]
  -f, --follow         keep reading as files grow and rotate (default: read to the end and exit)
      --from-start     with --follow, start at the beginning of each file (default: at its current end)
  -q, --query <QUERY>  keep only matching records, e.g. 'level>=warn AND svc=api'
      --lag <DURATION> with --follow, how long to hold a record waiting for older ones from quieter files (default 1s)
      --max-line <BYTES>  longest line kept whole (default 1 MiB); longer lines are truncated and marked
```

- **Batch mode** (no `-f`): every record in every file, merged in timestamp order, written once, then exit.
- **Follow mode** (`-f`): like `tail -F` on several files at once. New records appear within about the lag plus the
  poll interval of being written, in timestamp order across files, and following survives rotation.
- **Output:** one JSON object per line on stdout, and nothing else on stdout. Diagnostics go to stderr.
- **Range:** from one empty file up to several files of 5 GiB or more each, with memory that does not grow with file
  size; from one file to a few dozen in follow mode.

### Exit codes

`0` success (including stdout closed early, as in `| head`, and Ctrl-C in follow mode); `2` bad arguments or a query
that doesn't parse; `1` an I/O error that stops the run, such as a file that can't be opened in batch mode.

## Records

A **record** is one log line, plus any continuation lines that follow it (lines with no timestamp of their own, such
as a stack trace). Each record carries the file it came from, its timestamp and its fields.

Two input shapes are recognised per line, without any flag:

1. **JSON object lines.** The timestamp is the first present of `ts`, `time`, `timestamp`, `@timestamp`; the level
   is `level`, `lvl` or `severity`; the message is `msg` or `message`. Other top-level fields are kept as fields.
2. **Text lines** that start with an RFC 3339 / ISO 8601 timestamp (`2026-11-09T12:00:00.123Z`,
   `2026-11-09 12:00:00,123`, with or without a zone). After the timestamp, an optional bare level word
   (`INFO`, `WARN`, ...), then the rest. Any `key=value` or `key="quoted value"` pairs in the rest become fields
   (logfmt); `level=` and `msg=` in that form are recognised too. The rest of the line is the message.

A line with no recognisable timestamp is a continuation of the previous record from the same file, appended to its
message with a newline. If a file starts with such lines, they form a record with no timestamp, which sorts as if it
had the timestamp of the next timestamped record in that file (or, at end of file, the last one seen), so it never
jumps to the front or back of the merged output.

Levels compare in the order `trace < debug < info < warn < error < fatal`, with common spellings mapped onto them
(`warning`, `err`, `crit`/`critical` to fatal, case-insensitive, numeric syslog-style levels are not mapped).

Invalid UTF-8 is replaced with U+FFFD, never fatal. A line longer than `--max-line` is truncated at that length and
the record gets `"truncated": true`; the rest of the line is skipped without being held in memory.

## Output schema

```json
{"ts":"2026-11-09T12:00:00.123Z","file":"api.log","level":"warn","msg":"slow request","svc":"api","ms":"812"}
```

- `ts` is normalised to RFC 3339 in UTC with the input's precision kept up to nanoseconds; omitted for a record with
  no timestamp. `file` is the path as given on the command line. `level` is the normalised level name, omitted if
  there is none. `msg` is the message.
- Other fields follow, keeping their JSON types for JSON input; logfmt values are strings.
- If an input field clashes with one of the four names above, the input's value is kept under `_<name>` (for
  example `_file`), so nothing is silently dropped.
- Every stdout line is exactly one valid JSON object followed by `\n`.

## Mechanisms

These are settled. The builder should not swap them out without a re-plan, because each is what makes one of the
owner's requirements possible.

### Streaming reads, never whole-file

Each file is read through a fixed-size buffered reader, line by line, holding at most one partial line (capped by
`--max-line`) and the records waiting in the merge. No mmap of whole files, no reading into a `Vec` or `String` of the
file, and no index of offsets. Memory is O(files × max line), not O(file size). That is the whole answer to "5 GB
files without loading them".

### K-way merge on a heap, one pending record per source

The merge keeps at most one parsed record per source in a min-heap ordered by `(timestamp, source index, sequence)`.
It pops the smallest, writes it, and refills from that source. Ties keep command-line file order, then file order, so
output is deterministic. Each file is assumed to be in time order already (the merge does not sort within a file); a
record out of order inside one file is written where it falls, after its predecessor, rather than buffered.

The continuation rule means a record isn't complete until the next timestamped line (or end of file) is read. So each
source holds the record it is building plus one finished record, still a constant per source.

### Follow mode: a lag watermark, not "wait for every source"

A plain k-way merge can't emit anything until every source has a pending record, so one quiet file would stall the
whole stream forever. In follow mode the merge emits the smallest pending record as soon as every source has a pending
record, or when it has been pending for `--lag` of wall-clock time, whichever is first. A record that turns up later
with a timestamp older than one already written is written immediately, not dropped and not reordered. The ordering
promise is therefore: batch output is fully sorted; follow output is sorted for any records that arrive within the lag
of each other. In follow mode a source's in-progress record is also flushed when it has had no new line for the lag,
so the last line before a quiet spell isn't held back waiting for a possible continuation.

### Rotation: poll the path, compare identity, drain the old descriptor

This is the `tail -F` mechanism (GNU coreutils follows by name the same way). For each followed path, logsift keeps
the descriptor it is reading and that descriptor's `(dev, inode)`. On every poll (250 ms, an internal constant), and
whenever its reader hits end of file:

1. `stat` the path. If its `(dev, inode)` differs from the open descriptor's, or the path is gone, the file was
   rotated by rename or deleted. Keep reading the **old** descriptor to its end first, because a logger often writes
   its last lines to the old file after the rename. Then emit any partial final line, open the path anew (once it
   exists) and read it **from the start**.
2. If the identity is the same but the path's size is now below the read offset, the file was truncated in place
   (copytruncate rotation). Emit nothing for the lost bytes, note it on stderr, and seek to 0.
3. A path that doesn't exist yet, or disappears and never comes back, is waited for with a note on stderr, never an
   error, in follow mode.

Polling is the mechanism, not filesystem events. Events (kqueue on macOS, inotify on Linux) report renames
differently per platform and can be missed; the builder may add them to wake the poll early, but correctness must not
depend on them. A partial line at end of file is held until its newline arrives; it's emitted without a newline only
when the descriptor is being abandoned (rotation, deletion, or end of input in batch mode).

### Query language: a small recursive-descent parser over records

```
query      := or
or         := and ( "OR" and )*
and        := not ( "AND" not )*
not        := "NOT" not | "(" or ")" | comparison
comparison := field op value
op         := "=" | "!=" | "<" | "<=" | ">" | ">=" | "~"      (~ is a regex match)
value      := bare word | "double-quoted string"
```

Keywords are case-insensitive; field names and values are case-sensitive except `level`, whose values are compared
in level order (`level>=warn` keeps warn, error and fatal). `ts` compares as a timestamp against an RFC 3339 value.
Other comparisons are numeric when both sides parse as numbers, otherwise string order. A record without the field
fails every comparison on it except `!=`. A query that doesn't parse exits 2 with the query echoed and a caret under
the error position, before any file is opened. Filtering happens after parsing a record and before it enters the
merge, so dropped records cost no merge memory.

### Stdout

Output is written through a buffered writer, flushed after each emitted batch in follow mode so records appear
promptly, and at exit. A broken pipe on stdout ends the run with exit 0 and no message.

## Costs

The owner has set no throughput or memory number. The plan records measurements and sets a tripwire rather than a
target: peak RSS above 100 MiB while streaming 5 GiB means memory is growing with input, which the design forbids.
Throughput on the scale test is recorded in the evidence each time it runs, for comparison, without a threshold.

## Assumptions

The owner couldn't be reached while this was planned. Each of these was decided by the planner and can be overturned
with `owner scope`:

1. Input formats are JSON lines and timestamp-led text with optional logfmt pairs, auto-detected per line. No
   custom format strings.
2. Timestamps without a zone are taken as UTC (no `--tz` flag yet).
3. Without `-f`, logsift reads whole files and exits; with `-f`, it starts at each file's end unless `--from-start`.
4. Lines without a timestamp attach to the previous record as continuations.
5. Follow-mode ordering is best-effort within `--lag` (default 1 s); late records are written, never dropped.
6. Unix only (macOS is the target, Linux expected to work). Windows is out of scope because rotation detection relies
   on inode identity.
7. Lines over 1 MiB are truncated and marked, to keep memory bounded.
8. Output field names `ts`, `file`, `level`, `msg` are fixed; clashing input fields move to `_<name>`.
9. No glob expansion inside logsift (the shell does that), and no directory watching for new files.
10. Not handled: compressed rotated files (`.gz`), and reading rotated-away history (`app.log.1`) at start.

## What this module promises

There are no other modules. Its promises are to the user and to scripts that consume its output: the CLI surface
above, the exit codes, and the output schema. Changing any of them is an owner decision.
