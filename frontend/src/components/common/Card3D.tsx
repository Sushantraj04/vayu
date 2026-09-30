import React, { useRef, useState, useCallback } from 'react';

interface Card3DProps {
  children: React.ReactNode;
  className?: string;
  maxTilt?: number;
  depth?: number;
  glowColor?: string;
  onClick?: () => void;
  accentBorder?: boolean;
}

export const Card3D: React.FC<Card3DProps> = ({
  children,
  className = '',
  maxTilt = 7,
  depth = 12,
  glowColor = 'rgba(20, 184, 166, 0.15)',
  onClick,
  accentBorder = false,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [style, setStyle] = useState<React.CSSProperties>({
    transform: 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)',
    transition: 'transform 0.5s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.5s ease',
  });
  const [glare, setGlare] = useState<{ x: number; y: number; opacity: number }>({
    x: 50,
    y: 50,
    opacity: 0,
  });

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!cardRef.current) return;
      const rect = cardRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const normX = (x / rect.width - 0.5) * 2;
      const normY = (y / rect.height - 0.5) * 2;

      const rotX = -normY * maxTilt;
      const rotY = normX * maxTilt;

      setStyle({
        transform: `perspective(1000px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateZ(${depth}px)`,
        transition: 'transform 0.08s ease-out, box-shadow 0.2s ease',
      });

      setGlare({
        x: (x / rect.width) * 100,
        y: (y / rect.height) * 100,
        opacity: 0.18,
      });
    },
    [maxTilt, depth]
  );

  const handleMouseLeave = useCallback(() => {
    setStyle({
      transform: 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)',
      transition: 'transform 0.6s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.6s ease',
    });
    setGlare((prev) => ({ ...prev, opacity: 0 }));
  }, []);

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={style}
      className={`relative rounded-2xl transition-shadow select-none group will-change-transform ${
        accentBorder ? 'border border-teal-500/30' : 'border border-slate-200/80 dark:border-slate-800/80'
      } bg-white dark:bg-slate-900/90 backdrop-blur-xl shadow-md hover:shadow-2xl dark:shadow-black/50 ${className}`}
    >
      {/* Specular Glare Reflection Layer */}
      <div
        className="absolute inset-0 rounded-2xl pointer-events-none transition-opacity duration-300 z-30 overflow-hidden"
        style={{
          opacity: glare.opacity,
          background: `radial-gradient(circle 220px at ${glare.x}% ${glare.y}%, rgba(255, 255, 255, 0.25), transparent 70%)`,
        }}
      />

      {/* Subtle Inset Bevel & Corner Highlights for Tactile Physical Look */}
      <div className="absolute inset-0 rounded-2xl pointer-events-none z-20 shadow-[inset_0_1px_0_rgba(255,255,255,0.12),inset_0_-1px_0_rgba(0,0,0,0.3)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.08),inset_0_-1px_0_rgba(0,0,0,0.6)]" />

      {/* Precision Technical Corner Crosshairs */}
      <div className="absolute top-1.5 left-1.5 w-1.5 h-1.5 border-t border-l border-slate-300 dark:border-slate-700 pointer-events-none" />
      <div className="absolute top-1.5 right-1.5 w-1.5 h-1.5 border-t border-r border-slate-300 dark:border-slate-700 pointer-events-none" />
      <div className="absolute bottom-1.5 left-1.5 w-1.5 h-1.5 border-b border-l border-slate-300 dark:border-slate-700 pointer-events-none" />
      <div className="absolute bottom-1.5 right-1.5 w-1.5 h-1.5 border-b border-r border-slate-300 dark:border-slate-700 pointer-events-none" />

      {/* Content Container */}
      <div className="relative z-10 h-full">{children}</div>
    </div>
  );
};
