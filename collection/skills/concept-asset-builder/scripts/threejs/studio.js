// Shared white studio for pipeline A (procedural three.js) and pipeline C (Blender GLB in three.js).
// Identical renderer, light, camera fitting and capture contract for both viewers.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

export async function loadSpec() {
  const res = await fetch('/spec/object.json');
  return res.json();
}

/** True if a static file exists (vite answers missing paths with index.html, so check the content type). */
export async function fileExists(url, typePrefix) {
  try {
    const res = await fetch(url, { method: 'HEAD', cache: 'no-store' });
    if (!res.ok) return false;
    const type = res.headers.get('content-type') || '';
    return typePrefix ? type.startsWith(typePrefix) : !type.startsWith('text/html');
  } catch {
    return false;
  }
}

export const params = new URLSearchParams(location.search);

export function createStudio(spec, container = document.body, opts = {}) {
  const view = params.get('view');
  // GTAO on by default (pipeline A); a viewer can default it off (C: AO is already baked into the GLB);
  // ?ao=0 / ?ao=1 overrides either way
  const useAO = params.has('ao') ? params.get('ao') !== '0' : (opts.ao ?? true);
  const [imgW, imgH] = spec.cameras.image;
  const width = view ? imgW : window.innerWidth;
  const height = view ? imgH : window.innerHeight;

  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(view ? 1 : Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  // Neutral (Khronos PBR Neutral) keeps albedo hue and saturation: ACES/AgX shift the red paint toward orange/pink.
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 0.82;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  // with the composer the OutputPass tone-maps the background too: ×1.35 compensates so the page bg matches the
  // concept; without it (renderer clear colour, not tone-mapped) the plain colour already matches
  scene.background = new THREE.Color(spec.palette.background).multiplyScalar(useAO ? 1.35 : 1.0);

  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 1.0;

  // Soft key: upper-left of the CAMERA. The concept sheet lights every view the same way relative to the
  // viewer (left side of the body lighter), so the key follows the camera instead of being fixed in the world.
  const key = new THREE.DirectionalLight(0xffffff, 1.25);
  const KEY_AZ = THREE.MathUtils.degToRad(-40), KEY_EL = THREE.MathUtils.degToRad(38);
  key.target.position.set(0, 0.6, 0);
  function placeKey() {
    const az = Math.atan2(camera.position.x - key.target.position.x, camera.position.z - key.target.position.z) + KEY_AZ;
    key.position.set(Math.sin(az) * Math.cos(KEY_EL), Math.sin(KEY_EL), Math.cos(az) * Math.cos(KEY_EL))
      .multiplyScalar(3.5).add(key.target.position);
    // RoomEnvironment is asymmetric: turn it with the camera so every view gets the same studio
    scene.environmentRotation.y = az - KEY_AZ;
  }
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.radius = 6;
  key.shadow.bias = -0.0004;
  key.shadow.normalBias = 0.015;
  const sc = key.shadow.camera;
  sc.left = -0.9; sc.right = 0.9; sc.top = 0.9; sc.bottom = -0.9; sc.near = 0.5; sc.far = 8;
  scene.add(key, key.target);

  // Invisible ground that only receives a faint shadow (concept sheet has almost none).
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(6, 6),
    new THREE.ShadowMaterial({ opacity: 0.04 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  const camera = new THREE.PerspectiveCamera(spec.cameras.fov_deg, width / height, 0.05, 50);

  let composer = null;
  if (useAO) {
    // multisampled target (MSAA x4): the composer path otherwise loses the canvas antialiasing
    composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(width, height, { type: THREE.HalfFloatType, samples: 4 }));
    composer.setPixelRatio(renderer.getPixelRatio());
    composer.setSize(width, height);
    composer.addPass(new RenderPass(scene, camera));
    const gtao = new GTAOPass(scene, camera, width, height);
    gtao.updateGtaoMaterial({ radius: 0.12, distanceExponent: 1.5, thickness: 1.0, scale: 1.0 });
    gtao.blendIntensity = 1.0;
    composer.addPass(gtao);
    composer.addPass(new OutputPass());
  }

  let controls = null;
  if (!view) {
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
      composer?.setSize(window.innerWidth, window.innerHeight);
    });
  }

  function render() {
    if (composer) composer.render();
    else renderer.render(scene, camera);
  }

  /** Place the camera for a named view and fit the object's bounding box to `fill` of the image height. */
  function frame(object, viewName = view || '3q', fill = spec.cameras.fill ?? 0.955) {
    const az = THREE.MathUtils.degToRad(spec.cameras.views[viewName] ?? -38);
    const el = THREE.MathUtils.degToRad(spec.cameras.elevation_deg);
    const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
    const box = new THREE.Box3().setFromObject(object);
    const corners = [];
    for (const x of [box.min.x, box.max.x])
      for (const y of [box.min.y, box.max.y])
        for (const z of [box.min.z, box.max.z]) corners.push(new THREE.Vector3(x, y, z));
    const target = box.getCenter(new THREE.Vector3());
    let dist = 6;
    for (let i = 0; i < 8; i++) {
      camera.position.copy(target).addScaledVector(dir, dist);
      camera.lookAt(target);
      camera.updateMatrixWorld();
      let ymin = Infinity, ymax = -Infinity, xmin = Infinity, xmax = -Infinity;
      for (const c of corners) {
        const p = c.clone().project(camera);
        ymin = Math.min(ymin, p.y); ymax = Math.max(ymax, p.y);
        xmin = Math.min(xmin, p.x); xmax = Math.max(xmax, p.x);
      }
      // fit BOTH axes: a wide object (a building in 3/4) would otherwise leave the frame sideways
      dist *= Math.max(ymax - ymin, xmax - xmin) / (2 * fill);
      // recentre vertically: shift target along camera up by the NDC offset
      const mid = (ymax + ymin) / 2;
      const halfH = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * dist;
      const up = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
      target.addScaledVector(up, mid * halfH);
    }
    camera.position.copy(target).addScaledVector(dir, dist);
    camera.lookAt(target);
    if (controls) {
      controls.target.copy(target);
      controls.update();
    }
  }

  function start() {
    let frames = 0;
    renderer.setAnimationLoop(() => {
      controls?.update();
      placeKey();
      render();
      if (++frames === 3) window.__ready = true;
    });
  }

  return { THREE, renderer, scene, camera, key, controls, frame, render, start, view };
}

/** Small corner label (hidden in capture mode). */
export function label(text, view) {
  if (view) return;
  const el = document.createElement('div');
  el.textContent = text;
  el.style.cssText = 'position:fixed;left:12px;top:10px;font:13px/1.3 system-ui;color:#5a4a42;opacity:.8;pointer-events:none';
  document.body.appendChild(el);
}
