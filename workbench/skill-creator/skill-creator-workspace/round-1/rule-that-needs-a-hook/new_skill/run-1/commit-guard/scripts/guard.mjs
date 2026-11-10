#!/usr/bin/env node
// The commit guard: a Claude Code PreToolUse hook for the Bash tool.
//
// Claude Code runs this script before every Bash command and passes the tool call as JSON on standard input.
// The script exits 0 to let the command run. When the command holds a `git commit` that would land on a
// protected branch, or would include a file Prettier has not formatted, it prints the reason on standard error
// and exits 2. Claude Code then cancels the whole command and shows the reason to the agent.
//
// The guard never changes the working tree, the branch or the real index. To check a commit that stages files
// in the same command (`git add x && git commit`, `git commit -a`), it replays the staging in a throwaway copy
// of the index.
//
// It covers the repository this file lives in, and that repository's worktrees. A commit in any other
// repository is let through. Needs Node 18 or later and git 2.5 or later.

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Branches that take no direct commits.
const PROTECTED_BRANCHES = ["main"];

const USAGE = `commit-guard: a Claude Code hook that cancels a \`git commit\` on a protected branch
(${PROTECTED_BRANCHES.join(", ")}) or one that includes a file Prettier has not formatted.

Claude Code runs it before each Bash command. To see what it says about a command without running
the command, pass the same JSON by hand:

  echo '{"cwd": "/path/to/repo", "tool_input": {"command": "git commit -m \\"Fix typo\\""}}' | node guard.mjs

Exit code 0: the command may run. Exit code 2: cancelled, with the reason on standard error.`;

// ---------------------------------------------------------------------------------------------------------
// Reading a shell command line
// ---------------------------------------------------------------------------------------------------------

// Removes the bodies of here-documents (`<<EOF ... EOF`), so that a commit message held in one is never read
// as commands.
function dropHeredocBodies(source) {
  const lines = source.split("\n");
  const kept = [];
  for (let i = 0; i < lines.length; i++) {
    kept.push(lines[i]);
    const start = lines[i].match(/(?<!<)<<(?!<)-?\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1/);
    if (!start) continue;
    const end = lines.findIndex((line, j) => j > i && line.trim() === start[2]);
    if (end !== -1) i = end;
  }
  return kept.join("\n");
}

// Returns the index just past the `)` that closes a `$(` or `<(` opened before `i`.
function skipParens(source, i) {
  let depth = 1;
  while (i < source.length) {
    const c = source[i];
    if (c === "\\") {
      i += 2;
    } else if (c === "'") {
      const end = source.indexOf("'", i + 1);
      i = end === -1 ? source.length : end + 1;
    } else if (c === '"') {
      i = readDoubleQuoted(source, i + 1, () => {});
    } else if (c === "(") {
      depth++;
      i++;
    } else if (c === ")") {
      depth--;
      i++;
      if (depth === 0) return i;
    } else {
      i++;
    }
  }
  return source.length;
}

// Reads a double-quoted string that opened just before `i`. Returns the index just past the closing quote.
function readDoubleQuoted(source, i, add) {
  while (i < source.length && source[i] !== '"') {
    const c = source[i];
    if (c === "\\" && i + 1 < source.length) {
      const next = source[i + 1];
      if (next === "\n") {
        i += 2;
      } else if ('$`"\\'.includes(next)) {
        add(next);
        i += 2;
      } else {
        add(c);
        i++;
      }
    } else if (c === "$" && source[i + 1] === "(") {
      const end = skipParens(source, i + 2);
      add(source.slice(i, end), false);
      i = end;
    } else if (c === "$" || c === "`") {
      add(c, false);
      i++;
    } else {
      add(c);
      i++;
    }
  }
  return i + 1;
}

