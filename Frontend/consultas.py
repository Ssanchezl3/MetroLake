"""Consultas y trazabilidad de datos almacenados (HU H05).

Lee los datos que genera el proyecto en dos ubicaciones:

- ``datos_sinteticos/YYYY-MM-DD/``  -> datasets historicos (batch).
- ``datos_streaming/streaming_YYYYMMDD_HHMMSS.json`` -> sesiones de streaming.

Y las sesiones que guarda la propia interfaz:

- ``datos_frontend/YYYY-MM-DD/*.json``

Reutiliza ``Persistencia.serializers.exportar_json`` para guardar, de modo
que no se duplica la logica de exportacion del proyecto.
"""

import glob
import json
import os
import re
from collections import Counter
from datetime import datetime
from typing import Dict, List

from Persistencia.serializers import exportar_json

# Rutas estandar del proyecto, relativas a la raiz.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SINTETICOS = os.path.join(_RAIZ, "datos_sinteticos")
DIR_STREAMING = os.path.join(_RAIZ, "datos_streaming")
DIR_FRONTEND = os.path.join(_RAIZ, "datos_frontend")

# Mapeo de nombre de archivo historico -> tipo de fuente.
_ARCHIVOS_SINTETICOS = {
    "pasajeros": ["torniquetes_pasajeros.json", "torniquetes_pasajeros.ndjson"],
    "vibracion": ["acelerometros_vibracion.json", "acelerometros_vibracion.ndjson"],
    "clima": ["clima_precipitacion.json"],
}

_RE_FECHA_DIA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_RE_FECHA_STREAM = re.compile(r"streaming_(\d{8})_\d{6}")


