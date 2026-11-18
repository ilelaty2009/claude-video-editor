// Escenas de datos y redes: pantalla dividida (el panel de contenido), gráfica que se construye sola,
// mapa con ruta animada y llamada a la acción (seguir + comentar).
import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, OffthreadVideo, spring, staticFile } from "remotion";
import { clamp, curvas, salida, useConfigDiseno, useCuadro } from "../tiempo";
import { fuenteEscenas } from "../fuentes";
import { colores, Fondo, useK } from "./base";
import { camaraPantalla, rectsDividida } from "./camara";
import type { Escena } from "./tipos";

const esVideo = (a: string) => /\.(mp4|mov|webm|m4v)$/i.test(a);

// ---------- PANTALLA DIVIDIDA (el panel; a la persona la mueve Edit.tsx) ----------
export const EscenaDividida: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames, width, height, fpsReal } = useConfigDiseno();
  const k = useK();
  const modo = e.modo ?? (width > height ? "lado" : "apilada");
  const { panel } = rectsDividida(modo, width, height, e.lado === "der" ? "der" : "izq");
  // mismo resorte que la persona (camara.ts -> estadoDividida), para que se muevan juntos
  const ent = spring({ frame, fps, config: { damping: 18, stiffness: 120 } });
  const sal = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], { ...clamp, easing: curvas.cambia });
  const t = Math.min(ent, sal);
  const kb = interpolate(frame, [0, durationInFrames], [1.03, 1.12], { ...clamp, easing: curvas.camara }); // Ken Burns
  const mover =
    modo === "apilada" ? `translateY(${(1 - t) * -panel.h}px)` : modo === "lado" ? `translateX(${(1 - t) * (e.lado === "der" ? panel.w : -panel.w)}px)` : `scale(${1.06 - 0.06 * t})`;
  const lineas = e.lineas ?? [];
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: panel.x,
          top: panel.y,
          width: panel.w,
          height: panel.h,
          overflow: "hidden",
          transform: mover,
          opacity: modo === "pip" ? t : 1,
          background: colores.fondo,
        }}
      >
        {e.archivo ? (
          <AbsoluteFill style={{ transform: `scale(${kb})` }}>
            {esVideo(e.archivo) ? (
              <OffthreadVideo src={staticFile(e.archivo)} muted trimBefore={Math.round((e.desdeSeg ?? 0) * fpsReal)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : (
              <Img src={staticFile(e.archivo)} style={{ width: "100%", height: "100%", objectFit: e.completo ? "contain" : "cover" }} />
            )}
          </AbsoluteFill>
        ) : null}
        {lineas.length || e.arriba ? (
          // sin archivo (o encima de él): puntos clave en grande dentro del panel
          <AbsoluteFill
            style={{
              justifyContent: "center",
              alignItems: "center",
              padding: 60 * k,
              background: e.archivo ? "linear-gradient(to top, rgba(5,7,16,0.8), transparent 60%)" : undefined,
              fontFamily: fuenteEscenas,
              textAlign: "center",
            }}
          >
            {e.arriba ? <div style={{ fontWeight: 700, fontSize: 40 * k, color: "rgba(255,255,255,0.85)", textTransform: "uppercase", marginBottom: 10 * k }}>{e.arriba}</div> : null}
            {lineas.map((l, i) => {
              const inicio = l.enMs !== undefined ? ((l.enMs - e.desdeMs) / 1000) * fps : 8 + i * 8;
              const s = spring({ frame: frame - inicio, fps, config: { damping: 14, stiffness: 180 } });
              return (
                <div key={i} style={{ fontWeight: 900, fontSize: 96 * k, lineHeight: 1.02, color: l.color ?? "white", textTransform: "uppercase", opacity: s, transform: `translateY(${(1 - s) * 30 * k}px)` }}>
                  {l.texto}
                </div>
              );
            })}
          </AbsoluteFill>
        ) : null}
        {e.credito ? (
          <div style={{ position: "absolute", right: 16 * k, bottom: 12 * k, fontFamily: fuenteEscenas, fontSize: 18 * k, color: "rgba(255,255,255,0.75)", background: "rgba(0,0,0,0.35)", padding: `${3 * k}px ${8 * k}px`, borderRadius: 6 * k }}>
            {e.credito}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

// ---------- GRÁFICA QUE SE CONSTRUYE SOLA ----------
const formatear = (n: number, dec: number) =>
  dec === 0 ? Math.round(n).toLocaleString("es-CO") : n.toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec });

export const EscenaGrafica: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames, width, height } = useConfigDiseno();
  const k = useK();
  const valores = e.valores?.length ? e.valores : [1, 2, 3];
  const etiquetas = e.etiquetas ?? [];
  const max = Math.max(...valores) || 1;
  const min = Math.min(0, ...valores);
  const color = e.lineas?.[0]?.color ?? colores.azul;
  const dec = e.decimales ?? 0;
  // se construye en el 65 % de la escena (mínimo 1 s), con curva suave
  const fin = Math.max(fps, durationInFrames * 0.65);
  const p = interpolate(frame, [6, fin], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const vertical = height > width;
  // el área de la gráfica termina en el 70 % del alto: abajo quedan los subtítulos (no se tapan con el eje)
  const g = { x: width * 0.1, y: height * (vertical ? 0.36 : 0.3), w: width * 0.8, h: height * (vertical ? 0.3 : 0.4) };
  const yDe = (v: number) => g.y + g.h - ((v - min) / (max - min || 1)) * g.h;
  const xDe = (i: number) => g.x + (valores.length === 1 ? g.w / 2 : (i / (valores.length - 1)) * g.w);
  // valor actual del contador = el punto de la curva donde va el dibujo
  const pos = p * (valores.length - 1);
  const i0 = Math.floor(pos);
  const actual = valores.length === 1 ? valores[0] * p : valores[i0] + (valores[Math.min(i0 + 1, valores.length - 1)] - valores[i0]) * (pos - i0);
  const barras = e.grafica === "barras";
  const puntos = valores.map((v, i) => `${xDe(i)},${yDe(v)}`);
  const camino = `M${puntos.join(" L")}`;
  const largo = valores.reduce((s, v, i) => (i ? s + Math.hypot(xDe(i) - xDe(i - 1), yDe(v) - yDe(valores[i - 1])) : 0), 0);
  const titulo = spring({ frame, fps, config: { damping: 18 } });
  return (
    <Fondo entrada={e.entrada}>
      <div style={{ position: "absolute", left: g.x, top: height * (vertical ? 0.16 : 0.1), fontFamily: fuenteEscenas, opacity: titulo }}>
        {e.titulo ? <div style={{ fontWeight: 700, fontSize: 38 * k, color: "rgba(255,255,255,0.75)" }}>{e.titulo}</div> : null}
        <div style={{ fontWeight: 900, fontSize: 130 * k, color: "white", lineHeight: 1, fontVariantNumeric: "tabular-nums", letterSpacing: -3 * k }}>
          {e.prefijo ?? ""}
          {formatear(barras ? valores[valores.length - 1] * p : actual, dec)}
          {e.sufijo ?? ""}
        </div>
      </div>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <linearGradient id="relleno-grafica" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
          <clipPath id="avance-grafica">
            <rect x={0} y={0} width={g.x + g.w * p + 2} height={height} />
          </clipPath>
        </defs>
        {[0, 0.5, 1].map((f) => (
          <line key={f} x1={g.x} x2={g.x + g.w} y1={g.y + g.h * f} y2={g.y + g.h * f} stroke="rgba(255,255,255,0.12)" strokeWidth={2 * k} />
        ))}
        {barras
          ? valores.map((v, i) => {
              const s = interpolate(p * valores.length - i, [0, 1], [0, 1], { ...clamp, easing: curvas.entra });
              const bw = (g.w / valores.length) * 0.62;
              const x = g.x + (i + 0.5) * (g.w / valores.length) - bw / 2;
              const h = (yDe(min) - yDe(v)) * s;
              return <rect key={i} x={x} y={yDe(min) - h} width={bw} height={h} rx={10 * k} fill={i === valores.length - 1 ? color : "rgba(255,255,255,0.55)"} />;
            })
          : (
            <>
              <path d={`${camino} L${xDe(valores.length - 1)},${g.y + g.h} L${xDe(0)},${g.y + g.h} Z`} fill="url(#relleno-grafica)" clipPath="url(#avance-grafica)" />
              <path d={camino} fill="none" stroke={color} strokeWidth={7 * k} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={largo} strokeDashoffset={largo * (1 - p)} />
              <circle cx={g.x + g.w * p} cy={yDe(actual)} r={14 * k} fill="white" stroke={color} strokeWidth={6 * k} />
            </>
          )}
        {etiquetas.map((t, i) => (
          <text key={i} x={barras ? g.x + (i + 0.5) * (g.w / Math.max(1, etiquetas.length)) : xDe(Math.round((i / Math.max(1, etiquetas.length - 1)) * (valores.length - 1)))} y={g.y + g.h + 46 * k} textAnchor="middle" fill="rgba(255,255,255,0.65)" fontSize={28 * k} fontFamily={fuenteEscenas} fontWeight={700}>
            {t}
          </text>
        ))}
      </svg>
    </Fondo>
  );
};

// ---------- MAPA CON RUTA ANIMADA ----------
// Mapa dibujado (calles, manzanas y parques generados), sin internet ni licencias. La ruta va de origen a destino.
const azar = (n: number) => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

export const EscenaMapa: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames, width, height } = useConfigDiseno();
  const k = useK();
  const paso = Math.round(Math.min(width, height) * 0.11);
  const columnas = Math.ceil(width / paso) + 1;
  const filas = Math.ceil(height / paso) + 1;
  // ruta con quiebres, de abajo a la izquierda hacia arriba a la derecha (sobre las calles), lejos de los subtítulos
  const calle = (v: number) => Math.round(v / paso) * paso;
  const a = { x: calle(width * 0.16), y: calle(height * (height > width ? 0.6 : 0.62)) };
  const b = { x: calle(width * 0.82), y: calle(height * 0.26) };
  const m1 = { x: paso * Math.round(columnas / 2), y: a.y };
  const m2 = { x: m1.x, y: paso * Math.round(filas / 2) };
  const m3 = { x: b.x, y: m2.y };
  const ruta = [a, m1, m2, m3, b];
  const largo = ruta.reduce((s, p, i) => (i ? s + Math.hypot(p.x - ruta[i - 1].x, p.y - ruta[i - 1].y) : 0), 0);
  const p = interpolate(frame, [10, Math.max(fps, durationInFrames * 0.7)], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  // punto que viaja por la ruta
  let resto = p * largo;
  let punto = a;
  for (let i = 1; i < ruta.length; i++) {
    const d = Math.hypot(ruta[i].x - ruta[i - 1].x, ruta[i].y - ruta[i - 1].y);
    if (resto <= d) {
      const t = d ? resto / d : 0;
      punto = { x: ruta[i - 1].x + (ruta[i].x - ruta[i - 1].x) * t, y: ruta[i - 1].y + (ruta[i].y - ruta[i - 1].y) * t };
      break;
    }
    resto -= d;
    punto = ruta[i];
  }
  const llega = spring({ frame: frame - Math.max(fps, durationInFrames * 0.7), fps, config: { damping: 10, stiffness: 200 } });
  const zoom = interpolate(frame, [0, durationInFrames], [1.08, 1], { ...clamp, easing: curvas.camara });
  const sale = salida(frame, durationInFrames, 7);
  const pin = (x: number, y: number, color: string, texto: string | undefined, escala: number) => (
    <g transform={`translate(${x} ${y}) scale(${escala})`}>
      <circle r={22 * k} fill={color} stroke="white" strokeWidth={7 * k} />
      {texto ? (
        <text y={-40 * k} textAnchor="middle" fill="#1d2433" fontSize={34 * k} fontWeight={800} fontFamily={fuenteEscenas} paintOrder="stroke" stroke="white" strokeWidth={10 * k}>
          {texto}
        </text>
      ) : null}
    </g>
  );
  return (
    <AbsoluteFill style={{ background: "#EEF1F4", opacity: sale }}>
      <svg width={width} height={height} style={{ transform: `scale(${zoom})` }}>
        {Array.from({ length: columnas * filas }).map((_, i) => {
          const c = i % columnas;
          const f = Math.floor(i / columnas);
          const parque = azar(i) > 0.88;
          return <rect key={i} x={c * paso + 9 * k} y={f * paso + 9 * k} width={paso - 18 * k} height={paso - 18 * k} rx={8 * k} fill={parque ? "#BFE3B4" : "#DDE2E8"} />;
        })}
        <polyline points={ruta.map((q) => `${q.x},${q.y}`).join(" ")} fill="none" stroke="rgba(37,99,235,0.18)" strokeWidth={18 * k} strokeLinejoin="round" strokeLinecap="round" />
        <polyline points={ruta.map((q) => `${q.x},${q.y}`).join(" ")} fill="none" stroke="#2563EB" strokeWidth={12 * k} strokeLinejoin="round" strokeLinecap="round" strokeDasharray={largo} strokeDashoffset={largo * (1 - p)} />
        {pin(a.x, a.y, "#2563EB", e.origen, 1)}
        {pin(b.x, b.y, colores.rojo, e.destino, 0.4 + 0.6 * llega)}
        <circle cx={punto.x} cy={punto.y} r={16 * k} fill="white" stroke="#2563EB" strokeWidth={8 * k} />
      </svg>
      {e.texto ? (
        <div style={{ position: "absolute", left: 60 * k, top: height * (height > width ? 0.13 : 0.07), display: "flex", alignItems: "center", gap: 14 * k, background: "white", borderRadius: 18 * k, padding: `${14 * k}px ${22 * k}px`, boxShadow: `0 ${10 * k}px ${30 * k}px rgba(0,0,0,0.15)`, fontFamily: fuenteEscenas, opacity: spring({ frame: frame - 6, fps, config: { damping: 16 } }) }}>
          <div style={{ width: 54 * k, height: 54 * k, borderRadius: 12 * k, background: "#2563EB", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 30 * k }}>➜</div>
          <div>
            <div style={{ fontWeight: 900, fontSize: 44 * k, color: "#1d2433", lineHeight: 1 }}>{e.texto}</div>
            {e.etiqueta ? <div style={{ fontWeight: 600, fontSize: 24 * k, color: "#6B7280", marginTop: 4 * k }}>{e.etiqueta}</div> : null}
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

// ---------- LLAMADA A LA ACCIÓN: SEGUIR + COMENTAR ----------
export const EscenaCta: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, durationInFrames, width, height } = useConfigDiseno();
  const k = useK() * (height > width ? 1.55 : 1.25); // en vertical, más grande (se ve en el celular)
  const tarjeta = spring({ frame, fps, config: { damping: 16, stiffness: 150 } });
  const clic = durationInFrames * 0.32; // el cursor llega al botón y hace clic
  const siguiendo = frame >= clic;
  const palabra = e.palabra ?? "";
  const escribe = interpolate(frame, [clic + 10, clic + 10 + palabra.length * 2.2], [0, palabra.length], clamp);
  const publicado = frame > clic + 16 + palabra.length * 2.2;
  // el cursor viaja al botón y luego al campo del comentario
  const cx = interpolate(frame, [4, clic - 2, clic + 4, clic + 10], [420, 330, 330, 120], { ...clamp, easing: curvas.cambia });
  const cy = interpolate(frame, [4, clic - 2, clic + 4, clic + 10], [190, 24, 24, 130], { ...clamp, easing: curvas.cambia });
  const presion = frame > clic - 2 && frame < clic + 3 ? 0.92 : 1;
  const sale = salida(frame, durationInFrames, 7);
  const fila = { display: "flex", alignItems: "center", gap: 16 * k } as const;
  const numero = (n: number) => (
    <div style={{ width: 34 * k, height: 34 * k, borderRadius: 99, background: colores.rojo, color: "white", fontWeight: 800, fontSize: 20 * k, display: "flex", alignItems: "center", justifyContent: "center" }}>{n}</div>
  );
  return (
    // en vertical va en la mitad de arriba: al centro están los subtítulos y abajo los botones de la app
    <AbsoluteFill style={{ alignItems: "center", justifyContent: height > width ? "flex-start" : "center", paddingTop: height > width ? height * 0.25 : 0, background: "rgba(5,7,16,0.55)", opacity: sale, fontFamily: fuenteEscenas }}>
      <div style={{ position: "relative", width: 560 * k, padding: 30 * k, borderRadius: 24 * k, background: "white", boxShadow: `0 ${30 * k}px ${80 * k}px rgba(0,0,0,0.45)`, opacity: tarjeta, transform: `translateY(${(1 - tarjeta) * 40 * k}px) scale(${0.9 + 0.1 * tarjeta})` }}>
        {e.titulo ? <div style={{ fontWeight: 800, fontSize: 24 * k, color: colores.rojo, marginBottom: 18 * k }}>{e.titulo}</div> : null}
        <div style={{ ...fila, marginBottom: 22 * k }}>
          {numero(1)}
          <div style={{ width: 52 * k, height: 52 * k, borderRadius: 99, background: "#1d2447", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontSize: 24 * k }}>
            {(e.usuario ?? "?").replace("@", "").slice(0, 1).toUpperCase()}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 800, fontSize: 30 * k, color: "#111" }}>Seguir</div>
            <div style={{ fontWeight: 600, fontSize: 18 * k, color: "#6B7280" }}>{e.usuario ?? ""}</div>
          </div>
          <div style={{ padding: `${10 * k}px ${22 * k}px`, borderRadius: 10 * k, fontWeight: 800, fontSize: 20 * k, background: siguiendo ? "#E5E7EB" : "#4F46E5", color: siguiendo ? "#111" : "white", transform: `scale(${presion})` }}>
            {siguiendo ? "Siguiendo" : "Seguir"}
          </div>
        </div>
        <div style={fila}>
          {numero(2)}
          <div style={{ fontWeight: 800, fontSize: 30 * k, color: "#111" }}>Comenta</div>
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "space-between", border: `${2 * k}px solid ${frame > clic + 8 ? "#4F46E5" : "#E5E7EB"}`, borderRadius: 10 * k, padding: `${8 * k}px ${12 * k}px`, fontSize: 22 * k }}>
            <span style={{ color: escribe > 0 ? "#111" : "#9CA3AF", fontWeight: 700 }}>{escribe > 0 ? palabra.slice(0, Math.round(escribe)) : "Comenta…"}</span>
            <span style={{ color: publicado ? "#4F46E5" : "#C7D2FE", fontWeight: 800 }}>Publicar</span>
          </div>
        </div>
        {/* cursor */}
        <svg width={34 * k} height={34 * k} viewBox="0 0 24 24" style={{ position: "absolute", left: cx * k, top: cy * k + 70 * k, filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.4))" }}>
          <path d="M4 2l15 9-7 1.5L8.5 20z" fill="white" stroke="#111" strokeWidth={1.6} strokeLinejoin="round" />
        </svg>
      </div>
    </AbsoluteFill>
  );
};