// Splits a command line into simple commands, each a list of words. A word is { text, literal }. `literal`
// is false when the shell would rewrite the word before the program sees it (a variable, a pattern, a command
// substitution), which means the guard can't know its final value.
function splitCommands(source) {
  const commands = [];
  let words = [];
  let word = null;
  let dropNextWord = false; // the word after a redirection is a file name, not an argument

  const add = (text, literal = true) => {
    word ??= { text: "", literal: true };
    word.text += text;
    if (!literal) word.literal = false;
  };
  const endWord = () => {
    if (!word) return;
    if (dropNextWord) dropNextWord = false;
    else words.push(word);
    word = null;
  };
  const endCommand = () => {
    endWord();
    dropNextWord = false;
    if (words.length) commands.push(words);
    words = [];
  };

  let i = 0;
  while (i < source.length) {
    const c = source[i];
    const next = source[i + 1];
    if (c === "\\") {
      if (next !== "\n") add(next ?? "");
      i += 2;
    } else if (c === "'") {
      const end = source.indexOf("'", i + 1);
      const stop = end === -1 ? source.length : end;
      add(source.slice(i + 1, stop));
      i = stop + 1;
    } else if (c === '"') {
      add("");
      i = readDoubleQuoted(source, i + 1, add);
    } else if (c === "$" && next === "(") {
      const end = skipParens(source, i + 2);
      add(source.slice(i, end), false);
      i = end;
    } else if (c === "`") {
      const end = source.indexOf("`", i + 1);
      const stop = end === -1 ? source.length : end + 1;
      add(source.slice(i, stop), false);
      i = stop;
    } else if (c === "#" && !word) {
      const end = source.indexOf("\n", i);
      i = end === -1 ? source.length : end;
    } else if (c === " " || c === "\t") {
      endWord();
      i++;
    } else if (c === "<" || c === ">") {
      if (word && /^\d+$/.test(word.text)) word = null; // the 2 in 2>file
      endWord();
      while (i < source.length && "<>&|".includes(source[i])) i++;
      if (source[i] === "(") i = skipParens(source, i + 1); // <(process substitution)
      else dropNextWord = true;
    } else if ("\n;|&()".includes(c)) {
      endCommand();
      i++;
    } else if ((c === "{" || c === "}") && !word && (next === undefined || " \t\n;".includes(next))) {
      endCommand();
      i++;
    } else if ("$*?[~{".includes(c)) {
      add(c, false);
      i++;
    } else {
      add(c);
      i++;
    }
  }
  endCommand();
  return commands;
}

// ---------------------------------------------------------------------------------------------------------
// git and Prettier
// ---------------------------------------------------------------------------------------------------------

function git(cwd, args, options = {}) {
  const result = spawnSync("git", args, {
    cwd,
    env: { ...process.env, GIT_OPTIONAL_LOCKS: "0", ...options.env },
    encoding: options.buffer ? "buffer" : "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    maxBuffer: 512 * 1024 * 1024,
  });
  return { ok: result.status === 0, out: result.stdout ?? "", err: String(result.stderr ?? "") };
}

const firstLine = (text) => text.trim().split("\n")[0] ?? "";

// macOS reaches /tmp through a link, and git reports the real path. Compare real paths with real paths.
function realPath(dir) {
  try {
    return fs.realpathSync(dir);
  } catch {
    return dir;
  }
}

function toplevel(dir) {
  const result = git(dir, ["rev-parse", "--show-toplevel"]);
  return result.ok ? result.out.trim() : null;
}

// The directory that a repository and all its worktrees share. Two folders belong to the same repository
// when this is the same for both.
function sharedGitDir(dir) {
  const result = git(dir, ["rev-parse", "--git-common-dir"]);
  if (!result.ok) return null;
  try {
    return fs.realpathSync(path.resolve(dir, result.out.trim()));
  } catch {
    return null;
  }
}

// Finds the project's own Prettier, looking in `node_modules` from `from` up to the repository's top folder.
function findPrettier(from, top) {
  let dir = realPath(from);
  top = realPath(top);
  for (;;) {
    const manifest = path.join(dir, "node_modules", "prettier", "package.json");
    if (fs.existsSync(manifest)) {
      const bin = JSON.parse(fs.readFileSync(manifest, "utf8")).bin;
      const relative = typeof bin === "string" ? bin : bin?.prettier;
      if (relative) return path.join(path.dirname(manifest), relative);
    }
    const parent = path.dirname(dir);
    if (dir === top || parent === dir || path.relative(top, parent).startsWith("..")) return null;
    dir = parent;
  }
}

