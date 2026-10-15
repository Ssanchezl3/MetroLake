/* Interfaz de MetroLake · Metro de Medellín.
   Vistas: panel, batch, streaming, consultas (H05) y comparar días (H05). */
"use strict";

const VISTAS = {
  panel: { titulo: "Panel general", desc: "Vista rápida del sistema de simulación." },
  batch: { titulo: "Simuladores (batch)", desc: "Genera un lote histórico con los tres simuladores." },
  streaming: { titulo: "Streaming en vivo", desc: "Eventos emitidos en tiempo real, fuente aleatoria." },
  consultas: { titulo: "Consultas y trazabilidad", desc: "Busca por día los datos almacenados y revísalos en tabla." },
  comparar: { titulo: "Comparar días", desc: "Guarda sesiones y compara el Día A contra el Día B." },
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
  // Al entrar a consultas o comparar, refresca la lista de dias disponibles.
  if (nombre === "consultas" || nombre === "comparar") cargarDias();
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
  return v === undefined || v === null ? "—" : v;
}

const ETIQUETAS = {
  total_eventos: "Eventos", total_entradas: "Entradas", total_salidas: "Salidas",
  total_personas: "Personas", ocupacion_promedio_pct: "Ocupación media %",
  ocupacion_maxima_pct: "Ocupación máx %", estacion_mas_activa: "Estación top",
  eventos_hora_pico: "En hora pico", rms_promedio: "RMS medio", rms_maximo: "RMS máx",
  anomalias: "Anomalías", sensores_distintos: "Sensores", fatiga_maxima: "Fatiga máx",
  precipitacion_promedio_mm_h: "Lluvia media mm/h", precipitacion_maxima_mm_h: "Lluvia máx mm/h",
  lecturas_con_lluvia: "Con lluvia", niveles_alerta: "Alertas", pluviometros_distintos: "Pluviómetros",
  eventos: "Eventos", entradas: "Entradas", salidas: "Salidas",
  por_tipo: "Por fuente", por_origen: "Por origen",
};

function grupoMetricas(titulo, tagClase, resumen) {
  if (!resumen || !Object.keys(resumen).length) {
    return `<div class="metric-group"><div class="metric-group-title">
      <span class="tag ${tagClase}">${titulo}</span></div>
      <div class="muted">Sin datos.</div></div>`;
  }
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
    const d = await (await fetch("/api/estado")).json();
    document.getElementById("cfg-estaciones").textContent = d.total_estaciones;
    document.getElementById("cfg-tramos").textContent = d.total_tramos;
    document.getElementById("cfg-sensores").textContent = d.total_sensores;
    document.getElementById("cfg-pluviometros").textContent = d.pluviometros.length;
  } catch (e) {
    console.error("No se pudo cargar el estado:", e);
  }
}

/* ---------- Batch ---------- */
async function ejecutarBatch() {
  const minutos = document.getElementById("batch-minutos").value;
  const statusEl = document.getElementById("batch-status");
  statusEl.textContent = "Generando…";
  const d = await (await fetch(`/api/batch?minutos=${minutos}`)).json();
  renderResumen(document.getElementById("batch-resumen"), d.resumen);
  const filas = [];
  for (const tipo of ["pasajeros", "vibracion", "clima"]) {
    (d.muestras[tipo] || []).forEach((ev) => filas.push(filaEvento(ev, tipo, CLASE_FUENTE[tipo])));
  }
  document.getElementById("batch-muestras").innerHTML = filas.join("");
  statusEl.textContent = `Listo · ventana ${d.ventana_min} min`;
}

async function guardarBatch() {
  const minutos = document.getElementById("batch-minutos").value;
  const statusEl = document.getElementById("batch-status");
  statusEl.textContent = "Guardando…";
  const r = await fetch(`/api/guardar/batch?minutos=${minutos}`, { method: "POST" });
  const d = await r.json();
  statusEl.textContent = d.guardado
    ? `💾 Guardado · ${d.eventos} eventos → ${d.ruta}`
    : `No se pudo guardar: ${d.motivo || "error"}`;
}

