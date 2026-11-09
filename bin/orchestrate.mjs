#!/usr/bin/env node

import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { cancel, confirm, intro, isCancel, multiselect, note, outro, select } from '@clack/prompts';

const installer = fileURLToPath(new URL('../install.py', import.meta.url));
const args = process.argv.slice(2);

function python(arguments_, options) {
  const result = spawnSync('python3', [installer, ...arguments_], options);
  if (result.error?.code === 'ENOENT') {
    throw new Error('Python 3 is required. Install python3 and make sure it is on PATH.');
  }
  if (result.error) throw result.error;
  return result;
}

async function run() {
  if (args.includes('--help') || args.includes('-h')) {
    console.log('Usage: npx @ryannel/orchestrate [--replace-standalone]\n\n'
      + 'Choose agents and scope for the Orchestrate plugin and evaluator.\n'
      + '  --replace-standalone  Move aside earlier standalone orchestration skills.');
    return 0;
  }
  const unknown = args.find((arg) => arg !== '--replace-standalone');
  if (unknown) throw new Error(`Unknown option: ${unknown}. Run with --help for usage.`);
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    throw new Error('Run this command in an interactive terminal to choose agents and scope.');
  }

  const detection = python(['--detect-orchestration-targets'], { encoding: 'utf8' });
  if (detection.status !== 0) throw new Error(detection.stderr.trim() || 'Could not detect agents.');
  const { claude, codex, project } = JSON.parse(detection.stdout);
  const options = [];
  if (claude) options.push({ value: 'claude', label: 'Claude Code' });
  if (codex) options.push({ value: 'codex', label: 'Codex', hint: 'Global only' });
  if (!options.length) throw new Error('Install Claude Code or Codex before running this installer.');

  intro('Install Orchestrate');
  const agents = await multiselect({
    message: 'Which agents should get Orchestrate?',
    options,
    required: true,
  });
  if (isCancel(agents)) {
    cancel('Installation cancelled.');
    return 0;
  }

  const scope = agents.includes('claude') && project
    ? await select({
        message: 'Where should Orchestrate be installed for Claude Code?',
        options: [
          { value: 'user', label: 'Global', hint: 'Available in all projects' },
          { value: 'project', label: 'Local to this project', hint: project },
        ],
      })
    : 'user';
  if (isCancel(scope)) {
    cancel('Installation cancelled.');
    return 0;
  }

  const summary = options.filter(({ value }) => agents.includes(value)).map(({ value, label }) =>
    value === 'claude' && scope === 'project' ? `${label} · Local (${project})` : `${label} · Global`);
  if (claude && agents.includes('claude') && !project) {
    summary.push('', 'Run from a Git repository to choose local scope for Claude Code.');
  }
  if (args.includes('--replace-standalone')) {
    summary.push('', 'Earlier standalone copies will be moved to a backup.');
  }
  note(summary.join('\n'), 'Install the Orchestrate plugin and evaluator');
  const proceed = await confirm({ message: 'Proceed with installation?', initialValue: false });
  if (isCancel(proceed) || !proceed) {
    cancel('Installation cancelled.');
    return 0;
  }

  const host = agents.length === 2 ? 'both' : agents[0];
  const repoArgs = scope === 'project' ? ['--repo', project] : [];
  const result = python([
    '--plugins', 'orchestrate', '--source', 'ryannel/skills',
    '--host', host, '--scope', scope, ...repoArgs, ...args,
  ], { stdio: 'inherit' });
  if (result.status === 0) outro('Open a new session in your project and run plan-module to get started.');
  return result.status ?? 1;
}

try {
  process.exitCode = await run();
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
