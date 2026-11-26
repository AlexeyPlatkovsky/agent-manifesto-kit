// STUB — replace with the real model. Contract: export async function buildModel(spec) -> THREE.Object3D
// (Y up, front faces +Z, ground at y = 0, metres, built from spec/object.json).
import * as THREE from 'three';
export async function buildModel(spec) {
  const h = spec.height, w = spec.width ?? h * 0.45, d = spec.depth ?? w * 0.7;
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({ color: '#999999', roughness: 0.7 }));
  m.position.y = h / 2; m.castShadow = true;
  return m;
}