function projectUsesPrettier(top) {
  if (fs.readdirSync(top).some((name) => /^\.prettierrc(\.|$)|^prettier\.config\./.test(name))) return true;
  try {
    const manifest = JSON.parse(fs.readFileSync(path.join(top, "package.json"), "utf8"));
    return Boolean(manifest.prettier || manifest.devDependencies?.prettier || manifest.dependencies?.prettier);
  } catch {
    return false;
  }
}

function prettier(bin, top, args, input) {
  const result = spawnSync(process.execPath, [bin, ...args], {
    cwd: top,
    input,
    stdio: [input === undefined ? "ignore" : "pipe", "pipe", "pipe"],
    maxBuffer: 512 * 1024 * 1024,
  });
  return { status: result.status, out: result.stdout ?? Buffer.alloc(0), err: String(result.stderr ?? "") };
}

// ---------------------------------------------------------------------------------------------------------
// Checking one commit
// ---------------------------------------------------------------------------------------------------------

// Reads the arguments of `git commit`: does it stage all tracked files, and does it name files to commit?
function commitOptions(args) {
  const takesValue = new Set([
    "--message", "--file", "--reuse-message", "--reedit-message", "--template", "--author", "--date", "--fixup",
    "--squash", "--cleanup", "--trailer",
  ]);
  const options = { all: false, paths: [], fromFile: false, dryRun: false };
  let onlyPaths = false;
  for (let i = 0; i < args.length; i++) {
    const text = args[i].text;
    if (onlyPaths) options.paths.push(args[i]);
    else if (text === "--") onlyPaths = true;
    else if (text === "--all") options.all = true;
    else if (text === "--dry-run" || text === "--help") options.dryRun = true;
    else if (text.startsWith("--pathspec-from-file")) options.fromFile = true;
    else if (takesValue.has(text)) i++;
    else if (text.startsWith("--")) continue;
    else if (text.startsWith("-") && text.length > 1) {
      // A group of one-letter options such as -am. The last one may take the next word as its value.
      const letters = text.slice(1);
      for (let k = 0; k < letters.length; k++) {
        if (letters[k] === "a") options.all = true;
        if ("mFCct".includes(letters[k])) {
          if (k === letters.length - 1) i++;
          break;
        }
        if ("Su".includes(letters[k])) break;
      }
    } else options.paths.push(args[i]);
  }
  return options;
}

