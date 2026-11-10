#!/usr/bin/env node
// commit-guard: a Claude Code PreToolUse hook for the Bash tool.
//
// It reads the hook's JSON from stdin, and when the command contains a `git commit` it checks two rules:
//   1. The commit must not land on a protected branch (main and master, or COMMIT_GUARD_BRANCHES).
//   2. Every file the commit would contain must already be formatted with the project's own Prettier.
// Exit 0 lets the command run. Exit 2 blocks it, and Claude reads stderr as the reason.
// Exit 1 means the guard itself failed: the command still runs, and the person sees the error.
//
// The hook runs before the command starts, so it has to predict what the command will commit. It reads `git add`,
// `git commit -a`, pathspecs, `cd`, `git -C` and branch switches on the same command line. A formatter chained in
// front of the commit is not predicted: the files are checked as they are on disk right now.

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const PROTECTED = (process.env.COMMIT_GUARD_BRANCHES || 'main,master')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);

const MAX_BUFFER = 64 * 1024 * 1024;

// ---------------------------------------------------------------------------------------------------------------
// Shell reading. Splits a command line into simple commands, each a list of words. It understands quotes,
// $(...) and backticks, heredocs, redirections, and the separators ; & | && || ( ) and newline. It does not
// expand variables. It exists so that a commit message that mentions "git commit" or "&&" isn't read as a command.
// ---------------------------------------------------------------------------------------------------------------

