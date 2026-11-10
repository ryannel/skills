#!/usr/bin/env node
// Checks the commit-guard skill's two scripts against throwaway git repositories.
//
//   npm install      once, to fetch the pinned Prettier
//   node run.mjs     prints one line per case and exits 1 if any case fails
//
// Each case builds a small repository under ./tmp with the skill copied into .claude/skills/commit-guard,
// hands guard.mjs the JSON Claude Code would send for a Bash command, and compares the exit code (0 lets the
// command run, 2 cancels it) and the message. Nothing is ever committed by the guard; the cases only stage.

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const skill = path.resolve(here, "..", "commit-guard");
const tmp = path.join(here, "tmp");
const env = {
  ...process.env,
  GIT_CONFIG_GLOBAL: "/dev/null",
  GIT_CONFIG_NOSYSTEM: "1",
  GIT_AUTHOR_NAME: "Test",
  GIT_AUTHOR_EMAIL: "test@example.com",
  GIT_COMMITTER_NAME: "Test",
  GIT_COMMITTER_EMAIL: "test@example.com",
};
const GOOD = "const a = 1;\n";
const BAD = "const   a=1\n";

if (!fs.existsSync(path.join(here, "node_modules", "prettier"))) {
  console.error("Prettier is missing. Run `npm install` in this folder first.");
  process.exit(1);
}

function sh(cwd, script) {
  const result = spawnSync("bash", ["-c", script], { cwd, env, encoding: "utf8" });
  if (result.status !== 0) throw new Error(`setup failed: ${script}\n${result.stderr}`);
  return result.stdout.trim();
}

let count = 0;
// Makes a repository on `main` with one commit. Options: guard (copy the skill in), prettier ("installed",
// "listed" in package.json only, or "none").
function repo({ guard = true, prettier = "installed", branch = "feature" } = {}) {
  const dir = path.join(tmp, `repo-${++count}`);
  fs.mkdirSync(dir, { recursive: true });
  sh(dir, "git init -q -b main");
  fs.writeFileSync(path.join(dir, ".gitignore"), "node_modules\n");
  if (prettier !== "none") {
    fs.writeFileSync(path.join(dir, "package.json"), '{ "devDependencies": { "prettier": "3.6.2" } }\n');
  }
  if (prettier === "installed") fs.symlinkSync(path.join(here, "node_modules"), path.join(dir, "node_modules"));
  if (guard) fs.cpSync(skill, path.join(dir, ".claude", "skills", "commit-guard"), { recursive: true });
  sh(dir, "git add -A && git commit -q -m init");
  if (branch !== "main") sh(dir, `git switch -q -c ${branch}`);
  return dir;
}

function write(dir, name, content) {
  fs.mkdirSync(path.dirname(path.join(dir, name)), { recursive: true });
  fs.writeFileSync(path.join(dir, name), content);
}

// Runs the guard as Claude Code would. `guardIn` is the repository whose copy of the guard is used.
function guard(guardIn, cwd, command) {
  const script = path.join(guardIn, ".claude", "skills", "commit-guard", "scripts", "guard.mjs");
  const result = spawnSync("node", [script], {
    env,
    encoding: "utf8",
    input: JSON.stringify({ hook_event_name: "PreToolUse", tool_name: "Bash", cwd, tool_input: { command } }),
  });
  return { code: result.status, message: result.stderr };
}

let failed = 0;
function expect(name, result, code, ...patterns) {
  const problems = [];
  if (result.code !== code) problems.push(`exit code ${result.code}, expected ${code}`);
  for (const pattern of patterns) {
    if (!pattern.test(result.message)) problems.push(`message does not match ${pattern}`);
  }
  if (problems.length) failed++;
  console.log(`${problems.length ? "FAIL" : "ok  "}  ${name}`);
  for (const problem of problems) console.log(`        ${problem}\n        message: ${result.message.trim().replace(/\n/g, "\n                 ")}`);
}

fs.rmSync(tmp, { recursive: true, force: true });
const HEREDOC = `git commit -m "$(cat <<'EOF'\nDon't break "quotes" (or parens\n\ngit add && git commit on main\nEOF\n)"`;

