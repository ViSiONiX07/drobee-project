"use client";
// components/drone/ExplodedDrone.jsx
// Scroll-driven exploded view for a GLB drone model.
// npm i three @react-three/fiber @react-three/drei gsap
//
// MODEL NAMING: in Blender, name each part's top-level object so it contains one of
// the `match` keys below (e.g. "esp32s3_body", "motor_FL", "motor_FR"...).
// Export as GLB with "+Y Up". Put it at /public/models/aerospark.glb

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Html, useGLTF } from "@react-three/drei";
import * as THREE from "three";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

/* ---------- 1. Part config: edit to match your model ---------- */
// dir: explode direction. radial: push outward from the model centre (for motors).
// dist: how far (scene units). info: shown in the HUD card.
export const PARTS = [
  { id: "esp32", match: "esp32", dir: [0, 1, 0], dist: 2.4,
    info: { title: "XIAO ESP32S3", specs: ["Dual-core LX7 @ 240 MHz", "USB-C serial/JTAG", "3.3 V logic"], weight: "3.0 g" } },
  { id: "pcb", match: "pcb", dir: [0, 1, 0], dist: 1.4,
    info: { title: "MPU6050 + Custom PCB", specs: ["6-axis IMU, I²C", "Power + signal baseplate"], weight: "4.5 g" } },
  { id: "mosfet", match: "mosfet", dir: [0, 1, 0], dist: 0.6,
    info: { title: "IRLZ44N MOSFETs + Flyback Diodes", specs: ["Logic-level gate drive", "One per motor channel"], weight: "2.0 g" } },
  { id: "sensors", match: "sensor", dir: [0, -1, 0], dist: 1.6,
    info: { title: "ADNS-3080 + VL53L0X", specs: ["Optical flow vectors", "ToF altitude, I²C"], weight: "2.5 g" } },
  { id: "motor", match: "motor", radial: true, dist: 1.8,
    info: { title: "Coreless Motors", specs: ["Amber/gold wire scheme", "PWM via MOSFET"], weight: "4 × 3.2 g" } },
  { id: "frame", match: "frame", dir: [0, -1, 0], dist: 0.3,
    info: { title: "3D-Printed Micro-Frame", specs: ["Lightweight structural base"], weight: "~6 g" } },
];

/* ---------- 2. Scroll progress via GSAP ScrollTrigger (0 → 1) ---------- */
export function useScrollProgress(triggerRef) {
  const progress = useRef(0);
  useEffect(() => {
    if (!triggerRef.current) return;
    const st = ScrollTrigger.create({
      trigger: triggerRef.current,
      start: "top top",
      end: "bottom bottom",
      scrub: true,
      onUpdate: (self) => (progress.current = self.progress),
    });
    return () => st.kill();
  }, [triggerRef]);
  return progress;
}

// 0–0.15 assembled → 0.15–0.4 explode → 0.4–0.65 hold → 0.65–0.9 reassemble → 0.9–1 assembled
const smooth = (a, b, x) => THREE.MathUtils.smoothstep(x, a, b);
const explodeAmount = (p) => smooth(0.15, 0.4, p) - smooth(0.65, 0.9, p);

