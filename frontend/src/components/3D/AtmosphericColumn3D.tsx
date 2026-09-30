import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { Layers, Thermometer, ArrowUp, ShieldAlert, Sparkles } from 'lucide-react';

interface AtmosphericColumn3DProps {
  blh: number; // in meters (e.g. 180, 420, etc.)
  pm25: number;
  className?: string;
}

export const AtmosphericColumn3D: React.FC<AtmosphericColumn3DProps> = ({
  blh,
  pm25,
  className = '',
}) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth || 320;
    const height = container.clientHeight || 280;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(2.8, 2.2, 4.2);
    camera.lookAt(0, 0.8, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 2. Main Atmospheric Column Group
    const columnGroup = new THREE.Group();
    scene.add(columnGroup);

    // Base Ground Disc
    const groundGeo = new THREE.CylinderGeometry(1.2, 1.2, 0.08, 32);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.9,
      metalness: 0.1,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.position.y = 0;
    columnGroup.add(ground);

    // Circular Grid on Ground
    const gridHelper = new THREE.PolarGridHelper(1.2, 4, 8, 32, 0x14b8a6, 0x334155);
    gridHelper.position.y = 0.045;
    columnGroup.add(gridHelper);

    // Height normalization: 2000m max represented by 2.2 units
    const maxAltitudeM = 1500;
    const maxUnits = 2.0;
    const blhRatio = Math.max(0.1, Math.min(1.0, blh / maxAltitudeM));
    const blhUnits = blhRatio * maxUnits;

    // Trapped Boundary Layer Cylinder (Surface to BLH)
    const trappedGeo = new THREE.CylinderGeometry(0.85, 0.95, blhUnits, 24, 1, true);
    const trappedMat = new THREE.MeshStandardMaterial({
      color: pm25 > 120 ? 0xef4444 : pm25 > 60 ? 0xf59e0b : 0x10b981,
      transparent: true,
      opacity: 0.35,
      side: THREE.DoubleSide,
      roughness: 0.3,
    });
    const trappedCylinder = new THREE.Mesh(trappedGeo, trappedMat);
    trappedCylinder.position.y = blhUnits / 2 + 0.04;
    columnGroup.add(trappedCylinder);

    // Inversion Ceiling Lid (Shimmering thermal boundary disc)
    const lidGeo = new THREE.CylinderGeometry(0.86, 0.86, 0.03, 32);
    const lidMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.8,
    });
    const lidMesh = new THREE.Mesh(lidGeo, lidMat);
    lidMesh.position.y = blhUnits + 0.04;
    columnGroup.add(lidMesh);

    // Upper Free Troposphere Cylinder (Above Inversion to 1500m)
    const upperHeight = maxUnits - blhUnits;
    if (upperHeight > 0.1) {
      const upperGeo = new THREE.CylinderGeometry(0.75, 0.85, upperHeight, 24, 1, true);
      const upperMat = new THREE.MeshStandardMaterial({
        color: 0x0284c7,
        transparent: true,
        opacity: 0.12,
        side: THREE.DoubleSide,
        wireframe: true,
      });
      const upperCylinder = new THREE.Mesh(upperGeo, upperMat);
      upperCylinder.position.y = blhUnits + upperHeight / 2 + 0.04;
      columnGroup.add(upperCylinder);
    }

    // Trapped Particulate Aerosol Cloud inside the inversion layer
    const particleCount = 450;
    const particleGeo = new THREE.BufferGeometry();
    const particlePos = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const r = Math.random() * 0.75;
      const theta = Math.random() * Math.PI * 2;
      const y = 0.06 + Math.random() * (blhUnits - 0.05);

      particlePos[i * 3] = r * Math.cos(theta);
      particlePos[i * 3 + 1] = y;
      particlePos[i * 3 + 2] = r * Math.sin(theta);
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));
    const particleMat = new THREE.PointsMaterial({
      color: pm25 > 120 ? 0xff4d4d : pm25 > 60 ? 0xffb703 : 0x2dd4bf,
      size: 0.045,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    columnGroup.add(particles);

    // Ambient and Directional Lights
    const ambLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambLight);

    const ptLight = new THREE.PointLight(0x38bdf8, 2, 8);
    ptLight.position.set(2, 3, 2);
    scene.add(ptLight);

    // 3. Animation loop with gentle rotation & particle swirling
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const time = clock.getElapsedTime();

      // Gentle column rotation
      columnGroup.rotation.y = time * 0.25;

      // Lid breathing shimmer
      lidMesh.scale.x = 1 + 0.02 * Math.sin(time * 3);
      lidMesh.scale.z = 1 + 0.02 * Math.sin(time * 3);

      // Swirl trapped particles
      const positions = particleGeo.attributes.position.array as Float32Array;
      for (let i = 0; i < particleCount; i++) {
        let x = positions[i * 3];
        let z = positions[i * 3 + 2];
        const angle = 0.015 * (1 + (i % 3) * 0.5);
        const cosA = Math.cos(angle);
        const sinA = Math.sin(angle);
        positions[i * 3] = x * cosA - z * sinA;
        positions[i * 3 + 2] = x * sinA + z * cosA;
      }
      particleGeo.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animId);
      groundGeo.dispose();
      groundMat.dispose();
      trappedGeo.dispose();
      trappedMat.dispose();
      lidGeo.dispose();
      lidMat.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
    };
  }, [blh, pm25]);

  const isInversionSevere = blh < 300;

  return (
    <div
      className={`relative rounded-2xl bg-gradient-to-b from-slate-900 via-slate-950 to-black border border-slate-800 p-4 shadow-xl overflow-hidden flex flex-col justify-between ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">
              3D Atmospheric Strata
            </div>
            <div className="text-xs font-black text-white">Boundary Layer (BLH) Trapping</div>
          </div>
        </div>

        <span
          className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
            isInversionSevere
              ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-[0_0_8px_rgba(244,63,94,0.3)]'
              : 'bg-teal-500/20 text-teal-300 border-teal-500/40'
          }`}
        >
          {isInversionSevere ? 'Severe Inversion Lid' : 'Active Mixing'}
        </span>
      </div>

      {/* 3D WebGL Column Visualizer */}
      <div className="relative w-full flex items-center justify-center my-1 select-none">
        <div ref={mountRef} className="w-full h-48 cursor-pointer" />

        {/* Altitude Marker HUD Pins */}
        <div className="absolute right-2 top-2 bottom-2 flex flex-col justify-between text-[9px] font-mono text-slate-500 pointer-events-none text-right">
          <div className="text-slate-400 flex items-center gap-1">
            <span>1500m</span>
            <span className="w-2 h-[1px] bg-slate-600 inline-block" />
          </div>
          <div className="text-cyan-400 font-bold flex items-center gap-1">
            <span className="bg-cyan-500/20 px-1 py-0.5 rounded border border-cyan-500/40">
              LID: {blh}m
            </span>
            <span className="w-3 h-[2px] bg-cyan-400 inline-block" />
          </div>
          <div className="text-slate-400 flex items-center gap-1">
            <span>0m (Surface)</span>
            <span className="w-2 h-[1px] bg-slate-600 inline-block" />
          </div>
        </div>
      </div>

      {/* Footer Explanation Note */}
      <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
        <span className="font-sans leading-tight">
          {isInversionSevere
            ? 'Thandi hawa se dhuan 180m ki ceiling ke neeche trap ho gaya hai.'
            : 'Boundary layer open hai, dhuan asani se fail raha hai.'}
        </span>
        <span className="text-[10px] font-mono text-cyan-400 font-bold shrink-0 ml-2">
          {blh}m DEPTH
        </span>
      </div>
    </div>
  );
};
