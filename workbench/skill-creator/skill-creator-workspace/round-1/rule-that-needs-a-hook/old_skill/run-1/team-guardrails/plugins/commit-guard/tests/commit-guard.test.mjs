// Tests for the commit-guard hook. Run from the plugin folder with: node --test
//
// Each test builds a throwaway git repository in the system temp folder and feeds the hook the JSON that
// Claude Code would send. Prettier is a small stand-in written into the repository's node_modules, so the tests
// need no install and no network. The stand-in calls a file unformatted when it contains the word UNFORMATTED,
// knows only .js, .ts, .json, .css and .md files, and fails to parse a file that contains SYNTAXERROR.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gitSteps, parseCommitArgs } from '../scripts/commit-guard.mjs';

const HOOK = fileURLToPath(new URL('../scripts/commit-guard.mjs', import.meta.url));

const FAKE_PRETTIER = `#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const args = process.argv.slice(2);
const known = (f) => ['.js', '.ts', '.json', '.css', '.md'].includes(path.extname(f));
const stdinAt = args.indexOf('--stdin-filepath');
if (stdinAt >= 0) {
  const file = args[stdinAt + 1];
  if (!known(file)) { console.error('[error] No parser could be inferred for file "' + file + '".'); process.exit(2); }
  process.stdout.write(fs.readFileSync(0, 'utf8').replaceAll('UNFORMATTED', 'formatted'));
} else {
  let code = 0;
  for (const f of args.slice(args.indexOf('--') + 1)) {
    if (!known(f)) continue;
    const text = fs.readFileSync(f, 'utf8');
    if (text.includes('SYNTAXERROR')) { console.error('[error] ' + f + ': SyntaxError: Unexpected token'); code = 2; }
    else if (text.includes('UNFORMATTED')) { console.log(f); code = Math.max(code, 1); }
  }
  process.exit(code);
}
`;

