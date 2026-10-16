"use client";
// components/drone/DroneScene.jsx
// Scroll-driven exploded view with a HUD frame, live readout and part labels.
// Needs: three @react-three/fiber @react-three/drei gsap
// Model: /public/models/aerospark.glb  (parts named esp32 / pcb / mosfet / sensor / motor / frame)

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, Html, useGLTF } from "@react-three/drei";
import * as THREE from "three";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

/* ---------- 1. Parts (facts only, taken from the team's docs) ---------- */
// side: which way the label sits next to the part
export const PARTS = [
  { id: "esp32", match: "esp32", dir: [0, 1, 0], dist: 1.8, side: "right",
    label: "XIAO ESP32-S3",
    specs: ["Dual-core LX7, Wi-Fi / BLE", "The flight computer"] },
  { id: "pcb", match: "pcb", dir: [0, 1, 0], dist: 1.1, side: "left",
    label: "PCB baseplate",
    specs: ["Perfboard carrier with sockets", "Carries the ESP32 and drivers"] },
  { id: "mosfet", match: "mosfet", dir: [0, 1, 0], dist: 0.5, side: "left",
    label: "MOSFET drivers",
    specs: ["Gate drivers for the 4 motors", "PWM from the ESP32 (LEDC)"] },
  { id: "sensors", match: "sensor", dir: [0, -1, 0], dist: 1.4, side: "left",
    label: "ToF + optical flow",
    specs: ["VL53L0X altitude (I2C)", "ADNS3080 drift (SPI)"] },
  { id: "motor", match: "motor", radial: true, dist: 1.6, side: "right",
    label: "8520 coreless motors",
    specs: ["4× DC motors", "PWM 0–255 per motor"] },
  { id: "frame", match: "frame", dir: [0, -1, 0], dist: 0.2, side: "left",
    label: "Airframe",
    specs: ["Printable CAD frame", "Keeps the build light"] },
];

