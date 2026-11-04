"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function Interactive3DJack() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Full Dynamic Three.js Setup with Orbit & Rainbow Shaders
    const scene = new THREE.Scene();

    const width = container.clientWidth || 700;
    const height = container.clientHeight || 700;

    const camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 100);
    camera.position.set(0, 0, 8.2);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.4;
    container.replaceChildren(renderer.domElement);

    // 2. High-Fidelity Iridescent Rainbow Chrome Shader
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

        // Rainbow spectral function
        vec3 spectral(float t) {
          return 0.5 + 0.5 * cos(6.28318 * (vec3(1.0, 1.0, 1.0) * t + vec3(0.0, 0.33, 0.67)));
        }

        void main() {
          vec3 N = normalize(vNormal);
          vec3 V = normalize(vViewPosition);

          float fresnel = 1.0 - max(dot(N, V), 0.0);
          float fresnelPow = pow(fresnel, 2.2);

          // Key specular highlights
          vec3 L1 = normalize(vec3(4.0, 5.0, 6.0));
          vec3 H1 = normalize(L1 + V);
          float spec1 = pow(max(dot(N, H1), 0.0), 32.0);

          vec3 L2 = normalize(vec3(-5.0, -4.0, 5.0));
          vec3 H2 = normalize(L2 + V);
          float spec2 = pow(max(dot(N, H2), 0.0), 20.0);

          // Iridescent normal rainbow map
          float iridCoord = dot(N, vec3(0.4, 0.7, 0.6)) * 0.85 + fresnelPow * 1.4 + uTime * 0.15;
          vec3 irid = spectral(iridCoord);

          // Deep metallic emerald / cyan / sapphire base
          vec3 deepBase = mix(vec3(0.01, 0.18, 0.45), vec3(0.0, 0.95, 0.55), N.y * 0.5 + 0.5);

          vec3 finalColor = mix(deepBase, irid, fresnelPow * 0.9 + 0.2);
          finalColor += vec3(1.0, 1.0, 1.0) * spec1 * 1.6;
          finalColor += irid * spec2 * 1.3;
          finalColor += vec3(0.0, 1.0, 0.65) * pow(fresnel, 4.0) * 1.1;

          gl_FragColor = vec4(finalColor, 1.0);
        }
      `,
    });

    // 3. Construct Orthogonal Tri-Cylinder Jack Geometry
    const jackGroup = new THREE.Group();
    const tubeRadius = 0.62;
    const tubeLength = 3.6;

    const createAxisCylinder = () => {
      const geom = new THREE.CylinderGeometry(tubeRadius, tubeRadius, tubeLength, 64, 1, false);
      return new THREE.Mesh(geom, customMaterial);
    };

    // Y Axis
    jackGroup.add(createAxisCylinder());

    // X Axis
    const cylX = createAxisCylinder();
    cylX.rotation.z = Math.PI / 2;
    jackGroup.add(cylX);

    // Z Axis
    const cylZ = createAxisCylinder();
    cylZ.rotation.x = Math.PI / 2;
    jackGroup.add(cylZ);

    // Rounded Lips / Torus Collars on all 6 ends
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
      const ring = new THREE.Mesh(ringGeom, customMaterial);
      ring.position.set(e.pos[0], e.pos[1], e.pos[2]);
      ring.rotation.set(e.rot[0], e.rot[1], e.rot[2]);
      jackGroup.add(ring);

      // Deep dark hollow interior cap
      const capGeom = new THREE.CircleGeometry(tubeRadius * 0.74, 32);
      const capMat = new THREE.MeshBasicMaterial({ color: 0x010814 });
      const cap = new THREE.Mesh(capGeom, capMat);
      cap.position.set(e.pos[0] * 0.98, e.pos[1] * 0.98, e.pos[2] * 0.98);
      cap.rotation.set(e.rot[0], e.rot[1], e.rot[2]);
      jackGroup.add(cap);
    });

    // Central Sphere Core
    const coreGeom = new THREE.SphereGeometry(tubeRadius * 1.18, 48, 48);
    const coreMesh = new THREE.Mesh(coreGeom, customMaterial);
    jackGroup.add(coreMesh);

    // Starting rotation
    jackGroup.rotation.x = 0.58;
    jackGroup.rotation.y = 0.82;
    jackGroup.rotation.z = -0.32;
    scene.add(jackGroup);

    // 4. Live Mouse Movement Tracking & Smooth Animation Loop
    let animId: number;
    let mouseX = 0;
    let mouseY = 0;
    let isDragging = false;
    let prevMousePos = { x: 0, y: 0 };
    let dragVelocity = { x: 0, y: 0 };

    const onPointerMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      customMaterial.uniforms.uMouse.value.set(mouseX, mouseY);

      if (isDragging) {
        const deltaX = e.clientX - prevMousePos.x;
        const deltaY = e.clientY - prevMousePos.y;
        dragVelocity.x = deltaX * 0.008;
        dragVelocity.y = deltaY * 0.008;
        jackGroup.rotation.y += dragVelocity.x;
        jackGroup.rotation.x += dragVelocity.y;
        prevMousePos = { x: e.clientX, y: e.clientY };
      }
    };

    const onPointerDown = (e: MouseEvent) => {
      isDragging = true;
      prevMousePos = { x: e.clientX, y: e.clientY };
    };

    const onPointerUp = () => {
      isDragging = false;
    };

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointerup", onPointerUp);

    const clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      customMaterial.uniforms.uTime.value = elapsed;

      if (!isDragging) {
        // Continuous organic rotation + subtle follow
        jackGroup.rotation.y += 0.005 + (mouseX * 0.3 - jackGroup.rotation.y) * 0.015;
        jackGroup.rotation.x += Math.sin(elapsed * 0.7) * 0.003 + (mouseY * 0.25 - jackGroup.rotation.x) * 0.015;
        jackGroup.rotation.z += Math.cos(elapsed * 0.5) * 0.002;
      } else {
        dragVelocity.x *= 0.95;
        dragVelocity.y *= 0.95;
      }

      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className="w-full h-full cursor-grab active:cursor-grabbing flex items-center justify-center select-none"
    />
  );
}
