#!/usr/bin/env node

const { spawnSync } = require('node:child_process');
const { join } = require('node:path');

const result = spawnSync(
  'python3',
  [join(__dirname, '..', 'install.py'), '--interactive', ...process.argv.slice(2)],
  { stdio: 'inherit' },
);

if (result.error) {
  console.error(result.error.code === 'ENOENT'
    ? 'Python 3 is required. Install python3 and make sure it is on PATH.'
    : result.error.message);
}
process.exitCode = result.status ?? 1;
