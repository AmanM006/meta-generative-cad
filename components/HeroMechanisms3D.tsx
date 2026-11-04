"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { ChevronLeft, ChevronRight, RotateCcw } from "lucide-react";

export interface HeroModelOption {
  id: string;
  name: string;
  subtitle: string;
  tag: string;
  shapeType: "jack" | "torus-knot" | "gyroid" | "polyhedra";
}

export const HERO_MODELS: HeroModelOption[] = [
  {
    id: "orthogonal-jack",
    name: "Orthogonal Continuum Core",
    subtitle: "Tri-axial continuum intersection mechanism with iridized boundary lips",
    tag: "TRI-AXIAL JACK",
    shapeType: "jack",
  },
  {
    id: "torus-hyperflex",
    name: "Closed-Loop Kinematic Knot",
    subtitle: "Non-linear manifold torsion ring with continuous topological curvature",
    tag: "TORUS KNOT",
    shapeType: "torus-knot",
  },
  {
    id: "minimal-gyroid",
    name: "Triply Periodic Iso-Surface",
    subtitle: "Schwartz-P minimal surface flexure unit cell with zero mean curvature",
    tag: "GYROID CELL",
    shapeType: "gyroid",
  },
  {
    id: "polyhedral-cage",
    name: "Icosahedral Lattice Node",
    subtitle: "Truncated geodesic compliance node optimized for isotropic load dissipation",
    tag: "LATTICE NODE",
    shapeType: "polyhedra",
  },
];

