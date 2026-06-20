#!/usr/bin/env node
import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';

const branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf-8' }).trim();

let bumpType;
if (branch.startsWith('bugfix/')) bumpType = 'patch';
else if (branch.startsWith('feature/')) bumpType = 'minor';
else if (branch.startsWith('release/')) bumpType = 'major';
else process.exit(0);

const suffix = branch.replace(/[^a-zA-Z0-9-]/g, '-').toLowerCase();
const pkgPath = new URL('../../package.json', import.meta.url);
const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));

if (pkg.version.includes(suffix)) {
  console.log(`  - Already bumped for ${branch}, skipping`);
  process.exit(0);
}

let latestTag;
try {
  latestTag = execSync('git describe --tags --abbrev=0', { encoding: 'utf-8' }).trim();
} catch {
  latestTag = 'v0.0.0';
}

const [major, minor, patch] = latestTag.replace(/^v/, '').split('.').map(Number);
let next = [major, minor, patch];

switch (bumpType) {
  case 'patch': next = [major, minor, patch + 1]; break;
  case 'minor': next = [major, minor + 1, 0];    break;
  case 'major': next = [major + 1, 0, 0];         break;
}

const newVersion = `${next.join('.')}-${suffix}.0`;
pkg.version = newVersion;
writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');

execSync('git add package.json', { stdio: 'pipe' });
execSync(`git commit -m "chore(branch): bump to ${newVersion}"`, { stdio: 'inherit' });

console.log(`  ✓ Version bumped to ${newVersion}`);
