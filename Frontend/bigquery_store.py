"""Acceso a BigQuery para el frontend (dataset ``project_data``).

Lee y escribe las tablas del Metro en BigQuery para que las vistas de
Consultas, Comparar dias y Riesgo Diario funcionen con datos **permanentes**
(a diferencia del disco efimero de Cloud Run).

Tablas por fuente (hay una version "en vivo" y una "_batch" de cada una):

    clima      / clima_batch       -> SimuladorClima
    pasajeros  / pasajeros_batch   -> SimuladorTorniquetes
    vibracion  / vibracion_batch   -> SimuladorAcelerometro

El dia se obtiene con ``DATE(timestamp)``. Cada fila devuelta se anota con
``_tipo_fuente`` (clima|pasajeros|vibracion) y ``_origen`` (vivo|batch) para
que el resto del frontend la trate igual que antes.

Se activa cuando existe la variable de entorno ``BQ_DATASET`` (p. ej.
``project_data``). Si no esta definida, el frontend usa los archivos locales.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

# Mapeo: tipo de fuente -> (tabla en vivo, tabla batch)
TABLAS = {
    "clima": ("clima", "clima_batch"),
    "pasajeros": ("pasajeros", "pasajeros_batch"),
    "vibracion": ("vibracion", "vibracion_batch"),
}

# Columna de marca de tiempo en todas las tablas.
COL_TIMESTAMP = "timestamp"


def bq_configurado() -> bool:
    """True si el frontend debe usar BigQuery (variable BQ_DATASET definida)."""
    return bool(os.getenv("BQ_DATASET"))


def _dataset() -> str:
    return os.environ["BQ_DATASET"]


def _project() -> Optional[str]:
    # Si no se indica, el cliente usa el proyecto por defecto de las credenciales.
    return os.getenv("GCP_PROJECT_ID") or os.getenv("BQ_PROJECT")


def _cliente():
    from google.cloud import bigquery  # import diferido: solo si se usa BQ
    return bigquery.Client(project=_project())


def _fqtn(tabla: str) -> str:
    """Nombre de tabla totalmente cualificado: `project.dataset.tabla`."""
    proyecto = _project()
    prefijo = f"`{proyecto}`." if proyecto else ""
    return f"{prefijo}`{_dataset()}`.`{tabla}`"


def listar_dias() -> List[str]:
    """Devuelve los dias (YYYY-MM-DD) presentes en cualquier tabla, desc."""
    cliente = _cliente()
    selects = []
    for vivo, batch in TABLAS.values():
        for tabla in (vivo, batch):
            selects.append(
                f"SELECT DISTINCT FORMAT_DATE('%Y-%m-%d', DATE({COL_TIMESTAMP})) AS dia "
                f"FROM {_fqtn(tabla)}"
            )
    consulta = " UNION DISTINCT ".join(selects) + " ORDER BY dia DESC"
    try:
        return [fila["dia"] for fila in cliente.query(consulta).result() if fila["dia"]]
    except Exception as error:  # tabla inexistente u otro problema: no romper la UI
        print(f"[BQ] listar_dias error: {error}")
        return []


def _cargar_tabla_dia(cliente, tabla: str, tipo: str, origen: str, dia: str) -> List[Dict]:
    consulta = (
        f"SELECT * FROM {_fqtn(tabla)} "
        f"WHERE DATE({COL_TIMESTAMP}) = @dia"
    )
    from google.cloud import bigquery
    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("dia", "DATE", dia)]
    )
    eventos: List[Dict] = []
    try:
        for fila in cliente.query(consulta, job_config=cfg).result():
            ev = dict(fila)
            # Normaliza timestamp a string ISO para la UI.
            if isinstance(ev.get(COL_TIMESTAMP), datetime):
                ev[COL_TIMESTAMP] = ev[COL_TIMESTAMP].isoformat()
            ev["_tipo_fuente"] = tipo
            ev["_origen"] = origen
            eventos.append(ev)
    except Exception as error:
        print(f"[BQ] cargar {tabla} ({dia}) error: {error}")
    return eventos


def cargar_dia(dia: str, origen: str = "todos") -> List[Dict]:
    """Carga los eventos de un dia desde BigQuery.

    ``origen``: ``todos`` | ``batch`` | ``streaming``. Como las tablas en vivo y
    las ``_batch`` representan lo mismo, por defecto se combinan ambas.
    """
    cliente = _cliente()
    eventos: List[Dict] = []
    for tipo, (vivo, batch) in TABLAS.items():
        # 'vivo' se etiqueta como streaming; '_batch' como batch.
        if origen in ("todos", "streaming"):
            eventos += _cargar_tabla_dia(cliente, vivo, tipo, "streaming", dia)
        if origen in ("todos", "batch"):
            eventos += _cargar_tabla_dia(cliente, batch, tipo, "batch", dia)
    return eventos


def guardar_eventos(eventos: List[Dict], modo: str = "batch") -> int:
    """Inserta eventos en las tablas ``*_batch`` segun su ``_tipo_fuente``.

    Devuelve cuantas filas se insertaron. Escribe en las tablas batch para no
    interferir con la ingesta en vivo de Pub/Sub sobre las tablas principales.
    """
    cliente = _cliente()
    por_tipo: Dict[str, List[Dict]] = {t: [] for t in TABLAS}
    for ev in eventos:
        tipo = ev.get("_tipo_fuente")
        if tipo in por_tipo:
            fila = {k: v for k, v in ev.items() if not k.startswith("_")}
            por_tipo[tipo].append(fila)

    insertadas = 0
    for tipo, filas in por_tipo.items():
        if not filas:
            continue
        tabla_batch = TABLAS[tipo][1]
        tabla_ref = f"{_project() + '.' if _project() else ''}{_dataset()}.{tabla_batch}"
        errores = cliente.insert_rows_json(tabla_ref, filas)
        if errores:
            print(f"[BQ] errores insertando en {tabla_batch}: {errores}")
        else:
            insertadas += len(filas)
    return insertadas
