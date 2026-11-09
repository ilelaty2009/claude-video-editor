// Escenas con gráficos: engranajes, tarjetas que se voltean y documento con íconos y robots.
import React from "react";
import { AbsoluteFill, interpolate, spring } from "remotion";
import { clamp, curvas, useConfigDiseno, useCuadro } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { colores, Fondo, Icono, ms2f, Titular, useK } from "./base";
import type { Escena } from "./tipos";

// ---------- ENGRANAJES ----------
const caminoEngranaje = (dientes: number, R: number, r: number): string => {
  const pts: string[] = [];
  const paso = (Math.PI * 2) / dientes;
  for (let i = 0; i < dientes; i++) {
    const a = i * paso;
    const p = [
      [r, a],
      [R, a + paso * 0.18],
      [R, a + paso * 0.48],
      [r, a + paso * 0.66],
    ];
    for (const [rad, ang] of p) pts.push(`${(rad * Math.cos(ang)).toFixed(1)},${(rad * Math.sin(ang)).toFixed(1)}`);
  }
  return `M${pts.join("L")}Z`;
};

const Engranaje: React.FC<{ dientes: number; radio: number; x: number; y: number; giro: number; color: "oro" | "plata" | "acero"; aparece: number }> = ({
  dientes,
  radio,
  x,
  y,
  giro,
  color,
  aparece,
}) => {
  const grad = { oro: ["#F5CF6B", "#B07A1F", "#5E3E0A"], plata: ["#F2F4F8", "#9AA0AE", "#4C5160"], acero: ["#8E95A8", "#4A5064", "#22252F"] }[color];
  const id = `g-${color}-${dientes}-${Math.round(x)}`;
  return (
    <g transform={`translate(${x} ${y}) scale(${aparece})`} opacity={Math.min(1, aparece * 1.5)}>
      <ellipse cx={0} cy={radio * 1.05} rx={radio * 0.9} ry={radio * 0.12} fill="rgba(0,0,0,0.45)" />
      <g transform={`rotate(${giro})`}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={grad[0]} />
            <stop offset="55%" stopColor={grad[1]} />
            <stop offset="100%" stopColor={grad[2]} />
          </linearGradient>
        </defs>
        <path d={caminoEngranaje(dientes, radio, radio * 0.84)} fill={`url(#${id})`} stroke="rgba(0,0,0,0.35)" strokeWidth={2} />
        <circle r={radio * 0.55} fill="none" stroke="rgba(0,0,0,0.25)" strokeWidth={radio * 0.06} />
        <circle r={radio * 0.22} fill="#0d1024" stroke="rgba(255,255,255,0.25)" strokeWidth={radio * 0.04} />
      </g>
    </g>
  );
};

export const EscenaEngranajes: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, width, height } = useConfigDiseno();
  const lado = e.lado ?? "der"; // lado del texto; los engranajes van al otro lado
  const base = (frame / fps) * 40; // grados por segundo
  const ap = (d: number) => spring({ frame: frame - d, fps, config: { damping: 12, stiffness: 140 } });
  const k = useK();
  const cx = lado === "der" ? width * 0.3 : width * 0.68;
  const cy = height * 0.48;
  // radios pensados para encajar: el pequeño gira al revés y más rápido
  const g = [
    { dientes: 18, radio: 190 * k, x: cx - 130 * k, y: cy - 20 * k, color: "oro" as const, vel: 1, d: 0 },
    { dientes: 12, radio: 128 * k, x: cx + 170 * k, y: cy + 60 * k, color: "plata" as const, vel: -1.5, d: 6 },
    { dientes: 14, radio: 150 * k, x: cx + 60 * k, y: cy - 250 * k, color: "acero" as const, vel: -1.28, d: 12 },
  ];
  return (
    <Fondo entrada={e.entrada}>
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {g.map((q, i) => (
          <Engranaje key={i} dientes={q.dientes} radio={q.radio} x={q.x} y={q.y} giro={base * q.vel + i * 7} color={q.color} aparece={ap(q.d)} />
        ))}
      </svg>
      <Titular e={{ ...e, lado, vertical: e.vertical ?? "centro" }} ancho={760} />
    </Fondo>
  );
};

export const EscenaTarjetas: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps } = useConfigDiseno();
  const k = useK();
  const tarjetas = e.tarjetas ?? [];
  const huecos = Math.max(tarjetas.length, 3);
  const ti = spring({ frame, fps, config: { damping: 18 } });
  return (
    <Fondo entrada={e.entrada}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 90 * k }}>
        {e.titulo ? (
          <div
            style={{
              fontFamily: fuenteEscenas,
              fontWeight: 800,
              fontSize: 46 * k,
              color: "rgba(255,255,255,0.92)",
              textTransform: "uppercase",
              marginBottom: 40 * k,
              opacity: ti,
            }}
          >
            {e.titulo}
          </div>
        ) : null}
        <div style={{ display: "flex", gap: 34 * k, perspective: 1400 * k }}>
          {Array.from({ length: huecos }).map((_, i) => {
            const t = tarjetas[i];
            const inicio = t?.enMs !== undefined ? ms2f(t.enMs - e.desdeMs, fps) : 6 + i * 14;
            const s = t ? spring({ frame: frame - inicio, fps, config: { damping: 11, stiffness: 150 } }) : 0;
            const giro = interpolate(s, [0, 1], [90, 0]);
            const visible = t && frame >= inicio;
            const borde = t?.tipo === "si" ? colores.verde : t?.tipo === "no" ? colores.rojo : "transparent";
            return (
              <div key={i} style={{ width: 270 * k, height: 370 * k, position: "relative" }}>
                {/* hueco vacío */}
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    borderRadius: 22 * k,
                    background: "linear-gradient(160deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02))",
                    border: "1px solid rgba(255,255,255,0.06)",
                  }}
                />
                {visible ? (
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      borderRadius: 22 * k,
                      background: "linear-gradient(170deg, #FBF8F1, #E9E3D6)",
                      border: `${4 * k}px solid ${borde}`,
                      boxShadow: `0 ${24 * k}px ${50 * k}px rgba(0,0,0,0.5), 0 0 ${40 * k}px ${borde}55`,
                      transform: `rotateY(${giro}deg) rotate(${(i % 2 ? 2 : -2) * s}deg) translateY(${(1 - s) * -30 * k}px)`,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 26 * k,
                    }}
                  >
                    <Icono tipo={t.tipo ?? "neutro"} tam={110 * k} />
                    <div style={{ fontFamily: fuenteEscenas, fontWeight: 900, fontSize: 52 * k, color: "#121420", textTransform: "uppercase", letterSpacing: -1 }}>
                      {t.texto}
                    </div>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </Fondo>
  );
};

