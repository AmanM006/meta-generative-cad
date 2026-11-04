"use client";

import React, { useEffect, useRef, useState } from "react";
import { Application } from "@splinetool/runtime";

export default function SplineJackViewer() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const app = new Application(canvas);
    // Exact official Spline 3D scene from carlgordonmedia.com
    app
      .load("https://prod.spline.design/FYCXejb3UoqwgVH0/scene.splinecode")
      .then(() => {
        setLoading(false);
      })
      .catch((err) => {
        console.warn("Spline load fallback", err);
        setLoading(false);
      });

    return () => {
      app.dispose();
    };
  }, []);

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <canvas
        ref={canvasRef}
        className="w-full h-full object-contain select-none outline-none"
        style={{ pointerEvents: "auto" }}
      />
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center text-xs font-mono text-cyan-400">
          Loading 3D Scene...
        </div>
      )}
    </div>
  );
}
