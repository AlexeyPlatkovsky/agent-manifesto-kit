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
const meshScript = fileURLToPath(new URL('../collection/bundles/blender-3d/skills/blender-reference-model/scripts/mesh_report.py', import.meta.url));

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

test('Blender organic mesh gates persist connectivity and overlap evidence', {
  skip: available || process.env.BLENDER ? false : `Blender unavailable (${blender}); set BLENDER or add blender to PATH`,
  timeout: 180000,
}, async t => {
  const dir = mkdtempSync(join(tmpdir(), 'amk-mesh-'));
  try {
    const generated = run(fileURLToPath(new URL('./fixtures/blender-mesh.py', import.meta.url)), [dir]);
    assert.equal(generated.status, 0, generated.output);
    let n = 0;
    const mesh = (collection, args = []) => {
      const json = join(dir, `mesh-${++n}.json`);
      const result = run(meshScript, ['--collection', collection, ...args, '--json', json], join(dir, 'mesh.blend'));
      return { ...result, report: JSON.parse(readFileSync(json, 'utf8')) };
    };
    await t.test('evaluated triangles and shared-vertex faces pass organic checks', () => {
      const result = mesh('Valid', ['--organic']);
      assert.equal(result.status, 0, result.output);
      assert.equal(result.report.organic_checked, true);
      assert.equal(result.report.objects.find(o => o.object === 'Cube').tris, 12);
      for (const ob of result.report.objects) {
        assert.equal(ob.components, 1);
        assert.equal(ob.self_overlap_pairs, 0);
      }
      assert.match(result.output, /parts\s+self/);
    });
    await t.test('disconnected islands fail organic checks while legacy strict stays compatible', () => {
      const result = mesh('Split', ['--organic']);
      assert.notEqual(result.status, 0);
      assert.equal(result.report.objects[0].components, 2);
      assert.equal(result.report.objects[0].self_overlap_pairs, 0);
      const legacy = mesh('Split', ['--strict']);
      assert.equal(legacy.status, 0, legacy.output);
      assert.equal(legacy.report.organic_checked, false);
      assert.equal(legacy.report.objects[0].self_overlap_pairs, null);
    });
    await t.test('crossing faces in one connected component fail organic checks', () => {
      const result = mesh('Crossing', ['--organic']);
      assert.notEqual(result.status, 0);
      assert.equal(result.report.objects[0].components, 1);
      assert.equal(result.report.objects[0].self_overlap_pairs, 1);
      assert.equal(mesh('Crossing', ['--strict']).status, 0);
    });
    await t.test('surface pairs use world transforms and strict gates their persisted counts', () => {
      const clear = mesh('Pairs', ['--strict', '--pairs', 'PairA:PairB']);
      assert.equal(clear.status, 0, clear.output);
      assert.equal(clear.report.pair_overlaps['PairA x PairB'], 0);
      const crossing = mesh('Pairs', ['--strict', '--pairs', 'PairA:PairB,PairB:PairC']);
      assert.notEqual(crossing.status, 0);
      assert.equal(crossing.report.pair_overlaps['PairB x PairC'], 1);
      const diagnostic = mesh('Pairs', ['--pairs', 'PairB:PairC']);
      assert.equal(diagnostic.status, 0);
      assert.equal(diagnostic.report.pair_overlaps['PairB x PairC'], 1);
      assert.notEqual(mesh('Pairs', ['--organic', '--pairs', 'PairB:PairC']).status, 0);
    });
    await t.test('organic mode retains degenerate, loose and material checks', () => {
      for (const flag of ['--strict', '--organic']) {
        const result = mesh('BadHealth', [flag]);
        assert.notEqual(result.status, 0);
        assert.equal(result.report.objects[0].degenerate_faces, 1);
        assert.equal(result.report.objects[0].loose_verts, 1);
        assert.equal(result.report.objects[0].empty_material_slots, 1);
      }
    });
    await t.test('empty or wholly excluded required scope cannot pass', () => {
      for (const flag of ['--organic', '--strict']) {
        const result = mesh('Empty', [flag]);
        assert.notEqual(result.status, 0);
        assert.deepEqual(result.report.objects, []);
      }
      const excluded = mesh('Split', ['--organic', '--exclude-prefix', 'Split']);
      assert.notEqual(excluded.status, 0);
      assert.deepEqual(excluded.report.objects, []);
      assert.equal(mesh('Empty').status, 0);
    });
    await t.test('faceless objects fail required surface checks without reporting zero overlap', () => {
      const organic = mesh('NoSurface', ['--organic']);
      assert.notEqual(organic.status, 0);
      for (const ob of organic.report.objects) assert.equal(ob.self_overlap_pairs, null);
      const pair = mesh('NoSurface', ['--strict', '--pairs', 'Wire:NoVerts']);
      assert.notEqual(pair.status, 0);
      assert.equal(pair.report.pair_overlaps['Wire x NoVerts'], null);
      assert.match(pair.output, /not_tested/);
      assert.equal(mesh('NoSurface', ['--strict']).status, 0);
    });
    await t.test('missing collections and malformed, missing, self or out-of-scope pairs fail', () => {
      for (const args of [['--collection', 'Missing'],
        ...['PairA', 'PairA:PairB:PairC', 'PairA:Missing', 'PairA:PairA', 'PairA:Cube', 'PairA:PairB,']
          .map(value => ['--collection', 'Pairs', '--pairs', value]),
        ['--collection', 'Pairs', '--exclude-prefix', 'PairB', '--pairs', 'PairA:PairB']]) {
        const result = run(meshScript, args, join(dir, 'mesh.blend'));
        assert.notEqual(result.status, 0, result.output);
      }
    });
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
