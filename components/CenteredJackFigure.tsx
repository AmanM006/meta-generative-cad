"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function CenteredJackFigure() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Scene setup
    const scene = new THREE.Scene();

    const width = container.clientWidth || 550;
    const height = container.clientHeight || 550;

    const camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
    camera.position.set(0, 0, 7.2);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    container.replaceChildren(renderer.domElement);

    // 2. High-End Liquid Glass Soap Bubble / Dispersion Refraction Shader
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

        // Rainbow spectral thin-film dispersion function
        vec3 spectral(float t) {
          // Vivid rainbow: violet -> indigo -> cyan -> emerald -> golden yellow -> magenta
          return 0.5 + 0.5 * cos(6.28318 * (vec3(1.0, 1.0, 1.0) * t + vec3(0.05, 0.35, 0.72)));
        }

        // Secondary pastel iridescence for soap bubble pearlescence
        vec3 pastelIrid(float t) {
          vec3 a = vec3(0.85, 0.88, 0.95);
          vec3 b = vec3(0.45, 0.50, 0.55);
          vec3 c = vec3(1.0, 1.0, 1.0);
          vec3 d = vec3(0.00, 0.33, 0.67);
          return a + b * cos(6.28318 * (c * t + d));
        }

        void main() {
          vec3 N = normalize(vNormal);
          vec3 V = normalize(vViewPosition);

          // Incident angle & Fresnel
          float NdotV = dot(N, V);
          float fresnel = 1.0 - max(abs(NdotV), 0.0);
          float fresnelPow = pow(fresnel, 2.0);
          float rimSheen = pow(fresnel, 4.2);

          // Studio Lights
          // Main high-gloss softbox
          vec3 L1 = normalize(vec3(3.5, 6.0, 4.5));
          vec3 H1 = normalize(L1 + V);
          float spec1 = pow(max(dot(N, H1), 0.0), 64.0);
          float specBroad = pow(max(dot(N, H1), 0.0), 16.0);

          // Rim specular from back right
          vec3 L2 = normalize(vec3(-4.0, -3.0, 3.5));
          vec3 H2 = normalize(L2 + V);
          float spec2 = pow(max(dot(N, H2), 0.0), 32.0);

          // Counter fill
          vec3 L3 = normalize(vec3(0.0, -5.0, 2.0));
          vec3 H3 = normalize(L3 + V);
          float spec3 = pow(max(dot(N, H3), 0.0), 20.0);

          // Multi-layer chromatic dispersion coordinate (simulating internal reflection wave distortion)
          float wave = sin(N.x * 3.0 + N.y * 2.5 + uTime * 0.25) * 0.12;
          float coord1 = dot(N, vec3(0.45, 0.65, 0.6)) * 0.8 + fresnelPow * 1.6 + wave;
          float coord2 = dot(N, vec3(-0.5, 0.3, 0.8)) * 1.1 + fresnelPow * 1.2 - uTime * 0.08;

          vec3 rainbow1 = spectral(coord1);
          vec3 rainbow2 = spectral(coord2 * 0.85);
          vec3 mixedRainbow = mix(rainbow1, rainbow2, 0.5);

          // Ultra-clean crystal glass core: Clear with subtle periwinkle / lavender tint
          vec3 glassCore = vec3(0.92, 0.95, 0.99); // transparent crystalline
          vec3 softViolet = vec3(0.78, 0.82, 0.98); // interior caustics tint
          vec3 baseBody = mix(glassCore, softViolet, 0.35);

          // Combine luminous iridescent dispersion with crystalline body
          // Notice in the reference: the rainbow is prominent across the face and swirls, not just edges
          vec3 finalColor = mix(baseBody, mixedRainbow, 0.68 + fresnelPow * 0.32);

          // Layer on vibrant soap-bubble pearlescence
          vec3 pearl = pastelIrid(dot(N, vec3(0.2, 0.8, 0.5)) + fresnel);
          finalColor = mix(finalColor, pearl, 0.3);

          // Glossy liquid glass highlights:
          // 1. Sharp pure white reflection ribbon
          finalColor += vec3(1.0, 1.0, 1.0) * spec1 * 2.2;
          // 2. Soft chromatic glow around reflection
          finalColor += mixedRainbow * specBroad * 0.9;
          // 3. Crisp secondary edge gleam
          finalColor += vec3(0.9, 0.95, 1.0) * spec2 * 1.4;
          // 4. Glowing electric rainbow rim
          finalColor += mixedRainbow * rimSheen * 2.0;

          // Alpha blending: high clarity liquid glass with rim presence
          float alpha = 0.92 + fresnelPow * 0.08;
          gl_FragColor = vec4(finalColor, alpha);
        }
      `,
      transparent: true,
    });

    // 3. Construct the Tri-Cylinder Orthogonal Jack
    const jackGroup = new THREE.Group();
    const tubeRadius = 0.65;
    const tubeLength = 3.6;

    const createCylinder = () => {
      const geom = new THREE.CylinderGeometry(tubeRadius, tubeRadius, tubeLength, 64, 1, false);
      return new THREE.Mesh(geom, customMaterial);
    };

    // Axes
    jackGroup.add(createCylinder());

    const cylX = createCylinder();
    cylX.rotation.z = Math.PI / 2;
    jackGroup.add(cylX);

    const cylZ = createCylinder();
    cylZ.rotation.x = Math.PI / 2;
    jackGroup.add(cylZ);

    // Rounded lip rings on all 6 pipe endpoints
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

      const capGeom = new THREE.CircleGeometry(tubeRadius * 0.74, 32);
      // Dark internal cavity reflecting deep refraction inside the tube
      const capMat = new THREE.MeshBasicMaterial({ color: 0x070c18 });
      const cap = new THREE.Mesh(capGeom, capMat);
      cap.position.set(e.pos[0] * 0.98, e.pos[1] * 0.98, e.pos[2] * 0.98);
      cap.rotation.set(e.rot[0], e.rot[1], e.rot[2]);
      jackGroup.add(cap);
    });

    // Central Sphere Core
    const coreGeom = new THREE.SphereGeometry(tubeRadius * 1.2, 48, 48);
    const coreMesh = new THREE.Mesh(coreGeom, customMaterial);
    jackGroup.add(coreMesh);

    // Initial scale and rotation - scaled slightly up from 0.76 to 0.83
    jackGroup.scale.set(0.83, 0.83, 0.83);
    jackGroup.rotation.x = 0.52;
    jackGroup.rotation.y = -0.58;
    scene.add(jackGroup);

    // 4. Subtle interactive tilt
    let targetRotX = 0.52;
    let targetRotY = -0.58;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
      targetRotY = -0.58 + nx * 0.22;
      targetRotX = 0.52 + ny * 0.22;
    };

    window.addEventListener("mousemove", handleMouseMove);

    // 5. Animation loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      customMaterial.uniforms.uTime.value = elapsed;

      jackGroup.rotation.x += (targetRotX - jackGroup.rotation.x) * 0.05;
      jackGroup.rotation.y += (targetRotY - jackGroup.rotation.y) * 0.05;
      jackGroup.rotation.z = Math.sin(elapsed * 0.35) * 0.05;

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
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      customMaterial.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className="w-full h-full min-h-[360px] max-h-[460px] relative flex items-center justify-center cursor-default pointer-events-none select-none"
    />
  );
}
