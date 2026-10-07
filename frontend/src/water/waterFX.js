// Water effects for LuxuryForm's viewer (scope §10).
// Techniques re-implemented from a study of AquaFlow's renderer (read-only):
// - 0.92*apex core column with aerated taper + KH-style t^2.2 wobble + tip fade
// - Gerstner 4-wave surface, Schlick fresnel with water's true F0 = 0.02
//   driving BOTH color mix and alpha (the strongest "this is water" cue)
// - apex mist + impact foam with reduced gravity
// - launch speed follows the hydraulics; apex = v0^2 / 2g
import * as THREE from 'three'

const GRAVITY = 9.81

// ── Core column shader (tapered, wobbling, tip-dissolving jet body) ──────
const CORE_VERT = /* glsl */ `
  uniform float uTime;
  uniform float uHeight;
  varying float vT;
  varying float vAlpha;
  void main() {
    float t = position.y;              // geometry baked so y in [0,1]
    vT = t;
    // Aerated expansion through the body, feathered crown.
    float taper = mix(1.0, 1.35, t) * mix(1.0, 0.65, smoothstep(0.82, 1.0, t));
    taper *= 1.0 + 0.06 * sin(t * 75.0 - uTime * 19.0);
    vec3 p = vec3(position.x * taper, t * uHeight, position.z * taper);
    // KH-style turbulence growing with height.
    float turb = pow(t, 2.2);
    p.x += sin(t * 14.0 + uTime * 7.0) * 0.030 * turb;
    p.z += cos(t * 11.0 - uTime * 5.5) * 0.026 * turb;
    // Solid at base, dissolving in the top ~22% where droplets take over.
    vAlpha = (1.0 - smoothstep(0.78, 1.0, t)) * 0.72;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  }
`
const CORE_FRAG = /* glsl */ `
  uniform float uTime;
  uniform vec3 uColor;
  varying float vT;
  varying float vAlpha;
  void main() {
    vec3 deep = uColor * 0.7;
    vec3 shallow = mix(uColor, vec3(0.85, 0.95, 1.0), 0.55);
    vec3 col = mix(shallow, deep, vT * 0.6);
    col *= 0.92 + 0.08 * sin(vT * 42.0 - uTime * 24.0);   // flow animation
    gl_FragColor = vec4(col, vAlpha);
  }
`

// ── Water surface: 4 Gerstner waves + F0=0.02 fresnel color/alpha ────────
const SURF_VERT = /* glsl */ `
  uniform float uTime;
  varying vec3 vNormal;
  varying vec3 vWorld;
  varying float vR;
  vec3 gerstner(vec2 p, vec2 dir, float amp, float freq, float speed,
                float steep, float t, inout vec2 slope) {
    float phase = dot(dir, p) * freq + t * speed;
    slope += amp * freq * dir * cos(phase);
    return vec3(steep * amp * dir.x * cos(phase), amp * sin(phase),
                steep * amp * dir.y * cos(phase));
  }
  void main() {
    vec4 world = modelMatrix * vec4(position, 1.0);
    vec2 p = world.xz;
    vec2 slope = vec2(0.0);
    vec3 disp = vec3(0.0);
    disp += gerstner(p, vec2( 1.0,  0.6), 0.035, 2.1, 1.20, 0.8, uTime * 1.00, slope);
    disp += gerstner(p, vec2(-0.7,  1.0), 0.028, 1.8, 0.90, 0.6, uTime * 0.85, slope);
    disp += gerstner(p, vec2( 0.3, -1.0), 0.018, 3.5, 1.80, 0.4, uTime * 1.15, slope);
    disp += gerstner(p, vec2(-1.0,  0.4), 0.012, 4.8, 2.40, 0.3, uTime * 0.70, slope);
    world.xz += disp.xz;
    world.y  += disp.y;
    vWorld = world.xyz;
    vR = length(p);
    vNormal = normalize(vec3(-slope.x, 1.0, -slope.y));
    gl_Position = projectionMatrix * viewMatrix * world;
  }
`
const SURF_FRAG = /* glsl */ `
  uniform vec3 uDeep;
  uniform vec3 uShallow;
  uniform vec3 uSky;
  uniform float uRadius;
  varying vec3 vNormal;
  varying vec3 vWorld;
  varying float vR;
  void main() {
    if (vR > uRadius) discard;
    vec3 N = normalize(vNormal);
    vec3 V = normalize(cameraPosition - vWorld);
    float ndv = clamp(dot(N, V), 0.0, 1.0);
    // Schlick fresnel, water F0 = 0.02 — drives color AND alpha.
    float fres = 0.02 + 0.98 * pow(1.0 - ndv, 5.0);
    float depthMix = smoothstep(0.0, uRadius, vR);
    vec3 base = mix(uShallow, uDeep, depthMix * 0.7);
    vec3 col = mix(base, uSky, fres);
    // Simple sun glint.
    vec3 L = normalize(vec3(0.4, 1.0, 0.6));
    float spec = pow(max(dot(reflect(-L, N), V), 0.0), 64.0) * 0.35;
    col += spec;
    float alpha = mix(0.86, 1.0, fres);
    gl_FragColor = vec4(col, alpha);
  }
`