// Returns the list of reasons this commit must not run. An empty list means it may.
function checkCommit(args, cwd, elsewhere, state, session) {
  const reasons = [];
  const cannotCheck = (why) => [
    `The guard reads the repository before the command starts, so it can't vouch for this \`git commit\`: ${why}. ` +
      "Before `git commit`, the same command may hold only `cd`, `git add`, `git status`, `git diff`, `git log`, " +
      "`git show`, `git switch -c <name>` or `git checkout -b <name>`. Run the rest as a separate command first, " +
      "then run `git commit`.",
  ];

  const options = commitOptions(args);
  if (options.dryRun) return reasons;
  if (elsewhere) return cannotCheck("it points git at another directory with --git-dir, --work-tree or a variable after -C");
  const top = toplevel(cwd);
  if (!top) return reasons; // not a repository; git will refuse the commit itself
  if (session.homeRepo && sharedGitDir(cwd) !== session.homeRepo) return reasons; // some other repository

  if (state.unknown) return cannotCheck(`it comes after ${state.unknown} in the same command`);
  if (options.fromFile || options.paths.some((word) => !word.literal)) {
    return cannotCheck("it names its files with a pattern, a variable or --pathspec-from-file");
  }
  for (const earlier of [...state.adds, ...(state.branch ? [state.branch] : [])]) {
    if (toplevel(earlier.cwd) !== top) return cannotCheck(`\`${earlier.shown}\` is aimed at a different repository`);
  }

  // Rule 1: no commit on a protected branch.
  const branch = state.branch
    ? state.branch.name
    : git(cwd, ["symbolic-ref", "--quiet", "--short", "HEAD"]).out.trim();
  if (PROTECTED_BRANCHES.includes(branch)) {
    reasons.push(
      `This commit would land on \`${branch}\`, and this repository takes no commits directly on ${branch}. ` +
        "Move to a branch with `git switch -c <branch-name>` (staged and unstaged changes come along), then commit. " +
        "The guard applies only to commands the agent runs, so if the person wants this commit on " +
        `${branch} they can make it themselves in a terminal.`,
    );
  }

  // Rule 2: every file in the commit is formatted with Prettier.
  // Work out what the commit will contain. Staging done by this same command is replayed in a copy of the index.
  let env = {};
  let scratch = null;
  try {
    if (state.adds.length || options.all || options.paths.length) {
      const realIndex = path.resolve(cwd, git(cwd, ["rev-parse", "--git-path", "index"]).out.trim());
      scratch = fs.mkdtempSync(path.join(os.tmpdir(), "commit-guard-"));
      const copy = path.join(scratch, "index");
      if (fs.existsSync(realIndex)) fs.copyFileSync(realIndex, copy);
      env = { GIT_INDEX_FILE: copy };
      for (const add of state.adds) {
        const result = git(add.cwd, ["add", ...add.args], { env });
        if (!result.ok) return cannotCheck(`\`${add.shown}\` could not be previewed (${firstLine(result.err)})`);
      }
      if (options.all) git(top, ["add", "--update"], { env });
      if (options.paths.length) git(cwd, ["add", "--", ...options.paths.map((word) => word.text)], { env });
    }

    // Added, copied and modified regular files, as `:oldmode newmode oldhash newhash status NUL path NUL`.
    const raw = git(top, ["diff", "--cached", "--raw", "-z", "--no-renames", "--no-abbrev", "--diff-filter=ACM"], { env });
    const fields = raw.out.split("\0");
    let files = [];
    for (let i = 0; i + 1 < fields.length; i += 2) {
      const [, mode, , hash] = fields[i].split(" ");
      if (mode.startsWith("100")) files.push({ path: fields[i + 1], hash });
    }
    // While a merge is being concluded, the other branch's files are not this commit's work. Keep only the
    // files that differ from both sides, which are the ones resolved or edited by hand.
    if (git(top, ["rev-parse", "--quiet", "--verify", "MERGE_HEAD"]).ok) {
      const names = git(top, ["diff", "--cached", "--name-only", "-z", "--no-renames", "MERGE_HEAD"], { env });
      const differsFromTheirs = new Set(names.out.split("\0"));
      files = files.filter((file) => differsFromTheirs.has(file.path));
    }
    if (!files.length) return reasons;

    const bin = findPrettier(cwd, top);
    if (!bin) {
      if (projectUsesPrettier(top)) {
        reasons.push(
          `Prettier is not installed in ${top} (there is no node_modules/prettier), so the files in this commit ` +
            "can't be checked. Run the project's install command, such as `npm install`, then commit.",
        );
      }
      return reasons;
    }

    // A file whose staged content differs from the file on disk is checked from the staged content.
    const changedOnDisk = new Set(git(top, ["diff", "--name-only", "-z", "--no-renames"], { env }).out.split("\0"));
    const unformatted = [];
    const errors = [];

    const fromDisk = files.filter((file) => !changedOnDisk.has(file.path)).map((file) => file.path);
    for (let i = 0; i < fromDisk.length; i += 100) {
      const batch = fromDisk.slice(i, i + 100).map((name) => (name.startsWith("-") ? `./${name}` : name));
      const result = prettier(bin, top, ["--list-different", "--ignore-unknown", "--no-error-on-unmatched-pattern", ...batch]);
      for (const line of result.out.toString().split("\n")) {
        if (line.trim()) unformatted.push({ path: line.trim().replace(/^\.\//, "") });
      }
      if (result.status !== 0 && result.status !== 1) errors.push(result.err.trim());
    }

    for (const file of files.filter((candidate) => changedOnDisk.has(candidate.path))) {
      let info = null;
      try {
        info = JSON.parse(prettier(bin, top, ["--file-info", file.path]).out.toString());
      } catch {
        // Prettier could not describe the file; treat it as one it doesn't format.
      }
      if (!info || info.ignored || !info.inferredParser) continue;
      const staged = git(top, ["cat-file", "blob", file.hash], { buffer: true }).out;
      const result = prettier(bin, top, ["--stdin-filepath", file.path], staged);
      if (result.status !== 0) errors.push(result.err.trim());
      else if (!result.out.equals(staged)) unformatted.push({ path: file.path, stagedOnly: true });
    }

    const shown = (name) => path.relative(realPath(session.cwd), path.join(realPath(top), name)) || name;
    const quoted = (name) => (/^[\w@%+=:,./-]+$/.test(name) ? name : `'${name.replace(/'/g, "'\\''")}'`);
    if (unformatted.length) {
      const names = unformatted.map((file) => quoted(shown(file.path))).join(" ");
      reasons.push(
        "These files in the commit are not formatted with Prettier:\n" +
          unformatted
            .map((file) => `  ${shown(file.path)}${file.stagedOnly ? "  (the staged version; the file on disk has changes that are not staged)" : ""}`)
            .join("\n") +
          `\nFormat them, stage the formatted versions, then commit:\n  npx prettier --write ${names}\n  git add ${names}`,
      );
    }
    if (errors.length) {
      reasons.push(
        "Prettier could not read some files in the commit:\n" +
          errors.join("\n").split("\n").slice(0, 20).map((line) => `  ${line}`).join("\n") +
          "\nFix what it reports, stage the files, then commit.",
      );
    }
    return reasons;
  } finally {
    if (scratch) fs.rmSync(scratch, { recursive: true, force: true });
  }
}

// ---------------------------------------------------------------------------------------------------------
// Walking the command
// ---------------------------------------------------------------------------------------------------------

const SKIPPED_FIRST_WORDS = new Set(["if", "then", "elif", "else", "do", "while", "until", "!", "time", "command", "exec", "nohup", "env", "builtin"]);
const SHELLS = new Set(["bash", "sh", "zsh", "dash"]);
const READ_ONLY_GIT = new Set(["status", "diff", "log", "show"]);

// Goes through the command in order, keeping track of the directory and of the staging and branch changes
// made so far, and checks each `git commit` it meets. `state.unknown` names the first earlier command whose
// effect the guard can't predict; a commit after it can't be checked.
function walk(source, state, session, depth = 0) {
  for (const allWords of splitCommands(dropHeredocBodies(source))) {
    if (state.reasons.length) return;
    let words = allWords;
    while (words.length && (SKIPPED_FIRST_WORDS.has(words[0].text) || /^[A-Za-z_]\w*=/.test(words[0].text))) {
      words = words.slice(1);
    }
    if (!words.length) continue;
    const shown = words.map((word) => word.text).join(" ").replace(/\s+/g, " ").slice(0, 80);
    const program = path.basename(words[0].text);
    const rest = words.slice(1);

    if (program === "cd") {
      if (!rest.length) state.cwd = os.homedir();
      else if (!rest[0].literal || rest[0].text === "-") state.unknown ??= `\`${shown}\` (a directory the guard can't work out)`;
      else state.cwd = path.resolve(state.cwd, rest[0].text);
    } else if (SHELLS.has(program) && rest.some((word) => /^-[a-z]*c$/.test(word.text)) && depth < 5) {
      const script = rest[rest.findIndex((word) => /^-[a-z]*c$/.test(word.text)) + 1];
      if (script) walk(script.text, state, session, depth + 1);
    } else if (program === "eval" && depth < 5) {
      walk(rest.map((word) => word.text).join(" "), state, session, depth + 1);
    } else if (program === "git") {
      gitCommand(rest, shown, state, session);
    } else {
      state.unknown ??= `\`${shown}\``;
    }
  }
}

function gitCommand(args, shown, state, session) {
  // Options that come before the subcommand, such as `git -C dir commit`.
  let cwd = state.cwd;
  let elsewhere = false;
  let i = 0;
  for (; i < args.length; i++) {
    const text = args[i].text;
    if (text === "-C") {
      const dir = args[++i];
      if (!dir || !dir.literal) elsewhere = true;
      else cwd = path.resolve(cwd, dir.text);
    } else if (text === "-c" || text === "--namespace" || text === "--config-env") {
      i++;
    } else if (/^--(git-dir|work-tree)/.test(text)) {
      elsewhere = true;
      if (!text.includes("=")) i++;
    } else if (!text.startsWith("-")) {
      break;
    }
  }
  const subcommand = args[i]?.text;
  const rest = args.slice(i + 1);
  if (!subcommand) return;

  if (subcommand === "commit") {
    state.reasons = checkCommit(rest, cwd, elsewhere, state, session);
    state.unknown ??= `\`${shown}\``; // a later commit in the same command starts from a state the guard can't see
  } else if (READ_ONLY_GIT.has(subcommand)) {
    // changes nothing
  } else if (elsewhere) {
    state.unknown ??= `\`${shown}\``;
  } else if (subcommand === "add") {
    const interactive = rest.some((word) => /^(-p|-i|-e|--patch|--interactive|--edit)$/.test(word.text));
    if (interactive) state.unknown ??= `\`${shown}\``;
    else if (rest.some((word) => !word.literal)) state.unknown ??= `\`${shown}\` (a pattern or variable the guard can't expand)`;
    else state.adds.push({ cwd, args: rest.map((word) => word.text), shown });
  } else if (subcommand === "switch" || subcommand === "checkout") {
    const creates = subcommand === "switch" ? ["-c", "-C", "--create", "--force-create"] : ["-b", "-B"];
    const name = rest[rest.findIndex((word) => creates.includes(word.text)) + 1];
    const created = rest.some((word) => creates.includes(word.text)) && name && name.literal && !name.text.startsWith("-");
    if (created) state.branch = { name: name.text, cwd, shown };
    else state.unknown ??= `\`${shown}\``;
  } else {
    state.unknown ??= `\`${shown}\``;
  }
}

// ---------------------------------------------------------------------------------------------------------

function main() {
  if (process.argv.includes("--help") || process.argv.includes("-h") || process.stdin.isTTY) {
    console.log(USAGE);
    return 0;
  }
  let call;
  try {
    call = JSON.parse(fs.readFileSync(0, "utf8"));
  } catch {
    return 0; // not a hook call
  }
  const command = call?.tool_input?.command;
  if ((call.tool_name && call.tool_name !== "Bash") || typeof command !== "string") return 0;
  if (!/\bgit\b/.test(command) || !/\bcommit\b/.test(command)) return 0;

  const cwd = typeof call.cwd === "string" ? call.cwd : process.cwd();
  // Null when this file is not inside a repository, as in a personal install. The guard then covers every repository.
  const homeRepo = sharedGitDir(path.dirname(fileURLToPath(import.meta.url)));
  const state = { cwd, adds: [], branch: null, unknown: null, reasons: [] };
  try {
    walk(command, state, { cwd, homeRepo });
  } catch (error) {
    state.reasons = [
      `The guard failed while checking this command (${error.message}). That is a fault in the guard, not in the ` +
        "commit. Tell the person, and leave the commit unmade until they have looked.",
    ];
  }
  if (!state.reasons.length) return 0;

  console.error(`Commit guard: the command was cancelled before any part of it ran.\n\n${state.reasons.join("\n\n")}`);
  return 2;
}

process.exitCode = main();
