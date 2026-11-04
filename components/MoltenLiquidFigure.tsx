"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function MoltenLiquidFigure() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const scene = new THREE.Scene();

    const width = container.clientWidth || 440;
    const height = container.clientHeight || 440;

    const camera = new THREE.PerspectiveCamera(36, width / height, 0.1, 100);
    camera.position.set(0, 0, 6.8);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    container.replaceChildren(renderer.domElement);

    // Subtle, high-end iridescent liquid glass shader (not overblown white)
    const customMaterial = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uMouse: { value: new THREE.Vector2(0, 0) },
      },
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        varying vec3 vWorldPosition;
        uniform float uTime;

        vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
        vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
        vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
        vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

        float snoise(vec3 v) {
          const vec2 C = vec2(1.0/6.0, 1.0/3.0);
          const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
          vec3 i  = floor(v + dot(v, C.yyy));
          vec3 x0 = v - i + dot(i, C.xxx);
          vec3 g = step(x0.yzx, x0.xyz);
          vec3 l = 1.0 - g;
          vec3 i1 = min(g.xyz, l.zxy);
          vec3 i2 = max(g.xyz, l.zxy);
          vec3 x1 = x0 - i1 + C.xxx;
          vec3 x2 = x0 - i2 + C.yyy;
          vec3 x3 = x0 - D.yyy;
          i = mod289(i);
          vec4 p = permute(permute(permute(
                    i.z + vec4(0.0, i1.z, i2.z, 1.0))
                  + i.y + vec4(0.0, i1.y, i2.y, 1.0))
                  + i.x + vec4(0.0, i1.x, i2.x, 1.0));
          float n_ = 0.142857142857;
          vec3 ns = n_ * D.wyz - D.xzx;
          vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
          vec4 x_ = floor(j * ns.z);
          vec4 y_ = floor(j - 7.0 * x_);
          vec4 x = x_ *ns.x + ns.yyyy;
          vec4 y = y_ *ns.x + ns.yyyy;
          vec4 h = 1.0 - abs(x) - abs(y);
          vec4 b0 = vec4(x.xy, y.xy);
          vec4 b1 = vec4(x.zw, y.zw);
          vec4 s0 = floor(b0)*2.0 + 1.0;
          vec4 s1 = floor(b1)*2.0 + 1.0;
          vec4 sh = -step(h, vec4(0.0));
          vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
          vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
          vec3 p0 = vec3(a0.xy, h.x);
          vec3 p1 = vec3(a0.zw, h.y);
          vec3 p2 = vec3(a1.xy, h.z);
          vec3 p3 = vec3(a1.zw, h.w);
          vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
          p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
          vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
          m = m * m;
          return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
        }

        void main() {
          vec3 pos = position;
          // Controllable, tight fluid ridges
          float n1 = snoise(pos * 0.95 + vec3(uTime * 0.25));
          float n2 = snoise(pos * 2.1 - vec3(uTime * 0.18));
          pos += normal * (n1 * 0.22 + n2 * 0.09);

          vNormal = normalize(normalMatrix * (normal + vec3(n1, n2, n1) * 0.25));
          vec4 worldPos = modelMatrix * vec4(pos, 1.0);
          vWorldPosition = worldPos.xyz;
          vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
          vViewPosition = -mvPosition.xyz;
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        varying vec3 vWorldPosition;
        uniform float uTime;

        vec3 rainbow(float t) {
          return 0.5 + 0.5 * cos(6.28318 * (vec3(1.0, 1.0, 1.0) * t + vec3(0.0, 0.33, 0.67)));
        }

        void main() {
          vec3 N = normalize(vNormal);
          vec3 V = normalize(vViewPosition);

          float fresnel = 1.0 - max(dot(N, V), 0.0);
          float fresnelPow = pow(fresnel, 2.5);

          vec3 L1 = normalize(vec3(3.0, 4.0, 4.5));
          vec3 H1 = normalize(L1 + V);
          float spec1 = pow(max(dot(N, H1), 0.0), 32.0);

          vec3 L2 = normalize(vec3(-3.5, -2.5, 3.5));
          vec3 H2 = normalize(L2 + V);
          float spec2 = pow(max(dot(N, H2), 0.0), 20.0);

          // Controlled subtle chromatic iridescence
          float chroma = dot(N, vec3(0.35, 0.6, 0.65)) * 0.8 + fresnelPow * 1.2 + sin(uTime * 0.15) * 0.1;
          vec3 irid = rainbow(chroma);

          // Deep chrome / smoked metallic cyan-gray base (keeps contrast with white bg)
          vec3 bodyTint = vec3(0.38, 0.52, 0.64);
          float diffuse = max(dot(N, L1), 0.0) * 0.45 + 0.55;

          vec3 color = mix(bodyTint * diffuse, irid, fresnelPow * 0.75 + 0.25);
          color += vec3(1.0, 1.0, 1.0) * spec1 * 1.4;
          color += irid * spec2 * 0.9;
          color += vec3(0.2, 0.6, 0.8) * pow(fresnel, 3.5) * 0.6;

          gl_FragColor = vec4(color, 0.95);
        }
      `,
      transparent: true,
    });

    const geometry = new THREE.IcosahedronGeometry(1.4, 64);
    const liquidMesh = new THREE.Mesh(geometry, customMaterial);
    scene.add(liquidMesh);

    let mouseX = 0;
    let mouseY = 0;

    const onPointerMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
    };

    window.addEventListener("pointermove", onPointerMove);

    let animId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      customMaterial.uniforms.uTime.value = elapsed;

      liquidMesh.rotation.y += 0.003 + (mouseX * 0.25 - liquidMesh.rotation.y) * 0.02;
      liquidMesh.rotation.x += Math.sin(elapsed * 0.5) * 0.002 + (mouseY * 0.2 - liquidMesh.rotation.x) * 0.02;

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
      className="w-full h-full flex items-center justify-center select-none"
      style={{ cursor: "default", pointerEvents: "none" }}
    />
  );
}