// ---------- FONDO NUEVO (pantalla verde desde una toma normal) ----------
// Va detrás de la persona recortada (scripts/recorte_persona.py): cambia todo lo que hay detrás de ella.
export const EscenaFondo: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { durationInFrames, fpsReal } = useConfigDiseno();
  const o = Math.min(interpolate(frame, [0, 8], [0, 1], { ...clamp, easing: curvas.entra }), salida(frame, durationInFrames, 8));
  const kb = interpolate(frame, [0, durationInFrames], [1.04, 1.1], { ...clamp, easing: curvas.camara });
  return (
    <AbsoluteFill style={{ opacity: o, background: e.color ?? colores.fondo }}>
      {e.archivo ? (
        <AbsoluteFill style={{ transform: `scale(${kb})` }}>
          {esVideo(e.archivo) ? (
            <OffthreadVideo src={staticFile(e.archivo)} muted trimBefore={Math.round((e.desdeSeg ?? 0) * fpsReal)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <Img src={staticFile(e.archivo)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          )}
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};

// ---------- GRABACIÓN DE PANTALLA "CINEMATOGRÁFICA" (como Screen Studio) ----------
// La grabación va en una ventana con esquinas redondeadas y sombra sobre el fondo de la marca, y la cámara se acerca
// sola a donde pasa algo (recorrido de scripts/pantalla.py: "zooms" [{t, x, y, z}]).
export const EscenaPantalla: React.FC<{ e: Escena }> = ({ e }) => {
  const frame = useCuadro();
  const { fps, width, height, fpsReal } = useConfigDiseno();
  const k = useK();
  const seg = frame / fps + (e.desdeSeg ?? 0);
  const cam = camaraPantalla(e.zooms ?? [], seg);
  const margen = Math.min(width, height) * 0.08; // aire alrededor de la ventana (como Screen Studio)
  const W = width - margen * 2;
  const H = height > width ? W * (9 / 16) : height - margen * 2; // en vertical: ventana 16:9 en el centro
  // mover para que el punto (x, y) quede al centro, sin mostrar bordes vacíos
  const lim = (v: number) => ((cam.z - 1) / 2) * v;
  const tx = Math.max(-lim(W), Math.min(lim(W), (0.5 - cam.x) * W * cam.z));
  const ty = Math.max(-lim(H), Math.min(lim(H), (0.5 - cam.y) * H * cam.z));
  return (
    <Fondo entrada={e.entrada}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: W, height: H, borderRadius: 18 * k, overflow: "hidden", boxShadow: `0 ${30 * k}px ${80 * k}px rgba(0,0,0,0.55)`, background: "#000", position: "relative" }}>
          <div style={{ position: "absolute", inset: 0, transform: `translate(${tx}px, ${ty}px) scale(${cam.z})` }}>
            {e.archivo ? (
              <OffthreadVideo src={staticFile(e.archivo)} muted trimBefore={Math.round((e.desdeSeg ?? 0) * fpsReal)} style={{ width: "100%", height: "100%", objectFit: "contain", background: "#fff" }} />
            ) : null}
          </div>
        </div>
      </AbsoluteFill>
    </Fondo>
  );
};

// ---------- CAPA (efecto con transparencia encima del video) ----------
// Un video .webm con fondo transparente (por ejemplo un efecto 3D hecho con HyperFrames: scripts/hyperframes.sh)
// que se pone encima del video, a pantalla completa. No tapa nada más que lo que dibuja.
export const EscenaCapa: React.FC<{ e: Escena }> = ({ e }) => {
  const { fpsReal } = useConfigDiseno();
  if (!e.archivo) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <OffthreadVideo src={staticFile(e.archivo)} transparent muted trimBefore={Math.round((e.desdeSeg ?? 0) * fpsReal)} style={{ width: "100%", height: "100%", objectFit: "contain" }} />
    </AbsoluteFill>
  );
};