export function parseShell(src) {
  const commands = [];
  const heredocs = [];
  let i = 0;

  const fail = (what) => {
    throw new Error(`could not read the shell command: ${what}`);
  };

  // Each reader below starts just after its opening quote and returns the text inside.
  function single() {
    const end = src.indexOf("'", i);
    if (end < 0) fail("unterminated '");
    const s = src.slice(i, end);
    i = end + 1;
    return s;
  }

  function ansiC() {
    let s = '';
    while (i < src.length) {
      const c = src[i];
      if (c === "'") {
        i++;
        return s;
      }
      if (c === '\\') {
        s += src[i + 1] ?? '';
        i += 2;
        continue;
      }
      s += c;
      i++;
    }
    fail("unterminated $'");
  }

  function double() {
    let s = '';
    while (i < src.length) {
      const c = src[i];
      if (c === '"') {
        i++;
        return s;
      }
      if (c === '\\') {
        s += src[i + 1] ?? '';
        i += 2;
        continue;
      }
      if (c === '$' || c === '`') {
        s += dollarOrTick();
        continue;
      }
      s += c;
      i++;
    }
    fail('unterminated "');
  }

  // Starts on a $ or a backtick. Returns the raw text it consumed. Commands inside a substitution are added to
  // `commands`, so a commit hidden in $(...) is still seen.
  function dollarOrTick() {
    const start = i;
    if (src[i] === '`') {
      i++;
      let inner = '';
      while (i < src.length && src[i] !== '`') {
        if (src[i] === '\\') {
          inner += src[i + 1] ?? '';
          i += 2;
        } else {
          inner += src[i++];
        }
      }
      if (i >= src.length) fail('unterminated `');
      i++;
      commands.push(...parseShell(inner));
      return src.slice(start, i);
    }
    if (src.startsWith('$((', i) && src.indexOf('))', i) >= 0) {
      i = src.indexOf('))', i) + 2;
      return src.slice(start, i);
    }
    if (src.startsWith('$(', i)) {
      i += 2;
      list(')');
      return src.slice(start, i);
    }
    if (src.startsWith('${', i)) {
      const end = src.indexOf('}', i);
      if (end < 0) fail('unterminated ${');
      i = end + 1;
      return src.slice(start, i);
    }
    i++;
    return '$';
  }

  // Starts just after <<. Records the delimiter; the body is skipped at the next newline.
  function heredocStart() {
    let stripTabs = false;
    if (src[i] === '-') {
      stripTabs = true;
      i++;
    }
    while (src[i] === ' ' || src[i] === '\t') i++;
    let delim = '';
    while (i < src.length && !/[\s;&|()<>]/.test(src[i])) {
      const c = src[i];
      if (c === "'") {
        i++;
        delim += single();
      } else if (c === '"') {
        const end = src.indexOf('"', i + 1);
        if (end < 0) fail('unterminated "');
        delim += src.slice(i + 1, end);
        i = end + 1;
      } else if (c === '\\') {
        delim += src[i + 1] ?? '';
        i += 2;
      } else {
        delim += c;
        i++;
      }
    }
    if (!delim) fail('heredoc without a delimiter');
    heredocs.push({ delim, stripTabs });
  }

  function skipHeredocBodies() {
    while (heredocs.length) {
      const { delim, stripTabs } = heredocs.shift();
      for (;;) {
        if (i >= src.length) return;
        let end = src.indexOf('\n', i);
        if (end < 0) end = src.length;
        let line = src.slice(i, end);
        i = Math.min(end + 1, src.length);
        if (stripTabs) line = line.replace(/^\t+/, '');
        if (line === delim) break;
      }
    }
  }

  function list(terminator) {
    let words = [];
    let word = null;
    let skipWord = false; // the next word is a redirection target, not an argument
    const endWord = () => {
      if (word === null) return;
      if (skipWord) skipWord = false;
      else words.push(word);
      word = null;
    };
    const endCommand = () => {
      endWord();
      skipWord = false;
      if (words.length) commands.push(words);
      words = [];
    };
    const add = (text) => {
      word = (word ?? '') + text;
    };

    while (i < src.length) {
      const c = src[i];
      if (c === terminator) {
        endCommand();
        i++;
        return;
      }
      if (c === ' ' || c === '\t') {
        endWord();
        i++;
      } else if (c === '\n') {
        endCommand();
        i++;
        skipHeredocBodies();
      } else if (c === '\\') {
        if (src[i + 1] !== '\n') add(src[i + 1] ?? '');
        i += 2;
      } else if (c === "'") {
        i++;
        add(single());
      } else if (c === '"') {
        i++;
        add(double());
      } else if (c === '$' && src[i + 1] === "'") {
        i += 2;
        add(ansiC());
      } else if (c === '$' || c === '`') {
        add(dollarOrTick());
      } else if (c === '#' && word === null) {
        while (i < src.length && src[i] !== '\n') i++;
      } else if (c === '&' && src[i + 1] === '>') {
        endWord();
        i++; // the > is read as a redirection on the next turn
      } else if (c === ';' || c === '&' || c === '|') {
        endCommand();
        i++;
      } else if (c === '(') {
        endCommand();
        i++;
        list(')');
      } else if (c === ')') {
        endCommand(); // a stray one, such as a case pattern
        i++;
      } else if (c === '<' || c === '>') {
        if (word !== null && /^\d+$/.test(word)) word = null; // a file descriptor, like the 2 in 2>&1
        endWord();
        if (src.startsWith('<<<', i)) {
          i += 3;
          skipWord = true;
        } else if (src.startsWith('<<', i)) {
          i += 2;
          heredocStart();
        } else if (src[i + 1] === '(') {
          i += 2;
          list(')'); // process substitution
        } else {
          i++;
          if (src[i] === '>') i++;
          if (src[i] === '&' || src[i] === '|') i++;
          skipWord = true;
        }
      } else {
        add(c);
        i++;
      }
    }
    endCommand();
    if (terminator) fail(`missing ${terminator}`);
  }

  list(null);
  return commands;
}

// ---------------------------------------------------------------------------------------------------------------
// From simple commands to the git steps that matter, each with the folder it would run in.
// ---------------------------------------------------------------------------------------------------------------

const PREFIX_WORDS = new Set([
  '{', '}', '!', 'if', 'then', 'elif', 'else', 'fi', 'do', 'done', 'while', 'until',
  'time', 'command', 'builtin', 'exec', 'nohup', 'env', 'sudo',
]);
const GIT_OPTIONS_WITH_VALUE = new Set(['-c', '--git-dir', '--work-tree', '--namespace', '--super-prefix', '--config-env']);
const SHELLS = new Set(['bash', 'sh', 'zsh', 'dash']);