def _leer_json_o_ndjson(ruta: str) -> List[Dict]:
    """Carga una lista de eventos desde un archivo .json o .ndjson."""
    if not os.path.isfile(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as archivo:
        if ruta.endswith(".ndjson"):
            return [json.loads(linea) for linea in archivo if linea.strip()]
        contenido = json.load(archivo)
        return contenido if isinstance(contenido, list) else [contenido]


def _clasificar_evento(evento: Dict) -> str:
    """Determina la fuente de un evento por sus campos o por ``_tipo_fuente``."""
    if "_tipo_fuente" in evento:
        return evento["_tipo_fuente"]
    if "vibracion_rms_mm_s2" in evento:
        return "vibracion"
    if "entradas" in evento:
        return "pasajeros"
    if "precipitacion_mm_h" in evento:
        return "clima"
    return "desconocido"


def _dias_sinteticos() -> List[str]:
    if not os.path.isdir(DIR_SINTETICOS):
        return []
    return [d for d in os.listdir(DIR_SINTETICOS)
            if _RE_FECHA_DIA.match(d) and os.path.isdir(os.path.join(DIR_SINTETICOS, d))]


def _dias_streaming() -> List[str]:
    dias = set()
    for ruta in glob.glob(os.path.join(DIR_STREAMING, "streaming_*.json")):
        m = _RE_FECHA_STREAM.search(os.path.basename(ruta))
        if m:
            dias.add(datetime.strptime(m.group(1), "%Y%m%d").strftime("%Y-%m-%d"))
    return list(dias)


def _dias_frontend() -> List[str]:
    if not os.path.isdir(DIR_FRONTEND):
        return []
    return [d for d in os.listdir(DIR_FRONTEND)
            if _RE_FECHA_DIA.match(d) and os.path.isdir(os.path.join(DIR_FRONTEND, d))]


def listar_dias() -> List[str]:
    """Devuelve todos los dias disponibles (de cualquier fuente), ordenados."""
    dias = set(_dias_sinteticos()) | set(_dias_streaming()) | set(_dias_frontend())
    return sorted(dias, reverse=True)


def _cargar_sinteticos_dia(dia: str) -> List[Dict]:
    carpeta = os.path.join(DIR_SINTETICOS, dia)
    eventos: List[Dict] = []
    if not os.path.isdir(carpeta):
        return eventos
    for tipo, nombres in _ARCHIVOS_SINTETICOS.items():
        for nombre in nombres:
            ruta = os.path.join(carpeta, nombre)
            if os.path.isfile(ruta):
                for ev in _leer_json_o_ndjson(ruta):
                    ev.setdefault("_tipo_fuente", tipo)
                    ev["_origen"] = "sintetico"
                    eventos.append(ev)
                break  # un formato por tipo es suficiente
    return eventos


def _cargar_streaming_dia(dia: str) -> List[Dict]:
    compacto = dia.replace("-", "")
    eventos: List[Dict] = []
    for ruta in glob.glob(os.path.join(DIR_STREAMING, f"streaming_{compacto}_*.json")):
        for ev in _leer_json_o_ndjson(ruta):
            ev["_tipo_fuente"] = _clasificar_evento(ev)
            ev["_origen"] = "streaming"
            eventos.append(ev)
    return eventos


def _cargar_frontend_dia(dia: str) -> List[Dict]:
    carpeta = os.path.join(DIR_FRONTEND, dia)
    eventos: List[Dict] = []
    if not os.path.isdir(carpeta):
        return eventos
    for ruta in glob.glob(os.path.join(carpeta, "*.json")):
        origen = "frontend_streaming" if "streaming" in os.path.basename(ruta) else "frontend_batch"
        for ev in _leer_json_o_ndjson(ruta):
            ev["_tipo_fuente"] = _clasificar_evento(ev)
            ev["_origen"] = origen
            eventos.append(ev)
    return eventos


def cargar_dia(dia: str, origen: str = "todos") -> List[Dict]:
    """Carga todos los eventos de un dia, opcionalmente filtrando por origen.

    ``origen`` puede ser:

    - ``todos``      -> todas las fuentes.
    - ``batch``      -> datasets batch, vengan del proyecto (``datos_sinteticos``)
                        o guardados desde la interfaz (``datos_frontend/*batch*``).
    - ``streaming``  -> eventos de streaming, del proyecto (``datos_streaming``)
                        o guardados desde la interfaz (``datos_frontend/*streaming*``).

    Se mantienen tambien los alias historicos ``sintetico`` y ``frontend``.
    """
    eventos: List[Dict] = []
    sinteticos = _cargar_sinteticos_dia(dia)
    streaming = _cargar_streaming_dia(dia)
    frontend = _cargar_frontend_dia(dia)

    fe_batch = [e for e in frontend if e.get("_origen") == "frontend_batch"]
    fe_streaming = [e for e in frontend if e.get("_origen") == "frontend_streaming"]

    if origen in ("todos", "batch", "sintetico"):
        eventos += sinteticos + fe_batch
    if origen in ("todos", "streaming"):
        eventos += streaming + fe_streaming
    if origen == "frontend":
        eventos += frontend
    return eventos


def resumir_dia(eventos: List[Dict]) -> Dict:
    """Resumen agregado y comparable de los eventos de un dia."""
    por_tipo = Counter(e.get("_tipo_fuente", "desconocido") for e in eventos)
    por_origen = Counter(e.get("_origen", "desconocido") for e in eventos)

    pasajeros = [e for e in eventos if e.get("_tipo_fuente") == "pasajeros"]
    vibracion = [e for e in eventos if e.get("_tipo_fuente") == "vibracion"]
    clima = [e for e in eventos if e.get("_tipo_fuente") == "clima"]

    resumen = {
        "total_eventos": len(eventos),
        "por_tipo": dict(por_tipo),
        "por_origen": dict(por_origen),
    }
    if pasajeros:
        entradas = sum(e.get("entradas", 0) for e in pasajeros)
        salidas = sum(e.get("salidas", 0) for e in pasajeros)
        resumen["pasajeros"] = {
            "eventos": len(pasajeros),
            "entradas": entradas,
            "salidas": salidas,
            "total_personas": entradas + salidas,
        }
    if vibracion:
        rms = [e.get("vibracion_rms_mm_s2", 0) for e in vibracion]
        resumen["vibracion"] = {
            "eventos": len(vibracion),
            "rms_promedio": round(sum(rms) / len(rms), 4) if rms else 0,
            "rms_maximo": round(max(rms), 4) if rms else 0,
            "anomalias": sum(1 for e in vibracion if e.get("es_anomalia")),
        }
    if clima:
        precip = [e.get("precipitacion_mm_h", 0) for e in clima]
        resumen["clima"] = {
            "eventos": len(clima),
            "precipitacion_promedio_mm_h": round(sum(precip) / len(precip), 2) if precip else 0,
            "precipitacion_maxima_mm_h": round(max(precip), 2) if precip else 0,
            "lecturas_con_lluvia": sum(1 for e in clima if e.get("esta_lloviendo")),
        }
    return resumen


def guardar_sesion(eventos: List[Dict], modo: str, fecha=None) -> str:
    """Guarda una sesion (batch o streaming) en ``datos_frontend/YYYY-MM-DD/``.

    ``fecha`` permite almacenar bajo un dia simulado concreto (p. ej. el ultimo
    lunes). Si no se indica, se usa la fecha actual. La marca horaria evita
    sobrescribir sesiones del mismo dia. Devuelve la ruta relativa creada.
    """
    fecha = fecha or datetime.now()
    dia = fecha.strftime("%Y-%m-%d")
    marca = datetime.now().strftime("%H%M%S")
    nombre = f"{modo}_{marca}.json"
    ruta = os.path.join(DIR_FRONTEND, dia, nombre)
    exportar_json(eventos, ruta)
    return os.path.relpath(ruta, _RAIZ)
