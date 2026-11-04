"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function HeroJackFigure() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Scene & Transparent Background
    const scene = new THREE.Scene();

    const width = container.clientWidth || 600;
    const height = container.clientHeight || 600;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
    camera.position.set(0, 0, 7.8);

    // 3. Renderer with physical tone mapping
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    container.replaceChildren(renderer.domElement);

    // 4. Custom Rainbow / Iridescent Metallic Chrome Shader Material
    // Simulates the exact chromatic aberration / rainbow sheen from the reference image
    const customMaterial = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uLightPos1: { value: new THREE.Vector3(5, 5, 6) },
        uLightPos2: { value: new THREE.Vector3(-5, -4, 4) },
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
        uniform vec3 uLightPos1;
        uniform vec3 uLightPos2;

        // Rainbow spectral transfer function
        vec3 spectral(float t) {
          return 0.5 + 0.5 * cos(6.28318 * (vec3(1.0, 1.0, 1.0) * t + vec3(0.0, 0.33, 0.67)));
        }

        void main() {
          vec3 N = normalize(vNormal);
          vec3 V = normalize(vViewPosition);

          // Fresnel / rim intensity
          float fresnel = 1.0 - max(dot(N, V), 0.0);
          float fresnelPow = pow(fresnel, 2.5);

          // Directional highlights
          vec3 L1 = normalize(uLightPos1 - vWorldPosition);
          vec3 H1 = normalize(L1 + V);
          float spec1 = pow(max(dot(N, H1), 0.0), 32.0);

          vec3 L2 = normalize(uLightPos2 - vWorldPosition);
          vec3 H2 = normalize(L2 + V);
          float spec2 = pow(max(dot(N, H2), 0.0), 24.0);

          // Iridescent iridescent color based on normal coordinates & view angle
          float rainbowCoord = dot(N, vec3(0.3, 0.6, 0.7)) * 0.8 + fresnelPow * 1.2 + sin(uTime * 0.4) * 0.1;
          vec3 irid = spectral(rainbowCoord);

          // Deep metallic cyan/blue base tone
          vec3 baseColor = mix(vec3(0.02, 0.25, 0.55), vec3(0.0, 0.85, 0.55), N.y * 0.5 + 0.5);

          // Inner metallic core mix
          vec3 finalColor = mix(baseColor, irid, fresnelPow * 0.85 + 0.25);
          finalColor += vec3(0.9, 0.95, 1.0) * spec1 * 1.5;
          finalColor += irid * spec2 * 1.2;

          // Rim glow boost
          finalColor += vec3(0.0, 1.0, 0.6) * pow(fresnel, 4.0) * 0.9;

          gl_FragColor = vec4(finalColor, 1.0);
        }
      `,
    });

    // 5. Construct the 3-Axis Orthogonal Hollow Cylindrical Jack (Mathematical Jack Shape)
    const jackGroup = new THREE.Group();

    // Tube dimensions: outer radius 0.65, inner radius 0.42, length 3.4
    const tubeRadius = 0.58;
    const tubeLength = 3.2;

    const createCylinderWithHole = () => {
      // Create a tube using cylinder geometry with chamfered lips
      const geom = new THREE.CylinderGeometry(tubeRadius, tubeRadius, tubeLength, 48, 1, false);
      const mesh = new THREE.Mesh(geom, customMaterial);
      return mesh;
    };

    // Axis 1: Y-axis
    const cylY = createCylinderWithHole();
    jackGroup.add(cylY);

    // Axis 2: X-axis
    const cylX = createCylinderWithHole();
    cylX.rotation.z = Math.PI / 2;
    jackGroup.add(cylX);

    // Axis 3: Z-axis
    const cylZ = createCylinderWithHole();
    cylZ.rotation.x = Math.PI / 2;
    jackGroup.add(cylZ);

    // End rim rings to give the hollow-pipe / torus lip look
    const ringGeom = new THREE.TorusGeometry(tubeRadius * 0.86, 0.12, 24, 48);
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

      // Dark inner cap to accentuate depth
      const innerCapGeom = new THREE.CircleGeometry(tubeRadius * 0.72, 32);
      const innerCapMat = new THREE.MeshBasicMaterial({ color: 0x010814 });
      const innerCap = new THREE.Mesh(innerCapGeom, innerCapMat);
      innerCap.position.set(e.pos[0] * 0.98, e.pos[1] * 0.98, e.pos[2] * 0.98);
      innerCap.rotation.set(e.rot[0], e.rot[1], e.rot[2]);
      jackGroup.add(innerCap);
    });

    // Central smoothing sphere junction
    const coreGeom = new THREE.SphereGeometry(tubeRadius * 1.15, 36, 36);
    const coreMesh = new THREE.Mesh(coreGeom, customMaterial);
    jackGroup.add(coreMesh);

    // Initial isometric rotation matching the reference image angle
    jackGroup.rotation.x = 0.55;
    jackGroup.rotation.y = 0.75;
    jackGroup.rotation.z = -0.35;
    scene.add(jackGroup);

    // 6. Interactive Float Animation
    let animId: number;
    const clock = new THREE.Clock();

    let targetRotX = 0.55;
    let targetRotY = 0.75;

    const onPointerMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      targetRotY = 0.75 + x * 0.45;
      targetRotX = 0.55 - y * 0.35;
    };
    window.addEventListener("pointermove", onPointerMove);

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      customMaterial.uniforms.uTime.value = elapsed;

      // Gentle continuous floating rotation + mouse response
      jackGroup.rotation.x += (targetRotX + Math.sin(elapsed * 0.8) * 0.12 - jackGroup.rotation.x) * 0.05;
      jackGroup.rotation.y += (targetRotY + Math.cos(elapsed * 0.6) * 0.15 - jackGroup.rotation.y) * 0.05;
      jackGroup.rotation.z += (Math.sin(elapsed * 0.5) * 0.08 - jackGroup.rotation.z) * 0.03;

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
