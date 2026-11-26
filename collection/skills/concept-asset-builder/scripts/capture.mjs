// Capture fixed-camera renders of pipeline A (threejs) and C (Blender GLB in three.js).
// Usage: node tools/capture.mjs [threejs|glb|all] [--views front,3q] [--query ao=0] [--base http://localhost:5181]
// Needs the vite server running (npx vite --port 5181).
import { chromium } from 'playwright';
import { readFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const spec = JSON.parse(readFileSync(path.join(root, 'spec/object.json'), 'utf8'));
const what = process.argv[2] || 'all';
const baseIdx = process.argv.indexOf('--base');
const base = baseIdx > 0 ? process.argv[baseIdx + 1] : 'http://localhost:5191';
const [w, h] = spec.cameras.image;
const viewsIdx = process.argv.indexOf('--views');
const views = viewsIdx > 0 ? process.argv[viewsIdx + 1].split(',') : Object.keys(spec.cameras.views);
const qIdx = process.argv.indexOf('--query');
const extraQuery = qIdx > 0 ? `&${process.argv[qIdx + 1]}` : '';

const targets = [];
if (what === 'threejs' || what === 'all') targets.push({ page: 'threejs/index.html', out: 'out/threejs' });
if (what === 'glb' || what === 'all') targets.push({ page: 'threejs/glb.html', out: 'out/glb_in_three' });

const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
page.on('pageerror', (e) => console.error('pageerror:', e.message));
// optional maps (roughness/normal) are probed and may 404: not an error
page.on('console', (m) => { if (m.type() === 'error' && !m.text().includes('404')) console.error('console:', m.text()); });

for (const t of targets) {
  mkdirSync(path.join(root, t.out), { recursive: true });
  for (const v of views) {
    await page.goto(`${base}/${t.page}?view=${v}${extraQuery}`);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
    if (await page.evaluate(() => window.__missing === true)) {
      console.log(`${t.page}: GLB missing, skipped`);
      break;
    }
    const file = path.join(root, t.out, `${v}.png`);
    await page.locator('canvas').screenshot({ path: file });
    console.log('saved', path.relative(root, file));
  }
}
await browser.close();
