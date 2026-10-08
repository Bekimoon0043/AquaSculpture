import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
import useBriefStore from '../store/briefStore'
import { buildWaterFX } from '../water/waterFX'

function toMesh(mesh, material) {
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position',
    new THREE.Float32BufferAttribute(mesh.vertices.flat(), 3))
  geo.setIndex(mesh.faces.flat())
  geo.computeVertexNormals()
  return new THREE.Mesh(geo, material)
}

export default function Viewer3D() {
  const mountRef = useRef(null)
  const sceneRef = useRef(null)
  const groupRef = useRef(null)
  const cameraRef = useRef(null)
  const controlsRef = useRef(null)
  const engineering = useBriefStore((s) => s.engineering)
  const [wireframe, setWireframe] = useState(false)
  const [showSkeleton, setShowSkeleton] = useState(false)
  const [showWater, setShowWater] = useState(true)
  const [night, setNight] = useState(false)
  const [showLux, setShowLux] = useState(false)
  const [backdrop, setBackdrop] = useState(null)  // site photo URL
  const backdropRef = useRef(null)
  backdropRef.current = backdrop
  const showLuxRef = useRef(false)
  showLuxRef.current = showLux
  const nightRef = useRef(false)
  nightRef.current = night
  const sceneLightsRef = useRef(null)
  const showSkeletonRef = useRef(false)
  showSkeletonRef.current = showSkeleton
  const showWaterRef = useRef(true)
  showWaterRef.current = showWater
  const waterRef = useRef(null)   // animated water particle systems
  const clockRef = useRef(new THREE.Clock())

  useEffect(() => {
    const mount = mountRef.current
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0b0e12) // dark studio
    scene.fog = new THREE.Fog(0x0b0e12, 20, 60)
    sceneRef.current = scene

    const camera = new THREE.PerspectiveCamera(
      50, mount.clientWidth / mount.clientHeight, 0.1, 200)
    camera.position.set(6, 4, 8)
    cameraRef.current = camera

    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(mount.clientWidth, mount.clientHeight)
    renderer.setPixelRatio(window.devicePixelRatio)
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.1
    mount.appendChild(renderer.domElement)

    // Environment map — metal surfaces only show what they reflect,
    // so without this mirror-polished steel renders almost black.
    const pmrem = new THREE.PMREMGenerator(renderer)
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture
    pmrem.dispose()

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.target.set(0, 1.5, 0)
    controlsRef.current = controls

    // Studio three-point lighting: key + fill + rim, over a hemisphere base.
    const hemi = new THREE.HemisphereLight(0xbfd4ff, 0x30343c, 0.9)
    scene.add(hemi)
    const key = new THREE.DirectionalLight(0xffffff, 2.0)
    key.position.set(5, 10, 6)
    scene.add(key)
    const fill = new THREE.DirectionalLight(0xcfe0ff, 0.8)
    fill.position.set(-6, 4, 3)
    scene.add(fill)
    const rim = new THREE.DirectionalLight(0xfff4e0, 0.55)
    rim.position.set(-3, 6, -8)
    scene.add(rim)
    sceneLightsRef.current = { hemi, key, fill, rim }

    scene.add(new THREE.GridHelper(20, 20, 0x3a3f4a, 0x262a32))

    function onResize() {
      camera.aspect = mount.clientWidth / mount.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(mount.clientWidth, mount.clientHeight)
    }
    window.addEventListener('resize', onResize)

    let frameId
    function animate() {
      frameId = requestAnimationFrame(animate)
      controls.update()
      // Animated water (scope §10): cores, droplets, mist, foam, waves.
      const elapsed = clockRef.current.getElapsedTime()
      waterRef.current?.update?.(elapsed)
      renderer.render(scene, camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(frameId)
      window.removeEventListener('resize', onResize)
      controls.dispose()
      renderer.dispose()
      mount.removeChild(renderer.domElement)
    }
  }, [])

  // Swap in the real sculpture + basin meshes on new engineering results.
  useEffect(() => {
    const scene = sceneRef.current
    if (!scene) return
    if (groupRef.current) {
      scene.remove(groupRef.current)
      groupRef.current.traverse?.((o) => {
        o.geometry?.dispose()
        o.material?.dispose()
      })
      groupRef.current = null
    }
    if (waterRef.current?.group) {
      scene.remove(waterRef.current.group)
      waterRef.current.group.traverse?.((o) => {
        o.geometry?.dispose()
        o.material?.dispose()
      })
      waterRef.current = null
    }
    if (!engineering) return

    const group = new THREE.Group()
    const steel = new THREE.MeshStandardMaterial({
      color: 0xffffff, roughness: 0.08, metalness: 1.0,
      envMapIntensity: 1.3, side: THREE.DoubleSide,
    })
    const stone = new THREE.MeshStandardMaterial({
      color: 0x35383e, roughness: 0.35, metalness: 0.2,
      envMapIntensity: 0.6, side: THREE.DoubleSide,
    })

    const sculpture = toMesh(engineering.sculpture.mesh, steel)
    sculpture.position.y = engineering.sculpture_offset_m
    group.add(sculpture)

    if (engineering.basin) {
      group.add(toMesh(engineering.basin, stone))
    }

    // Internal skeleton (scope §15) — x-ray overlay, toggled from the toolbar.
    if (engineering.skeleton?.mesh?.vertices?.length) {
      const skelMat = new THREE.MeshStandardMaterial({
        color: 0xff9f43, roughness: 0.5, metalness: 0.4,
        transparent: true, opacity: 0.9,
      })
      const skel = toMesh(engineering.skeleton.mesh, skelMat)
      skel.name = 'skeleton'
      skel.position.y = engineering.sculpture_offset_m
      skel.visible = showSkeletonRef.current
      group.add(skel)
    }

    scene.add(group)
    groupRef.current = group

    // Illumination heat-map overlay (scope §13): shell faces colored by lux.
    const faceLux = engineering.lighting?.illumination?.face_lux
    if (faceLux && faceLux.length === engineering.sculpture.mesh.faces.length) {
      const mesh = engineering.sculpture.mesh
      const geoL = new THREE.BufferGeometry()
      geoL.setAttribute('position',
        new THREE.Float32BufferAttribute(mesh.vertices.flat(), 3))
      geoL.setIndex(mesh.faces.flat())
      // Average face lux onto vertices, map to a blue->red ramp.
      const vLux = new Float32Array(mesh.vertices.length)
      const vCnt = new Float32Array(mesh.vertices.length)
      mesh.faces.forEach((f, i) => {
        for (const vi of f) { vLux[vi] += faceLux[i]; vCnt[vi] += 1 }
      })
      const colors = new Float32Array(mesh.vertices.length * 3)
      const maxLux = Math.max(...faceLux, 1)
      for (let vi = 0; vi < mesh.vertices.length; vi++) {
        const t = Math.min(vLux[vi] / (vCnt[vi] || 1) / (maxLux * 0.8), 1)
        const c = new THREE.Color().setHSL(0.63 * (1 - t), 0.9, 0.5)
        colors.set([c.r, c.g, c.b], vi * 3)
      }
      geoL.setAttribute('color', new THREE.BufferAttribute(colors, 3))
      const luxMesh = new THREE.Mesh(geoL, new THREE.MeshBasicMaterial({
        vertexColors: true, transparent: true, opacity: 0.85,
      }))
      luxMesh.name = 'luxmap'
      luxMesh.position.y = engineering.sculpture_offset_m + 0.005
      luxMesh.visible = showLuxRef.current
      group.add(luxMesh)
    }

    // Water effects (scope §10) — AquaFlow-derived stack: tapered core
    // columns, breakup droplets, apex mist, impact foam, Gerstner surface.
    const viz = engineering.water_viz
    if (viz) {
      const fx = buildWaterFX(viz)
      fx.group.visible = showWaterRef.current
      scene.add(fx.group)
      waterRef.current = { group: fx.group, update: fx.update }
    }
  }, [engineering])

  // Wireframe toggle applies to everything in the current model group.
  useEffect(() => {
    groupRef.current?.traverse((o) => {
      if (o.material && o.name !== 'skeleton') o.material.wireframe = wireframe
    })
  }, [wireframe, engineering])

  // Skeleton x-ray visibility.
  useEffect(() => {
    const skel = groupRef.current?.getObjectByName('skeleton')
    if (skel) skel.visible = showSkeleton
  }, [showSkeleton, engineering])

  // Water visibility toggle.
  useEffect(() => {
    if (waterRef.current?.group) waterRef.current.group.visible = showWater
  }, [showWater, engineering])

  // Lux heat-map visibility.
  useEffect(() => {
    const lm = groupRef.current?.getObjectByName('luxmap')
    if (lm) lm.visible = showLux
  }, [showLux, engineering])

  // Site photo backdrop (scope §30 site integration).
  useEffect(() => {
    const scene = sceneRef.current
    if (!scene) return
    if (!backdrop) {
      scene.background = new THREE.Color(night ? 0x06080c : 0x0b0e12)
      scene.backgroundBlurriness = 0
      return
    }
    new THREE.TextureLoader().load(backdrop, (tex) => {
      tex.colorSpace = THREE.SRGBColorSpace
      scene.background = tex
    })
    return () => URL.revokeObjectURL(backdrop)
  }, [backdrop, night])

  // Night mode (scope §30): dark sky, dimmed key lights, glowing water.
  useEffect(() => {
    const scene = sceneRef.current
    const lights = sceneLightsRef.current
    if (!scene || !lights) return
    if (!backdropRef.current) {
      scene.background = new THREE.Color(night ? 0x06080c : 0x0b0e12)
      scene.fog = new THREE.Fog(night ? 0x06080c : 0x0b0e12, 20, 60)
    }
    lights.hemi.intensity = night ? 0.25 : 0.9
    lights.key.intensity = night ? 0.4 : 1.6
    lights.fill.intensity = night ? 0.2 : 0.8
    lights.rim.intensity = night ? 0.9 : 0.55   // subtle warm rim
    if (waterRef.current?.group) {
      waterRef.current.group.traverse((o) => {
        if (o.material?.opacity !== undefined) {
          o.material.opacity = night
            ? Math.min(o.material.opacity * 1.3, 1.0)
            : o.material.opacity
        }
      })
    }
  }, [night, engineering])

  function setView(preset) {
    const camera = cameraRef.current
    const controls = controlsRef.current
    if (!camera || !controls) return
    const size = engineering?.geo_quantities?.bounding_box?.size ?? [4, 4, 4]
    const d = Math.max(size[0], size[1], size[2]) * 1.8 + 2
    const cy = size[1] / 2
    const pos = {
      front: [0, cy, d],
      top: [0, d * 1.2, 0.001],
      right: [d, cy, 0],
      iso: [d * 0.7, d * 0.55, d * 0.7],
    }[preset]
    camera.position.set(...pos)
    controls.target.set(0, cy, 0)
    controls.update()
  }

  const size = engineering?.geo_quantities?.bounding_box?.size

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mountRef} style={{ width: '100%', height: '100%' }} />
      <div className="view-tools">
        {['front', 'top', 'right', 'iso'].map((v) => (
          <button key={v} className="btn" onClick={() => setView(v)}>
            {v[0].toUpperCase() + v.slice(1)}
          </button>
        ))}
        <button
          className={`btn ${wireframe ? 'active' : ''}`}
          onClick={() => setWireframe((w) => !w)}
        >
          Wireframe
        </button>
        <button
          className={`btn ${showSkeleton ? 'active' : ''}`}
          onClick={() => setShowSkeleton((s) => !s)}
          disabled={!engineering?.skeleton}
          title="Show internal structural skeleton"
        >
          Skeleton
        </button>
        <button
          className={`btn ${showWater ? 'active' : ''}`}
          onClick={() => setShowWater((w) => !w)}
          disabled={!engineering?.water_viz}
          title="Show water effects"
        >
          Water
        </button>
        <button
          className={`btn ${night ? 'active' : ''}`}
          onClick={() => setNight((n) => !n)}
          title="Night rendering preview"
        >
          Night
        </button>
        <button
          className={`btn ${showLux ? 'active' : ''}`}
          onClick={() => setShowLux((l) => !l)}
          disabled={!engineering?.lighting?.illumination?.face_lux}
          title="Illumination heat map (lux on shell)"
        >
          Lux
        </button>
        <label className="btn" title="Load a site photo as the backdrop">
          Site
          <input type="file" accept="image/*" style={{ display: 'none' }}
                 onChange={(e) => {
                   const f = e.target.files?.[0]
                   if (f) setBackdrop(URL.createObjectURL(f))
                 }} />
        </label>
        {backdrop && (
          <button className="btn" onClick={() => setBackdrop(null)}>
            Clear
          </button>
        )}
      </div>
      {size && (
        <div className="view-dims">
          {size.map((v) => v.toFixed(2)).join(' × ')} m
        </div>
      )}
    </div>
  )
}
