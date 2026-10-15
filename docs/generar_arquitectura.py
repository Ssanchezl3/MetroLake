"""Genera el diagrama de arquitectura (PNG) de MetroLake en GCP.

Refleja unicamente lo que el proyecto implementa o documenta:

  Simuladores (Vibracion, Pasajeros, Clima+Open-Meteo)
      -> publicador_gcp.py (google-cloud-pubsub)
      -> 3 temas Pub/Sub (vibracion, pasajeros, clima)
      -> 3 BigQuery subscriptions (sub-metro-*-bq)
      -> BigQuery (tablas RT + agregadas historicas) + BigQuery ML
      -> Alertas Operacionales / Visualizacion

Capa de lote: Google Cloud Storage (historicos del batch) -> BigQuery.

Se eliminaron del diseno original los componentes NO usados: Dataflow,
Dataproc/Spark y el "Monolito de Ingesta API REST".

Uso:
    MPLCONFIGDIR=/tmp/mpl python docs/generar_arquitectura.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# Paleta Metro de Medellin
VERDE = "#00953b"
VERDE_OSC = "#007a30"
NARANJA = "#f29100"
AZUL = "#0072bc"
MORADO = "#8e44ad"
GRIS_BORDE = "#9aa7b2"
TEXTO = "#1f2b33"

fig, ax = plt.subplots(figsize=(12, 13.5))
ax.set_xlim(0, 100)
ax.set_ylim(0, 115)
ax.axis("off")


def caja(x, y, w, h, titulo, subtitulo="", color_borde=GRIS_BORDE,
         color_fondo="#ffffff", titulo_color=TEXTO, fs_titulo=11, fs_sub=8.5):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
        linewidth=1.6, edgecolor=color_borde, facecolor=color_fondo, zorder=2))
    cy = y + h / 2 + (1.4 if subtitulo else 0)
    ax.text(x + w / 2, cy, titulo, ha="center", va="center",
            fontsize=fs_titulo, fontweight="bold", color=titulo_color, zorder=3)
    if subtitulo:
        ax.text(x + w / 2, y + h / 2 - 2.0, subtitulo, ha="center", va="center",
                fontsize=fs_sub, color=TEXTO, zorder=3)


def contenedor(x, y, w, h, etiqueta, color=VERDE):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.5",
        linewidth=1.8, edgecolor=color, facecolor="none", linestyle="-", zorder=1))
    ax.text(x + 1.5, y + h - 2.2, etiqueta, ha="left", va="center",
            fontsize=10.5, fontweight="bold", color=color, zorder=3)


def flecha(x1, y1, x2, y2, texto="", color=VERDE_OSC, estilo="-", off=0):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
        linewidth=1.8, color=color, linestyle=estilo, zorder=2,
        shrinkA=2, shrinkB=2))
    if texto:
        mx, my = (x1 + x2) / 2 + off, (y1 + y2) / 2
        ax.text(mx, my, texto, ha="center", va="center", fontsize=8,
                color=color, style="italic", zorder=4,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))


# ===== Titulo =====
ax.text(50, 112, "MetroLake · Arquitectura de datos en GCP", ha="center",
        fontsize=16, fontweight="bold", color=VERDE_OSC)
ax.text(50, 108.5, "Mantenimiento Predictivo · Clima · Afluencia", ha="center",
        fontsize=10.5, color=TEXTO)

# ===== 1. Fuentes de datos =====
contenedor(14, 93, 72, 12.5, "1 · Fuentes de Datos (Simuladores Python)")
caja(18, 95, 19, 7, "Vibración", "SimuladorAcelerometro", AZUL, "#eaf3fb", AZUL)
caja(40.5, 95, 19, 7, "Pasajeros", "SimuladorTorniquetes", MORADO, "#f3eafa", MORADO)
caja(63, 95, 19, 7, "Clima", "Open-Meteo API + fallback", NARANJA, "#fcefd8", "#b56b00")

# ===== 2. Publicador =====
caja(33, 83, 34, 6.5, "Integraciones/publicador_gcp.py",
     "google-cloud-pubsub · pesos 50/35/15", VERDE, "#e4f3ea", VERDE_OSC, 10.5)
flecha(50, 95, 50, 89.5, "eventos JSON")

# ===== 3. Capa de velocidad: Pub/Sub (3 temas) =====
contenedor(10, 66, 80, 13.5, "2 · Capa de Velocidad — Google Cloud Pub/Sub", VERDE)
caja(13, 68, 22, 7, "tema-metro-\nvibracion", "", AZUL, "#eaf3fb", AZUL, 9.5)
caja(39, 68, 22, 7, "tema-metro-\npasajeros", "", MORADO, "#f3eafa", MORADO, 9.5)
caja(65, 68, 22, 7, "tema-metro-\nclima", "", NARANJA, "#fcefd8", "#b56b00", 9.5)
flecha(42, 83, 24, 75.2, "", VERDE_OSC)
flecha(50, 83, 50, 75.2, "", VERDE_OSC)
flecha(58, 83, 76, 75.2, "", VERDE_OSC)

# ===== 4. BigQuery subscriptions =====
contenedor(10, 51, 80, 11.5, "3 · BigQuery Subscriptions", GRIS_BORDE)
caja(13, 52, 22, 6, "sub-metro-vib-bq", "", AZUL, "#f5f8fb", AZUL, 9)
caja(39, 52, 22, 6, "sub-metro-pass-bq", "", MORADO, "#f8f5fb", MORADO, 9)
caja(65, 52, 22, 6, "sub-metro-clima-bq", "", NARANJA, "#fdf7ec", "#b56b00", 9)
flecha(24, 68, 24, 58.2, "", VERDE_OSC)
flecha(50, 68, 50, 58.2, "", VERDE_OSC)
flecha(76, 68, 76, 58.2, "escribe en BQ", VERDE_OSC, off=8)

# ===== 5. Serving layer: BigQuery =====
contenedor(14, 23, 72, 27, "4 · Capa de Servicio — BigQuery Data Warehouse", VERDE)
caja(18, 39, 30, 7.5, "Tablas en tiempo real",
     "vibracion · pasajeros · clima", VERDE, "#e4f3ea", VERDE_OSC, 10)
caja(52, 39, 30, 7.5, "Tablas agregadas",
     "metricas historicas", VERDE, "#e4f3ea", VERDE_OSC, 10)
caja(37, 26.5, 26, 7, "BigQuery ML",
     "modelo predictivo", VERDE_OSC, "#d4ebdd", VERDE_OSC, 10.5)
flecha(50, 53, 50, 46.6, "ingesta continua", VERDE_OSC)
flecha(33, 39, 44, 33.6, "vibración actual", VERDE_OSC, "--", off=-3)
flecha(67, 39, 56, 33.6, "desgaste acumulado", VERDE_OSC, "--", off=4)

# ===== Capa de lote (GCS) — columna lateral izquierda =====
# Se dibuja arriba-izquierda (a la altura del publicador) y baja por el margen
# izquierdo con una flecha en L, sin cruzar ninguna otra caja.
caja(0.5, 82.5, 15, 7, "Cloud Storage", "Data Lake\nhistóricos", GRIS_BORDE, "#eef2f5", TEXTO, 9.5, 8)
ax.add_patch(FancyArrowPatch(  # tramo vertical por el margen
    (4.5, 82.5), (4.5, 43.6), arrowstyle="-", linewidth=1.8, color=GRIS_BORDE,
    linestyle="--", zorder=1))
ax.add_patch(FancyArrowPatch(  # tramo horizontal hacia la capa de servicio
    (4.5, 43.6), (17.5, 43), arrowstyle="-|>", mutation_scale=16, linewidth=1.8,
    color=GRIS_BORDE, linestyle="--", zorder=1, shrinkA=0, shrinkB=2))
ax.text(4.6, 64, "procesamiento\ndiario (batch)", ha="center", va="center",
        fontsize=8, color="#5a6b76", style="italic", zorder=4,
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))

# ===== 6. Consumo =====
contenedor(26, 8, 48, 11, "5 · Consumo, Alertas y Visualización", NARANJA)
caja(30, 9.5, 18, 6.5, "Alertas\nOperacionales", "", NARANJA, "#fcefd8", "#b56b00", 9.5)
caja(52, 9.5, 18, 6.5, "Dashboard", "Looker Studio", AZUL, "#eaf3fb", AZUL, 9.5)
flecha(50, 26.5, 50, 19.1, "inspección preventiva", VERDE_OSC)

# ===== Nota de diseno =====
ax.text(50, 3.2,
        "Diseño alineado al código: ingesta directa de los simuladores a Pub/Sub (3 temas) "
        "y de Pub/Sub a BigQuery vía subscriptions.\nSe omiten componentes no implementados "
        "(Dataflow, Dataproc/Spark, monolito API REST).",
        ha="center", va="center", fontsize=8, color="#5a6b76", style="italic")

plt.tight_layout()
import os
salida = os.path.join(os.path.dirname(__file__), "img", "arquitectura.png")
os.makedirs(os.path.dirname(salida), exist_ok=True)
fig.savefig(salida, dpi=160, bbox_inches="tight", facecolor="white")
print("Diagrama generado en:", salida)