document.getElementById("btn-batch").addEventListener("click", ejecutarBatch);
document.getElementById("btn-batch-save").addEventListener("click", guardarBatch);

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
    const ev = await (await fetch("/api/streaming/evento")).json();
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

async function guardarStreaming() {
  const statusEl = document.getElementById("stream-status");
  const r = await fetch("/api/guardar/streaming", { method: "POST" });
  const d = await r.json();
  statusEl.classList.remove("live");
  statusEl.textContent = d.guardado
    ? `💾 Guardado · ${d.eventos} eventos → ${d.ruta}`
    : `Nada que guardar (${d.motivo || "sin eventos"})`;
}

document.getElementById("btn-stream-start").addEventListener("click", iniciarStreaming);
document.getElementById("btn-stream-stop").addEventListener("click", detenerStreaming);
document.getElementById("btn-stream-save").addEventListener("click", guardarStreaming);
document.getElementById("stream-intervalo").addEventListener("change", () => {
  if (streamTimer) { detenerStreaming(); iniciarStreaming(); }
});

/* ---------- Consultas (H05) ---------- */
let filasActuales = [];   // cache de la ultima consulta, para el buscador

async function cargarDias() {
  try {
    const d = await (await fetch("/api/consultas/dias")).json();
    const dias = d.dias || [];
    const opciones = dias.length
      ? dias.map((x) => `<option value="${x}">${x}</option>`).join("")
      : `<option value="">— sin datos —</option>`;
    for (const id of ["q-dia", "cmp-dia-a", "cmp-dia-b"]) {
      const sel = document.getElementById(id);
      if (sel) {
        const previo = sel.value;
        sel.innerHTML = opciones;
        if (dias.includes(previo)) sel.value = previo;
      }
    }
    // Por comodidad, deja A y B en dias distintos si hay al menos dos.
    if (dias.length >= 2) {
      document.getElementById("cmp-dia-a").value = dias[0];
      document.getElementById("cmp-dia-b").value = dias[1];
    }
  } catch (e) {
    console.error("No se pudieron cargar los días:", e);
  }
}

const COLUMNAS = {
  pasajeros: ["timestamp", "estacion", "entradas", "salidas", "total_personas", "ocupacion_estimada_pct", "hora_pico"],
  vibracion: ["timestamp", "sensor_id", "tramo_id", "vibracion_rms_mm_s2", "frecuencia_hz", "fatiga_acumulada", "es_anomalia"],
  clima: ["timestamp", "pluviometro_id", "nombre_estacion", "precipitacion_mm_h", "nivel_alerta", "esta_lloviendo"],
  mixto: ["_tipo_fuente", "_origen", "timestamp", "event_id", "estacion", "sensor_id", "pluviometro_id"],
};

function renderTabla(filas, tipo) {
  const tabla = document.getElementById("q-tabla");
  const thead = tabla.querySelector("thead");
  const tbody = tabla.querySelector("tbody");
  if (!filas.length) {
    thead.innerHTML = ""; tbody.innerHTML = `<tr><td class="muted">No hay datos para este filtro.</td></tr>`;
    return;
  }
  const cols = (tipo !== "todos" && COLUMNAS[tipo]) ? COLUMNAS[tipo] : COLUMNAS.mixto;
  thead.innerHTML = "<tr>" + cols.map((c) => `<th>${c.replace(/^_/, "")}</th>`).join("") + "</tr>";
  tbody.innerHTML = filas.slice(0, 500).map((f) => {
    return "<tr>" + cols.map((c) => {
      let v = f[c];
      if (c === "_tipo_fuente" && v) return `<td><span class="pill pill-${v}">${v}</span></td>`;
      if (c === "_origen" && v) return `<td><span class="pill pill-origen">${v}</span></td>`;
      return `<td>${v === undefined || v === null ? "" : fmt(v)}</td>`;
    }).join("") + "</tr>";
  }).join("");
}