const DEEP = new THREE.Color(0x0c3558)
const SHALLOW = new THREE.Color(0x5294aa)
const SKY = new THREE.Color(0x9fc3d8)
const JET_COLOR = new THREE.Color(0.65, 0.82, 1.0)

function buildCoreColumn(jet) {
  const r = 0.045
  const geo = new THREE.CylinderGeometry(r, r * 1.1, 1.0, 10, 40, true)
  geo.translate(0, 0.5, 0) // y in [0,1]
  const apex = (jet.exit_velocity_ms ** 2) / (2 * GRAVITY)
  const mat = new THREE.ShaderMaterial({
    vertexShader: CORE_VERT,
    fragmentShader: CORE_FRAG,
    uniforms: {
      uTime: { value: 0 },
      uHeight: { value: 0.92 * apex }, // core stops where breakup takes over
      uColor: { value: JET_COLOR },
    },
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
  })
  const mesh = new THREE.Mesh(geo, mat)
  mesh.position.set(jet.position[0], jet.position[1], jet.position[2])
  return mesh
}

// Drifting particle system: particles cycle through a lifetime along a
// velocity function — mist at the apex, foam at the surface.
function buildDriftParticles({ count, origin, radius, speed, life, size,
                               color, opacity, up = 0.0, gravity = 0.0 }) {
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position',
    new THREE.Float32BufferAttribute(new Float32Array(count * 3), 3))
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({
    color, size, transparent: true, opacity,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }))
  const seeds = Array.from({ length: count }, () => ({
    phase: Math.random(),
    angle: Math.random() * Math.PI * 2,
    r: 0.3 + Math.random() * 0.7,
  }))
  pts.userData.update = (elapsed) => {
    const pos = geo.attributes.position
    for (let i = 0; i < count; i++) {
      const s = seeds[i]
      const t = ((elapsed / life) + s.phase) % 1.0
      const spread = radius * s.r * (0.4 + t)
      pos.setXYZ(i,
        origin[0] + Math.cos(s.angle) * spread + speed * t * Math.cos(s.angle),
        origin[1] + up * t - 0.5 * gravity * t * t,
        origin[2] + Math.sin(s.angle) * spread + speed * t * Math.sin(s.angle))
    }
    pos.needsUpdate = true
  }
  return pts
}

