# LOGSIFT design

logsift is one module: the whole binary. The owner suggested one module and that holds up. There is only one kind of
state that matters (each followed file's open handle, identity and offset, plus the merge buffer), and every feature
is a stage on one pipeline over it, so splitting would create contracts with nobody on the other side. If the query
language later grows into a library other tools use, it can be split out then. No `ARCHITECTURE.md` is needed.

## Purpose and goal

A command-line tool that reads several log files at once, merges their lines into one stream ordered by timestamp,
keeps the lines a small query selects (`level>=warn AND svc=api`), and writes them as NDJSON. It works on files of any
size without loading them, and in follow mode it keeps tailing through log rotation.

The current goal is finished when M1 to M3 in `LOGSIFT-PLAN.md` are accepted.

## What users get

- `logsift app.log db.log` prints every line of both files, merged by timestamp, one JSON object per line, and exits.
- `logsift -f app.log db.log` does the same, then keeps following both files, through rename-and-recreate rotation
  and truncation, until Ctrl-C.
- `logsift -q 'level>=warn AND svc=api' ...` keeps only matching lines, in either mode.
- A 5 GiB input runs in the same memory as a 50 MiB one. Throughput is recorded, not targeted (nobody has set one).
- Errors read like ripgrep's: what went wrong, where, and what to do. A bad query fails before any file is read.

### Command line

```
logsift [-f|--follow] [-q|--query QUERY] [--start begin|end] [--window DURATION] [--poll DURATION]
        [--max-line BYTES] FILE...
```

- `--start` (default `begin`): where each file is read from. `end` is `tail -f`-style, only lines appended from now.
- `--window` (default `500ms`): the follow-mode reorder window, below.
- `--poll` (default `250ms`): how often followed paths are checked for growth, rotation and truncation.
- `--max-line` (default `1MiB`): the longest line kept whole.
- Exit codes: 0 success; 1 an I/O error (a file named on the command line is missing or unreadable in batch mode);
  2 a usage error or malformed query; 130 after Ctrl-C in follow mode, once pending output is flushed. A closed
  stdout (`| head`) ends the run quietly with 0.

## Input

Each line is parsed on its own, so files can mix formats:

1. **JSON object** if the line starts with `{` and parses. Fields keep their JSON types; nested fields are reachable
   by dotted path (`http.status`).
2. **logfmt** (`key=value key2="quoted value"`) if the line has at least one `key=value` pair. Values are strings,
   compared as numbers where both sides parse as numbers.
3. **Anything else** is a raw line with no fields.

**Timestamp.** Taken from the first present of `ts`, `time`, `timestamp`, `@timestamp`, `t`. Accepted forms: RFC 3339
and ISO 8601 with `T` or a space, optional fraction and optional offset; and numeric epoch, read as seconds, millis,
micros or nanos by magnitude. A time with no offset is UTC. Everything is normalised to UTC nanoseconds.

A line with no timestamp (a stack-trace continuation, a raw line) takes the timestamp of the previous line in the same
file, so it stays next to the line it belongs to. Lines before the first timestamp in a file have no timestamp; they
sort before every timestamped line and are emitted with `"_ts": null`.

**Level.** Taken from the first present of `level`, `lvl`, `severity`, `levelname`, case-insensitive, normalised to
`trace < debug < info < warn < error < fatal`. Aliases: `warning`→warn, `err`→error, `crit`, `critical`, `panic`,
`emerg`→fatal, `notice`→info, `dbg`→debug. Unknown values keep their text but have no rank.

**Bytes.** Invalid UTF-8 is replaced lossily. A line longer than `--max-line` is cut at the limit, the rest of it up
to the next newline is skipped without being buffered, and the record carries `"_truncated": true`. CRLF endings are
accepted.

## Output

One JSON object per line on stdout, UTF-8, nothing else on stdout:

- For a JSON line, its own fields unchanged; for logfmt, its pairs as strings; for a raw line, `"_raw": <line>`.
- Added fields: `"_ts"` (normalised RFC 3339 UTC with nanoseconds, or null), `"_src"` (the path as given on the command
  line), and `"_truncated": true` when cut. If the input already has a field with one of these names, the input's
  value wins and logsift's is not added, so input is never silently rewritten.

Diagnostics (rotation noticed, file missing while following) go to stderr, one line each, prefixed `logsift:`.

## Mechanisms

These are settled. The builder chooses everything else (crates, layout, types) within the licence rule.

### 1. Streaming readers: memory independent of file size

Each file is read through its own fixed-size buffered reader, one line at a time, and the merge holds at most one
parsed line per file in batch mode. Nothing ever reads a whole file, seeks to count lines, or memory-maps it. With
`--max-line` capping a single line, peak memory is bounded by (files × (buffer + max line)) plus the follow-mode
reorder buffer, and does not grow with file size. This is what makes 5 GiB work, and it is proved by measuring peak
RSS on 5 GiB against 50 MiB of the same content.

### 2. k-way merge: `sort -m` semantics, not sort

Batch mode is a k-way merge with a min-heap keyed by (timestamp, argument position, line number in file). It assumes
each file is roughly ordered already, as logs are. A line that is out of order inside its own file is emitted when it
reaches the head of its file, not moved earlier, because moving it would require holding the file. That is the same
contract as `sort -m`, and the help text says so. Ties break by the order files were given, then by line order, so
output is deterministic.

This was checked against the range: a fully sorted output for unsorted input is impossible in bounded memory, so the
only alternative would be an external sort, which the owner did not ask for and which cannot work while following.

### 3. Follow mode: watermark merge with a reorder window

While following, a file with nothing new cannot hold up the others, or one quiet file would stop all output. Each
followed file has a head (its next unread line, if any) and a time it last produced data. The merge emits the
smallest head when every file either has a head or has been idle for longer than `--window`. So lines that arrive
within the window of each other come out in timestamp order, and no line waits more than about `--window` plus
`--poll` after it is written. A line whose timestamp is earlier than one already emitted (it arrived too late) is
emitted straight away rather than dropped. The pending buffer has a hard cap (100,000 lines); past it the oldest line
is emitted early, so a burst cannot grow memory without limit.

This was checked against the range: writers whose clocks agree and whose lag is under the window give globally
sorted output; a writer lagging by more than the window gives late lines, which are kept, not lost. No setting gives
both perfect order and bounded latency, so this is the trade, and `--window` is the knob.

### 4. Rotation and truncation: follow the path, drain the old handle

logsift follows a path, like `tail -F`, by polling: every `--poll` it `stat`s the path and compares the (device,
inode) pair with the handle it has open, and the size with its read offset. Polling rather than filesystem events
because it behaves identically on macOS and Linux and on network filesystems, and a 250 ms poll is cheap.

- **Rename and recreate.** When the path's identity differs from the open handle, the old handle is kept and read to
  EOF, then kept open for a grace period (2 × `--poll`) to catch lines the writer appends before it reopens, then
  read once more and closed. Then the new file at the path is opened and read from offset 0. Because the old file was
  renamed, not deleted, it cannot share an inode with the new one, so the identity check is reliable.
- **Path missing.** Between rename and recreate the path may not exist. logsift notes it once on stderr and keeps
  polling until it reappears, without exiting.
- **Truncation (copytruncate).** If the identity is unchanged but the size is below the read offset, the file was
  truncated; reading restarts from offset 0.
- **Partial lines.** Bytes after the last newline are held until the newline arrives, so a line written in two
  `write` calls is not split. The held bytes are emitted as a line when the old handle is closed after rotation.
- **Delete and recreate with inode reuse** is caught by the truncation rule when the new file is smaller than the
  offset. A file rotated away and replaced again before logsift ever opened it (two rotations inside one poll) cannot
  be followed by path, and its lines are not seen. Supported range: rotation intervals of at least 2 × `--poll`.
  logrotate and most loggers rotate at most every few seconds, well inside that.

Platform: macOS and Linux. Windows is out of scope, because holding a file open there blocks the writer's rename.

### 5. Query language

A small boolean language, parsed by a hand-written recursive-descent parser into an expression tree once, before any
file is opened, and evaluated per record.

```
query      := or
or         := and ( OR and )*
and        := not ( AND not )*
not        := NOT not | primary
primary    := '(' or ')' | comparison
comparison := field op value
field      := [A-Za-z_@][A-Za-z0-9_.@-]*        (dotted path into nested JSON)
op         := '=' | '!=' | '<' | '<=' | '>' | '>='
value      := bare | '"' ( [^"\\] | '\' any )* '"'
bare       := one or more characters that are not whitespace, quote, '(' or ')'
```

`AND`, `OR` and `NOT` are case-insensitive keywords. Precedence is NOT, then AND, then OR.

Comparison rules, in order:

- `level` compares by rank when both sides are known levels (`level>=warn` matches warn, error and fatal, and every
  alias of them). Unknown levels match only `=` and `!=` by text.
- `_ts`, `ts` and the other timestamp fields compare as times when the value parses as a timestamp
  (`ts>=2026-11-09T10:00:00Z`).
- If both sides parse as numbers, they compare numerically (`http.status>=500`, `"500"` in logfmt included).
- Otherwise `=` and `!=` compare the text exactly, case-sensitively; `<`, `<=`, `>`, `>=` on text are false.
- A field that is absent makes every comparison on it false, including `!=`. So `svc!=api` means "has a svc that is not
  api", and `NOT svc=api` also includes lines with no svc. This is SQL's NULL rule, and the help text says so.

A malformed query exits 2 before reading any file and prints the query with a caret under the problem and what was
expected there, like rustc and ripgrep do.

## Contracts

None with other modules. The external contract is the command line and the output shape above; changing either is a
re-plan.

## Cost

No owner budget exists. Peak RSS and throughput on the 5 GiB fixture are recorded on the evidence page as the
baseline; the only threshold is the property that memory does not grow with file size.

## Decisions taken without the owner

The owner couldn't be reached. Each of these is a guess that a short answer from them could overturn; change them by
re-planning.

1. **Input format** was not stated. Assumed JSON lines and logfmt, auto-detected per line, with raw lines passed
   through, because `svc=api` implies structured fields.
2. **Timestamp and level field names and formats** are the common ones listed above; no-offset times are UTC.
3. **Batch and follow are both supported**, defaulting to batch, because "tails" and "5 GB files" together read as
   both "merge these big files" and "keep following them". Follow starts from the beginning unless `--start end`.
4. **Merge is `sort -m`, not a full sort**, because a full sort cannot be done without loading the files.
5. **Follow-mode ordering uses a 500 ms reorder window**, trading a little latency for order.
6. **Missing fields make comparisons false** (SQL NULL semantics).
7. **Output keeps the input's fields** and adds `_ts`, `_src` and `_truncated`.
8. **macOS and Linux only.**
9. **Integrate is `local`**: there is no permission to push.