function renderResumenConsulta(resumen) {
  const cont = document.getElementById("q-resumen");
  const general = { total_eventos: resumen.total_eventos, por_tipo: resumen.por_tipo, por_origen: resumen.por_origen };
  cont.innerHTML =
    grupoMetricas("Resumen del día", "tag-clima", general) +
    (resumen.pasajeros ? grupoMetricas("Pasajeros", "tag-pasajeros", resumen.pasajeros) : "") +
    (resumen.vibracion ? grupoMetricas("Vibración", "tag-vibracion", resumen.vibracion) : "") +
    (resumen.clima ? grupoMetricas("Clima", "tag-clima", resumen.clima) : "");
}

async function consultarDia() {
  const dia = document.getElementById("q-dia").value;
  const origen = document.getElementById("q-origen").value;
  const tipo = document.getElementById("q-tipo").value;
  const statusEl = document.getElementById("q-status");
  if (!dia) { statusEl.textContent = "Selecciona un día."; return; }
  statusEl.textContent = "Consultando…";
  const d = await (await fetch(`/api/consultas/dia?dia=${dia}&origen=${origen}&tipo=${tipo}`)).json();
  filasActuales = d.filas || [];
  renderResumenConsulta(d.resumen);
  aplicarBuscador(tipo);
  document.getElementById("q-count").textContent = `· ${d.total.toLocaleString("es")} eventos`;
  statusEl.textContent = `Listo · ${dia}`;
}

function aplicarBuscador(tipo) {
  const q = document.getElementById("q-buscar").value.trim().toLowerCase();
  const tipoActual = tipo || document.getElementById("q-tipo").value;
  const filtradas = q
    ? filasActuales.filter((f) => JSON.stringify(f).toLowerCase().includes(q))
    : filasActuales;
  renderTabla(filtradas, tipoActual);
}

document.getElementById("btn-consultar").addEventListener("click", consultarDia);
document.getElementById("btn-refrescar-dias").addEventListener("click", cargarDias);
document.getElementById("q-buscar").addEventListener("input", () => aplicarBuscador());

/* ---------- Comparar días A vs B (H05) ---------- */
async function compararDias() {
  const a = document.getElementById("cmp-dia-a").value;
  const b = document.getElementById("cmp-dia-b").value;
  const statusEl = document.getElementById("comparar-status");
  if (!a || !b) { statusEl.textContent = "Selecciona ambos días."; return; }
  statusEl.textContent = "Comparando…";
  const d = await (await fetch(`/api/consultas/comparar?dia_a=${a}&dia_b=${b}`)).json();
  document.getElementById("cmp-head-a").textContent = `Día ${a}`;
  document.getElementById("cmp-head-b").textContent = `Día ${b}`;
  renderResumenComparacion(document.getElementById("cmp-a"), d.dia_a.resumen);
  renderResumenComparacion(document.getElementById("cmp-b"), d.dia_b.resumen);
  statusEl.textContent = "Comparación lista";
}

function renderResumenComparacion(cont, resumen) {
  const general = { total_eventos: resumen.total_eventos, por_tipo: resumen.por_tipo, por_origen: resumen.por_origen };
  cont.innerHTML =
    grupoMetricas("Resumen", "tag-clima", general) +
    (resumen.pasajeros ? grupoMetricas("Pasajeros", "tag-pasajeros", resumen.pasajeros) : "") +
    (resumen.vibracion ? grupoMetricas("Vibración", "tag-vibracion", resumen.vibracion) : "") +
    (resumen.clima ? grupoMetricas("Clima", "tag-clima", resumen.clima) : "");
}

document.getElementById("btn-comparar").addEventListener("click", compararDias);

/* ---------- Init ---------- */
cargarEstado();