// ---------- ICONOS (documento + íconos + robots) ----------
const Robot: React.FC<{ tam: number; i: number }> = ({ tam, i }) => {
  const frame = useCuadro();
  const parpadea = (frame + i * 11) % 70 < 4;
  return (
    <div
      style={{
        width: tam,
        height: tam * 0.82,
        borderRadius: tam * 0.24,
        background: "linear-gradient(170deg, #3A3F52, #1A1D28)",
        boxShadow: `0 ${tam * 0.15}px ${tam * 0.3}px rgba(0,0,0,0.55), inset 0 2px 0 rgba(255,255,255,0.12)`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: tam * 0.18,
      }}
    >
      {[0, 1].map((o) => (
        <span key={o} style={{ width: tam * 0.13, height: parpadea ? tam * 0.03 : tam * 0.13, borderRadius: 99, background: "#EDEFF7" }} />
      ))}
    </div>
  );
};

export const EscenaIconos: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, width, height } = useConfigDiseno();
  const k = useK();
  const lado = e.lado ?? "der";
  const cx = lado === "der" ? width * 0.36 : width * 0.64;
  const cy = height * 0.47;
  const doc = spring({ frame, fps, config: { damping: 14, stiffness: 130 } });
  const iconos = e.iconos ?? ["⚙️", "🤖", "📊", "💡", "📈", "🧠"];
  const nRobots = e.robots ?? 8;
  return (
    <Fondo entrada={e.entrada}>
      {/* íconos en arco alrededor del documento */}
      {iconos.map((ic, i) => {
        const ang = Math.PI + (i / Math.max(1, iconos.length - 1)) * Math.PI; // arco de arriba
        const s = spring({ frame: frame - 10 - i * 5, fps, config: { damping: 10, stiffness: 180 } });
        const flota = Math.sin((frame + i * 9) / 12) * 6 * k;
        const x = cx + Math.cos(ang) * 330 * k;
        const y = cy - 40 * k + Math.sin(ang) * 230 * k + flota;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - 42 * k,
              top: y - 42 * k,
              width: 84 * k,
              height: 84 * k,
              borderRadius: 20 * k,
              background: "linear-gradient(160deg, #C9CFEA, #8E97C2)",
              boxShadow: `0 ${12 * k}px ${26 * k}px rgba(0,0,0,0.45)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 44 * k,
              transform: `scale(${s}) rotate(${(1 - s) * -30}deg)`,
            }}
          >
            {ic}
          </div>
        );
      })}
      {/* documento */}
      <div
        style={{
          position: "absolute",
          left: cx - 120 * k,
          top: cy - 150 * k + (1 - doc) * 80 * k,
          width: 240 * k,
          height: 300 * k,
          borderRadius: 10 * k,
          background: "linear-gradient(170deg, #FFFFFF, #E4E6EE)",
          boxShadow: `0 ${30 * k}px ${60 * k}px rgba(0,0,0,0.55)`,
          opacity: doc,
          padding: 22 * k,
          transform: `rotate(${-3 * doc}deg)`,
          fontFamily: fuenteEscenas,
        }}
      >
        <div style={{ fontWeight: 900, fontSize: 24 * k, color: "#1A1D28", textTransform: "uppercase", lineHeight: 1.05 }}>{e.centro ?? ""}</div>
        <div style={{ width: 40 * k, height: 4 * k, background: colores.rojo, margin: `${10 * k}px 0 ${16 * k}px` }} />
        {[0.9, 0.75, 0.85, 0.6, 0.8, 0.7].map((w, i) => {
          const linea = interpolate(frame, [12 + i * 4, 22 + i * 4], [0, w], { ...clamp, easing: curvas.cambia });
          return <div key={i} style={{ height: 9 * k, width: `${linea * 100}%`, background: "#C3C7D4", borderRadius: 4, marginBottom: 12 * k }} />;
        })}
      </div>
      {/* fila de robots */}
      {nRobots > 0 ? (
        <div style={{ position: "absolute", left: cx - (nRobots * 96 * k) / 2, top: cy + 190 * k, display: "flex", gap: 18 * k }}>
          {Array.from({ length: nRobots }).map((_, i) => {
            const s = spring({ frame: frame - 18 - i * 3, fps, config: { damping: 9, stiffness: 200 } });
            return (
              <div key={i} style={{ transform: `translateY(${(1 - s) * 60 * k}px)`, opacity: s }}>
                <Robot tam={78 * k} i={i} />
              </div>
            );
          })}
        </div>
      ) : null}
      <Titular e={{ ...e, lado, vertical: e.vertical ?? "arriba" }} ancho={720} />
    </Fondo>
  );
};