/* ---------- 3. The model ---------- */
function Drone({ progress, onSelect }) {
  const { scene } = useGLTF("/models/aerospark.glb");
  const root = useRef();
  const amount = useRef(0);

  // Collect parts once: remember each node's original position + resolved direction.
  const parts = useMemo(() => {
    const found = [];
    const claimed = new Set();
    const box = new THREE.Box3().setFromObject(scene);
    const centre = box.getCenter(new THREE.Vector3());

    scene.traverse((node) => {
      const name = node.name.toLowerCase();
      const cfg = PARTS.find((p) => name.includes(p.match));
      if (!cfg) return;
      // skip children of an already-claimed node
      for (let n = node.parent; n; n = n.parent) if (claimed.has(n)) return;
      claimed.add(node);

      const origin = node.position.clone();
      let dir = new THREE.Vector3(...(cfg.dir ?? [0, 0, 0]));
      if (cfg.radial) {
        const world = node.getWorldPosition(new THREE.Vector3()).sub(centre);
        dir = new THREE.Vector3(world.x, 0, world.z).normalize();
      }
      node.userData.partId = cfg.id;
      found.push({ node, origin, dir, dist: cfg.dist });
    });
    return found;
  }, [scene]);

  useFrame((state, delta) => {
    const p = progress.current;
    // damp so fast scrolling never makes parts snap
    amount.current = THREE.MathUtils.damp(amount.current, explodeAmount(p), 6, delta);

    for (const { node, origin, dir, dist } of parts) {
      node.position.copy(origin).addScaledVector(dir, dist * amount.current);
    }

    // idle hero spin that eases off while exploded so tooltips stay readable
    if (root.current) root.current.rotation.y += delta * 0.35 * (1 - amount.current);

    // camera: pull back + tilt as parts separate
    const cam = state.camera;
    const target = new THREE.Vector3(
      THREE.MathUtils.lerp(0, 4, amount.current),
      THREE.MathUtils.lerp(1.2, 2.6, amount.current),
      THREE.MathUtils.lerp(5, 8, amount.current)
    );
    cam.position.lerp(target, 1 - Math.exp(-4 * delta));
    cam.lookAt(0, 0.4 * amount.current, 0);
    state.__amount = amount.current;
  });

  const handleOver = (e) => {
    e.stopPropagation();
    let n = e.object;
    while (n && !n.userData.partId) n = n.parent;
    if (n && amount.current > 0.6) onSelect({ id: n.userData.partId, point: e.point.clone() });
  };

  return (
    <group ref={root}>
      <primitive
        object={scene}
        onPointerOver={handleOver}
        onClick={handleOver}
        onPointerMissed={() => onSelect(null)}
      />
    </group>
  );
}

/* ---------- 4. HUD card (glass) ---------- */
function HudCard({ selected }) {
  if (!selected) return null;
  const part = PARTS.find((p) => p.id === selected.id);
  return (
    <Html position={selected.point} distanceFactor={8} zIndexRange={[20, 0]}>
      <div className="w-56 rounded-xl border border-[#00F2FE]/40 bg-[#121824]/80 p-3 text-[#F0F4F8] shadow-[0_0_24px_#00F2FE33] backdrop-blur-md">
        <p className="text-sm font-semibold text-[#00F2FE]">{part.info.title}</p>
        <ul className="mt-1 space-y-0.5 text-xs text-[#64748B]">
          {part.info.specs.map((s) => <li key={s}>{s}</li>)}
        </ul>
        <p className="mt-2 text-xs text-[#FFB300]">Weight: {part.info.weight}</p>
      </div>
    </Html>
  );
}

/* ---------- 5. Scene + scroll section (drop this on your page) ---------- */
export default function DroneScroll() {
  const sectionRef = useRef(null);
  const progress = useScrollProgress(sectionRef);
  const [selected, setSelected] = useState(null);

  return (
    // tall section = scroll runway; the canvas stays pinned with sticky
    <section ref={sectionRef} className="relative h-[500vh] bg-[#0A0D14]">
      <div className="sticky top-0 h-screen w-full">
        <Canvas camera={{ position: [0, 1.2, 5], fov: 40 }} dpr={[1, 2]}>
          <ambientLight intensity={0.5} />
          <directionalLight position={[5, 6, 4]} intensity={1.2} color="#F0F4F8" />
          <pointLight position={[-4, 2, -3]} intensity={30} color="#00F2FE" />
          <Suspense fallback={null}>
            <Drone progress={progress} onSelect={setSelected} />
            <HudCard selected={selected} />
            <Environment preset="city" environmentIntensity={0.3} />
          </Suspense>
        </Canvas>
      </div>
    </section>
  );
}

useGLTF.preload("/models/aerospark.glb");
