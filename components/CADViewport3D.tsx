"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three-stdlib";
import {
  Eye,
  Maximize2,
  RotateCcw,
  Layers,
  Compass,
  Sparkles,
  Palette,
  Camera,
  Grid,
} from "lucide-react";

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
  const [wireframe, setWireframe] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [showBoundingBox, setShowBoundingBox] = useState(true);
  const [colormap, setColormap] = useState<"turbo" | "viridis" | "magma">("turbo");

  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const gridRef = useRef<THREE.GridHelper | null>(null);
  const wireBoxRef = useRef<THREE.LineSegments | null>(null);
  const mechGroupRef = useRef<THREE.Group | null>(null);

  // Set camera angles
  const setView = (type: "iso" | "top" | "front" | "side") => {
    if (!cameraRef.current || !controlsRef.current) return;
    const target = new THREE.Vector3(0.045, 0.0275, 0);
    controlsRef.current.target.copy(target);

    if (type === "iso") {
      cameraRef.current.position.set(0.045, -0.09, 0.13);
      cameraRef.current.up.set(0, 0, 1);
    } else if (type === "top") {
      cameraRef.current.position.set(0.045, 0.0275, 0.16);
      cameraRef.current.up.set(0, 1, 0);
    } else if (type === "front") {
      cameraRef.current.position.set(0.045, -0.14, 0.0);
      cameraRef.current.up.set(0, 0, 1);
    } else if (type === "side") {
      cameraRef.current.position.set(0.18, 0.0275, 0.0);
      cameraRef.current.up.set(0, 0, 1);
    }
    controlsRef.current.update();
  };

  const resetView = () => setView("iso");

  // Toggle wireframe on meshes
  useEffect(() => {
    if (mechGroupRef.current) {
      mechGroupRef.current.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const m = (child as THREE.Mesh).material as THREE.MeshStandardMaterial;
          if (m) m.wireframe = wireframe;
        }
      });
    }
  }, [wireframe]);

  // Toggle grid
  useEffect(() => {
    if (gridRef.current) {
      gridRef.current.visible = showGrid;
    }
  }, [showGrid]);

  // Toggle bounding box
  useEffect(() => {
    if (wireBoxRef.current) {
      wireBoxRef.current.visible = showBoundingBox;
    }
  }, [showBoundingBox]);

  useEffect(() => {
    const currentMount = mountRef.current;
    if (!currentMount) return;

    // 1. Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x020408); // Deep space graphite / engineering dark

    const width = currentMount.clientWidth || 800;
    const height = currentMount.clientHeight || 560;

    // 2. Camera setup centered on 90x55mm mechanism (0.045, 0.0275, 0)
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.001, 10);
    camera.position.set(0.045, -0.09, 0.13);
    camera.up.set(0, 0, 1);
    cameraRef.current = camera;

    // 3. Renderer with ACES Filmic tone mapping
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;
    renderer.shadowMap.enabled = true;
    currentMount.replaceChildren(renderer.domElement);

    // 4. OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0.045, 0.0275, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.screenSpacePanning = true;
    controls.minDistance = 0.03;
    controls.maxDistance = 0.35;
    controls.update();
    controlsRef.current = controls;

    // 5. High-contrast Engineering Studio Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.4);
    scene.add(ambientLight);

    // Cyan Keylight
    const keyLight = new THREE.DirectionalLight(0x00f7ff, 2.8);
    keyLight.position.set(0.12, 0.12, 0.18);
    scene.add(keyLight);

    // Rimlight
    const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.6);
    rimLight.position.set(-0.12, -0.12, 0.18);
    scene.add(rimLight);

    // Top fill
    const topLight = new THREE.DirectionalLight(0xffffff, 1.2);
    topLight.position.set(0.045, 0.0275, 0.2);
    scene.add(topLight);

    // 6. Professional CAD Grid Floor
    const grid = new THREE.GridHelper(0.18, 36, 0x0284c7, 0x0f172a);
    grid.rotation.x = Math.PI / 2;
    grid.position.set(0.045, 0.0275, -0.0051);
    scene.add(grid);
    gridRef.current = grid;

    // 7. Bounding Box [0, 90] x [0, 55] x [-5, +5] mm
    const boxGeo = new THREE.BoxGeometry(0.090, 0.055, 0.010);
    const boxEdges = new THREE.EdgesGeometry(boxGeo);
    const boxMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.35 });
    const wireBox = new THREE.LineSegments(boxEdges, boxMat);
    wireBox.position.set(0.045, 0.0275, 0);
    scene.add(wireBox);
    wireBoxRef.current = wireBox;

    // 8. Mechanism Group
    const mechGroup = new THREE.Group();
    scene.add(mechGroup);
    mechGroupRef.current = mechGroup;

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
                roughness: 0.32,
                metalness: 0.28,
                wireframe: wireframe,
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
    const clock = new THREE.Clock();

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
    <div className="relative w-full h-[580px] bg-neutral-950 rounded-2xl overflow-hidden border border-neutral-800 shadow-2xl transition group">
      {/* Three.js Canvas Container */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Modern Top CAD Control Bar */}
      <div className="absolute top-4 left-4 right-4 flex items-center justify-between pointer-events-none">
        {/* Left: Viewport Status & Coordinate Telemetry */}
        <div className="pointer-events-auto bg-black/85 backdrop-blur-md border border-neutral-800/80 rounded-xl px-4 py-2 text-xs font-mono text-neutral-300 flex items-center gap-4 shadow-xl">
          <div className="flex items-center space-x-2 text-cyan-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="tracking-wide">CAD VIEWPORT 3D</span>
          </div>
          <div className="hidden sm:flex items-center gap-3 text-neutral-400 text-[11px] border-l border-neutral-800 pl-4">
            <span>Envelope: <strong className="text-white">90×55×10mm</strong></span>
            <span>Target: <strong className="text-neutral-200">(45.0, 27.5, 0.0)</strong></span>
          </div>
        </div>

        {/* Right: Camera Orientation Quick-Toggles */}
        <div className="pointer-events-auto flex items-center gap-1.5 bg-black/85 backdrop-blur-md border border-neutral-800/80 rounded-xl p-1.5 shadow-xl text-xs font-mono">
          <button
            onClick={() => setView("iso")}
            className="px-2.5 py-1 rounded-lg bg-neutral-900 hover:bg-neutral-800 hover:text-cyan-400 text-neutral-300 transition text-[11px] font-medium"
            title="Isometric 3D View"
          >
            ISO
          </button>
          <button
            onClick={() => setView("top")}
            className="px-2.5 py-1 rounded-lg bg-neutral-900 hover:bg-neutral-800 hover:text-cyan-400 text-neutral-300 transition text-[11px] font-medium"
            title="Plan / Top View"
          >
            TOP
          </button>
          <button
            onClick={() => setView("front")}
            className="px-2.5 py-1 rounded-lg bg-neutral-900 hover:bg-neutral-800 hover:text-cyan-400 text-neutral-300 transition text-[11px] font-medium"
            title="Front Elevation"
          >
            FRONT
          </button>
          <button
            onClick={() => setView("side")}
            className="px-2.5 py-1 rounded-lg bg-neutral-900 hover:bg-neutral-800 hover:text-cyan-400 text-neutral-300 transition text-[11px] font-medium"
            title="Side Elevation"
          >
            SIDE
          </button>
          <div className="h-4 w-px bg-neutral-800 mx-1" />
          <button
            onClick={() => setWireframe(!wireframe)}
            className={`p-1.5 rounded-lg transition ${
              wireframe ? "bg-cyan-400 text-black font-bold" : "bg-neutral-900 text-neutral-400 hover:text-white"
            }`}
            title="Toggle Wireframe Mesh"
          >
            <Layers className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`p-1.5 rounded-lg transition ${
              showGrid ? "bg-neutral-800 text-cyan-400" : "bg-neutral-900 text-neutral-500 hover:text-white"
            }`}
            title="Toggle CAD Grid"
          >
            <Grid className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={resetView}
            className="p-1.5 rounded-lg bg-neutral-900 text-neutral-400 hover:text-white hover:bg-neutral-800 transition"
            title="Reset Camera Center"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Floating Instructions HUD Bottom-Left */}
      <div className="absolute bottom-4 left-4 bg-black/85 backdrop-blur-md border border-neutral-800/80 rounded-xl p-3 text-[11px] font-mono text-neutral-400 space-y-1 select-none pointer-events-none shadow-xl">
        <div className="flex items-center gap-1.5 text-neutral-300 font-semibold mb-0.5">
          <Compass className="w-3.5 h-3.5 text-cyan-400" />
          <span>Interactive Orbit Controls</span>
        </div>
        <div>Left Click: <span className="text-neutral-200">Orbit</span> • Right Click: <span className="text-neutral-200">Pan</span></div>
        <div>Scroll Wheel: <span className="text-neutral-200">Continuous Zoom</span></div>
      </div>

      {/* Deformation & Stress Color Scale HUD Bottom-Right */}
      <div className="absolute bottom-4 right-4 bg-black/85 backdrop-blur-md border border-neutral-800/80 rounded-xl p-3 text-xs font-mono text-neutral-300 select-none pointer-events-none shadow-xl min-w-[210px]">
        <div className="flex items-center justify-between text-[10px] uppercase tracking-wider text-neutral-400 mb-1.5">
          <span>Von Mises Stress Field</span>
          <span className="text-cyan-400 font-bold">FEA Q4</span>
        </div>
        <div className="w-full h-2.5 rounded-full bg-gradient-to-r from-blue-600 via-cyan-400 via-amber-400 to-rose-500 shadow-inner" />
        <div className="flex justify-between text-[11px] text-neutral-400 mt-1.5 font-semibold">
          <span>0.0 MPa</span>
          <span>{(maxStressMPa / 2).toFixed(1)}</span>
          <span className="text-rose-400 font-bold">{maxStressMPa.toFixed(1)} MPa</span>
        </div>
      </div>

      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/90 backdrop-blur-md text-cyan-400 text-xs font-mono space-y-2 z-20">
          <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
          <span>Rendering Solid Spatial CAD Geometry...</span>
        </div>
      )}
    </div>
  );
}
