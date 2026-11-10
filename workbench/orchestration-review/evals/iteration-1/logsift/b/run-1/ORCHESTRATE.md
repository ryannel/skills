# Orchestrate profile: logsift

- **Purpose:** docs/modules/LOGSIFT.md#purpose
- **Quality bar:** A Unix CLI as dependable as `tail -F` under rotation, as clear in its help and errors as ripgrep, and as easy to pipe as jq: memory flat whatever the file size, nothing lost or duplicated, every output line valid JSON.
- **Anchors:** none
- **Plans:** docs/modules  *(loop)*
- **Evidence:** docs/evidence  *(loop: review files and evidence pages)*
- **Graded examples:** docs/evidence/graded-examples.md  *(past verdicts the owner agreed with or overturned)*
- **Check:** cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test  *(loop: required; the 5 GiB scale test is `#[ignore]`d and runs only as its item's check)*
- **Integrate:** local  *(loop: required; no remote is configured and the owner has not given permission to push)*
- **Branch:** master  *(loop)*
- **Remote:** origin  *(loop: not configured yet; unused while Integrate is local)*
- **Builders:** usually one Codex builder  *(one module, built in order; parallel builders would only collide)*
- **Effort:** medium  *(loop)*
- **Claude permissions:** auto  *(loop)*
- **Codex sandbox:** workspace-write  *(loop)*
- **Writable roots:** ~/.cargo, $TMPDIR  *(loop: crates download into ~/.cargo; the scale and rotation tests write into $TMPDIR)*

## Starting from a clean clone
`cargo build` is the whole setup; there are no services, secrets or seed data. Tests create their own log files in a
fresh temporary directory per test (the `tempfile` crate or equivalent), so parallel worktrees and parallel test
threads never share a file. The scale test needs about 6 GiB free in `$TMPDIR` and deletes its input when it finishes.

## Targets

| Target | What it is | Run | Capture | Edge conditions |
|---|---|---|---|---|
| cli | The release binary on the owner's Mac (macOS, APFS); Linux is expected to work by the same code but is not a build target yet | `cargo build --release && target/release/logsift …` | Terminal transcript, stdout and stderr kept apart, exit code, peak RSS from `/usr/bin/time -l` | Bad arguments, bad query, missing file, empty file, file with no timestamps, invalid UTF-8, a line over the length cap, piped into `head`, Ctrl-C while following, rotation by rename and by truncation |

## Rules
- **Exclusive resources:** scale (the 5 GiB scale test: one run at a time, for disk space and so its timings aren't skewed)
- **Large captures:** generated test inputs are never committed; tests generate them into `$TMPDIR` and delete them. Evidence pages record sizes, timings and peak RSS as text.
- **Owner decides:** changing the goal or the query language's syntax beyond what the design states; adding a Windows target; publishing to crates.io; pushing or adding a remote  *(loop)*
- **Licences and paths not to touch:** dependencies must be MIT, Apache-2.0 or similarly permissive (no GPL/AGPL); write only inside this repository and `$TMPDIR`  *(loop)*

## Project guidance
- Rust edition 2024, stable toolchain. Prefer small, widely used crates (clap, serde_json, a time-parsing crate) over hand-rolled equivalents, except where the design settles the mechanism.
- Assumptions made while the owner was unreachable are listed in docs/modules/LOGSIFT.md#assumptions; the owner may overturn any of them with `owner scope`.
