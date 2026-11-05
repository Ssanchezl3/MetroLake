"""Evaluacion de Riesgo Diario de la operacion del Metro.

Analiza los eventos almacenados de un dia (vibracion, pasajeros y clima) y
calcula un nivel de riesgo operativo: BAJO, MEDIO o ALTO, explicando el porque
con los datos concretos que lo motivan.

El riesgo es la suma de puntos de tres factores, cada uno basado en criterios
derivados de los propios simuladores del proyecto:

- Infraestructura (vibracion): anomalias, RMS maximo y fatiga de los sensores.
- Clima (pluviometros): precipitacion y niveles de alerta amarilla/naranja/roja.
- Demanda (pasajeros): ocupacion estimada y volumen de personas.
"""

from typing import Dict, List

# Umbrales de puntuacion. Cada factor aporta como maximo ~4 puntos.
# El total se mapea a BAJO (<4), MEDIO (4-7) y ALTO (>=8).
UMBRAL_MEDIO = 4
UMBRAL_ALTO = 8

# Niveles de alerta climatica que se consideran de atencion.
_ALERTAS_SERIAS = {"naranja", "roja"}


def _factor_vibracion(vibracion: List[Dict]) -> Dict:
    puntos = 0
    razones = []
    if not vibracion:
        return {"puntos": 0, "razones": ["Sin datos de vibracion para evaluar."], "metricas": {}}

    rms = [e.get("vibracion_rms_mm_s2", 0) for e in vibracion]
    anomalias = sum(1 for e in vibracion if e.get("es_anomalia"))
    rms_max = round(max(rms), 3) if rms else 0
    rms_prom = round(sum(rms) / len(rms), 3) if rms else 0
    fatiga_max = round(max((e.get("fatiga_acumulada", 0) for e in vibracion), default=0), 3)
    pct_anomalias = round(anomalias / len(vibracion) * 100, 1)

    if anomalias == 0:
        razones.append("Sin anomalias de vibracion registradas.")
    elif pct_anomalias < 2:
        puntos += 1
        razones.append(f"{anomalias} anomalias de vibracion ({pct_anomalias}% de las lecturas).")
    elif pct_anomalias < 5:
        puntos += 2
        razones.append(f"Nivel moderado de anomalias: {anomalias} ({pct_anomalias}%).")
    else:
        puntos += 3
        razones.append(f"Alto numero de anomalias: {anomalias} ({pct_anomalias}%).")

    if rms_max >= 4.5:
        puntos += 1
        razones.append(f"Vibracion RMS maxima elevada: {rms_max} mm/s2.")
    if fatiga_max >= 0.8:
        puntos += 1
        razones.append(f"Fatiga acumulada alta en algun tramo: {fatiga_max}.")

    return {
        "puntos": puntos,
        "razones": razones,
        "metricas": {
            "anomalias": anomalias, "pct_anomalias": pct_anomalias,
            "rms_promedio": rms_prom, "rms_maximo": rms_max, "fatiga_maxima": fatiga_max,
        },
    }


def _factor_clima(clima: List[Dict]) -> Dict:
    puntos = 0
    razones = []
    if not clima:
        return {"puntos": 0, "razones": ["Sin datos de clima para evaluar."], "metricas": {}}

    precip = [e.get("precipitacion_mm_h", 0) for e in clima]
    precip_max = round(max(precip), 2) if precip else 0
    precip_prom = round(sum(precip) / len(precip), 2) if precip else 0
    alertas_serias = sum(1 for e in clima if e.get("nivel_alerta") in _ALERTAS_SERIAS)
    con_lluvia = sum(1 for e in clima if e.get("esta_lloviendo"))
    pct_lluvia = round(con_lluvia / len(clima) * 100, 1)

    if precip_max < 10:
        razones.append(f"Precipitacion baja (maxima {precip_max} mm/h).")
    elif precip_max < 30:
        puntos += 1
        razones.append(f"Lluvia moderada (maxima {precip_max} mm/h).")
    elif precip_max < 60:
        puntos += 2
        razones.append(f"Lluvia fuerte (maxima {precip_max} mm/h).")
    else:
        puntos += 3
        razones.append(f"Lluvia muy fuerte (maxima {precip_max} mm/h).")

    if alertas_serias > 0:
        puntos += 1
        razones.append(f"{alertas_serias} lecturas con alerta naranja/roja.")
    if pct_lluvia >= 60:
        razones.append(f"Lluvia presente en {pct_lluvia}% de las lecturas.")

    return {
        "puntos": puntos,
        "razones": razones,
        "metricas": {
            "precipitacion_promedio": precip_prom, "precipitacion_maxima": precip_max,
            "alertas_serias": alertas_serias, "pct_lluvia": pct_lluvia,
        },
    }


def _factor_pasajeros(pasajeros: List[Dict]) -> Dict:
    puntos = 0
    razones = []
    if not pasajeros:
        return {"puntos": 0, "razones": ["Sin datos de pasajeros para evaluar."], "metricas": {}}

    ocup = [e.get("ocupacion_estimada_pct", 0) for e in pasajeros]
    ocup_max = round(max(ocup), 1) if ocup else 0
    ocup_prom = round(sum(ocup) / len(ocup), 1) if ocup else 0
    personas = sum(e.get("total_personas", 0) for e in pasajeros)
    saturadas = sum(1 for o in ocup if o >= 80)

    if ocup_max < 50:
        razones.append(f"Ocupacion controlada (maxima {ocup_max}%).")
    elif ocup_max < 80:
        puntos += 1
        razones.append(f"Ocupacion alta en algun momento (maxima {ocup_max}%).")
    else:
        puntos += 2
        razones.append(f"Ocupacion muy alta / saturacion (maxima {ocup_max}%).")

    if saturadas > 0:
        puntos += 1
        razones.append(f"{saturadas} eventos con ocupacion >= 80%.")

    return {
        "puntos": puntos,
        "razones": razones,
        "metricas": {
            "ocupacion_promedio": ocup_prom, "ocupacion_maxima": ocup_max,
            "total_personas": personas, "eventos_saturados": saturadas,
        },
    }


def evaluar_riesgo(eventos: List[Dict]) -> Dict:
    """Calcula el nivel de riesgo del dia a partir de sus eventos."""
    pasajeros = [e for e in eventos if e.get("_tipo_fuente") == "pasajeros"]
    vibracion = [e for e in eventos if e.get("_tipo_fuente") == "vibracion"]
    clima = [e for e in eventos if e.get("_tipo_fuente") == "clima"]

    f_vib = _factor_vibracion(vibracion)
    f_cli = _factor_clima(clima)
    f_pax = _factor_pasajeros(pasajeros)
    total = f_vib["puntos"] + f_cli["puntos"] + f_pax["puntos"]

    if total >= UMBRAL_ALTO:
        nivel = "ALTO"
    elif total >= UMBRAL_MEDIO:
        nivel = "MEDIO"
    else:
        nivel = "BAJO"

    if not eventos:
        nivel = "SIN DATOS"

    return {
        "nivel": nivel,
        "puntaje": total,
        "puntaje_maximo": 12,
        "umbrales": {"medio": UMBRAL_MEDIO, "alto": UMBRAL_ALTO},
        "factores": {
            "infraestructura": f_vib,
            "clima": f_cli,
            "demanda": f_pax,
        },
    }
