"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three-stdlib";

export type LiveGraph = {
  anchors: number[][];
  stages: { center: number[]; height: number }[];
  connections: { from_type: string; from_index: number; from_port: string; to_type: string; to_index: number; to_port: string; thickness: number }[];
};

function endpoint(graph: LiveGraph, kind: string, index: number, port: string) {
  if (kind === "anchor") return graph.anchors[index];
  const stage = graph.stages[index];
  return [stage.center[0], stage.center[1] + (port === "top" ? stage.height / 2 : port === "bot" ? -stage.height / 2 : 0)];
}

export default function LiveGraph3D({ graph }: { graph: LiveGraph }) {
  const hostRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    } catch {
      host.textContent = "3D preview unavailable in this browser; the plan view remains available.";
      return;
    }
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050b12);
    const width = Math.max(...graph.anchors.map(p => p[0]), ...graph.stages.map(s => s.center[0]));
    const height = Math.max(...graph.anchors.map(p => p[1]), ...graph.stages.map(s => s.center[1] + s.height / 2));
    const center = new THREE.Vector3(width / 2, height / 2, 0);
    const camera = new THREE.PerspectiveCamera(42, 1, 0.001, 2);
    camera.position.set(center.x + width * .35, center.y - height * 1.25, .12);
    camera.up.set(0, 0, 1);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.copy(center);
    controls.enableDamping = true;
    controls.update();
    scene.add(new THREE.AmbientLight(0xffffff, 1.5));
    const light = new THREE.DirectionalLight(0x92eaff, 2);
    light.position.set(width, height, .15);
    scene.add(light);
    const blue = new THREE.MeshStandardMaterial({ color: 0x22d3ee, metalness: .35, roughness: .4 });
    const purple = new THREE.MeshStandardMaterial({ color: 0xa78bfa, metalness: .25, roughness: .5 });
    const amber = new THREE.MeshStandardMaterial({ color: 0xfbbf24, metalness: .2, roughness: .5 });
    const disposable: THREE.BufferGeometry[] = [];
    const addBox = (size: [number, number, number], position: THREE.Vector3, material: THREE.Material, direction?: THREE.Vector3) => {
      const geometry = new THREE.BoxGeometry(...size);
      disposable.push(geometry);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.copy(position);
      if (direction) mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
      scene.add(mesh);
    };
    for (const edge of graph.connections) {
      const a = endpoint(graph, edge.from_type, edge.from_index, edge.from_port);
      const b = endpoint(graph, edge.to_type, edge.to_index, edge.to_port);
      const start = new THREE.Vector3(a[0], a[1], 0);
      const end = new THREE.Vector3(b[0], b[1], 0);
      const length = start.distanceTo(end);
      if (length > 0) addBox([edge.thickness, length, .01], start.clone().add(end).multiplyScalar(.5), blue, end.sub(start).normalize());
    }
    for (const stage of graph.stages) addBox([.006, stage.height, .01], new THREE.Vector3(stage.center[0], stage.center[1], 0), purple);
    for (const anchor of graph.anchors) addBox([.004, .004, .012], new THREE.Vector3(anchor[0], anchor[1], 0), amber);
    const bounds = new THREE.BoxGeometry(width, height, .012);
    disposable.push(bounds);
    const lines = new THREE.LineSegments(new THREE.EdgesGeometry(bounds), new THREE.LineBasicMaterial({ color: 0x24516c, transparent: true, opacity: .6 }));
    lines.position.copy(center);
    scene.add(lines);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    host.replaceChildren(renderer.domElement);
    const resize = () => {
      const w = Math.max(1, host.clientWidth), h = Math.max(1, host.clientHeight);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();
    let frame = 0;
    const draw = () => { controls.update(); renderer.render(scene, camera); frame = requestAnimationFrame(draw); };
    draw();
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      controls.dispose();
      for (const geometry of disposable) geometry.dispose();
      (lines.geometry as THREE.BufferGeometry).dispose();
      (lines.material as THREE.Material).dispose();
      blue.dispose(); purple.dispose(); amber.dispose();
      renderer.dispose();
      if (host.contains(renderer.domElement)) host.removeChild(renderer.domElement);
    };
  }, [graph]);

  return <div className="relative h-64 w-full overflow-hidden rounded border border-cyan-900 bg-black">
    <div ref={hostRef} className="h-full w-full" aria-label="Interactive 3D view of selected evaluated graph" role="img" />
    <p className="pointer-events-none absolute bottom-2 left-2 rounded bg-black/80 px-2 py-1 text-xs text-neutral-300">Orbit to inspect · fixed 10 mm display depth · 2D beam FEA</p>
  </div>;
}
