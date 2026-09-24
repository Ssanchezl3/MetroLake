/* Interfaz de MetroLake: navegacion, batch, streaming y comparacion. */
"use strict";

const VISTAS = {
  panel: { titulo: "Panel general", desc: "Vista rápida del sistema de simulación." },
  batch: { titulo: "Simuladores (batch)", desc: "Genera un lote histórico con los tres simuladores." },
  streaming: { titulo: "Streaming en vivo", desc: "Eventos emitidos en tiempo real, fuente aleatoria." },
  comparar: { titulo: "Comparar", desc: "Simuladores batch frente a streaming, lado a lado." },
};

const CLASE_FUENTE = { pasajeros: "b-pasajeros", vibracion: "b-vibracion", clima: "b-clima" };

/* ---------- Navegacion del menu ---------- */
function activarVista(nombre) {
  document.querySelectorAll(".menu-item").forEach((b) =>
    b.classList.toggle("active", b.dataset.view === nombre)
  );
  document.querySelectorAll(".view").forEach((v) =>
    v.classList.toggle("active", v.id === `view-${nombre}`)
  );
  document.getElementById("view-title").textContent = VISTAS[nombre].titulo;
  document.getElementById("view-desc").textContent = VISTAS[nombre].desc;
}

document.querySelectorAll(".menu-item").forEach((b) =>
  b.addEventListener("click", () => activarVista(b.dataset.view))
);

/* ---------- Helpers de render ---------- */
function fmt(v) {
  if (typeof v === "number") return Number.isInteger(v) ? v.toLocaleString("es") : v;
  if (v && typeof v === "object") {
    return Object.entries(v).map(([k, n]) => `${k}: ${n}`).join(" · ");
  }
  return v;
}

const ETIQUETAS = {
  total_eventos: "Eventos", total_entradas: "Entradas", total_salidas: "Salidas",
  total_personas: "Personas", ocupacion_promedio_pct: "Ocupación media %",
  ocupacion_maxima_pct: "Ocupación máx %", estacion_mas_activa: "Estación top",
  eventos_hora_pico: "En hora pico", rms_promedio: "RMS medio", rms_maximo: "RMS máx",
  anomalias: "Anomalías", sensores_distintos: "Sensores", fatiga_maxima: "Fatiga máx",
  precipitacion_promedio_mm_h: "Lluvia media mm/h", precipitacion_maxima_mm_h: "Lluvia máx mm/h",
  lecturas_con_lluvia: "Con lluvia", niveles_alerta: "Alertas", pluviometros_distintos: "Pluviómetros",
};

function grupoMetricas(titulo, tagClase, resumen) {
  const items = Object.entries(resumen)
    .map(([k, v]) => `<div class="metric"><b>${fmt(v)}</b><span>${ETIQUETAS[k] || k}</span></div>`)
    .join("");
  return `
    <div class="metric-group">
      <div class="metric-group-title"><span class="tag ${tagClase}">${titulo}</span></div>
      <div class="metric-list">${items}</div>
    </div>`;
}

function renderResumen(contenedor, resumen) {
  contenedor.innerHTML =
    grupoMetricas("Pasajeros", "tag-pasajeros", resumen.pasajeros) +
    grupoMetricas("Vibración", "tag-vibracion", resumen.vibracion) +
    grupoMetricas("Clima", "tag-clima", resumen.clima);
}

function filaEvento(ev, tipo, cssBorde) {
  const claves = Object.entries(ev)
    .filter(([k]) => !k.startsWith("_"))
    .slice(0, 6)
    .map(([k, v]) => `<span class="k">${k}</span>=<span class="v">${fmt(v)}</span>`)
    .join("  ");
  return `<div class="feed-row ${cssBorde}">${claves}</div>`;
}

/* ---------- Estado / configuracion ---------- */
async function cargarEstado() {
  try {
    const r = await fetch("/api/estado");
    const d = await r.json();
    document.getElementById("cfg-estaciones").textContent = d.total_estaciones;
    document.getElementById("cfg-tramos").textContent = d.total_tramos;
    document.getElementById("cfg-sensores").textContent = d.total_sensores;
    document.getElementById("cfg-pluviometros").textContent = d.pluviometros.length;
  } catch (e) {
    console.error("No se pudo cargar el estado:", e);
  }
}

/* ---------- Batch ---------- */
async function ejecutarBatch(destinoResumen, destinoMuestras, statusEl) {
  const minutos = document.getElementById("batch-minutos")?.value || 30;
  statusEl.textContent = "Generando…";
  const r = await fetch(`/api/batch?minutos=${minutos}`);
  const d = await r.json();
  renderResumen(destinoResumen, d.resumen);
  if (destinoMuestras) {
    const filas = [];
    for (const tipo of ["pasajeros", "vibracion", "clima"]) {
      (d.muestras[tipo] || []).forEach((ev) =>
        filas.push(filaEvento(ev, tipo, CLASE_FUENTE[tipo]))
      );
    }
    destinoMuestras.innerHTML = filas.join("");
  }
  statusEl.textContent = `Listo · ventana ${d.ventana_min} min`;
  return d;
}

document.getElementById("btn-batch").addEventListener("click", () =>
  ejecutarBatch(
    document.getElementById("batch-resumen"),
    document.getElementById("batch-muestras"),
    document.getElementById("batch-status")
  )
);

