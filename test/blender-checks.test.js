import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const blender = process.env.BLENDER || 'blender';
const available = spawnSync(blender, ['--version'], { encoding: 'utf8' }).status === 0;
const scripts = fileURLToPath(new URL('../collection/bundles/blender-3d/skills/blender-mocap-retarget/scripts/', import.meta.url));
const fixture = fileURLToPath(new URL('./fixtures/blender-checks.py', import.meta.url));

function run(script, args, blend) {
  const result = spawnSync(blender, ['-b', '--factory-startup', ...(blend ? [blend] : []),
    '--python-exit-code', '1', '--python', script, '--', ...args], {
    encoding: 'utf8', timeout: 60000, maxBuffer: 4 * 1024 * 1024,
  });
  assert.ifError(result.error);
  return { ...result, output: result.stdout + result.stderr };
}

// Rename an original animation in an otherwise genuine Blender GLB export.
function renameClip(input, output, from, to) {
  const data = readFileSync(input);
  const jsonLength = data.readUInt32LE(12);
  const source = JSON.parse(data.subarray(20, 20 + jsonLength).toString());
  source.animations.find(a => a.name === from).name = to;
  const text = Buffer.from(JSON.stringify(source));
  const padded = Buffer.alloc(Math.ceil(text.length / 4) * 4, 0x20);
  text.copy(padded);
  const header = Buffer.from(data.subarray(0, 20));
  header.writeUInt32LE(padded.length, 12);
  const rest = data.subarray(20 + jsonLength);
  header.writeUInt32LE(20 + padded.length + rest.length, 8);
  writeFileSync(output, Buffer.concat([header, padded, rest]));
}

