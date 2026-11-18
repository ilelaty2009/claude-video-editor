// /grafica — tus números se vuelven una gráfica que se construye sola, con el contador grande arriba.
// Estilo limpio (fondo claro, como las apps de estadísticas) o oscuro. Línea suave o barras.
import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, curvas, FPS_DISENO } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { AnimacionData, escalaDe } from "./comun";
import { Leyenda } from "./Leyenda";

const abreviar = (v: number) => (Math.abs(v) >= 1e6 ? `${+(v / 1e6).toFixed(1)}M` : Math.abs(v) >= 1e3 ? `${+(v / 1e3).toFixed(0)}K` : `${+v.toFixed(1)}`);

/** Techo "bonito" para el eje (como hacen las apps de estadísticas): 63 -> 80, 940 -> 1.000, 99.385 -> 100.000. */
export const techoBonito = (x: number) => {
  if (x <= 0) return 1;
  const mag = 10 ** Math.floor(Math.log10(x));
  for (const m of [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (m * mag >= x) return m * mag;
  return 10 * mag;
};

/** Curva suave que pasa por todos los puntos sin pasarse de largo (monótona). */
const curvaSuave = (pts: { x: number; y: number }[]) => {
  if (pts.length < 3) return `M${pts.map((p) => `${p.x},${p.y}`).join(" L")}`;
  let d = `M${pts[0].x},${pts[0].y}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i];
    const b = pts[i + 1];
    const dx = (b.x - a.x) / 3;
    const pendA = i > 0 ? (b.y - pts[i - 1].y) / (b.x - pts[i - 1].x) : (b.y - a.y) / (b.x - a.x);
    const pendB = i < pts.length - 2 ? (pts[i + 2].y - a.y) / (pts[i + 2].x - a.x) : (b.y - a.y) / (b.x - a.x);
    d += ` C${a.x + dx},${a.y + pendA * dx} ${b.x - dx},${b.y - pendB * dx} ${b.x},${b.y}`;
  }
  return d;
};

export const GraficaLimpia: React.FC<{ data: AnimacionData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { width: W, height: H, fps } = useVideoConfig();
  const k = escalaDe(W, H);
  const t = (frame * FPS_DISENO) / fps;
  const total = (data.durationInFrames / fps) * FPS_DISENO;
  const claro = data.tema !== "oscuro";
  const tinta = claro ? "#111111" : "#FFFFFF";
  const suave = claro ? "rgba(0,0,0,0.38)" : "rgba(255,255,255,0.45)";
  const valores = data.valores?.length ? data.valores : [1, 2, 3];
  const etiquetas = data.etiquetas ?? [];
  const max = techoBonito(Math.max(...valores) * 1.04);
  const vertical = H > W;
  const g = { x: W * 0.09, y: H * (vertical ? 0.36 : 0.36), w: W * (vertical ? 0.74 : 0.8), h: H * (vertical ? 0.3 : 0.4) };
  const p = interpolate(t, [10, total * 0.8], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const barras = data.grafica === "barras";
  const pts = valores.map((v, i) => ({ x: g.x + (valores.length === 1 ? g.w / 2 : (i / (valores.length - 1)) * g.w), y: g.y + g.h - (v / max) * g.h }));
  // valor del contador = donde va el dibujo
  const pos = p * (valores.length - 1);
  const i0 = Math.min(valores.length - 1, Math.floor(pos));
  const actual = valores.length === 1 ? valores[0] * p : valores[i0] + ((valores[Math.min(i0 + 1, valores.length - 1)] ?? valores[i0]) - valores[i0]) * (pos - i0);
  const dec = data.decimales ?? 0;
  const numero = (barras ? valores[valores.length - 1] * p : actual).toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec });
  const cabeza = { x: g.x + g.w * p, y: g.y + g.h - (actual / max) * g.h };
  const titulo = spring({ frame: t, fps: FPS_DISENO, config: { damping: 18 } });
  const camino = curvaSuave(pts);
  return (
    <AbsoluteFill style={{ background: claro ? "#FFFFFF" : "radial-gradient(ellipse at 50% 35%, #1d2447 0%, #07080f 100%)" }}>
      <div style={{ position: "absolute", left: g.x, top: H * (vertical ? 0.13 : 0.1), fontFamily: fuenteEscenas, color: tinta, opacity: titulo, transform: `translateY(${(1 - titulo) * 20 * k}px)` }}>
        <div style={{ fontWeight: 700, fontSize: 40 * k, opacity: 0.65 }}>{data.etiqueta ?? data.titulo ?? ""}</div>
        <div style={{ fontWeight: 900, fontSize: 170 * k, lineHeight: 1, letterSpacing: -4 * k, fontVariantNumeric: "tabular-nums" }}>
          {data.prefijo ?? ""}
          {numero}
          {data.sufijo ?? ""}
        </div>
      </div>
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <linearGradient id="area-limpia" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={claro ? "#E5484D" : "#5CC8FF"} stopOpacity={0.14} />
            <stop offset="100%" stopColor={claro ? "#E5484D" : "#5CC8FF"} stopOpacity={0} />
          </linearGradient>
          <clipPath id="hasta-donde">
            <rect x={0} y={0} width={g.x + g.w * p + 1} height={H} />
          </clipPath>
        </defs>
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1={g.x} x2={g.x + g.w} y1={g.y + g.h * f} y2={g.y + g.h * f} stroke={claro ? "#EEEEEE" : "rgba(255,255,255,0.1)"} strokeWidth={2 * k} />
            <text x={g.x + g.w + 14 * k} y={g.y + g.h * f + 8 * k} fill={suave} fontSize={22 * k} fontFamily={fuenteEscenas} fontWeight={700}>
              {abreviar(max * (1 - f))}
            </text>
          </g>
        ))}
        {barras ? (
          valores.map((v, i) => {
            const s = interpolate(p * valores.length - i, [0, 1], [0, 1], { ...clamp, easing: curvas.entra });
            const bw = (g.w / valores.length) * 0.6;
            const x = g.x + (i + 0.5) * (g.w / valores.length) - bw / 2;
            const h = (v / max) * g.h * s;
            return <rect key={i} x={x} y={g.y + g.h - h} width={bw} height={h} rx={10 * k} fill={i === valores.length - 1 ? "#E5484D" : claro ? "#111111" : "rgba(255,255,255,0.7)"} />;
          })
        ) : (
          <g clipPath="url(#hasta-donde)">
            <path d={`${camino} L${pts[pts.length - 1].x},${g.y + g.h} L${pts[0].x},${g.y + g.h} Z`} fill="url(#area-limpia)" />
            <path d={camino} fill="none" stroke={tinta} strokeWidth={5 * k} strokeLinecap="round" strokeLinejoin="round" />
          </g>
        )}
        {!barras ? (
          <g>
            <circle cx={cabeza.x} cy={cabeza.y} r={20 * k} fill={claro ? "rgba(0,0,0,0.08)" : "rgba(255,255,255,0.12)"} />
            <circle cx={cabeza.x} cy={cabeza.y} r={9 * k} fill={tinta} />
          </g>
        ) : null}
        {etiquetas.map((e, i) => (
          <text key={i} x={barras ? g.x + (i + 0.5) * (g.w / etiquetas.length) : g.x + (i / Math.max(1, etiquetas.length - 1)) * g.w} y={g.y + g.h + 44 * k} textAnchor="middle" fill={suave} fontSize={24 * k} fontFamily={fuenteEscenas} fontWeight={700}>
            {e}
          </text>
        ))}
      </svg>
      <Leyenda data={data} claro={claro} />
    </AbsoluteFill>
  );
};