const expandHome = (p) => (p === '~' ? os.homedir() : p.startsWith('~/') ? path.join(os.homedir(), p.slice(2)) : p);

export function gitSteps(command, cwd) {
  const steps = [];
  let dir = cwd;
  for (const raw of parseShell(command)) {
    let k = 0;
    while (k < raw.length && (PREFIX_WORDS.has(raw[k]) || /^[A-Za-z_]\w*=/.test(raw[k]))) k++;
    const w = raw.slice(k);
    if (!w.length) continue;
    const name = path.basename(w[0]);

    if (name === 'cd' || name === 'pushd') {
      const target = w.slice(1).find((a) => a === '-' || !a.startsWith('-'));
      // A target the guard can't work out (cd -, cd "$DIR") leaves the folder as it was.
      if (target === undefined) dir = os.homedir();
      else if (target !== '-' && !/[$`]/.test(target)) dir = path.resolve(dir, expandHome(target));
    } else if (name === 'git') {
      let j = 1;
      let gitDir = dir;
      while (j < w.length && w[j].startsWith('-')) {
        if (w[j] === '-C') {
          gitDir = path.resolve(gitDir, expandHome(w[j + 1] ?? '.'));
          j += 2;
        } else if (GIT_OPTIONS_WITH_VALUE.has(w[j])) {
          j += 2;
        } else {
          j += 1;
        }
      }
      if (j < w.length) steps.push({ sub: w[j], args: w.slice(j + 1), dir: gitDir });
    } else if (SHELLS.has(name)) {
      const c = w.findIndex((a, n) => n > 0 && /^-[a-z]*c[a-z]*$/.test(a));
      if (c > 0 && w[c + 1]) steps.push(...gitSteps(w[c + 1], dir));
    } else if (name === 'eval') {
      steps.push(...gitSteps(w.slice(1).join(' '), dir));
    }
  }
  return steps;
}

const COMMIT_SHORT_WITH_VALUE = 'mFCct';
const COMMIT_LONG_WITH_VALUE = new Set([
  '--message', '--file', '--reuse-message', '--reedit-message', '--author', '--date', '--template', '--cleanup',
  '--fixup', '--squash', '--trailer', '--pathspec-from-file',
]);

export function parseCommitArgs(args) {
  const out = { all: false, include: false, dryRun: false, pathspecs: [] };
  for (let k = 0; k < args.length; k++) {
    const a = args[k];
    if (a === '--') {
      out.pathspecs.push(...args.slice(k + 1));
      break;
    }
    if (a.startsWith('--')) {
      if (a === '--all') out.all = true;
      else if (a === '--include') out.include = true;
      else if (a === '--dry-run') out.dryRun = true;
      else if (COMMIT_LONG_WITH_VALUE.has(a)) k++;
    } else if (a.startsWith('-') && a.length > 1) {
      for (let j = 1; j < a.length; j++) {
        const flag = a[j];
        if (flag === 'a') out.all = true;
        else if (flag === 'i') out.include = true;
        else if (COMMIT_SHORT_WITH_VALUE.includes(flag)) {
          if (j === a.length - 1) k++; // the value is the next word
          break;
        } else if (flag === 'S' || flag === 'u') break; // the rest of the word is this flag's value
      }
    } else {
      out.pathspecs.push(a);
    }
  }
  return out;
}

function parseAddArgs(args) {
  const out = { all: false, update: false, force: false, dryRun: false, pathspecs: [] };
  for (let k = 0; k < args.length; k++) {
    const a = args[k];
    if (a === '--') {
      out.pathspecs.push(...args.slice(k + 1));
      break;
    }
    if (a.startsWith('--')) {
      if (a === '--all' || a === '--no-ignore-removal') out.all = true;
      else if (a === '--update') out.update = true;
      else if (a === '--force') out.force = true;
      else if (a === '--dry-run') out.dryRun = true;
    } else if (a.startsWith('-') && a.length > 1) {
      if (a.includes('A')) out.all = true;
      if (a.includes('u')) out.update = true;
      if (a.includes('f')) out.force = true;
      if (a.includes('n')) out.dryRun = true;
    } else {
      out.pathspecs.push(a);
    }
  }
  return out;
}

// The branch a step leaves the repository on, when that can be told from the words alone. `git checkout <word>`
// could be restoring a file, so it only counts when the word is a protected branch.
function branchAfter(step) {
  const a = step.args;
  const firstPlain = a.find((x) => !x.startsWith('-'));
  if (step.sub === 'switch') {
    const create = a.findIndex((x) => ['-c', '-C', '--create', '--force-create'].includes(x));
    if (create >= 0) return a[create + 1] ?? null;
    if (a.includes('--detach') || a.includes('-d') || a.includes('--orphan')) return null;
    return firstPlain ?? null;
  }
  if (step.sub === 'checkout') {
    if (a.includes('--')) return null;
    const create = a.findIndex((x) => x === '-b' || x === '-B');
    if (create >= 0) return a[create + 1] ?? null;
    return firstPlain && PROTECTED.includes(firstPlain) ? firstPlain : null;
  }
  return null;
}

// ---------------------------------------------------------------------------------------------------------------
// Git and Prettier helpers.
// ---------------------------------------------------------------------------------------------------------------

function git(args, cwd) {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8', maxBuffer: MAX_BUFFER });
  return { ok: r.status === 0, out: r.stdout ?? '' };
}

const names = (out) => out.split('\0').filter(Boolean);

function topLevel(dir) {
  const r = git(['rev-parse', '--show-toplevel'], dir);
  return r.ok ? path.resolve(r.out.trim()) : null;
}

// Git reports the top folder with symlinks resolved, so resolve `dir` the same way before comparing the two.
function isInside(dir, top) {
  try {
    const real = fs.realpathSync(dir);
    return real === top || real.startsWith(top + path.sep) ? real : null;
  } catch {
    return null;
  }
}

// The project's own Prettier, looked for in node_modules from `dir` up to the top of the repository. It stops
// there so a stray install higher up doesn't start formatting checks in a project that doesn't use Prettier.
function findPrettier(dir, top) {
  for (let d = dir; ; d = path.dirname(d)) {
    const pkgPath = path.join(d, 'node_modules', 'prettier', 'package.json');
    try {
      const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
      const bin = typeof pkg.bin === 'string' ? pkg.bin : pkg.bin?.prettier;
      if (bin) return path.resolve(path.dirname(pkgPath), bin);
    } catch {
      // not here; keep walking up
    }
    if (d === top || path.dirname(d) === d) return null;
  }
}

function usesPrettier(top) {
  try {
    if (fs.readdirSync(top).some((f) => f.startsWith('.prettierrc') || f.startsWith('prettier.config.'))) return true;
    const pkg = JSON.parse(fs.readFileSync(path.join(top, 'package.json'), 'utf8'));
    return Boolean(pkg.prettier || pkg.dependencies?.prettier || pkg.devDependencies?.prettier);
  } catch {
    return false;
  }
}

function runPrettier(bin, args, cwd, input) {
  return spawnSync(process.execPath, [bin, ...args], { cwd, input, encoding: 'utf8', maxBuffer: MAX_BUFFER, timeout: 60_000 });
}

const isRegularFile = (p) => {
  try {
    return fs.lstatSync(p).isFile();
  } catch {
    return false;
  }
};

const shellQuote = (s) => (/^[\w./@:+-]+$/.test(s) ? s : `'${s.replaceAll("'", `'\\''`)}'`);

// ---------------------------------------------------------------------------------------------------------------
// The two rules.
// ---------------------------------------------------------------------------------------------------------------

// Files a `git add` on the same command line would stage, relative to the top of the repository.
function filesAddWouldStage(step) {
  const opts = parseAddArgs(step.args);
  if (opts.dryRun) return [];
  const pathspecs = opts.pathspecs.length ? opts.pathspecs : opts.all || opts.update ? [':/'] : [];
  if (!pathspecs.length) return [];
  const which = opts.update ? ['-m'] : opts.force ? ['-m', '-o'] : ['-m', '-o', '--exclude-standard'];
  return names(git(['ls-files', '--full-name', '-z', ...which, '--', ...pathspecs], step.dir).out);
}

function checkCommit(step, state, problems, warnings) {
  const top = topLevel(step.dir);
  if (!top) return; // not a repository the guard can see; git will say so itself
  const opts = parseCommitArgs(step.args);
  if (opts.dryRun) return;

  // Rule 1: not on a protected branch. The first commit of a brand-new repository is let through, because there
  // is no other branch for it to go on yet.
  const predicted = state.branch.get(top);
  const branch = predicted ?? git(['symbolic-ref', '--short', '-q', 'HEAD'], top).out.trim();
  const hasHead = git(['rev-parse', '--verify', '-q', 'HEAD'], top).ok;
  if (PROTECTED.includes(branch) && (hasHead || predicted !== undefined)) {
    problems.push(
      [
        `This commit would land on \`${branch}\` in ${top}, and this team never commits to ${branch} directly.`,
        'Move to a branch first, as its own command. Staged and unstaged changes come along:',
        '  git switch -c <short-name-for-this-work>',
        'Then run the commit again.',
        state.sawOtherSwitch
          ? 'The guard checks the branch before the command starts, so a branch switch chained in front of the commit may not be seen. Run the switch as its own command.'
          : null,
        `If the person asked for a commit on ${branch} itself, don't look for another route. Tell them the guard stopped it, so they can make that commit themselves.`,
      ]
        .filter(Boolean)
        .join('\n'),
    );
  }

  // Rule 2: every file in the commit is Prettier-formatted. First work out which files, and whether the commit
  // takes each one from the index or from disk.
  let fromIndex = new Set(names(git(['diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z'], top).out));
  const fromDisk = new Set();
  if (opts.pathspecs.length) {
    // `git commit <paths>` commits those paths as they are on disk and, without --include, nothing else.
    const listed = hasHead
      ? git(['diff', '--name-only', '--diff-filter=ACMR', '-z', 'HEAD', '--', ...opts.pathspecs], step.dir)
      : git(['ls-files', '--full-name', '-z', '--', ...opts.pathspecs], step.dir);
    for (const f of names(listed.out)) fromDisk.add(f);
    if (!opts.include) fromIndex = new Set();
  }
  if (opts.all) {
    for (const f of names(git(['diff', '--name-only', '--diff-filter=ACMR', '-z'], top).out)) fromDisk.add(f);
  }
  for (const added of state.adds) {
    if (added.top === top) for (const f of added.files) fromDisk.add(f);
  }
  if (git(['rev-parse', '--verify', '-q', 'MERGE_HEAD'], top).ok) {
    // Concluding a merge: files that came over unchanged from the other branch aren't this commit's work.
    const differs = new Set(names(git(['diff', '--cached', '--name-only', '-z', 'MERGE_HEAD'], top).out));
    fromIndex = new Set([...fromIndex].filter((f) => differs.has(f)));
  }

  // A staged file with later edits on disk is checked as staged, through stdin. Everything else is checked on disk.
  const unstaged = new Set(names(git(['diff', '--name-only', '-z'], top).out));
  const onDisk = [...fromDisk];
  const asStaged = [];
  for (const f of fromIndex) {
    if (fromDisk.has(f)) continue;
    (unstaged.has(f) ? asStaged : onDisk).push(f);
  }
  const diskFiles = onDisk.filter((f) => isRegularFile(path.join(top, f)));
  if (!diskFiles.length && !asStaged.length) return;

  const prettier = findPrettier(isInside(step.dir, top) ?? top, top);
  if (!prettier) {
    if (usesPrettier(top)) {
      problems.push(
        [
          `This project uses Prettier, but it isn't installed under ${top} (no node_modules/prettier), so the commit can't be checked.`,
          "Install the project's dependencies with its package manager, then run the commit again.",
        ].join('\n'),
      );
    }
    return;
  }

  const unformatted = [];
  const errors = [];
  for (let n = 0; n < diskFiles.length; n += 100) {
    const r = runPrettier(prettier, ['--list-different', '--ignore-unknown', '--', ...diskFiles.slice(n, n + 100)], top);
    if (r.status === null) {
      warnings.push(`Prettier did not finish (${r.error?.message ?? r.signal}), so formatting was not checked.`);
      return;
    }
    for (const line of r.stdout.split('\n')) if (line.trim()) unformatted.push(line.trim());
    if (r.status > 1) errors.push(r.stderr.trim());
  }
  for (const f of asStaged) {
    const blob = spawnSync('git', ['show', `:${f}`], { cwd: top, maxBuffer: MAX_BUFFER });
    if (blob.status !== 0) continue;
    const staged = blob.stdout.toString('utf8');
    const r = runPrettier(prettier, ['--stdin-filepath', path.join(top, f)], top, staged);
    if (r.status === 0) {
      if (r.stdout !== staged) unformatted.push(`${f}  (the staged copy; the file on disk has later changes)`);
    } else if (r.status !== null && !/No parser could be inferred/i.test(r.stderr)) {
      errors.push(r.stderr.trim());
    }
  }

  if (unformatted.length) {
    const paths = unformatted.map((u) => shellQuote(u.split('  (')[0])).join(' ');
    problems.push(
      [
        `These files would be committed without Prettier formatting (paths from ${top}):`,
        ...unformatted.map((u) => `  ${u}`),
        'Format them, stage the result, then run the commit again:',
        `  npx prettier --write -- ${paths}`,
        `  git add -- ${paths}`,
        'Run Prettier as its own command, before the commit command. The guard checks the files as they are when the commit command starts, so Prettier chained in front of `git commit` on the same line comes too late.',
      ].join('\n'),
    );
  }
  if (errors.length) {
    problems.push(['Prettier could not check some of the files in this commit:', ...errors.map((e) => `  ${e.split('\n').slice(0, 20).join('\n  ')}`), 'Fix these, then run the commit again.'].join('\n'));
  }
}

// ---------------------------------------------------------------------------------------------------------------
// Entry point.
// ---------------------------------------------------------------------------------------------------------------

export function guard(input) {
  const problems = [];
  const warnings = [];
  const command = input?.tool_input?.command;
  if (input?.tool_name !== 'Bash' || typeof command !== 'string') return { problems, warnings };
  if (!/\bgit\b/.test(command) || !/\bcommit\b/.test(command)) return { problems, warnings };
  const cwd = input.cwd || process.cwd();

  let steps;
  try {
    steps = gitSteps(command, cwd);
  } catch {
    // The command is beyond this reader. If it looks like it commits, check the folder it starts in.
    const looksLikeCommit = /(^|[\s;&|(])git\s+([^\n;&|]*\s)?commit(\s|$)/.test(command);
    steps = looksLikeCommit ? [{ sub: 'commit', args: [], dir: cwd }] : [];
  }

  const state = { branch: new Map(), adds: [], sawOtherSwitch: false };
  for (const step of steps) {
    if (step.sub === 'checkout' || step.sub === 'switch') {
      const next = branchAfter(step);
      const top = next === null ? null : topLevel(step.dir);
      if (top) state.branch.set(top, next);
      else state.sawOtherSwitch = true;
    } else if (step.sub === 'add') {
      const top = topLevel(step.dir);
      if (top) state.adds.push({ top, files: filesAddWouldStage(step) });
    } else if (step.sub === 'commit') {
      checkCommit(step, state, problems, warnings);
    }
  }
  return { problems: [...new Set(problems)], warnings };
}

function main() {
  let input;
  try {
    input = JSON.parse(fs.readFileSync(0, 'utf8'));
  } catch {
    return 0; // not a hook call
  }
  const { problems, warnings } = guard(input);
  for (const w of warnings) process.stderr.write(`commit-guard: ${w}\n`);
  if (!problems.length) return warnings.length ? 1 : 0;
  process.stderr.write(`commit-guard blocked this commit.\n\n${problems.join('\n\n')}\n`);
  return 2;
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    process.exitCode = main();
  } catch (err) {
    process.stderr.write(`commit-guard: the guard itself failed, so this commit was not checked: ${err?.stack ?? err}\n`);
    process.exitCode = 1;
  }
}
