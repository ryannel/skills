#!/usr/bin/env node
// Registers the commit guard as a Claude Code hook for the repository this skill is installed in.
//
// It adds one PreToolUse entry for the Bash tool to <repository>/.claude/settings.json, the settings file that
// is committed and shared with the team, and leaves everything else in that file as it was. Running it again
// changes nothing.

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const USAGE = `Registers the commit guard in this repository's .claude/settings.json.

Usage:
  node setup.mjs            add the hook, if it is not there yet
  node setup.mjs --dry-run  print what would be written, and write nothing

The skill's folder must be inside the repository, normally at .claude/skills/commit-guard.
Prints a JSON summary on standard output. Commit .claude/settings.json afterwards so the team gets the hook.`;

function fail(message) {
  console.error(message);
  process.exit(1);
}

const args = process.argv.slice(2);
if (args.includes("--help") || args.includes("-h")) {
  console.log(USAGE);
  process.exit(0);
}
const unknown = args.filter((arg) => arg !== "--dry-run");
if (unknown.length) fail(`Unknown argument: ${unknown.join(" ")}. Expected nothing or --dry-run.\n\n${USAGE}`);
const dryRun = args.includes("--dry-run");

const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
const found = spawnSync("git", ["rev-parse", "--show-toplevel"], { cwd: scriptsDir, encoding: "utf8" });
if (found.status !== 0) {
  fail(
    `This copy of the skill is at ${path.dirname(scriptsDir)}, which is not inside a git repository. ` +
      "Copy the commit-guard folder to <repository>/.claude/skills/commit-guard and run the script from there.",
  );
}
const top = found.stdout.trim();
const guard = path.relative(top, path.join(fs.realpathSync(scriptsDir), "guard.mjs")).split(path.sep).join("/");
if (guard.startsWith("..")) {
  fail(`The skill's real location, ${path.dirname(scriptsDir)}, is outside ${top}. Copy the folder into the repository; a link won't do.`);
}
const command = `node "$CLAUDE_PROJECT_DIR/${guard}"`;
const settingsPath = path.join(top, ".claude", "settings.json");
const entry = { matcher: "Bash", hooks: [{ type: "command", command, timeout: 120 }] };

let settings = {};
if (fs.existsSync(settingsPath)) {
  try {
    settings = JSON.parse(fs.readFileSync(settingsPath, "utf8"));
  } catch (error) {
    fail(
      `${settingsPath} is not valid JSON (${error.message}), so it was left alone. Fix the file, or add this ` +
        `entry to its hooks.PreToolUse list by hand:\n${JSON.stringify(entry, null, 2)}`,
    );
  }
}
if (typeof settings !== "object" || settings === null || Array.isArray(settings)) {
  fail(`${settingsPath} does not hold a JSON object, so it was left alone.`);
}

const existing = settings.hooks?.PreToolUse ?? [];
if (!Array.isArray(existing)) fail(`hooks.PreToolUse in ${settingsPath} is not a list, so the file was left alone.`);
const registered = existing.some((group) =>
  (group?.hooks ?? []).some((hook) => typeof hook?.command === "string" && hook.command.includes(guard)),
);

if (!registered) {
  settings.hooks = { ...settings.hooks, PreToolUse: [...existing, entry] };
  if (!dryRun) {
    fs.mkdirSync(path.dirname(settingsPath), { recursive: true });
    fs.writeFileSync(settingsPath, `${JSON.stringify(settings, null, 2)}\n`);
  }
}

console.log(
  JSON.stringify(
    {
      settings: settingsPath,
      hookCommand: command,
      result: registered ? "already registered" : dryRun ? "would add the hook" : "added the hook",
      ...(dryRun && !registered ? { wouldWrite: settings } : {}),
    },
    null,
    2,
  ),
);