/* ---------- 2. Scroll progress (GSAP ScrollTrigger, 0 → 1) ---------- */
function useScrollProgress(triggerRef) {
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

// assembled → explode (0.15-0.4) → hold → reassemble (0.65-0.9) → assembled
const smooth = (a, b, x) => THREE.MathUtils.smoothstep(x, a, b);
const explodeAmount = (p) => smooth(0.15, 0.4, p) - smooth(0.65, 0.9, p);

/* ---------- 3. The drone model ---------- */
function Drone({ progress, amountRef, onParts, onSelect }) {
  const { scene } = useGLTF("/models/aerospark.glb");
  const root = useRef();

  const parts = useMemo(() => {
    const found = [];
    const claimed = new Set();
    const box = new THREE.Box3().setFromObject(scene);
    const centre = box.getCenter(new THREE.Vector3());

    scene.traverse((node) => {
      const name = node.name.toLowerCase();
      const cfg = PARTS.find((p) => name.includes(p.match));
      if (!cfg) return;
      for (let n = node.parent; n; n = n.parent) if (claimed.has(n)) return;
      claimed.add(node);

      const origin = node.position.clone();
      let dir = new THREE.Vector3(...(cfg.dir ?? [0, 0, 0]));
      if (cfg.radial) {
        const w = node.getWorldPosition(new THREE.Vector3()).sub(centre);
        dir = new THREE.Vector3(w.x, 0, w.z).normalize();
      }
      node.userData.partId = cfg.id;
      found.push({ node, origin, dir, dist: cfg.dist });
    });
    return found;
  }, [scene]);

  // tell the parent which node to hang each label on (first node of each part)
  useEffect(() => {
    const firsts = PARTS.map((cfg) => {
      const hit = parts.find((p) => p.node.userData.partId === cfg.id);
      return hit ? { cfg, node: hit.node } : null;
    }).filter(Boolean);
    onParts(firsts);
  }, [parts, onParts]);

  useFrame((state, delta) => {
    amountRef.current = THREE.MathUtils.damp(
      amountRef.current,
      explodeAmount(progress.current),
      6,
      delta
    );
    const a = amountRef.current;

    for (const { node, origin, dir, dist } of parts) {
      node.position.copy(origin).addScaledVector(dir, dist * a);
    }
    if (root.current) root.current.rotation.y += delta * 0.35 * (1 - a);

    const cam = state.camera;
    const aspect = state.size.width / state.size.height;
    const fit = aspect < 1 ? 1 + (1 - aspect) * 0.9 : 1;
    const target = new THREE.Vector3(
      THREE.MathUtils.lerp(0, 3.2, a),
      THREE.MathUtils.lerp(1.3, 2.4, a),
      THREE.MathUtils.lerp(5.2, 8.6, a) * fit
    );
    cam.position.lerp(target, 1 - Math.exp(-4 * delta));
    cam.lookAt(0, 0.3 * a, 0);
  });

  const handleOver = (e) => {
    e.stopPropagation();
    let n = e.object;
    while (n && !n.userData.partId) n = n.parent;
    if (n && amountRef.current > 0.6) onSelect({ id: n.userData.partId, point: e.point.clone() });
  };

  return (
    <group ref={root}>
      <primitive object={scene} onPointerOver={handleOver} onClick={handleOver} onPointerMissed={() => onSelect(null)} />
    </group>
  );
}

/* ---------- 4. Labels that follow each part ---------- */
function PartLabel({ cfg, node, amountRef }) {
  const group = useRef();
  const el = useRef();
  const v = useMemo(() => new THREE.Vector3(), []);

  useFrame(() => {
    node.getWorldPosition(v);
    group.current.position.copy(v);
    if (el.current) {
      el.current.style.opacity = String(THREE.MathUtils.clamp((amountRef.current - 0.55) * 3, 0, 1));
    }
  });

  const left = cfg.side === "left";
  return (
    <group ref={group}>
      <Html zIndexRange={[10, 0]} style={{ pointerEvents: "none" }}>
        <div
          ref={el}
          style={{ opacity: 0, transform: left ? "translate(-100%, -50%)" : "translateY(-50%)" }}
          className={`flex items-center gap-2 whitespace-nowrap ${left ? "flex-row-reverse" : ""}`}
        >
          <span className="h-2 w-2 shrink-0 rounded-full bg-[#00F2FE] shadow-[0_0_10px_#00F2FE]" />
          <span className="h-px w-12 bg-gradient-to-r from-[#00F2FE] to-[#00F2FE]/10" style={left ? { transform: "scaleX(-1)" } : undefined} />
          <span className="rounded border border-[#00F2FE]/40 bg-[#121824]/85 px-2 py-1 font-mono text-[11px] text-[#F0F4F8] backdrop-blur">
            {cfg.label}
          </span>
        </div>
      </Html>
    </group>
  );
}

/* ---------- 5. Click / hover info card ---------- */
function HudCard({ selected }) {
  if (!selected) return null;
  const part = PARTS.find((p) => p.id === selected.id);
  return (
    <Html position={selected.point} distanceFactor={8} zIndexRange={[30, 0]}>
      <div className="w-56 rounded-xl border border-[#00F2FE]/50 bg-[#121824]/85 p-3 text-[#F0F4F8] shadow-[0_0_28px_#00F2FE40] backdrop-blur-md">
        <p className="font-mono text-xs tracking-widest text-[#00F2FE]">{part.label.toUpperCase()}</p>
        <ul className="mt-2 space-y-0.5 text-xs text-[#94a3b8]">
          {part.specs.map((s) => <li key={s}>• {s}</li>)}
        </ul>
      </div>
    </Html>
  );
}

function InfoPanel({ selected }) {
  const part = selected ? PARTS.find((p) => p.id === selected.id) : null;
  if (!part) return null;
  return (
    <div className="pointer-events-none absolute inset-x-5 bottom-14 z-10 flex justify-center md:bottom-16">
      <div className="w-full max-w-sm rounded-xl border border-[#00F2FE]/50 bg-[#121824]/90 p-3 text-[#F0F4F8] shadow-[0_0_28px_#00F2FE40] backdrop-blur-md">
        <p className="font-mono text-xs tracking-widest text-[#00F2FE]">{part.label.toUpperCase()}</p>
        <ul className="mt-2 space-y-0.5 text-xs text-[#94a3b8]">
          {part.specs.map((sp) => <li key={sp}>• {sp}</li>)}
        </ul>
      </div>
    </div>
  );
}

/* ---------- 6. HUD frame drawn over the canvas ---------- */
const corner = "absolute h-6 w-6 border-[#00F2FE]/70";

function Hud({ progress }) {
  const pctRef = useRef(null);
  const stageRef = useRef(null);
  const barRef = useRef(null);

  useEffect(() => {
    const id = setInterval(() => {
      const p = progress.current;
      const a = explodeAmount(p);
      if (pctRef.current) pctRef.current.textContent = String(Math.round(a * 100)).padStart(3, "0");
      if (barRef.current) barRef.current.style.width = `${Math.round(p * 100)}%`;
      if (stageRef.current) {
        stageRef.current.textContent =
          a < 0.02 ? "ASSEMBLED" : a > 0.98 ? "EXPLODED" : p < 0.5 ? "SEPARATING" : "REASSEMBLING";
      }
    }, 60);
    return () => clearInterval(id);
  }, [progress]);

  return (
    <div className="pointer-events-none absolute inset-x-5 bottom-5 top-28 md:inset-x-10 md:top-24">
      <span className={`${corner} left-0 top-0 border-l border-t`} />
      <span className={`${corner} right-0 top-0 border-r border-t`} />
      <span className={`${corner} bottom-0 left-0 border-b border-l`} />
      <span className={`${corner} bottom-0 right-0 border-b border-r`} />

      <p className="absolute left-4 top-3 font-mono text-[11px] tracking-widest text-[#00F2FE]">
        AEROSPARK // EXPLODED VIEW
      </p>
      <p ref={stageRef} className="absolute right-4 top-3 font-mono text-[11px] tracking-widest text-[#FFB300]">
        ASSEMBLED
      </p>
      <p className="absolute bottom-3 left-4 font-mono text-[11px] tracking-widest text-[#94a3b8]">
        EXPLOSION <span ref={pctRef} className="text-[#F0F4F8]">000</span>%
      </p>
      <p className="absolute bottom-3 right-4 hidden font-mono text-[11px] tracking-widest text-[#64748B] sm:block">
        HOVER A PART FOR DETAILS
      </p>
      <div className="absolute inset-x-0 bottom-3 mx-auto hidden h-1 w-40 overflow-hidden rounded bg-white/10 sm:block">
        <div ref={barRef} className="h-full w-0 bg-[#00F2FE]" />
      </div>
    </div>
  );
}

/* ---------- 7. The section you drop on the page ---------- */
export default function DroneScene() {
  const sectionRef = useRef(null);
  const progress = useScrollProgress(sectionRef);
  const amountRef = useRef(0);
  const [selected, setSelected] = useState(null);
  const [labelParts, setLabelParts] = useState([]);

  return (
    <section ref={sectionRef} className="relative h-[500vh] bg-[#0A0D14]">
      <div className="sticky top-0 h-screen w-full overflow-hidden">
        {/* background: grid + glow */}
        <div className="bg-grid bg-grid-fade absolute inset-0" />
        <div className="absolute left-1/2 top-1/2 h-[520px] w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#00F2FE]/10 blur-3xl" />

        <div className="absolute inset-0">
          <Canvas camera={{ position: [0, 1.3, 5.2], fov: 40 }} dpr={[1, 2]}>
            <ambientLight intensity={0.5} />
            <directionalLight position={[5, 6, 4]} intensity={1.2} color="#F0F4F8" />
            <pointLight position={[-4, 2, -3]} intensity={30} color="#00F2FE" />
            <Suspense fallback={null}>
              <Drone progress={progress} amountRef={amountRef} onParts={setLabelParts} onSelect={setSelected} />
              {labelParts.map(({ cfg, node }) => (
                <PartLabel key={cfg.id} cfg={cfg} node={node} amountRef={amountRef} />
              ))}
              <Environment preset="city" environmentIntensity={0.3} />
            </Suspense>
          </Canvas>
        </div>

        <Hud progress={progress} />
        <InfoPanel selected={selected} />
      </div>
    </section>
  );
}

useGLTF.preload("/models/aerospark.glb");