/* ---------- Streaming ---------- */
let streamTimer = null;
const conteo = { vibracion: 0, pasajeros: 0, clima: 0 };

function actualizarConteos() {
  document.getElementById("c-vibracion").textContent = conteo.vibracion;
  document.getElementById("c-pasajeros").textContent = conteo.pasajeros;
  document.getElementById("c-clima").textContent = conteo.clima;
  document.getElementById("c-total").textContent =
    conteo.vibracion + conteo.pasajeros + conteo.clima;
}

async function tickStreaming() {
  try {
    const r = await fetch("/api/streaming/evento");
    const ev = await r.json();
    const tipo = ev._tipo_fuente;
    conteo[tipo] = (conteo[tipo] || 0) + 1;
    actualizarConteos();
    const feed = document.getElementById("stream-feed");
    feed.insertAdjacentHTML("afterbegin", filaEvento(ev, tipo, CLASE_FUENTE[tipo]));
    while (feed.children.length > 40) feed.removeChild(feed.lastChild);
  } catch (e) {
    console.error("Error de streaming:", e);
  }
}

function iniciarStreaming() {
  if (streamTimer) return;
  const intervalo = parseInt(document.getElementById("stream-intervalo").value, 10);
  document.getElementById("btn-stream-start").disabled = true;
  document.getElementById("btn-stream-stop").disabled = false;
  const s = document.getElementById("stream-status");
  s.textContent = "En vivo"; s.classList.add("live");
  tickStreaming();
  streamTimer = setInterval(tickStreaming, intervalo);
}

function detenerStreaming() {
  clearInterval(streamTimer);
  streamTimer = null;
  document.getElementById("btn-stream-start").disabled = false;
  document.getElementById("btn-stream-stop").disabled = true;
  const s = document.getElementById("stream-status");
  s.textContent = "Detenido"; s.classList.remove("live");
}

document.getElementById("btn-stream-start").addEventListener("click", iniciarStreaming);
document.getElementById("btn-stream-stop").addEventListener("click", detenerStreaming);
document.getElementById("stream-intervalo").addEventListener("change", () => {
  if (streamTimer) { detenerStreaming(); iniciarStreaming(); }
});

/* ---------- Comparar ---------- */
async function ejecutarComparacion() {
  const status = document.getElementById("comparar-status");
  status.textContent = "Procesando…";

  // Lado batch: reutiliza el endpoint batch (ventana de 30 min).
  const rb = await fetch("/api/batch?minutos=30");
  const db = await rb.json();
  renderResumen(document.getElementById("cmp-batch"), db.resumen);

  // Lado streaming: recolecta una muestra de eventos en vivo y la resume.
  const muestra = { pasajeros: [], vibracion: [], clima: [] };
  for (let i = 0; i < 60; i++) {
    const r = await fetch("/api/streaming/evento");
    const ev = await r.json();
    muestra[ev._tipo_fuente].push(ev);
  }
  renderResumen(document.getElementById("cmp-stream"), {
    pasajeros: resumirPasajeros(muestra.pasajeros),
    vibracion: resumirVibracion(muestra.vibracion),
    clima: resumirClima(muestra.clima),
  });
  status.textContent = "Comparación lista · 30 min batch vs 60 eventos live";
}

/* Resumenes en cliente para la muestra de streaming (equivalentes al backend). */
function resumirPasajeros(evs) {
  if (!evs.length) return { total_eventos: 0 };
  const ent = evs.reduce((a, e) => a + e.entradas, 0);
  const sal = evs.reduce((a, e) => a + e.salidas, 0);
  const oc = evs.map((e) => e.ocupacion_estimada_pct);
  return {
    total_eventos: evs.length, total_entradas: ent, total_salidas: sal,
    total_personas: ent + sal,
    ocupacion_promedio_pct: +(oc.reduce((a, b) => a + b, 0) / oc.length).toFixed(1),
    ocupacion_maxima_pct: Math.max(...oc),
    eventos_hora_pico: evs.filter((e) => e.hora_pico).length,
  };
}
function resumirVibracion(evs) {
  if (!evs.length) return { total_eventos: 0 };
  const rms = evs.map((e) => e.vibracion_rms_mm_s2);
  return {
    total_eventos: evs.length,
    rms_promedio: +(rms.reduce((a, b) => a + b, 0) / rms.length).toFixed(4),
    rms_maximo: Math.max(...rms),
    anomalias: evs.filter((e) => e.es_anomalia).length,
    sensores_distintos: new Set(evs.map((e) => e.sensor_id)).size,
  };
}
function resumirClima(evs) {
  if (!evs.length) return { total_eventos: 0 };
  const p = evs.map((e) => e.precipitacion_mm_h);
  const niveles = {};
  evs.forEach((e) => (niveles[e.nivel_alerta] = (niveles[e.nivel_alerta] || 0) + 1));
  return {
    total_eventos: evs.length,
    precipitacion_promedio_mm_h: +(p.reduce((a, b) => a + b, 0) / p.length).toFixed(2),
    precipitacion_maxima_mm_h: Math.max(...p),
    lecturas_con_lluvia: evs.filter((e) => e.esta_lloviendo).length,
    niveles_alerta: niveles,
  };
}

document.getElementById("btn-comparar").addEventListener("click", ejecutarComparacion);

/* ---------- Init ---------- */
cargarEstado();
