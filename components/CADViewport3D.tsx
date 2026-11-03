"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three-stdlib";

interface ViewportProps {
  modelUrl: string;
  isDeformed: boolean;
  deformationScale: number;
  strokeDyMm: number;
  maxStressMPa: number;
}

export default function CADViewport3D({
  modelUrl,
  isDeformed,
  deformationScale,
  strokeDyMm,
  maxStressMPa,
}: ViewportProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const currentMount = mountRef.current;
    if (!currentMount) return;

    // 1. Ultra Pure Pitch-Black Scene (#000000)
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);

    const width = currentMount.clientWidth || 800;
    const height = currentMount.clientHeight || 560;

    // 2. Camera looking at the geometric center of the 90x55mm envelope: (0.045, 0.0275, 0)
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.001, 10);
    camera.position.set(0.045, -0.09, 0.13);
    camera.up.set(0, 0, 1);

    // 3. Renderer with pure black tone mapping
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    renderer.shadowMap.enabled = true;
    currentMount.replaceChildren(renderer.domElement);

    // 4. Smooth CAD OrbitControls centered exactly on mechanism
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0.045, 0.0275, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.screenSpacePanning = true;
    controls.minDistance = 0.03;
    controls.maxDistance = 0.35;
    controls.update();

    // 5. High-contrast Studio Lighting on Pure Black
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);

    // Cyber Cyan Keylight
    const keyLight = new THREE.DirectionalLight(0x00f7ff, 3.0);
    keyLight.position.set(0.12, 0.12, 0.18);
    scene.add(keyLight);

    // Subtle Rimlight
    const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.8);
    rimLight.position.set(-0.12, -0.12, 0.18);
    scene.add(rimLight);

    // Deep Toplight
    const topLight = new THREE.DirectionalLight(0xffffff, 1.0);
    topLight.position.set(0.045, 0.0275, 0.2);
    scene.add(topLight);

    // 6. Minimalist Dark Grid Floor on Pure Black
    const grid = new THREE.GridHelper(0.18, 36, 0x1e293b, 0x090d16);
    grid.rotation.x = Math.PI / 2;
    grid.position.set(0.045, 0.0275, -0.0051);
    scene.add(grid);

    // 7. Precision Physical Bounding Wireframe [0, 90] x [0, 55] x [-5, +5] mm
    const boxGeo = new THREE.BoxGeometry(0.090, 0.055, 0.010);
    const boxEdges = new THREE.EdgesGeometry(boxGeo);
    const boxMat = new THREE.LineBasicMaterial({ color: 0x0ea5e9, transparent: true, opacity: 0.35 });
    const wireBox = new THREE.LineSegments(boxEdges, boxMat);
    wireBox.position.set(0.045, 0.0275, 0);
    scene.add(wireBox);

    // 8. Mechanism Group
    const mechGroup = new THREE.Group();
    scene.add(mechGroup);

    // 9. Load Solid GLTF Model
    let isSubscribed = true;
    import("three/examples/jsm/loaders/GLTFLoader.js").then(({ GLTFLoader }) => {
      const loader = new GLTFLoader();
      loader.load(
        modelUrl,
        (gltf) => {
          if (!isSubscribed) return;
          mechGroup.clear();

          gltf.scene.traverse((child) => {
            if ((child as THREE.Mesh).isMesh) {
              const m = child as THREE.Mesh;
              m.material = new THREE.MeshStandardMaterial({
                vertexColors: true,
                roughness: 0.35,
                metalness: 0.25,
                flatShading: false,
              });
              m.castShadow = true;
              m.receiveShadow = true;
            }
          });

          mechGroup.add(gltf.scene);
          setLoading(false);
        },
        undefined,
        (err) => {
          console.error("Error loading GLTF:", err);
          setLoading(false);
        }
      );
    });

    // 10. Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      controls.update();

      if (isDeformed && mechGroup.children.length > 0) {
        const phase = (Math.sin(elapsed * 2.2) + 1.0) / 2.0;
        const dyMeters = (strokeDyMm / 1000.0) * deformationScale * phase;
        mechGroup.position.y = dyMeters;
      } else {
        mechGroup.position.y = 0;
      }

      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!currentMount) return;
      const w = currentMount.clientWidth;
      const h = currentMount.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      isSubscribed = false;
      cancelAnimationFrame(animId);
      controls.dispose();
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
    };
  }, [modelUrl, isDeformed, deformationScale, strokeDyMm]);

  return (
    <div className="relative w-full h-[540px] bg-black rounded-xl overflow-hidden border border-neutral-800 shadow-2xl">
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Floating CAD HUD Telemetry */}
      <div className="absolute top-4 left-4 bg-black/90 backdrop-blur-md border border-neutral-800 rounded-lg p-3 text-xs font-mono text-neutral-300 space-y-1 select-none pointer-events-none shadow-2xl">
        <div className="flex items-center space-x-2 text-cyan-400 font-semibold mb-1">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>3D ORBIT VIEWPORT</span>
        </div>
        <div className="text-neutral-400">Left-Click Orbit • Right-Click Pan • Scroll Zoom</div>
        <div className="text-neutral-400">Pivot Target: (45.0, 27.5, 0.0) mm [Mechanism Center]</div>
        <div className="text-neutral-300">Depth (Z): 10.00 mm Solid • Envelope: 90×55 mm</div>
      </div>

      {/* Deformation & Stress Color Scale */}
      <div className="absolute bottom-4 right-4 bg-black/90 backdrop-blur-md border border-neutral-800 rounded-lg p-3 text-xs font-mono text-neutral-300 select-none pointer-events-none shadow-2xl">
        <div className="text-[10px] uppercase tracking-wider text-neutral-400 mb-1">Von Mises Stress Field</div>
        <div className="w-40 h-2 rounded bg-gradient-to-r from-blue-600 via-cyan-400 via-amber-400 to-rose-500" />
        <div className="flex justify-between text-[10px] text-neutral-400 mt-1">
          <span>0 MPa</span>
          <span>{(maxStressMPa / 2).toFixed(1)}</span>
          <span className="text-rose-400 font-bold">{maxStressMPa.toFixed(1)} MPa</span>
        </div>
      </div>

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/90 backdrop-blur-sm text-cyan-400 text-sm font-mono">
          Loading 3D Solid Geometry...
        </div>
      )}
    </div>
  );
}