function makeRepo({ prettier = true, firstCommit = true } = {}) {
  const dir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'commit-guard-')));
  const git = (...args) => execFileSync('git', args, { cwd: dir, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  const write = (file, text) => {
    fs.mkdirSync(path.dirname(path.join(dir, file)), { recursive: true });
    fs.writeFileSync(path.join(dir, file), text);
  };
  git('init', '-q', '-b', 'main');
  git('config', 'user.email', 'test@example.com');
  git('config', 'user.name', 'Test');
  git('config', 'commit.gpgsign', 'false');
  write('.gitignore', 'node_modules\n');
  if (prettier) {
    write('package.json', JSON.stringify({ name: 'fixture', devDependencies: { prettier: '^3.0.0' } }));
    write('node_modules/prettier/package.json', JSON.stringify({ name: 'prettier', version: '0.0.0', bin: './bin/prettier.cjs' }));
    write('node_modules/prettier/bin/prettier.cjs', FAKE_PRETTIER);
  }
  if (firstCommit) {
    write('README.md', 'fixture\n');
    git('add', '-A');
    git('commit', '-q', '-m', 'first');
  }
  return { dir, git, write };
}

// Runs the hook the way Claude Code does and returns its exit code and stderr.
function hook(repo, command, { cwd = repo.dir, env = {} } = {}) {
  const input = JSON.stringify({ hook_event_name: 'PreToolUse', tool_name: 'Bash', cwd, tool_input: { command } });
  const r = spawnSync(process.execPath, [HOOK], { input, encoding: 'utf8', env: { ...process.env, ...env } });
  return { code: r.status, stderr: r.stderr };
}

const HEREDOC_COMMIT = `git commit -m "$(cat <<'EOF'
Explain why "git commit" && friends aren't commands here

It's a message; don't read (this) as shell.
EOF
)"`;

// --- Reading the command line ---

test('a heredoc commit message is one commit, whatever the message says', () => {
  const steps = gitSteps(HEREDOC_COMMIT, '/repo');
  assert.equal(steps.length, 1);
  assert.equal(steps[0].sub, 'commit');
  assert.equal(steps[0].args[0], '-m');
});

test('add and commit on one line are two steps, and redirections are not arguments', () => {
  const steps = gitSteps('git add a.js "b c.js" && git commit -m "x" 2>&1 | tail -5', '/repo');
  assert.deepEqual(steps.map((s) => s.sub), ['add', 'commit']);
  assert.deepEqual(steps[0].args, ['a.js', 'b c.js']);
  assert.deepEqual(steps[1].args, ['-m', 'x']);
});

test('cd and git -C set the folder the commit runs in', () => {
  assert.equal(gitSteps('cd packages/web && git commit -m x', '/repo')[0].dir, path.resolve('/repo/packages/web'));
  assert.equal(gitSteps('git -C ../other commit -m x', '/repo')[0].dir, path.resolve('/other'));
  assert.equal(gitSteps('FOO=1 git -c user.name=x commit -m x', '/repo')[0].sub, 'commit');
  assert.equal(gitSteps('bash -c "git commit -m x"', '/repo')[0].sub, 'commit');
});

test('text that only mentions a commit is not a commit', () => {
  for (const command of [
    'echo "git commit -m x"',
    "grep -rn 'git commit' docs/",
    'git log --grep commit',
    'gh pr create --title "fix" --body "run git commit after this"',
    'git show HEAD # then git commit',
  ]) {
    assert.equal(gitSteps(command, '/repo').filter((s) => s.sub === 'commit').length, 0, command);
  }
});

test('commit options are read for -a and pathspecs', () => {
  assert.deepEqual(parseCommitArgs(['-am', 'msg']), { all: true, include: false, dryRun: false, pathspecs: [] });
  assert.deepEqual(parseCommitArgs(['-m', 'msg', 'src/a.js']).pathspecs, ['src/a.js']);
  assert.deepEqual(parseCommitArgs(['-m', 'msg', '--', 'a.js', 'b.js']).pathspecs, ['a.js', 'b.js']);
  assert.deepEqual(parseCommitArgs(['--author', 'A <a@b.c>', '-F', 'msg.txt']).pathspecs, []);
});

// --- Rule 1: no commits on main ---

test('a commit on main is blocked', () => {
  const repo = makeRepo();
  repo.write('a.js', 'ok\n');
  repo.git('add', 'a.js');
  const r = hook(repo, HEREDOC_COMMIT);
  assert.equal(r.code, 2);
  assert.match(r.stderr, /would land on `main`/);
  assert.match(r.stderr, /git switch -c/);
});

test('a commit on another branch passes', () => {
  const repo = makeRepo();
  repo.git('switch', '-q', '-c', 'feature');
  repo.write('a.js', 'ok\n');
  repo.git('add', 'a.js');
  assert.equal(hook(repo, HEREDOC_COMMIT).code, 0);
});

test('a branch made on the same line counts, and a switch back to main is caught', () => {
  const repo = makeRepo();
  assert.equal(hook(repo, 'git checkout -b feature && git commit --allow-empty -m x').code, 0);
  assert.equal(hook(repo, 'git switch -c feature && git commit --allow-empty -m x').code, 0);
  repo.git('switch', '-q', '-c', 'feature');
  assert.equal(hook(repo, 'git checkout main && git commit --allow-empty -m x').code, 2);
  assert.equal(hook(repo, 'git switch main; git commit --allow-empty -m x').code, 2);
});

test('the commit is judged in the repository it targets, not the session folder', () => {
  const onMain = makeRepo();
  const onFeature = makeRepo();
  onFeature.git('switch', '-q', '-c', 'feature');
  assert.equal(hook(onFeature, `git -C ${onMain.dir} commit --allow-empty -m x`).code, 2);
  assert.equal(hook(onFeature, `cd ${onMain.dir} && git commit --allow-empty -m x`).code, 2);
  assert.equal(hook(onMain, `git -C ${onFeature.dir} commit --allow-empty -m x`).code, 0);
});

test('the first commit of a new repository, a detached HEAD and a dry run pass', () => {
  const fresh = makeRepo({ firstCommit: false });
  assert.equal(hook(fresh, 'git add -A && git commit -m first').code, 0);
  const repo = makeRepo();
  assert.equal(hook(repo, 'git commit --dry-run').code, 0);
  repo.git('checkout', '-q', '--detach');
  assert.equal(hook(repo, 'git commit --allow-empty -m x').code, 0);
});

test('COMMIT_GUARD_BRANCHES replaces the protected list', () => {
  const repo = makeRepo();
  repo.git('switch', '-q', '-c', 'release');
  const env = { COMMIT_GUARD_BRANCHES: 'main, release' };
  assert.equal(hook(repo, 'git commit --allow-empty -m x', { env }).code, 2);
  assert.equal(hook(repo, 'git commit --allow-empty -m x').code, 0);
});

test('commands that are not commits pass without a look', () => {
  const repo = makeRepo();
  assert.equal(hook(repo, 'git status').code, 0);
  assert.equal(hook(repo, 'echo "git commit"').code, 0);
  assert.equal(hook(repo, 'npm test').code, 0);
});

// --- Rule 2: Prettier-formatted files only ---

function featureRepo(options) {
  const repo = makeRepo(options);
  repo.git('switch', '-q', '-c', 'feature');
  return repo;
}

test('a staged unformatted file blocks the commit and is named', () => {
  const repo = featureRepo();
  repo.write('src/a.js', 'UNFORMATTED\n');
  repo.write('src/b.js', 'ok\n');
  repo.git('add', '-A');
  const r = hook(repo, 'git commit -m x');
  assert.equal(r.code, 2);
  assert.match(r.stderr, /src\/a\.js/);
  assert.doesNotMatch(r.stderr, /src\/b\.js/);
  assert.match(r.stderr, /npx prettier --write -- src\/a\.js/);
});

test('formatted files, unknown file types and unstaged mess pass', () => {
  const repo = featureRepo();
  repo.write('a.js', 'ok\n');
  repo.write('logo.png', 'UNFORMATTED\n');
  repo.git('add', '-A');
  repo.write('not-staged.js', 'UNFORMATTED\n');
  assert.equal(hook(repo, 'git commit -m x').code, 0);
});

test('git add on the same line is counted', () => {
  const repo = featureRepo();
  repo.write('new.js', 'UNFORMATTED\n');
  repo.write('other.js', 'UNFORMATTED\n');
  const named = hook(repo, 'git add new.js && git commit -m x');
  assert.equal(named.code, 2);
  assert.match(named.stderr, /new\.js/);
  assert.doesNotMatch(named.stderr, /other\.js/);
  assert.match(hook(repo, 'git add -A && git commit -m x').stderr, /other\.js/);
  assert.match(hook(repo, 'git add . && git commit -m x').stderr, /other\.js/);
  repo.write('new.js', 'ok\n');
  assert.equal(hook(repo, 'git add new.js && git commit -m x').code, 0);
});

test('git commit -a checks tracked files as they are on disk', () => {
  const repo = featureRepo();
  repo.write('a.js', 'ok\n');
  repo.git('add', '-A');
  repo.git('commit', '-q', '-m', 'add a');
  repo.write('a.js', 'UNFORMATTED\n');
  assert.equal(hook(repo, 'git commit -m x --allow-empty').code, 0);
  assert.equal(hook(repo, 'git commit -am x').code, 2);
  assert.equal(hook(repo, 'git commit --all -m x').code, 2);
});

test('a staged copy that was formatted on disk but not staged again is caught', () => {
  const repo = featureRepo();
  repo.write('a.js', 'UNFORMATTED\n');
  repo.git('add', 'a.js');
  repo.write('a.js', 'formatted\n');
  const r = hook(repo, 'git commit -m x');
  assert.equal(r.code, 2);
  assert.match(r.stderr, /a\.js {2}\(the staged copy/);
});

test('a formatted staged copy passes even when the file on disk has later unformatted edits', () => {
  const repo = featureRepo();
  repo.write('a.js', 'ok\n');
  repo.git('add', 'a.js');
  repo.write('a.js', 'ok\nUNFORMATTED\n');
  assert.equal(hook(repo, 'git commit -m x').code, 0);
});

test('a pathspec commit checks only the paths it names', () => {
  const repo = featureRepo();
  repo.write('a.js', 'ok\n');
  repo.write('b.js', 'UNFORMATTED\n');
  repo.git('add', '-A');
  assert.equal(hook(repo, 'git commit -m x -- a.js').code, 0);
  assert.equal(hook(repo, 'git commit -m x b.js').code, 2);
});

test('a commit from a subfolder finds the files and the root Prettier', () => {
  const repo = featureRepo();
  repo.write('packages/web/a.js', 'UNFORMATTED\n');
  const r = hook(repo, 'git add a.js && git commit -m x', { cwd: path.join(repo.dir, 'packages/web') });
  assert.equal(r.code, 2);
  assert.match(r.stderr, /packages\/web\/a\.js/);
});

test('a file Prettier cannot parse blocks the commit with its error', () => {
  const repo = featureRepo();
  repo.write('a.js', 'SYNTAXERROR\n');
  repo.git('add', 'a.js');
  const r = hook(repo, 'git commit -m x');
  assert.equal(r.code, 2);
  assert.match(r.stderr, /could not check/);
});

test('concluding a merge skips files that came over unchanged from the other branch', () => {
  const repo = makeRepo();
  repo.write('theirs.js', 'UNFORMATTED\n');
  repo.git('add', '-A');
  repo.git('commit', '-q', '-m', 'unformatted on main');
  repo.git('switch', '-q', '-c', 'feature', 'HEAD~1');
  repo.write('mine.js', 'ok\n');
  repo.git('add', '-A');
  repo.git('commit', '-q', '-m', 'mine');
  repo.git('merge', '-q', '--no-commit', '--no-ff', 'main');
  assert.equal(hook(repo, 'git commit -m merge').code, 0);
});

test('a project without Prettier is not checked, and one with Prettier missing is blocked', () => {
  const plain = featureRepo({ prettier: false });
  plain.write('a.js', 'UNFORMATTED\n');
  plain.git('add', '-A');
  assert.equal(hook(plain, 'git commit -m x').code, 0);

  const missing = featureRepo();
  fs.rmSync(path.join(missing.dir, 'node_modules'), { recursive: true });
  missing.write('a.js', 'ok\n');
  missing.git('add', '-A');
  const r = hook(missing, 'git commit -m x');
  assert.equal(r.code, 2);
  assert.match(r.stderr, /isn't installed/);
});

test('both rules are reported together', () => {
  const repo = makeRepo();
  repo.write('a.js', 'UNFORMATTED\n');
  repo.git('add', '-A');
  const r = hook(repo, 'git commit -m x');
  assert.equal(r.code, 2);
  assert.match(r.stderr, /would land on `main`/);
  assert.match(r.stderr, /without Prettier formatting/);
});
