import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
import useBriefStore from '../store/briefStore'

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
  const showSkeletonRef = useRef(false)
  showSkeletonRef.current = showSkeleton
  const showWaterRef = useRef(true)
  showWaterRef.current = showWater
  const waterRef = useRef(null)   // animated water particle systems
  const clockRef = useRef(new THREE.Clock())

  useEffect(() => {
    const mount = mountRef.current
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x14161a) // dark studio
    scene.fog = new THREE.Fog(0x14161a, 20, 60)
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
    scene.add(new THREE.HemisphereLight(0xbfd4ff, 0x30343c, 0.9))
    const key = new THREE.DirectionalLight(0xffffff, 2.0)
    key.position.set(5, 10, 6)
    scene.add(key)
    const fill = new THREE.DirectionalLight(0xcfe0ff, 0.8)
    fill.position.set(-6, 4, 3)
    scene.add(fill)
    const rim = new THREE.DirectionalLight(0xffe8c0, 1.2)
    rim.position.set(-3, 6, -8)
    scene.add(rim)

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
      // Ballistic jet particles (scope §10: trajectory + gravity).
      const elapsed = clockRef.current.getElapsedTime()
      if (waterRef.current?.jets) {
        for (const jet of waterRef.current.jets) {
          const { v0, origin, count, phases } = jet.userData
          const pos = jet.geometry.attributes.position
          const tMax = (2 * v0) / 9.81
          for (let i = 0; i < count; i++) {
            const t = (elapsed * 1.0 + phases[i] * tMax) % tMax
            const y = Math.max(v0 * t - 4.905 * t * t, 0)
            pos.setXYZ(i, origin[0], origin[1] + y, origin[2])
          }
          pos.needsUpdate = true
        }
      }
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

    // Water effects (scope §10): surface + animated jets + curtain sheets.
    waterRef.current = null
    const viz = engineering.water_viz
    if (viz && showWaterRef.current) {
      const waterGroup = new THREE.Group()
      waterGroup.name = 'water'
      const jetSystems = []

      if (viz.basin_inner?.radius_m) {
        const surface = new THREE.Mesh(
          new THREE.CircleGeometry(viz.basin_inner.radius_m, 64),
          new THREE.MeshStandardMaterial({
            color: 0x1a4a6e, transparent: true, opacity: 0.75,
            roughness: 0.05, metalness: 0.4, side: THREE.DoubleSide,
          }))
        surface.rotation.x = -Math.PI / 2
        surface.position.y = viz.water_level_m
        waterGroup.add(surface)
      }

      for (const j of viz.jets || []) {
        const count = 24
        const geoJ = new THREE.BufferGeometry()
        geoJ.setAttribute('position',
          new THREE.Float32BufferAttribute(new Float32Array(count * 3), 3))
        const pts = new THREE.Points(geoJ, new THREE.PointsMaterial({
          color: 0xbfe3ff, size: 0.07, transparent: true, opacity: 0.75,
          blending: THREE.AdditiveBlending, depthWrite: false,
        }))
        pts.userData = {
          v0: j.exit_velocity_ms, origin: j.position, count,
          phases: Array.from({ length: count }, (_, i) => i / count),
        }
        jetSystems.push(pts)
        waterGroup.add(pts)
      }

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
        waterGroup.add(sheet)
      }

      scene.add(waterGroup)
      groupRef.current = group // keep model group reference
      waterRef.current = { group: waterGroup, jets: jetSystems }
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
      </div>
      {size && (
        <div className="view-dims">
          {size.map((v) => v.toFixed(2)).join(' × ')} m
        </div>
      )}
    </div>
  )
}