// --- The branch rule -------------------------------------------------------------------------------------
{
  const r = repo({ branch: "main" });
  write(r, "a.js", GOOD);
  sh(r, "git add a.js");
  expect("main: plain commit is cancelled", guard(r, r, 'git commit -m "x"'), 2, /would land on `main`/);
  expect("main: commit with a here-document message is cancelled", guard(r, r, HEREDOC), 2, /would land on `main`/);
  expect("main: cd into a subfolder then commit is cancelled", guard(r, r, "cd .claude && git commit -m x"), 2, /`main`/);
  expect("main: git -C <repo> commit from elsewhere is cancelled", guard(r, tmp, `git -C ${r} commit -m x`), 2, /`main`/);
  expect("main: bash -c 'git commit' is cancelled", guard(r, r, `bash -c 'git commit -m x'`), 2, /`main`/);
  expect("main: commit piped to tail is cancelled", guard(r, r, "git commit -m x 2>&1 | tail -5"), 2, /`main`/);
  expect("main: --amend is cancelled", guard(r, r, "git commit --amend --no-edit"), 2, /`main`/);
  expect("main: new branch, add and commit in one command is allowed", guard(r, r, "git checkout -b fix/typo && git add a.js && git commit -m x"), 0);
  expect("main: git switch -c then commit is allowed", guard(r, r, "git switch -c fix && git commit -m x"), 0);
  expect("main: git commit --dry-run is allowed", guard(r, r, "git commit --dry-run"), 0);
  expect("main: a command that only mentions git commit is allowed", guard(r, r, 'grep -rn "git commit" docs/ ; echo git commit'), 0);
  expect("main: other git commands are allowed", guard(r, r, "git status && git log --oneline -3 && git push"), 0);
  expect("main: a non-git command is allowed", guard(r, r, "npm test"), 0);
  sh(r, "git checkout -q --detach");
  expect("detached HEAD: commit is allowed", guard(r, r, "git commit -m x"), 0);
}
{
  const r = path.join(tmp, `repo-${++count}`);
  fs.mkdirSync(r, { recursive: true });
  sh(r, "git init -q -b main");
  fs.cpSync(skill, path.join(r, ".claude", "skills", "commit-guard"), { recursive: true });
  sh(r, "git add -A");
  expect("new repository with no commits yet, on main: cancelled", guard(r, r, "git commit -m first"), 2, /`main`/);
  expect("new repository with no commits yet, new branch first: allowed", guard(r, r, "git switch -c setup && git commit -m first"), 0);
}
{
  const r = repo();
  expect("feature: switching back to main and committing can't be checked", guard(r, r, "git checkout main && git commit -m x"), 2, /comes after `git checkout main`/);
  expect("feature: git switch -c main then commit is cancelled", guard(r, r, "git switch -c main && git commit -m x"), 2, /would land on `main`/);
}