export default function HeroMechanisms3D() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentIndex, setCurrentIndex] = useState(0);

  // Three.js object references
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const mechGroupRef = useRef<THREE.Group | null>(null);
  const shaderMatRef = useRef<THREE.ShaderMaterial | null>(null);

  const targetRotationRef = useRef<{ x: number; y: number }>({ x: 0.45, y: -0.65 });
  const currentRotationRef = useRef<{ x: number; y: number }>({ x: 0.45, y: -0.65 });
  const isDraggingRef = useRef(false);
  const lastMousePosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const activeModel = HERO_MODELS[currentIndex];

  const nextModel = () => {
    setCurrentIndex((prev) => (prev + 1) % HERO_MODELS.length);
  };

  const prevModel = () => {
    setCurrentIndex((prev) => (prev - 1 + HERO_MODELS.length) % HERO_MODELS.length);
  };

  const resetView = () => {
    targetRotationRef.current = { x: 0.45, y: -0.65 };
  };

  // 1. Initialize Scene & Shader
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 550;
    const height = container.clientHeight || 550;

    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
    camera.position.set(0, 0, 7.2);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
    renderer.domElement.style.cursor = "default";
    container.replaceChildren(renderer.domElement);
    rendererRef.current = renderer;

    // Iridescent Carl-Gordon Spectral Shader
    const customMaterial = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uMouse: { value: new THREE.Vector2(0, 0) },
      },
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        varying vec3 vWorldPosition;

        void main() {
          vNormal = normalize(normalMatrix * normal);
          vec4 worldPos = modelMatrix * vec4(position, 1.0);
          vWorldPosition = worldPos.xyz;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          vViewPosition = -mvPosition.xyz;
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        varying vec3 vWorldPosition;
        uniform float uTime;
        uniform vec2 uMouse;

        vec3 spectral(float t) {
          return 0.5 + 0.5 * cos(6.28318 * (vec3(1.0, 1.0, 1.0) * t + vec3(0.0, 0.33, 0.67)));
        }

        void main() {
          vec3 N = normalize(vNormal);
          vec3 V = normalize(vViewPosition);

          float fresnel = 1.0 - max(dot(N, V), 0.0);
          float fresnelPow = pow(fresnel, 2.4);

          vec3 L1 = normalize(vec3(4.0, 5.0, 5.5));
          vec3 H1 = normalize(L1 + V);
          float spec1 = pow(max(dot(N, H1), 0.0), 32.0);

          vec3 L2 = normalize(vec3(-4.5, -3.5, 4.0));
          vec3 H2 = normalize(L2 + V);
          float spec2 = pow(max(dot(N, H2), 0.0), 20.0);

          float iridCoord = dot(N, vec3(0.35, 0.65, 0.6)) * 0.85 + fresnelPow * 1.3 + uTime * 0.12;
          vec3 irid = spectral(iridCoord);

          // Deep metallic cyan/emerald base from Carl Gordon
          vec3 baseTone = mix(vec3(0.02, 0.22, 0.48), vec3(0.0, 0.88, 0.55), N.y * 0.5 + 0.5);

          vec3 finalColor = mix(baseTone, irid, fresnelPow * 0.85 + 0.25);
          finalColor += vec3(1.0, 1.0, 1.0) * spec1 * 1.6;
          finalColor += irid * spec2 * 1.2;
          finalColor += vec3(0.0, 1.0, 0.65) * pow(fresnel, 4.0) * 1.0;

          gl_FragColor = vec4(finalColor, 1.0);
        }
      `,
    });
    shaderMatRef.current = customMaterial;

    const mechGroup = new THREE.Group();
    scene.add(mechGroup);
    mechGroupRef.current = mechGroup;

    // Mouse drag controls
    const onMouseDown = (e: MouseEvent) => {
      isDraggingRef.current = true;
      lastMousePosRef.current = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      if (isDraggingRef.current) {
        const deltaX = e.clientX - lastMousePosRef.current.x;
        const deltaY = e.clientY - lastMousePosRef.current.y;
        targetRotationRef.current.y += deltaX * 0.008;
        targetRotationRef.current.x += deltaY * 0.008;
        lastMousePosRef.current = { x: e.clientX, y: e.clientY };
      } else {
        const rect = container.getBoundingClientRect();
        const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
        const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
        targetRotationRef.current.y = -0.65 + nx * 0.12;
        targetRotationRef.current.x = 0.45 + ny * 0.12;
      }
    };

    const onMouseUp = () => {
      isDraggingRef.current = false;
    };

    const dom = renderer.domElement;
    dom.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    // Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      if (customMaterial) {
        customMaterial.uniforms.uTime.value = elapsed;
      }

      // Smooth interpolation
      currentRotationRef.current.x += (targetRotationRef.current.x - currentRotationRef.current.x) * 0.07;
      currentRotationRef.current.y += (targetRotationRef.current.y - currentRotationRef.current.y) * 0.07;

      if (mechGroupRef.current) {
        mechGroupRef.current.rotation.x = currentRotationRef.current.x;
        mechGroupRef.current.rotation.y = currentRotationRef.current.y;
        mechGroupRef.current.rotation.z = Math.sin(elapsed * 0.25) * 0.08;
      }

      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      dom.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      customMaterial.dispose();
    };
  }, []);

  // 2. Rebuild Geometry on Model Index Change
  useEffect(() => {
    if (!mechGroupRef.current || !shaderMatRef.current) return;
    const group = mechGroupRef.current;
    const mat = shaderMatRef.current;

    // Clear old children
    while (group.children.length > 0) {
      const obj = group.children[0];
      group.remove(obj);
      if ((obj as THREE.Mesh).geometry) {
        (obj as THREE.Mesh).geometry.dispose();
      }
    }

    if (activeModel.shapeType === "jack") {
      // 1. Orthogonal Jack
      const tubeRadius = 0.65;
      const tubeLength = 3.6;

      const createCyl = () => new THREE.Mesh(new THREE.CylinderGeometry(tubeRadius, tubeRadius, tubeLength, 64, 1, false), mat);

      group.add(createCyl());

      const cylX = createCyl();
      cylX.rotation.z = Math.PI / 2;
      group.add(cylX);

      const cylZ = createCyl();
      cylZ.rotation.x = Math.PI / 2;
      group.add(cylZ);

      // Lips & End Caps
      const ringGeom = new THREE.TorusGeometry(tubeRadius * 0.88, 0.14, 32, 64);
      const ends = [
        { pos: [0, tubeLength / 2, 0], rot: [Math.PI / 2, 0, 0] },
        { pos: [0, -tubeLength / 2, 0], rot: [Math.PI / 2, 0, 0] },
        { pos: [tubeLength / 2, 0, 0], rot: [0, Math.PI / 2, 0] },
        { pos: [-tubeLength / 2, 0, 0], rot: [0, Math.PI / 2, 0] },
        { pos: [0, 0, tubeLength / 2], rot: [0, 0, 0] },
        { pos: [0, 0, -tubeLength / 2], rot: [0, 0, 0] },
      ];

      ends.forEach((e) => {
        const ring = new THREE.Mesh(ringGeom, mat);
        ring.position.set(e.pos[0], e.pos[1], e.pos[2]);
        ring.rotation.set(e.rot[0], e.rot[1], e.rot[2]);
        group.add(ring);

        const capGeom = new THREE.CircleGeometry(tubeRadius * 0.74, 32);
        const capMat = new THREE.MeshBasicMaterial({ color: 0x010814 });
        const cap = new THREE.Mesh(capGeom, capMat);
        cap.position.set(e.pos[0] * 0.98, e.pos[1] * 0.98, e.pos[2] * 0.98);
        cap.rotation.set(e.rot[0], e.rot[1], e.rot[2]);
        group.add(cap);
      });

      const coreMesh = new THREE.Mesh(new THREE.SphereGeometry(tubeRadius * 1.2, 48, 48), mat);
      group.add(coreMesh);
      group.scale.setScalar(0.72);
    } else if (activeModel.shapeType === "torus-knot") {
      // 2. High-Curvature Torus Knot
      const geom = new THREE.TorusKnotGeometry(1.2, 0.42, 128, 32, 2, 3);
      const mesh = new THREE.Mesh(geom, mat);
      group.add(mesh);
      group.scale.setScalar(0.75);
    } else if (activeModel.shapeType === "gyroid") {
      // 3. Triply Periodic Surface (Nested Toruses & Ellipsoid Shells)
      const subGroup = new THREE.Group();
      const t1 = new THREE.Mesh(new THREE.TorusGeometry(1.3, 0.38, 32, 64), mat);
      const t2 = new THREE.Mesh(new THREE.TorusGeometry(1.3, 0.38, 32, 64), mat);
      t2.rotation.x = Math.PI / 2;
      const t3 = new THREE.Mesh(new THREE.TorusGeometry(1.3, 0.38, 32, 64), mat);
      t3.rotation.y = Math.PI / 2;
      const sphere = new THREE.Mesh(new THREE.SphereGeometry(0.85, 48, 48), mat);

      subGroup.add(t1);
      subGroup.add(t2);
      subGroup.add(t3);
      subGroup.add(sphere);
      group.add(subGroup);
      group.scale.setScalar(0.72);
    } else if (activeModel.shapeType === "polyhedra") {
      // 4. Lattice Geodesic Node
      const ico = new THREE.Mesh(new THREE.IcosahedronGeometry(1.4, 0), mat);
      const ringOuter = new THREE.Mesh(new THREE.TorusGeometry(1.7, 0.22, 32, 64), mat);
      const ringCross = new THREE.Mesh(new THREE.TorusGeometry(1.7, 0.22, 32, 64), mat);
      ringCross.rotation.x = Math.PI / 2;

      group.add(ico);
      group.add(ringOuter);
      group.add(ringCross);
      group.scale.setScalar(0.72);
    }
  }, [currentIndex, activeModel.shapeType]);

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center select-none">
      {/* 3D Canvas Mount */}
      <div
        ref={containerRef}
        className="w-full h-full min-h-[360px] max-h-[460px] relative flex items-center justify-center"
      />

      {/* Floating Carousel Controller Pill */}
      <div className="absolute bottom-1 right-2 sm:right-6 z-30 flex items-center gap-3 bg-white/80 backdrop-blur-md px-4 py-2 rounded-full border border-neutral-200/80 shadow-md">
        {/* Previous Button */}
        <button
          onClick={prevModel}
          aria-label="Previous Model"
          className="w-7 h-7 rounded-full flex items-center justify-center bg-neutral-100 hover:bg-neutral-200 text-neutral-800 transition active:scale-95"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {/* Model Info Pill */}
        <div className="text-left min-w-[170px] max-w-[210px]">
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] font-mono font-bold tracking-wider uppercase text-cyan-700 bg-cyan-50 px-1.5 py-0.5 rounded">
              {activeModel.tag}
            </span>
            <span className="text-[10px] text-neutral-400 font-mono">
              {currentIndex + 1} / {HERO_MODELS.length}
            </span>
          </div>
          <div className="text-xs font-semibold text-neutral-900 truncate">
            {activeModel.name}
          </div>
        </div>

        {/* Next Button */}
        <button
          onClick={nextModel}
          aria-label="Next Model"
          className="w-7 h-7 rounded-full flex items-center justify-center bg-neutral-100 hover:bg-neutral-200 text-neutral-800 transition active:scale-95"
        >
          <ChevronRight className="w-4 h-4" />
        </button>

        {/* Reset Camera Button */}
        <button
          onClick={resetView}
          title="Reset View Orientation"
          aria-label="Reset View"
          className="w-7 h-7 rounded-full flex items-center justify-center bg-neutral-100 hover:bg-neutral-200 text-neutral-600 transition active:scale-95 ml-1"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
