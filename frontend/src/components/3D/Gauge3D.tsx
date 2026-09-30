import React from 'react';
import { getAqiColor, getAqiCategory } from '@/lib/aqi';

interface Gauge3DProps {
  aqi: number;
  dataOrigin: string;
  stationName: string;
  dataSource: string;
  size?: number;
}

export const Gauge3D: React.FC<Gauge3DProps> = ({
  aqi,
  dataOrigin,
  stationName,
  dataSource,
  size = 280,
}) => {
  const clampedAqi = Math.max(0, Math.min(500, aqi));
  const aqiColor = getAqiColor(clampedAqi);
  const aqiInfo = getAqiCategory(clampedAqi);
  const aqiCategoryName = aqiInfo ? aqiInfo.name : 'Moderate';

  // Gauge angle range: 240 degrees total (-210deg to +30deg, leaving bottom 120deg open)
  const startAngle = 150; // In degrees
  const angleSweep = 240; // Total angular travel
  const progressRatio = clampedAqi / 500;
  const currentAngle = startAngle + progressRatio * angleSweep;

  // SVG Geometry
  const center = size / 2;
  const outerRadius = size * 0.42;
  const trackRadius = size * 0.35;
  const innerRadius = size * 0.28;

  // Helper for polar to cartesian coordinates
  const polarToCartesian = (cx: number, cy: number, r: number, angleDeg: number) => {
    const rad = ((angleDeg - 90) * Math.PI) / 180.0;
    return {
      x: cx + r * Math.cos(rad),
      y: cy + r * Math.sin(rad),
    };
  };

  const describeArc = (cx: number, cy: number, r: number, startA: number, endA: number) => {
    const start = polarToCartesian(cx, cy, r, endA);
    const end = polarToCartesian(cx, cy, r, startA);
    const largeArcFlag = endA - startA <= 180 ? '0' : '1';
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
  };

  // Generate tick marks
  const ticks = [];
  const totalTicks = 25; // every 20 AQI units
  for (let i = 0; i <= totalTicks; i++) {
    const tickVal = i * 20;
    const tickAngle = startAngle + (i / totalTicks) * angleSweep;
    const isMajor = tickVal % 100 === 0 || tickVal === 50;
    const r1 = trackRadius + (isMajor ? 10 : 5);
    const r2 = trackRadius - (isMajor ? 4 : 2);
    const p1 = polarToCartesian(center, center, r1, tickAngle);
    const p2 = polarToCartesian(center, center, r2, tickAngle);
    const pText = polarToCartesian(center, center, r1 + 10, tickAngle);

    ticks.push(
      <g key={i}>
        <line
          x1={p1.x}
          y1={p1.y}
          x2={p2.x}
          y2={p2.y}
          stroke={tickVal <= clampedAqi ? aqiColor : '#475569'}
          strokeWidth={isMajor ? 2.5 : 1}
          opacity={isMajor ? 0.9 : 0.4}
        />
        {isMajor && (
          <text
            x={pText.x}
            y={pText.y}
            textAnchor="middle"
            dominantBaseline="central"
            className="fill-slate-400 font-mono text-[9px] font-bold"
          >
            {tickVal}
          </text>
        )}
      </g>
    );
  }

  // Active Needle / Cursor coordinate
  const needlePos = polarToCartesian(center, center, trackRadius, currentAngle);

  return (
    <div className="relative flex flex-col items-center justify-between p-6 rounded-3xl bg-gradient-to-b from-slate-900 via-slate-950 to-black border border-slate-800/90 shadow-[0_20px_50px_rgba(0,0,0,0.8),inset_0_1px_0_rgba(255,255,255,0.1)] text-white overflow-hidden group">
      {/* 3D Knurled Metallic Outer Bezel Effect */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(30,41,59,0.5)_0%,transparent_75%)] pointer-events-none" />

      {/* Top Header Status Strip */}
      <div className="w-full flex items-center justify-between z-10 pb-2 border-b border-slate-800/60">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span
              className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
              style={{ backgroundColor: aqiColor }}
            />
            <span
              className="relative inline-flex rounded-full h-2.5 w-2.5"
              style={{ backgroundColor: aqiColor }}
            />
          </span>
          <span className="text-[11px] font-bold tracking-wider uppercase text-slate-300 font-mono">
            TACTICAL NAQI TELEMETRY
          </span>
        </div>

        <span
          className={`text-[10px] font-mono px-2 py-0.5 rounded-md font-extrabold tracking-wider border shadow-xs ${
            dataOrigin === 'MEASURED'
              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.2)]'
              : 'bg-amber-500/15 text-amber-300 border-amber-500/40 shadow-[0_0_12px_rgba(245,158,11,0.2)]'
          }`}
        >
          ● {dataOrigin}
        </span>
      </div>

      {/* 3D Volumetric Dial Face */}
      <div className="relative my-2 select-none" style={{ width: size, height: size * 0.9 }}>
        {/* Recessed Convex Chamber Lighting */}
        <div
          className="absolute rounded-full pointer-events-none"
          style={{
            width: innerRadius * 2.3,
            height: innerRadius * 2.3,
            top: center - innerRadius * 1.15,
            left: center - innerRadius * 1.15,
            background: `radial-gradient(circle at 50% 40%, rgba(255,255,255,0.06) 0%, rgba(15,23,42,0.9) 70%, #030712 100%)`,
            boxShadow: `inset 0 4px 14px rgba(0,0,0,0.9), 0 0 35px ${aqiColor}20`,
          }}
        />

        <svg width={size} height={size} className="overflow-visible">
          <defs>
            {/* Active Glow Gradient */}
            <linearGradient id="activeArcGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="35%" stopColor="#f59e0b" />
              <stop offset="70%" stopColor="#ef4444" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>

            {/* Drop shadow for 3D Needle */}
            <filter id="dialShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#000" floodOpacity="0.8" />
            </filter>
            <filter id="needleGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Background Outer Metal Ring */}
          <circle
            cx={center}
            cy={center}
            r={outerRadius}
            fill="none"
            stroke="#1e293b"
            strokeWidth="1.5"
            strokeDasharray="4,4"
            opacity="0.6"
          />

          {/* Calibrated Ticks */}
          {ticks}

          {/* Inactive Track Arc */}
          <path
            d={describeArc(center, center, trackRadius, startAngle, startAngle + angleSweep)}
            fill="none"
            stroke="#1e293b"
            strokeWidth="10"
            strokeLinecap="round"
          />

          {/* Active Track Progress Arc */}
          {clampedAqi > 0 && (
            <path
              d={describeArc(center, center, trackRadius, startAngle, currentAngle)}
              fill="none"
              stroke={aqiColor}
              strokeWidth="10"
              strokeLinecap="round"
              style={{
                filter: `drop-shadow(0 0 8px ${aqiColor}80)`,
                transition: 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)',
              }}
            />
          )}

          {/* Glowing 3D Orbital Head / Needle Tip */}
          <g filter="url(#dialShadow)">
            <circle
              cx={needlePos.x}
              cy={needlePos.y}
              r="7"
              fill={aqiColor}
              filter="url(#needleGlow)"
              style={{ transition: 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)' }}
            />
            <circle
              cx={needlePos.x}
              cy={needlePos.y}
              r="3.5"
              fill="#ffffff"
              style={{ transition: 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)' }}
            />
          </g>
        </svg>

        {/* Center Recessed Digital Telemetry Hub */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none"
          style={{ transform: 'translateY(-12px)' }}
        >
          <div className="flex items-baseline justify-center gap-1">
            <span
              className="text-6xl font-black font-mono tracking-tight drop-shadow-[0_2px_12px_rgba(0,0,0,0.9)]"
              style={{
                color: aqiColor,
                textShadow: `0 0 24px ${aqiColor}60`,
              }}
            >
              {clampedAqi}
            </span>
          </div>

          <div
            className="text-xs font-black uppercase tracking-wider px-3 py-1 rounded-full border shadow-sm mt-1"
            style={{
              backgroundColor: `${aqiColor}18`,
              borderColor: `${aqiColor}40`,
              color: aqiColor,
              boxShadow: `0 0 14px ${aqiColor}25`,
            }}
          >
            {aqiCategoryName}
          </div>

          <span className="text-[10px] text-slate-500 font-mono tracking-widest uppercase mt-1">
            CPCB NAQI • 0-500 SCALE
          </span>
        </div>
      </div>

      {/* Tactical Monitor Details Footer */}
      <div className="w-full pt-3 border-t border-slate-800/80 z-10 space-y-1.5 text-xs text-slate-400">
        <div className="flex justify-between items-center text-slate-300 font-medium">
          <span className="flex items-center gap-1.5 text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
            Sensor Station:
          </span>
          <strong className="text-white font-mono text-[11px] truncate max-w-[170px]" title={stationName}>
            {stationName}
          </strong>
        </div>

        <div className="flex justify-between items-center text-[11px]">
          <span className="text-slate-500">Ingestion Origin:</span>
          <span className="text-slate-300 font-mono text-[10px]">{dataSource}</span>
        </div>

        <div className="text-[11px] text-teal-300/90 pt-1 leading-snug border-t border-slate-800/40 font-sans">
          {dataOrigin === 'MEASURED'
            ? '✓ CPCB/SPCB ground sensor se live maapa gaya pramaanik data.'
            : 'ℹ Modelled fallback: Real-time physical atmospheric satellite feed.'}
        </div>
      </div>
    </div>
  );
};