// --- The Prettier rule -----------------------------------------------------------------------------------
{
  const r = repo();
  write(r, "src/good.js", GOOD);
  write(r, "src/bad.js", BAD);
  write(r, "notes.txt", "free   text\n");
  write(r, "data.bin", "\u0000\u0001");
  sh(r, "git add src/good.js notes.txt data.bin");
  expect("feature: formatted files and files Prettier doesn't handle are allowed", guard(r, r, 'git commit -m "x"'), 0);
  expect("feature: here-document message is allowed", guard(r, r, HEREDOC), 0);
  expect("feature: commit followed by other commands is allowed", guard(r, r, "git commit -m x && git status && git push -u origin feature"), 0);
  expect("feature: unformatted file on disk but not in the commit is allowed", guard(r, r, "git commit -m x"), 0);
  expect("feature: add of an unformatted file and commit in one command is cancelled", guard(r, r, "git add src/bad.js && git commit -m x"), 2, /not formatted with Prettier:\n {2}src\/bad\.js\n/, /npx prettier --write src\/bad\.js\n {2}git add src\/bad\.js/);
  expect("feature: git add -A && commit is cancelled", guard(r, r, "git add -A && git commit -m x"), 2, /src\/bad\.js/);
  expect("feature: git add . from a subfolder, paths shown from the session folder", guard(r, path.join(r, "src"), "git add . && git commit -m x"), 2, /\n {2}bad\.js\n/);
  expect("feature: previewing git add left the real index alone", { code: sh(r, "git diff --cached --name-only").includes("bad.js") ? 1 : 0, message: "" }, 0);
  expect("feature: commit naming an unstaged unformatted file is cancelled", guard(r, r, "git commit src/bad.js -m x"), 2, /src\/bad\.js/);
  expect("feature: git add with a pattern can't be previewed", guard(r, r, "git add src/*.js && git commit -m x"), 2, /pattern or variable/);
  expect("feature: commit after an unrelated command can't be checked", guard(r, r, "npx prettier --write . && git commit -m x"), 2, /comes after `npx prettier --write \.`/);
  expect("feature: two commits in one command can't both be checked", guard(r, r, "git commit -m a && git add src/bad.js && git commit -m b"), 2, /comes after `git commit -m a`/);
  sh(r, "git add src/bad.js");
  expect("feature: staged unformatted file is cancelled", guard(r, r, "git commit -m x"), 2, /src\/bad\.js/);
  write(r, "src/bad.js", GOOD);
  expect("feature: formatted on disk but staged unformatted is cancelled", guard(r, r, "git commit -m x"), 2, /src\/bad\.js {2}\(the staged version/);
  expect("feature: the same, re-staged in the commit command, is allowed", guard(r, r, "git add src/bad.js && git commit -m x"), 0);
  sh(r, "git add src/bad.js");
  write(r, "src/bad.js", BAD);
  expect("feature: staged formatted, later unformatted edits left unstaged, is allowed", guard(r, r, "git commit -m x"), 0);
  expect("feature: the same with commit -am is cancelled", guard(r, r, "git commit -am x"), 2, /src\/bad\.js/);
  expect("feature: the same with commit --all is cancelled", guard(r, r, "git commit --all -m x"), 2, /src\/bad\.js/);
}
{
  const r = repo();
  write(r, ".prettierignore", "generated/\n");
  write(r, "generated/out.js", BAD);
  write(r, "app/[id]/my page.tsx", BAD);
  write(r, "broken.js", "const = ;\n");
  sh(r, "git add .prettierignore generated");
  expect("feature: a file in .prettierignore is allowed", guard(r, r, "git commit -m x"), 0);
  expect("feature: a path with brackets and a space is reported and quoted", guard(r, r, `git add "app/[id]/my page.tsx" && git commit -m x`), 2, /npx prettier --write 'app\/\[id\]\/my page\.tsx'/);
  expect("feature: a file Prettier can't parse is cancelled with its error", guard(r, r, "git add broken.js && git commit -m x"), 2, /could not read some files[\s\S]*broken\.js: SyntaxError/);
}
{
  const r = repo({ prettier: "listed" });
  write(r, "a.js", BAD);
  sh(r, "git add a.js");
  expect("feature: Prettier listed in package.json but not installed is cancelled", guard(r, r, "git commit -m x"), 2, /Prettier is not installed/);
}
{
  const r = repo({ prettier: "none" });
  write(r, "a.js", BAD);
  sh(r, "git add a.js");
  expect("feature: a repository with no sign of Prettier is allowed", guard(r, r, "git commit -m x"), 0);
}
{
  // A merge with a conflict: main's unformatted file comes in untouched, the conflicted file is resolved by hand.
  const r = repo({ branch: "main" });
  write(r, "shared.js", "const a = 1;\n");
  sh(r, "git add shared.js && git commit -q -m base && git switch -q -c feature");
  write(r, "shared.js", "const a = 2;\n");
  sh(r, "git commit -q -am feature && git switch -q main");
  write(r, "shared.js", "const a = 3;\n");
  write(r, "from-main.js", BAD);
  sh(r, "git add -A && git commit -q -m main && git switch -q feature && (git merge main >/dev/null 2>&1 || true)");
  write(r, "shared.js", "const a = 4;\n");
  expect("merge: resolved file formatted, incoming unformatted file not counted, is allowed", guard(r, r, "git add shared.js && git commit --no-edit"), 0);
  write(r, "shared.js", "const   a=4\n");
  expect("merge: resolved file unformatted is cancelled, incoming file not listed", guard(r, r, "git add shared.js && git commit --no-edit"), 2, /\n {2}shared\.js\n/, /^(?![\s\S]*from-main)/);
}

// --- Which repositories the guard covers -----------------------------------------------------------------
{
  const home = repo();
  const other = repo({ guard: false, branch: "main" });
  write(other, "a.js", BAD);
  sh(other, "git add a.js");
  expect("another repository: commit on main with unformatted files is allowed", guard(home, other, "git commit -m x"), 0);
  expect("another repository reached with cd: allowed", guard(home, home, `cd ${other} && git commit -m x`), 0);
  const worktree = path.join(tmp, "worktree-1");
  sh(home, `git worktree add -q ${worktree} -b in-worktree`);
  fs.symlinkSync(path.join(here, "node_modules"), path.join(worktree, "node_modules"));
  write(worktree, "a.js", BAD);
  sh(worktree, "git add a.js");
  expect("a worktree of the guarded repository: unformatted commit is cancelled", guard(home, worktree, "git commit -m x"), 2, /a\.js/);
  expect("outside any repository: allowed", guard(home, "/", "git commit -m x"), 0);
}

// --- setup.mjs -------------------------------------------------------------------------------------------
{
  const r = repo();
  const setup = (...args) => spawnSync("node", [path.join(r, ".claude/skills/commit-guard/scripts/setup.mjs"), ...args], { env, encoding: "utf8", cwd: "/" });
  const settingsPath = path.join(r, ".claude", "settings.json");
  const wanted = 'node "$CLAUDE_PROJECT_DIR/.claude/skills/commit-guard/scripts/guard.mjs"';
  const commands = () => JSON.parse(fs.readFileSync(settingsPath, "utf8")).hooks.PreToolUse.flatMap((group) => group.hooks.map((hook) => hook.command));

  let result = setup("--dry-run");
  expect("setup --dry-run writes nothing", { code: result.status || (fs.existsSync(settingsPath) ? 1 : 0), message: result.stdout }, 0, /would add the hook/);
  write(r, ".claude/settings.json", JSON.stringify({ permissions: { allow: ["Bash(npm test)"] }, hooks: { PreToolUse: [{ matcher: "Edit", hooks: [{ type: "command", command: "echo hi" }] }] } }));
  result = setup();
  const kept = JSON.parse(fs.readFileSync(settingsPath, "utf8"));
  expect("setup adds the hook and keeps what was there", { code: result.status || (kept.permissions.allow[0] === "Bash(npm test)" && commands().join("|") === `echo hi|${wanted}` ? 0 : 1), message: result.stdout }, 0, /added the hook/);
  result = setup();
  expect("setup run twice adds nothing", { code: result.status || (commands().length === 2 ? 0 : 1), message: result.stdout }, 0, /already registered/);
  write(r, ".claude/settings.json", "{ not json");
  result = setup();
  expect("setup leaves a broken settings file alone", { code: result.status, message: result.stderr }, 1, /not valid JSON/);
  const hookCommand = wanted.replace("$CLAUDE_PROJECT_DIR", r);
  const viaShell = spawnSync("bash", ["-c", hookCommand], { env, encoding: "utf8", input: JSON.stringify({ tool_name: "Bash", cwd: r, tool_input: { command: "git commit -m x" } }) });
  expect("the registered command runs the guard", { code: viaShell.status, message: viaShell.stderr }, 0);
}

fs.rmSync(tmp, { recursive: true, force: true });
console.log(failed ? `\n${failed} case(s) failed` : "\nall cases passed");
process.exit(failed ? 1 : 0);
