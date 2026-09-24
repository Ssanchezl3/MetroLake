"""Servidor web de MetroLake.

Expone una interfaz visual para simular el proyecto: ejecuta los mismos
simuladores del sistema (torniquetes, vibracion y clima) tanto en modo
batch (dataset historico) como en modo streaming, y permite compararlos.

No duplica la logica de negocio: reutiliza directamente las clases y
funciones existentes en `Fuentes/` y `Ejecucion/`.
"""

import os
import random
import sys
from collections import Counter
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request

# Permite importar los paquetes del proyecto al ejecutar desde cualquier ruta.
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from Fuentes.accelerometer import SimuladorAcelerometro  # noqa: E402
from Fuentes.turnstiles import SimuladorTorniquetes  # noqa: E402
from Fuentes.weather import SimuladorClima  # noqa: E402

app = Flask(__name__)

# Instancias unicas: conservan perfiles de estaciones y sensores entre peticiones.
_sim_vibracion = SimuladorAcelerometro()
_sim_pasajeros = SimuladorTorniquetes()
_sim_clima = SimuladorClima()

PESOS_STREAMING = {"vibracion": 0.5, "pasajeros": 0.35, "clima": 0.15}


def _resumir_pasajeros(eventos):
    if not eventos:
        return {}
    total_entradas = sum(e["entradas"] for e in eventos)
    total_salidas = sum(e["salidas"] for e in eventos)
    ocupacion = [e["ocupacion_estimada_pct"] for e in eventos]
    por_estacion = Counter(e["estacion"] for e in eventos)
    top = max(por_estacion, key=por_estacion.get)
    return {
        "total_eventos": len(eventos),
        "total_entradas": total_entradas,
        "total_salidas": total_salidas,
        "total_personas": total_entradas + total_salidas,
        "ocupacion_promedio_pct": round(sum(ocupacion) / len(ocupacion), 1),
        "ocupacion_maxima_pct": max(ocupacion),
        "estacion_mas_activa": top,
        "eventos_hora_pico": sum(1 for e in eventos if e["hora_pico"]),
    }


def _resumir_vibracion(eventos):
    if not eventos:
        return {}
    rms = [e["vibracion_rms_mm_s2"] for e in eventos]
    return {
        "total_eventos": len(eventos),
        "rms_promedio": round(sum(rms) / len(rms), 4),
        "rms_maximo": max(rms),
        "anomalias": sum(1 for e in eventos if e["es_anomalia"]),
        "sensores_distintos": len({e["sensor_id"] for e in eventos}),
        "fatiga_maxima": round(max(e["fatiga_acumulada"] for e in eventos), 4),
    }


def _resumir_clima(eventos):
    if not eventos:
        return {}
    precip = [e["precipitacion_mm_h"] for e in eventos]
    niveles = Counter(e["nivel_alerta"] for e in eventos)
    return {
        "total_eventos": len(eventos),
        "precipitacion_promedio_mm_h": round(sum(precip) / len(precip), 2),
        "precipitacion_maxima_mm_h": max(precip),
        "lecturas_con_lluvia": sum(1 for e in eventos if e["esta_lloviendo"]),
        "niveles_alerta": dict(niveles),
        "pluviometros_distintos": len({e["pluviometro_id"] for e in eventos}),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/estado")
def estado():
    """Metadatos de configuracion para poblar la interfaz."""
    return jsonify({
        "estaciones": _sim_pasajeros.estaciones,
        "total_estaciones": len(_sim_pasajeros.estaciones),
        "total_sensores": len(_sim_vibracion.sensores),
        "total_tramos": len(_sim_vibracion.tramos),
        "pluviometros": [p["nombre"] for p in _sim_clima.PLUVIOMETROS],
        "pesos_streaming": PESOS_STREAMING,
    })


@app.route("/api/batch")
def batch():
    """Genera un lote 'batch' (dataset historico) de las tres fuentes.

    Reutiliza los mismos metodos `generar_lote` que usa `dataset.py`.
    """
    minutos = max(1, min(int(request.args.get("minutos", 30)), 240))
    inicio = datetime.now().replace(second=0, microsecond=0) - timedelta(minutes=minutos)

    n_estaciones = len(_sim_pasajeros.estaciones)
    pasajeros = _sim_pasajeros.generar_lote(n_minutos=minutos, inicio=inicio)
    vibracion = _sim_vibracion.generar_lote(
        n=minutos * 2, inicio=inicio, intervalo_seg=30
    )
    clima = _sim_clima.generar_lote(
        n_lecturas=max(1, minutos // 5), inicio=inicio, intervalo_min=5
    )

    return jsonify({
        "modo": "batch",
        "ventana_min": minutos,
        "muestras": {
            "pasajeros": pasajeros[: 3 * n_estaciones][-6:],
            "vibracion": vibracion[-6:],
            "clima": clima[-6:],
        },
        "resumen": {
            "pasajeros": _resumir_pasajeros(pasajeros),
            "vibracion": _resumir_vibracion(vibracion),
            "clima": _resumir_clima(clima),
        },
    })


@app.route("/api/streaming/evento")
def streaming_evento():
    """Emite un unico evento de streaming, igual que `modo_streaming`.

    Selecciona una fuente al azar con los mismos pesos del proyecto y le
    agrega el campo `_tipo_fuente`.
    """
    ts = datetime.now()
    tipos = list(PESOS_STREAMING)
    tipo = random.choices(tipos, weights=[PESOS_STREAMING[t] for t in tipos])[0]

    if tipo == "vibracion":
        evento = _sim_vibracion.generar_evento(timestamp=ts)
    elif tipo == "pasajeros":
        evento = _sim_pasajeros.generar_evento(timestamp=ts)
    else:
        evento = _sim_clima.generar_lectura(timestamp=ts)

    evento["_tipo_fuente"] = tipo
    return jsonify(evento)


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=True)