export function buildWaterFX(viz) {
  const group = new THREE.Group()
  group.name = 'water'
  const updatables = []

  // Water surface: tessellated plane (fans can't displace interiors),
  // circle cut in the fragment shader.
  if (viz.basin_inner?.radius_m) {
    const R = viz.basin_inner.radius_m
    const geo = new THREE.PlaneGeometry(R * 2.2, R * 2.2, 48, 48)
    geo.rotateX(-Math.PI / 2)
    const mat = new THREE.ShaderMaterial({
      vertexShader: SURF_VERT,
      fragmentShader: SURF_FRAG,
      uniforms: {
        uTime: { value: 0 },
        uDeep: { value: DEEP },
        uShallow: { value: SHALLOW },
        uSky: { value: SKY },
        uRadius: { value: R },
      },
      transparent: true,
      depthWrite: false,
    })
    const surface = new THREE.Mesh(geo, mat)
    surface.position.y = viz.water_level_m
    group.add(surface)
    updatables.push((t) => { mat.uniforms.uTime.value = t })
  }

  // Jets: core column + breakup droplets + apex mist + impact foam.
  for (const j of viz.jets || []) {
    const apex = (j.exit_velocity_ms ** 2) / (2 * GRAVITY)
    const core = buildCoreColumn(j)
    group.add(core)
    updatables.push((t) => { core.material.uniforms.uTime.value = t })

    // Breakup droplets (ballistic, from the core crown upward).
    const count = 24
    const geoD = new THREE.BufferGeometry()
    geoD.setAttribute('position',
      new THREE.Float32BufferAttribute(new Float32Array(count * 3), 3))
    const drops = new THREE.Points(geoD, new THREE.PointsMaterial({
      color: 0xbfe3ff, size: 0.07, transparent: true, opacity: 0.75,
      blending: THREE.AdditiveBlending, depthWrite: false,
    }))
    const phases = Array.from({ length: count }, (_, i) => i / count)
    const v0 = j.exit_velocity_ms * 0.75  // droplets lag the core
    const tMax = (2 * v0) / GRAVITY
    updatables.push((elapsed) => {
      const pos = geoD.attributes.position
      for (let i = 0; i < count; i++) {
        const t = (elapsed + phases[i] * tMax) % tMax
        const y = Math.max(v0 * t - 0.5 * GRAVITY * t * t, 0)
        pos.setXYZ(i, j.position[0], j.position[1] + y, j.position[2])
      }
      pos.needsUpdate = true
    })
    group.add(drops)

    // Apex mist: slow drift, reduced gravity feel.
    const mist = buildDriftParticles({
      count: 12, origin: [j.position[0], j.position[1] + 0.85 * apex, j.position[2]],
      radius: 0.22, speed: 0.3, life: 1.2, size: 0.16,
      color: 0xe0f2ff, opacity: 0.35, up: 0.15,
    })
    group.add(mist)
    updatables.push((t) => mist.userData.update(t))

    // Impact foam ring at the water surface.
    const foam = buildDriftParticles({
      count: 10, origin: [j.position[0], viz.water_level_m + 0.02, j.position[2]],
      radius: 0.35, speed: 0.25, life: 1.0, size: 0.12,
      color: 0xffffff, opacity: 0.5,
    })
    group.add(foam)
    updatables.push((t) => foam.userData.update(t))

    // Splash-zone ring (engineering output made visible).
    if (j.splash_radius_m) {
      const pts = []
      for (let i = 0; i <= 48; i++) {
        const a = (i / 48) * Math.PI * 2
        pts.push(new THREE.Vector3(
          j.position[0] + Math.cos(a) * j.splash_radius_m,
          viz.water_level_m + 0.01,
          j.position[2] + Math.sin(a) * j.splash_radius_m))
      }
      const ring = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(pts),
        new THREE.LineBasicMaterial({ color: 0x4fa8ff, transparent: true,
                                      opacity: 0.5 }))
      group.add(ring)
    }
  }

  // Curtain sheets (unchanged translucent bands).
  for (const c of viz.curtains || []) {
    const h = c.top_y - c.bottom_y
    if (h <= 0) continue
    const sheet = new THREE.Mesh(
      new THREE.CylinderGeometry(c.radius_m, c.radius_m * 0.98, h, 48, 1, true),
      new THREE.MeshStandardMaterial({
        color: 0x9fd4ff, transparent: true, opacity: 0.22,
        roughness: 0.1, side: THREE.DoubleSide, depthWrite: false,
      }))
    sheet.position.y = c.bottom_y + h / 2
    group.add(sheet)
  }

  return { group, update: (t) => updatables.forEach((u) => u(t)) }
}
