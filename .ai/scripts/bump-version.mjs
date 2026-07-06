#!/usr/bin/env node
import { execFileSync, execSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const packageRoot = fileURLToPath(new URL('../..', import.meta.url));

const branch = execSync('git rev-parse --abbrev-ref HEAD', { cwd: packageRoot, encoding: 'utf-8' }).trim();
const pkgPath = new URL('../../package.json', import.meta.url);
const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));

let bumpType;
if (branch.startsWith('bugfix/')) bumpType = 'patch';
else if (branch.startsWith('feature/')) bumpType = 'minor';
else if (branch.startsWith('release/')) bumpType = 'major';
else process.exit(0);

const suffix = branch.replace(/[^a-zA-Z0-9-]/g, '-').toLowerCase();

if (pkg.version.includes(suffix)) {
  console.log(`  - Already bumped for ${branch}, skipping`);
  process.exit(0);
}

function parseVersion(value) {
  const match = value.trim().match(/^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$/);
  if (!match) return null;
  return match.slice(1).map(Number);
}

function compareVersion(a, b) {
  for (let i = 0; i < 3; i += 1) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return 0;
}

const baselines = [];

try {
  const latestTag = execSync('git describe --tags --abbrev=0', { cwd: packageRoot, encoding: 'utf-8' }).trim();
  const parsed = parseVersion(latestTag);
  if (parsed) baselines.push(parsed);
} catch {
  // Tags may be missing in a fresh clone; fall back to the published npm version below.
}

try {
  const npmVersion = execFileSync('npm', ['view', pkg.name, 'version'], { encoding: 'utf-8' }).trim();
  const parsed = parseVersion(npmVersion);
  if (parsed) baselines.push(parsed);
} catch {
  // Offline or unpublished package; fall back to the local package version below.
}

const localVersion = parseVersion(pkg.version);
if (localVersion) baselines.push(localVersion);

const [major, minor, patch] = baselines.sort(compareVersion).at(-1) ?? [0, 0, 0];
let next = [major, minor, patch];

switch (bumpType) {
  case 'patch': next = [major, minor, patch + 1]; break;
  case 'minor': next = [major, minor + 1, 0];    break;
  case 'major': next = [major + 1, 0, 0];         break;
}

const newVersion = `${next.join('.')}-${suffix}.0`;
pkg.version = newVersion;
writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');

try {
  execFileSync('npm', ['install', '--package-lock-only', '--ignore-scripts'], { cwd: packageRoot, stdio: 'inherit' });
} catch {
  console.error('  ✗ Failed to update package-lock.json for the branch version');
  process.exit(1);
}

execSync('git add package.json package-lock.json', { cwd: packageRoot, stdio: 'pipe' });
execSync(`git commit -m "chore(branch): bump to ${newVersion}"`, { cwd: packageRoot, stdio: 'inherit' });

console.log(`  ✓ Version bumped to ${newVersion}`);