test('Blender motion and exported glTF requirements', {
  skip: available || process.env.BLENDER ? false : `Blender unavailable (${blender}); set BLENDER or add blender to PATH`,
  timeout: 180000,
}, async t => {
  const dir = mkdtempSync(join(tmpdir(), 'amk-blender-'));
  try {
    const generated = run(fixture, [dir]);
    assert.equal(generated.status, 0, generated.output);
    let n = 0;
    const motion = (args = [], file = 'motion.blend') => {
      const json = join(dir, `motion-${++n}.json`);
      const result = run(join(scripts, 'check_motion.py'), ['--rig', 'Rig', ...args, '--json', json], join(dir, file));
      return { ...result, report: JSON.parse(readFileSync(json, 'utf8')) };
    };
    const verify = (file, args = []) => {
      const json = join(dir, `verify-${++n}.json`);
      const result = run(join(scripts, 'verify_gltf.py'), [join(dir, file), ...args, '--json', json]);
      return { ...result, report: JSON.parse(readFileSync(json, 'utf8')) };
    };
    const coverage = ['--feet', 'Foot', '--pairs', 'PairA:PairB'];
    const thresholds = ['--max-ground-penetration-mm', '3', '--max-planted-slide-mm-per-frame', '20',
      '--max-extra-overlap-tris', '2', '--max-loop-rotation-deg', '2'];

    await t.test('real deformation and collision measurements pass loose requested thresholds', () => {
      const result = motion([...coverage, '--strict', ...thresholds]);
      assert.equal(result.status, 0, result.output);
      assert.equal(result.report.status, 'pass');
      for (const check of Object.values(result.report.checks)) assert.equal(check.status, 'pass');
      assert.ok(Math.abs(result.report.ground.Foot.min_mm + 2) < 0.2);
      assert.ok(result.report.slide.Foot.max_mm_per_frame > 9);
      assert.equal(result.report.interpenetration['PairA x PairB'].max_extra_tris, 1);
      assert.ok(result.report.loop_seam.max_rotation_diff_deg > 1);
    });

    await t.test('each requested threshold rejects the measured violation', () => {
      for (const [flag, key] of [
        ['--max-ground-penetration-mm', 'ground'], ['--max-planted-slide-mm-per-frame', 'slide'],
        ['--max-extra-overlap-tris', 'interpenetration'], ['--max-loop-rotation-deg', 'loop_seam'],
      ]) {
        const result = motion([...coverage, '--strict', flag, '0']);
        assert.notEqual(result.status, 0, flag);
        assert.equal(result.report.checks[key].status, 'fail', result.output);
      }
    });

    await t.test('missing requested coverage fails without a false pass; diagnostic mode succeeds', () => {
      const missing = motion(['--strict', ...thresholds], 'no-action.blend');
      assert.notEqual(missing.status, 0);
      for (const check of Object.values(missing.report.checks)) assert.equal(check.status, 'not_tested');
      const emptyAction = motion(['--strict', '--max-loop-rotation-deg', '0'], 'empty-action.blend');
      assert.notEqual(emptyAction.status, 0);
      assert.equal(emptyAction.report.checks.loop_seam.status, 'not_tested');
      const diagnostic = motion();
      assert.equal(diagnostic.status, 0, diagnostic.output);
      assert.equal(diagnostic.report.status, 'not_tested');
      const noThreshold = motion(['--strict']);
      assert.notEqual(noThreshold.status, 0);
      const nonstrict = motion([...coverage, '--max-ground-penetration-mm', '0']);
      assert.equal(nonstrict.status, 0);
      assert.equal(nonstrict.report.checks.ground.status, 'fail');
    });

    await t.test('one airborne foot or a one-frame sample cannot satisfy planted slide coverage', () => {
      for (const [args, file] of [
        [['--feet', 'Foot,AirFoot'], 'air.blend'],
        [['--feet', 'Foot', '--frames', '0-0'], 'motion.blend'],
      ]) {
        const result = motion([...args, '--strict', '--max-planted-slide-mm-per-frame', '100'], file);
        assert.notEqual(result.status, 0);
        assert.equal(result.report.checks.slide.status, 'not_tested');
      }
    });

    await t.test('loop seam samples distinct fractional action endpoints without rounding', () => {
      const result = motion(['--strict', '--max-loop-rotation-deg', '1'], 'subframe.blend');
      assert.notEqual(result.status, 0);
      assert.equal(result.report.checks.loop_seam.status, 'fail');
      const [start, end] = result.report.loop_seam.action_range;
      assert.ok(Math.abs(start - .1) < 1e-6);
      assert.ok(Math.abs(end - .4) < 1e-6);
      assert.ok(result.report.loop_seam.max_rotation_diff_deg > 11);
    });

    await t.test('invalid numeric options, ranges, names, and pairs fail', () => {
      for (const args of [
        ['--contact-mm', '-1'], ['--contact-mm', 'nan'], ['--ground-z', 'inf'],
        ['--max-ground-penetration-mm', '-1'], ['--max-planted-slide-mm-per-frame', 'nan'],
        ['--max-extra-overlap-tris', 'inf'], ['--max-loop-rotation-deg', '-1'],
        ['--frames', '2-0'], ['--frames', 'oops'], ['--frames', '0-99999999999'],
        ['--pairs', 'Foot:Foot:Foot'], ['--feet', 'Absent'], ['--pairs', 'Foot:Absent'],
      ]) {
        const result = run(join(scripts, 'check_motion.py'), ['--rig', 'Rig', ...args], join(dir, 'motion.blend'));
        assert.notEqual(result.status, 0, `${args.join(' ')}\n${result.output}`);
      }
    });

    await t.test('exact named clips and real required skin/rig/geometry pass after import', () => {
      const result = verify('rig.glb', ['--expect-clips', 'Walk,Run', '--exact-clips',
        '--require-mesh', '--require-skin', '--require-rig']);
      assert.equal(result.status, 0, result.output);
      assert.deepEqual(result.report.exported_clips.sort(), ['Run', 'Walk']);
      assert.ok(result.report.skinned_meshes > 0);
      assert.ok(result.report.bones > 0);
    });

    await t.test('extras fail exact mode while legacy expected subset remains compatible', () => {
      const legacy = verify('rig.glb', ['--expect-clips', 'Walk']);
      assert.equal(legacy.status, 0, legacy.output);
      const exact = verify('rig.glb', ['--expect-clips', 'Walk', '--exact-clips']);
      assert.notEqual(exact.status, 0);
      assert.ok(exact.report.problems.some(p => p.includes('unexpected exported clips')));
      const missing = verify('rig.glb', ['--expect-clips', 'Missing']);
      assert.notEqual(missing.status, 0);
    });

    await t.test('exact names use original export names despite imported prefix compatibility', () => {
      renameClip(join(dir, 'rig.glb'), join(dir, 'renamed.glb'), 'Walk', 'Walk_extra');
      assert.equal(verify('renamed.glb', ['--expect-clips', 'Walk,Run']).status, 0);
      const result = verify('renamed.glb', ['--expect-clips', 'Walk,Run', '--exact-clips']);
      assert.notEqual(result.status, 0);
      assert.ok(result.report.problems.some(p => p.includes('expected exported clips missing')));
      assert.ok(result.report.problems.some(p => p.includes('unexpected exported clips')));
    });

    await t.test('missing geometry, skin, or rig fails requested structural checks', () => {
      assert.equal(verify('static.glb', ['--require-mesh', '--exact-clips']).status, 0);
      for (const flag of ['--require-skin', '--require-rig']) {
        const result = verify('static.glb', [flag]);
        assert.notEqual(result.status, 0);
        assert.ok(result.report.problems.length);
      }
      const empty = verify('empty.glb', ['--require-mesh']);
      assert.notEqual(empty.status, 0);
      assert.equal(empty.report.meshes, 0);
    });

    await t.test('invalid FPS and duplicate expected clips fail before import', () => {
      for (const args of [['--fps', '0'], ['--fps', 'nan'], ['--fps', 'inf'], ['--fps', '-1'],
        ['--expect-clips', 'Walk,Walk']]) {
        const result = run(join(scripts, 'verify_gltf.py'), [join(dir, 'rig.glb'), ...args]);
        assert.notEqual(result.status, 0, result.output);
      }
    });
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
