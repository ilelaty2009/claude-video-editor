// /mapa-ruta — mapa 3D (isométrico) de una ciudad con la ruta animada entre dos lugares, como una app de mapas.
// Todo dibujado aquí (manzanas, parques, árboles): no usa internet ni mapas con licencia.
import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, FPS_DISENO } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { AnimacionData, azar, escalaDe, iso } from "./comun";
import { Leyenda } from "./Leyenda";

const CELDA = 130; // manzana (100) + calle (30)
const MANZANA = 100;

export const Mapa3D: React.FC<{ data: AnimacionData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { width: W, height: H, fps } = useVideoConfig();
  const k = escalaDe(W, H);
  const t = (frame * FPS_DISENO) / fps;
  const total = (data.durationInFrames / fps) * FPS_DISENO;
  const N = 9;
  const vertical = H > W;
  const esc = Math.min(W, H) * (vertical ? 0.001 : 0.00085);
  const esquina = (c: number, f: number) => ({ x: c * CELDA - 15, y: f * CELDA - 15 });
  // en isométrico, avanzar en x e y a la vez baja por la pantalla: en vertical la ruta va de arriba a abajo
  // (cabe en el celular) y en horizontal va de izquierda a derecha
  const ruta = vertical
    ? [esquina(2, 1), esquina(2, 4), esquina(5, 4), esquina(5, 6), esquina(7, 6), esquina(7, 8)]
    : [esquina(1, 7), esquina(4, 7), esquina(4, 4), esquina(6, 4), esquina(6, 2), esquina(7, 2)];
  const largo = ruta.reduce((s, q, i) => (i ? s + Math.hypot(q.x - ruta[i - 1].x, q.y - ruta[i - 1].y) : 0), 0);
  const p = interpolate(t, [14, total * 0.75], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  // punto que avanza por la ruta
  let resto = p * largo;
  let cabeza = ruta[0];
  const hecha = [ruta[0]];
  for (let i = 1; i < ruta.length; i++) {
    const d = Math.hypot(ruta[i].x - ruta[i - 1].x, ruta[i].y - ruta[i - 1].y);
    if (resto <= d) {
      cabeza = { x: ruta[i - 1].x + ((ruta[i].x - ruta[i - 1].x) * resto) / d, y: ruta[i - 1].y + ((ruta[i].y - ruta[i - 1].y) * resto) / d };
      hecha.push(cabeza);
      break;
    }
    resto -= d;
    cabeza = ruta[i];
    hecha.push(ruta[i]);
  }
  // cámara: se acerca un poco y sigue suavemente al punto
  const medio = { x: (N * CELDA) / 2, y: (N * CELDA) / 2 };
  const foco = { x: medio.x + (cabeza.x - medio.x) * 0.35, y: medio.y + (cabeza.y - medio.y) * 0.35 };
  const zoom = interpolate(t, [0, total], [1.18, 1.02], { ...clamp, easing: Easing.inOut(Easing.sin) });
  const fc = iso(foco.x, foco.y, 0, esc * zoom);
  const P = (x: number, y: number, z: number) => {
    const q = iso(x, y, z, esc * zoom);
    return { x: W / 2 + q.x - fc.x, y: H * (vertical ? 0.5 : 0.55) + q.y - fc.y };
  };
  const poli = (pts: { x: number; y: number }[]) => pts.map((q) => `${q.x},${q.y}`).join(" ");
  const parque = (c: number, f: number) => azar(c * 31 + f * 7) > 0.84;
  const celdas: { c: number; f: number }[] = [];
  for (let f = 0; f < N; f++) for (let c = 0; c < N; c++) celdas.push({ c, f });
  celdas.sort((a, b) => a.c + a.f - (b.c + b.f)); // de atrás hacia adelante
  const llega = spring({ frame: t - total * 0.75, fps: FPS_DISENO, config: { damping: 9, stiffness: 180 } });
  const pastilla = spring({ frame: t - 6, fps: FPS_DISENO, config: { damping: 16 } });
  const pin = (q: { x: number; y: number }, color: string, texto: string | undefined, s: number) => {
    const a = P(q.x, q.y, 0);
    return (
      <g transform={`translate(${a.x} ${a.y}) scale(${s})`}>
        <circle r={16 * k} fill={color} stroke="white" strokeWidth={6 * k} />
        {texto ? (
          <text x={26 * k} y={8 * k} fill="#1d2433" fontSize={30 * k} fontWeight={800} fontFamily={fuenteEscenas} paintOrder="stroke" stroke="white" strokeWidth={8 * k}>
            {texto}
          </text>
        ) : null}
      </g>
    );
  };
  return (
    <AbsoluteFill style={{ background: "#E9ECF0" }}>
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {/* suelo (calles) */}
        <polygon points={poli([P(-40, -40, 0), P(N * CELDA, -40, 0), P(N * CELDA, N * CELDA, 0), P(-40, N * CELDA, 0)])} fill="#F7F8FA" />
        {celdas.map(({ c, f }) => {
          const x0 = c * CELDA;
          const y0 = f * CELDA;
          if (parque(c, f)) {
            return (
              <g key={`${c}-${f}`}>
                <polygon points={poli([P(x0, y0, 0), P(x0 + MANZANA, y0, 0), P(x0 + MANZANA, y0 + MANZANA, 0), P(x0, y0 + MANZANA, 0)])} fill="#CDEBC4" />
                {[0, 1, 2].map((j) => {
                  const a = P(x0 + 25 + azar(c + j) * 50, y0 + 25 + azar(f + j * 3) * 50, 18);
                  return <circle key={j} cx={a.x} cy={a.y} r={11 * esc * zoom * 2.2} fill="#5DBB63" stroke="#3E9447" strokeWidth={1.5} />;
                })}
              </g>
            );
          }
          const h = 14 + azar(c * 13 + f * 5) * 44;
          const arriba = [P(x0, y0, h), P(x0 + MANZANA, y0, h), P(x0 + MANZANA, y0 + MANZANA, h), P(x0, y0 + MANZANA, h)];
          const der = [P(x0 + MANZANA, y0, h), P(x0 + MANZANA, y0 + MANZANA, h), P(x0 + MANZANA, y0 + MANZANA, 0), P(x0 + MANZANA, y0, 0)];
          const frente = [P(x0, y0 + MANZANA, h), P(x0 + MANZANA, y0 + MANZANA, h), P(x0 + MANZANA, y0 + MANZANA, 0), P(x0, y0 + MANZANA, 0)];
          return (
            <g key={`${c}-${f}`}>
              <polygon points={poli(frente)} fill="#D5DAE1" />
              <polygon points={poli(der)} fill="#C3C9D2" />
              <polygon points={poli(arriba)} fill="#FFFFFF" stroke="#E1E5EA" strokeWidth={1} />
            </g>
          );
        })}
        {(data.calles ?? []).slice(0, 3).map((nombre, i) => {
          const a = P(esquina(2 + i * 2, 1 + i * 3).x + 30, esquina(2 + i * 2, 1 + i * 3).y - 6, 0);
          return (
            <text key={nombre} x={a.x} y={a.y} fill="#8B93A1" fontSize={18 * k} fontFamily={fuenteEscenas} fontWeight={700}>
              {nombre}
            </text>
          );
        })}
        {/* ruta: la línea completa tenue y lo recorrido en azul fuerte */}
        <polyline points={poli(ruta.map((q) => P(q.x, q.y, 0)))} fill="none" stroke="rgba(37,99,235,0.18)" strokeWidth={14 * k} strokeLinecap="round" strokeLinejoin="round" />
        <polyline points={poli(hecha.map((q) => P(q.x, q.y, 0)))} fill="none" stroke="#2563EB" strokeWidth={10 * k} strokeLinecap="round" strokeLinejoin="round" />
        {pin(ruta[0], "#2563EB", data.origen, 1)}
        {pin(ruta[ruta.length - 1], "#E5484D", data.destino, 0.3 + 0.7 * llega)}
        {p >= 0.995 ? null : (() => {
          // el punto que avanza desaparece al llegar (para que se vea el pin del destino)
          const a = P(cabeza.x, cabeza.y, 0);
          return <circle cx={a.x} cy={a.y} r={12 * k} fill="white" stroke="#2563EB" strokeWidth={7 * k} />;
        })()}
      </svg>
      {data.tiempo ? (
        <div style={{ position: "absolute", left: W * 0.06, top: H * (vertical ? 0.1 : 0.07), display: "flex", alignItems: "center", gap: 14 * k, padding: `${14 * k}px ${22 * k}px`, borderRadius: 18 * k, background: "white", boxShadow: `0 ${10 * k}px ${30 * k}px rgba(0,0,0,0.12)`, fontFamily: fuenteEscenas, opacity: pastilla, transform: `translateY(${(1 - pastilla) * -20 * k}px)` }}>
          <div style={{ width: 52 * k, height: 52 * k, borderRadius: 12 * k, background: "#2563EB", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 30 * k, fontWeight: 900 }}>➤</div>
          <div>
            <div style={{ fontWeight: 900, fontSize: 46 * k, color: "#111827", lineHeight: 1 }}>{data.tiempo}</div>
            <div style={{ fontWeight: 600, fontSize: 22 * k, color: "#6B7280", marginTop: 4 * k }}>
              {[data.distancia, data.origen && data.destino ? `${data.origen} → ${data.destino}` : ""].filter(Boolean).join(" · ")}
            </div>
          </div>
        </div>
      ) : null}
      <Leyenda data={data} claro />
    </AbsoluteFill>
  );
};
