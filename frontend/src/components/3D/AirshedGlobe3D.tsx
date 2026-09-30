import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Wind, Flame, Eye, RefreshCw, Compass, Maximize2 } from 'lucide-react';
import { getAqiColor } from '@/lib/aqi';

interface AirshedGlobe3DProps {
  selectedCity: string;
  onSelectCity?: (city: string) => void;
  aqi: number;
  windSpeed: number;
  windDir: number;
  firesCount: number;
  className?: string;
}

interface CityPin {
  name: string;
  lat: number;
  lng: number;
  aqi?: number;
}

const CORRIDOR_CITIES: CityPin[] = [
  { name: 'Ludhiana', lat: 30.901, lng: 75.8573 },
  { name: 'Ambala', lat: 30.3752, lng: 76.7821 },
  { name: 'Delhi-NCR', lat: 28.6139, lng: 77.209 },
  { name: 'Agra', lat: 27.1767, lng: 78.0081 },
  { name: 'Kanpur', lat: 26.4499, lng: 80.3319 },
  { name: 'Lucknow', lat: 26.8467, lng: 80.9462 },
];

export const AirshedGlobe3D: React.FC<AirshedGlobe3DProps> = ({
  selectedCity,
  onSelectCity,
  aqi,
  windSpeed,
  windDir,
  firesCount,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredCity, setHoveredCity] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'particles' | 'thermal'>('particles');
  const [isInteracting, setIsInteracting] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 450;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x030712, 0.08);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 1.2, 5.2);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.appendChild(renderer.domElement);

    // 2. Globe Group (Rotatable)
    const globeRadius = 2.0;
    const globeGroup = new THREE.Group();
    scene.add(globeGroup);

    // Focus initial orientation on Northern India (approx lat ~28°N, lon ~77°E)
    // Convert to rotation angles
    const targetRotX = 0.35;
    const targetRotY = -1.35;
    globeGroup.rotation.x = targetRotX;
    globeGroup.rotation.y = targetRotY;

    // Core Globe Material (Dark Titanium with subtle Grid Lines)
    const sphereGeo = new THREE.SphereGeometry(globeRadius, 48, 48);
    const sphereMat = new THREE.MeshStandardMaterial({
      color: 0x090d16,
      roughness: 0.8,
      metalness: 0.3,
      transparent: true,
      opacity: 0.95,
    });
    const globeMesh = new THREE.Mesh(sphereGeo, sphereMat);
    globeGroup.add(globeMesh);

    // Subtle Holographic Latitude / Longitude Wireframe
    const wireGeo = new THREE.SphereGeometry(globeRadius * 1.002, 24, 24);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x14b8a6,
      wireframe: true,
      transparent: true,
      opacity: 0.08,
    });
    const wireMesh = new THREE.Mesh(wireGeo, wireMat);
    globeGroup.add(wireMesh);

    // Outer Atmospheric Haze Glow
    const glowGeo = new THREE.SphereGeometry(globeRadius * 1.06, 32, 32);
    const glowMat = new THREE.MeshBasicMaterial({
      color: aqi > 200 ? 0xef4444 : aqi > 100 ? 0xf59e0b : 0x0d9488,
      transparent: true,
      opacity: 0.12,
      side: THREE.BackSide,
    });
    const glowMesh = new THREE.Mesh(glowGeo, glowMat);
    globeGroup.add(glowMesh);

    // 3. Helper: Convert Lat/Lng to 3D Sphere Coordinates
    const latLngToVector3 = (lat: number, lng: number, radius: number): THREE.Vector3 => {
      const phi = (90 - lat) * (Math.PI / 180);
      const theta = (lng + 180) * (Math.PI / 180);
      const x = -(radius * Math.sin(phi) * Math.cos(theta));
      const z = radius * Math.sin(phi) * Math.sin(theta);
      const y = radius * Math.cos(phi);
      return new THREE.Vector3(x, y, z);
    };

    // 4. City Beacons
    const cityObjects: { name: string; mesh: THREE.Mesh; pos: THREE.Vector3 }[] = [];
    CORRIDOR_CITIES.forEach((city) => {
      const pos = latLngToVector3(city.lat, city.lng, globeRadius * 1.01);
      const isSelected = city.name.toLowerCase() === selectedCity.toLowerCase();

      // Beacon Pin Base
      const pinGeo = new THREE.CylinderGeometry(0.015, 0.005, 0.12, 8);
      pinGeo.rotateX(Math.PI / 2);
      const pinMat = new THREE.MeshBasicMaterial({
        color: isSelected ? 0x14b8a6 : 0x94a3b8,
      });
      const pinMesh = new THREE.Mesh(pinGeo, pinMat);
      pinMesh.position.copy(pos);
      pinMesh.lookAt(new THREE.Vector3(0, 0, 0));
      pinMesh.position.add(pos.clone().normalize().multiplyScalar(0.06));
      globeGroup.add(pinMesh);

      // Glowing Beacon Head
      const headGeo = new THREE.SphereGeometry(isSelected ? 0.045 : 0.03, 16, 16);
      const headMat = new THREE.MeshBasicMaterial({
        color: isSelected ? 0x38bdf8 : 0x06b6d4,
      });
      const headMesh = new THREE.Mesh(headGeo, headMat);
      headMesh.position.copy(pinMesh.position).add(pos.clone().normalize().multiplyScalar(0.07));
      globeGroup.add(headMesh);

      cityObjects.push({ name: city.name, mesh: headMesh, pos: headMesh.position });
    });

    // 5. Thermal Active Fire Embers (from NASA FIRMS)
    const firePointsGroup = new THREE.Group();
    globeGroup.add(firePointsGroup);
    const fireCount = Math.min(firesCount, 80);
    const fireGeo = new THREE.BufferGeometry();
    const firePositions = new Float32Array(fireCount * 3);

    for (let i = 0; i < fireCount; i++) {
      // Scatter in Punjab-Haryana agricultural belt (~29-31° N, ~74-77° E)
      const lat = 29.2 + Math.random() * 2.2;
      const lng = 74.5 + Math.random() * 2.8;
      const fPos = latLngToVector3(lat, lng, globeRadius * 1.02);
      firePositions[i * 3] = fPos.x;
      firePositions[i * 3 + 1] = fPos.y;
      firePositions[i * 3 + 2] = fPos.z;
    }
    fireGeo.setAttribute('position', new THREE.BufferAttribute(firePositions, 3));
    const fireMat = new THREE.PointsMaterial({
      color: 0xff3b30,
      size: 0.06,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    });
    const firePoints = new THREE.Points(fireGeo, fireMat);
    firePointsGroup.add(firePoints);

    // 6. 3D Swirling Particulate / Aerosol Streamlines (PM2.5 & Wind Vector)
    const particleCount = 2800;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleVelocities: { x: number; y: number; z: number; speed: number; originLat: number; originLng: number }[] = [];
    const particleColors = new Float32Array(particleCount * 3);

    const aqiColorHex = new THREE.Color(getAqiColor(aqi));
    const cleanColorHex = new THREE.Color(0x10b981);
    const dustColorHex = new THREE.Color(0xf59e0b);

    for (let i = 0; i < particleCount; i++) {
      // Concentrate around the Indo-Gangetic Basin (24°N - 33°N, 73°E - 86°E)
      const pLat = 24.0 + Math.random() * 9.5;
      const pLng = 73.0 + Math.random() * 13.0;
      const pAlt = globeRadius * (1.02 + Math.random() * 0.12);
      const v = latLngToVector3(pLat, pLng, pAlt);

      particlePositions[i * 3] = v.x;
      particlePositions[i * 3 + 1] = v.y;
      particlePositions[i * 3 + 2] = v.z;

      // Color variation based on AQI and aerosol composition
      const blend = Math.random();
      const col = blend > 0.6 ? aqiColorHex : blend > 0.3 ? dustColorHex : cleanColorHex;
      particleColors[i * 3] = col.r;
      particleColors[i * 3 + 1] = col.g;
      particleColors[i * 3 + 2] = col.b;

      particleVelocities.push({
        x: 0,
        y: 0,
        z: 0,
        speed: (windSpeed / 25) * (0.003 + Math.random() * 0.005),
        originLat: pLat,
        originLng: pLng,
      });
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    particleGeo.setAttribute('color', new THREE.BufferAttribute(particleColors, 3));

    const particleMat = new THREE.PointsMaterial({
      size: 0.035,
      vertexColors: true,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending,
    });
    const particleSystem = new THREE.Points(particleGeo, particleMat);
    globeGroup.add(particleSystem);

    // 7. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x38bdf8, 1.8);
    dirLight1.position.set(5, 4, 3);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x14b8a6, 0.9);
    dirLight2.position.set(-5, -2, -3);
    scene.add(dirLight2);

    // 8. Interactive Drag to Orbit / Rotate Logic
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let autoRotate = true;

    const onPointerDown = (e: PointerEvent) => {
      isDragging = true;
      setIsInteracting(true);
      autoRotate = false;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onPointerMove = (e: PointerEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;

      globeGroup.rotation.y += deltaX * 0.005;
      globeGroup.rotation.x = Math.max(-0.6, Math.min(1.2, globeGroup.rotation.x + deltaY * 0.005));
    };

    const onPointerUp = () => {
      isDragging = false;
      setTimeout(() => {
        setIsInteracting(false);
      }, 500);
    };

    const domElement = renderer.domElement;
    domElement.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);

    // 9. Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Gentle auto rotation when user is not dragging
      if (autoRotate) {
        globeGroup.rotation.y += 0.0012;
      }

      // Pulse beacon heads
      cityObjects.forEach((c, idx) => {
        const scale = 1 + 0.15 * Math.sin(elapsedTime * 3 + idx);
        c.mesh.scale.set(scale, scale, scale);
      });

      // Animate fire embers shimmer
      if (fireMat) {
        fireMat.opacity = 0.65 + 0.3 * Math.sin(elapsedTime * 6);
      }

      // Advect particles along wind heading
      // Wind direction: 0 = North, 90 = East, 180 = South, 270 = West
      const windRad = (windDir * Math.PI) / 180.0;
      // Downwind displacement vector (lat/lng step)
      const dLat = -Math.cos(windRad) * 0.04;
      const dLng = -Math.sin(windRad) * 0.04;

      const positions = particleGeo.attributes.position.array as Float32Array;
      for (let i = 0; i < particleCount; i++) {
        const vel = particleVelocities[i];
        vel.originLat += dLat * vel.speed * 10;
        vel.originLng += dLng * vel.speed * 10;

        // Reset if drifted outside Indo-Gangetic bounding box
        if (
          vel.originLat < 23.0 ||
          vel.originLat > 34.0 ||
          vel.originLng < 72.0 ||
          vel.originLng > 87.0
        ) {
          vel.originLat = 28.5 + (Math.random() - 0.5) * 4.0;
          vel.originLng = 75.0 + (Math.random() - 0.5) * 4.0;
        }

        const alt = globeRadius * (1.02 + 0.04 * Math.sin(elapsedTime * 2 + i));
        const newPos = latLngToVector3(vel.originLat, vel.originLng, alt);
        positions[i * 3] = newPos.x;
        positions[i * 3 + 1] = newPos.y;
        positions[i * 3 + 2] = newPos.z;
      }
      particleGeo.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
    };

    animate();

    // 10. Resize handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      cancelAnimationFrame(animId);
      domElement.removeEventListener('pointerdown', onPointerDown);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('resize', handleResize);

      sphereGeo.dispose();
      sphereMat.dispose();
      wireGeo.dispose();
      wireMat.dispose();
      glowGeo.dispose();
      glowMat.dispose();
      fireGeo.dispose();
      fireMat.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      renderer.dispose();
      if (domElement.parentNode) {
        domElement.parentNode.removeChild(domElement);
      }
    };
  }, [selectedCity, aqi, windSpeed, windDir, firesCount]);

  return (
    <div
      className={`relative w-full rounded-3xl overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-black border border-slate-800 shadow-2xl flex flex-col justify-between ${className}`}
      style={{ minHeight: '440px' }}
    >
      {/* Precision Crosshair Grid Overlay */}
      <div className="absolute inset-0 bg-tactical-grid opacity-25 pointer-events-none" />

      {/* Top Tactical HUD Header */}
      <div className="relative z-10 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 bg-slate-950/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-400 shadow-[0_0_15px_rgba(20,184,166,0.25)]">
            <Compass className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-black uppercase tracking-wider text-teal-400 font-mono">
                3D TERRESTRIAL AIRSHED SIMULATOR
              </span>
              <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30">
                WEBGL 60 FPS
              </span>
            </div>
            <h3 className="text-base font-extrabold text-white tracking-tight flex items-center gap-2 mt-0.5">
              <span>Indo-Gangetic Basin</span>
              <span className="text-slate-500 font-light">—</span>
              <span className="text-teal-400">{selectedCity} Focus</span>
            </h3>
          </div>
        </div>

        {/* 3D Visual Controls & City Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {CORRIDOR_CITIES.map((c) => {
            const isSel = c.name.toLowerCase() === selectedCity.toLowerCase();
            return (
              <button
                key={c.name}
                onClick={() => onSelectCity && onSelectCity(c.name)}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                  isSel
                    ? 'bg-teal-500 text-slate-950 shadow-[0_0_12px_rgba(20,184,166,0.4)]'
                    : 'bg-slate-900/90 text-slate-300 hover:bg-slate-800 border border-slate-800'
                }`}
              >
                {c.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* WebGL 3D Canvas Mounting Container */}
      <div
        ref={containerRef}
        className="relative w-full flex-1 flex items-center justify-center cursor-grab active:cursor-grabbing overflow-hidden"
        style={{ minHeight: '360px' }}
      >
        {/* Subtle Orbit Guidance Overlay */}
        <div className="absolute bottom-3 left-4 z-10 pointer-events-none flex items-center gap-2 text-[10px] font-mono uppercase text-slate-400 bg-slate-950/70 backdrop-blur-md px-3 py-1.5 rounded-full border border-slate-800/80">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-ping" />
          <span>DRAG TO ROTATE 3D AIRSHED GLOBE • LIVE PARTICLES: 2,800</span>
        </div>

        {/* Live Vector Telemetry Floating Tag */}
        <div className="absolute top-3 right-4 z-10 pointer-events-none hidden sm:flex flex-col gap-1 text-right bg-slate-950/80 backdrop-blur-md p-3 rounded-xl border border-slate-800 text-xs font-mono">
          <div className="text-slate-400 text-[10px] uppercase font-bold">Synoptic Transport Vector</div>
          <div className="text-teal-400 font-bold flex items-center justify-end gap-1.5">
            <Wind className="w-3.5 h-3.5" />
            <span>{windSpeed.toFixed(1)} km/h @ {Math.round(windDir)}°</span>
          </div>
          <div className="text-rose-400 text-[11px] font-semibold flex items-center justify-end gap-1 mt-0.5">
            <Flame className="w-3 h-3" />
            <span>{firesCount} Upwind VIIRS Thermal Nodes</span>
          </div>
        </div>
      </div>
    </div>
  );
};
