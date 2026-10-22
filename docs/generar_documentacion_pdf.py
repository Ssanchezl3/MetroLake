"""Genera un PDF de documentacion de MetroLake, facil de entender.

Explica el codigo, los servicios/microservicios usados, la arquitectura y el
despliegue. Usa reportlab (Platypus) para un layout limpio con portada, indice
visual, tablas y el diagrama de arquitectura incrustado.

Uso:
    python docs/generar_documentacion_pdf.py   # escribe docs/MetroLake_Documentacion.pdf
"""

import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image, ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "MetroLake_Documentacion.pdf")
DIAGRAMA = os.path.join(AQUI, "img", "arquitectura.png")

# Paleta Metro de Medellin
VERDE = colors.HexColor("#00953b")
VERDE_OSC = colors.HexColor("#007a30")
NARANJA = colors.HexColor("#f29100")
GRIS = colors.HexColor("#5a6b76")
AZUL = colors.HexColor("#0072bc")
FONDO_SUAVE = colors.HexColor("#e4f3ea")

# ---------------------------------------------------------------- estilos
base = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=base["Heading1"], textColor=VERDE_OSC,
                    fontSize=18, spaceBefore=6, spaceAfter=10)
H2 = ParagraphStyle("H2", parent=base["Heading2"], textColor=VERDE,
                    fontSize=13.5, spaceBefore=12, spaceAfter=6)
H3 = ParagraphStyle("H3", parent=base["Heading3"], textColor=colors.HexColor("#1f2b33"),
                    fontSize=11.5, spaceBefore=8, spaceAfter=4)
BODY = ParagraphStyle("Body", parent=base["BodyText"], fontSize=10.3, leading=15,
                      alignment=TA_JUSTIFY, spaceAfter=6)
SMALL = ParagraphStyle("Small", parent=base["BodyText"], fontSize=8.8, leading=12,
                       textColor=GRIS)
CODE = ParagraphStyle("Code", parent=base["Code"], fontSize=8.8, leading=12,
                      backColor=colors.HexColor("#f0f3f5"), textColor=colors.HexColor("#1f2b33"),
                      borderPadding=6, spaceBefore=4, spaceAfter=8)
LI = ParagraphStyle("LI", parent=BODY, spaceAfter=3)


def p(texto, estilo=BODY):
    return Paragraph(texto, estilo)


def bullets(items, estilo=LI):
    return ListFlowable(
        [ListItem(p(t, estilo), leftIndent=6, value="•") for t in items],
        bulletType="bullet", start="•", leftIndent=12,
    )


def tabla(datos, anchos, encabezado_color=VERDE):
    t = Table(datos, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), encabezado_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe5ea")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


historia = []
S = historia.append


# ============================================================ PORTADA
S(Spacer(1, 3 * cm))
S(p("MetroLake", ParagraphStyle("T", parent=H1, fontSize=40, alignment=TA_CENTER,
                                textColor=VERDE_OSC, spaceAfter=6)))
S(p("Simulador y plataforma de datos del Metro de Medellín",
    ParagraphStyle("Sub", parent=BODY, fontSize=14, alignment=TA_CENTER,
                   textColor=GRIS, spaceAfter=4)))
S(p("Mantenimiento predictivo · Clima · Afluencia",
    ParagraphStyle("Sub2", parent=BODY, fontSize=11, alignment=TA_CENTER, textColor=NARANJA)))
S(Spacer(1, 1.2 * cm))
S(p("Documentación técnica", ParagraphStyle("DT", parent=BODY, fontSize=13,
                                            alignment=TA_CENTER, textColor=colors.HexColor("#1f2b33"))))
S(p("Código · Servicios y microservicios · Arquitectura · Despliegue",
    ParagraphStyle("DT2", parent=SMALL, alignment=TA_CENTER)))
S(Spacer(1, 2 * cm))
S(tabla([
    ["Repositorio", "github.com/Ssanchezl3/MetroLake"],
    ["Rama", "feature/frontend-simulador"],
    ["App desplegada", "Cloud Run (us-central1)"],
    ["Proyecto GCP", "terraform-demo-metro"],
    ["Lenguaje", "Python 3 (Flask) + HTML/CSS/JS"],
], [4 * cm, 10 * cm], encabezado_color=VERDE))
S(PageBreak())


# ============================================================ 1. RESUMEN
S(p("1. ¿Qué es MetroLake?", H1))
S(p(
    "MetroLake es una plataforma que <b>simula y analiza</b> los datos operativos del "
    "Metro de Medellín. Genera tres tipos de información —<b>pasajeros</b> (torniquetes), "
    "<b>vibración</b> (acelerómetros de la vía) y <b>clima</b> (pluviómetros)— y los publica "
    "en la nube de Google (GCP) para almacenarlos, consultarlos y evaluar el riesgo operativo.",
))
S(p("El proyecto tiene dos grandes bloques:", BODY))
S(bullets([
    "<b>Pipeline de datos:</b> los simuladores producen eventos y un publicador los envía a "
    "Google Cloud Pub/Sub; de ahí se cargan automáticamente a BigQuery.",
    "<b>Frontend web (interfaz):</b> una aplicación Flask desplegada en Cloud Run que permite "
    "generar datos, verlos en vivo, consultarlos por día, comparar días y evaluar el riesgo diario.",
]))
S(p("2. Objetivos funcionales", H2))
S(bullets([
    "<b>Simular</b> la operación del metro con datos realistas (incluye la lógica de días de "
    "semana vs. fin de semana y horas pico).",
    "<b>Trazabilidad:</b> consultar los datos almacenados por día y filtrarlos por fuente y origen.",
    "<b>Comparación:</b> contrastar dos días (A vs. B) lado a lado.",
    "<b>Riesgo diario:</b> calcular un nivel BAJO / MEDIO / ALTO con criterios explicados.",
]))


# ============================================================ 2. ARQUITECTURA
S(PageBreak())
S(p("3. Arquitectura general", H1))
S(p(
    "La arquitectura sigue un patrón de <b>capas</b> sobre GCP. Los simuladores alimentan una "
    "capa de velocidad (mensajería) que descarga en un almacén analítico (BigQuery), sobre el "
    "cual operan el modelo predictivo y el frontend.", BODY))
if os.path.isfile(DIAGRAMA):
    # Escala la imagen para que quepa en el ancho util de la pagina.
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(DIAGRAMA).getSize()
    ancho_util = 15.5 * cm
    alto = ancho_util * ih / iw
    max_alto = 20 * cm
    if alto > max_alto:
        alto = max_alto
        ancho_util = alto * iw / ih
    S(Spacer(1, 0.2 * cm))
    S(Image(DIAGRAMA, width=ancho_util, height=alto))
    S(p("Figura 1. Arquitectura de datos de MetroLake en GCP.",
        ParagraphStyle("cap", parent=SMALL, alignment=TA_CENTER)))
S(PageBreak())
S(p("3.1 Flujo de datos, paso a paso", H2))
S(bullets([
    "<b>1. Fuentes:</b> tres simuladores en Python generan eventos (vibración, pasajeros, clima). "
    "El clima intenta datos reales de la API pública Open-Meteo y, si no hay red, usa un fallback.",
    "<b>2. Publicación:</b> <font face='Courier'>publicador_gcp.py</font> envía cada evento al tema "
    "de Pub/Sub correspondiente, con una mezcla aproximada de 50% vibración, 35% pasajeros, 15% clima.",
    "<b>3. Mensajería (capa de velocidad):</b> tres temas de Pub/Sub reciben los eventos: "
    "<font face='Courier'>tema-metro-vibracion / -pasajeros / -clima</font>.",
    "<b>4. Carga a BigQuery:</b> tres <i>BigQuery subscriptions</i> "
    "(<font face='Courier'>sub-metro-*-bq</font>) escriben los mensajes en las tablas.",
    "<b>5. Almacén (capa de servicio):</b> BigQuery (dataset <font face='Courier'>project_data</font>) "
    "guarda las tablas en vivo y las tablas batch, y alimenta BigQuery ML.",
    "<b>6. Consumo:</b> el frontend (Cloud Run) lee/escribe BigQuery; además hay alertas y un "
    "dashboard (Looker Studio) para visualización.",
]))


# ============================================================ 3. SERVICIOS GCP
S(PageBreak())
S(p("4. Servicios y microservicios usados", H1))
S(p("4.1 Servicios de Google Cloud (GCP)", H2))
S(tabla([
    ["Servicio", "Rol en MetroLake"],
    ["Cloud Run", "Ejecuta el frontend web (contenedor serverless, escala a cero, HTTPS)."],
    ["Pub/Sub", "Mensajería: 3 temas que reciben los eventos de los simuladores."],
    ["BigQuery", "Almacén analítico (dataset project_data) con 6 tablas; agrupa por fecha."],
    ["BigQuery subscriptions", "Cargan automáticamente los mensajes de Pub/Sub a BigQuery."],
    ["BigQuery ML", "Modelo predictivo (mantenimiento) sobre las tablas."],
    ["Cloud Build", "Construye el contenedor del frontend al desplegar desde el código."],
    ["Artifact Registry", "Almacena la imagen del contenedor construida por Cloud Build."],
    ["Cloud Storage", "Data Lake de históricos del procesamiento batch (opcional)."],
    ["Looker Studio", "Dashboard de visualización (consumo)."],
], [4.2 * cm, 11.3 * cm], encabezado_color=AZUL))

S(p("4.2 ¿Es monolito o microservicios?", H2))
S(p(
    "MetroLake es una arquitectura <b>orientada a servicios desacoplados</b>, no un único "
    "programa monolítico. Cada pieza tiene una responsabilidad clara y se comunica por "
    "contratos simples (mensajes JSON en Pub/Sub, tablas en BigQuery, HTTP en el frontend):", BODY))
S(bullets([
    "<b>Simuladores</b> (librería Python): generan datos. No saben nada de la nube.",
    "<b>Publicador</b> (servicio de ingesta): traduce eventos a mensajes de Pub/Sub.",
    "<b>Pub/Sub + subscriptions</b>: transporte y carga, totalmente gestionados por GCP.",
    "<b>Frontend</b> (microservicio web en Cloud Run): interfaz y consultas, independiente del resto.",
]))
S(p(
    "Este desacople permite cambiar o escalar una pieza sin tocar las demás (por ejemplo, el "
    "frontend se redespliega sin afectar el pipeline de Pub/Sub).", BODY))


# ============================================================ 4. CODIGO
S(PageBreak())
S(p("5. Explicación del código", H1))
S(p("El proyecto se organiza por carpetas según su responsabilidad:", BODY))
S(tabla([
    ["Carpeta / archivo", "Qué hace"],
    ["Fuentes/", "Los simuladores: accelerometer.py (vibración), turnstiles.py (pasajeros), "
                 "weather.py (clima + Open-Meteo), config.py (estaciones, tramos, sensores)."],
    ["Ejecucion/", "Orquestación: dataset.py (lotes históricos), streaming.py (eventos en vivo), "
                   "simuladores.py (punto de entrada)."],
    ["Persistencia/", "serializers.py: exporta a JSON, CSV y NDJSON."],
    ["Integraciones/", "publicador_gcp.py: publica los eventos a Google Cloud Pub/Sub."],
    ["Frontend/", "La aplicación web (ver detalle abajo)."],
    ["docs/", "Diagrama de arquitectura y esta documentación."],
], [4.6 * cm, 10.9 * cm]))

S(p("5.1 Los simuladores (Fuentes/)", H2))
S(bullets([
    "<b>SimuladorTorniquetes</b> (pasajeros): calcula entradas/salidas por estación según la hora "
    "y el día; reduce la demanda en fin de semana y marca las horas pico.",
    "<b>SimuladorAcelerometro</b> (vibración): genera telemetría RMS por sensor, en función de la "
    "fatiga del tramo, la hora, los pasajeros y la lluvia; detecta anomalías.",
    "<b>SimuladorClima</b>: consulta precipitación real en Open-Meteo; si falla, genera datos "
    "sintéticos coherentes. Calcula el nivel de alerta (verde/amarilla/naranja/roja).",
]))

S(p("5.2 El frontend (Frontend/)", H2))
S(tabla([
    ["Archivo", "Responsabilidad"],
    ["app.py", "Servidor Flask y API: genera lotes, emite streaming, guarda, consulta, compara "
               "y evalúa riesgo. Lee el puerto de la variable PORT (compatible con Cloud Run)."],
    ["consultas.py", "Trazabilidad por día: lista días, carga un día, resume y guarda. Usa BigQuery "
                     "si está configurado; si no, archivos locales."],
    ["bigquery_store.py", "Acceso a BigQuery (dataset project_data): lee/escribe las 6 tablas, "
                          "agrupa por DATE(timestamp) y normaliza valores."],
    ["riesgo.py", "Calcula el nivel de riesgo diario (BAJO/MEDIO/ALTO) con criterios de "
                  "infraestructura, clima y demanda, y explica el porqué."],
    ["templates/index.html", "Interfaz de una sola página con el menú lateral y las vistas."],
    ["static/css, static/js", "Estilos (tema Metro de Medellín) y lógica de la interfaz."],
], [4.3 * cm, 11.2 * cm]))

S(p("5.3 La API del frontend (endpoints principales)", H2))
S(tabla([
    ["Método y ruta", "Para qué sirve"],
    ["GET /", "Carga la interfaz web."],
    ["GET /api/estado", "Configuración: estaciones, tramos, sensores, pluviómetros."],
    ["GET /api/batch", "Genera un lote batch de un día de la semana."],
    ["GET /api/streaming/evento", "Emite un evento de streaming (fuente aleatoria con pesos)."],
    ["POST /api/guardar/batch", "Genera y guarda un lote (en BigQuery o archivo)."],
    ["GET /api/consultas/dias", "Lista los días con datos almacenados."],
    ["GET /api/consultas/dia", "Tabla y resumen de un día (filtra por origen y fuente)."],
    ["GET /api/consultas/comparar", "Resúmenes de dos días para comparar (A vs. B)."],
    ["GET /api/riesgo/dia", "Nivel de riesgo del día con sus criterios."],
], [5.2 * cm, 10.3 * cm], encabezado_color=NARANJA))


# ============================================================ 5. BIGQUERY
S(PageBreak())
S(p("6. Datos en BigQuery", H1))
S(p(
    "El dataset <font face='Courier'>project_data</font> tiene seis tablas: una versión "
    "<b>en vivo</b> y una <b>batch</b> por cada fuente. El día se obtiene con "
    "<font face='Courier'>DATE(timestamp)</font>.", BODY))
S(tabla([
    ["Tabla", "Fuente", "Campos principales"],
    ["pasajeros / pasajeros_batch", "Torniquetes",
     "event_id, estacion, timestamp, entradas, salidas, total_personas, "
     "ocupacion_estimada_pct, hora_pico"],
    ["vibracion / vibracion_batch", "Acelerómetros",
     "event_id, sensor_id, tramo_id, timestamp, vibracion_rms_mm_s2, "
     "fatiga_acumulada, es_anomalia"],
    ["clima / clima_batch", "Pluviómetros",
     "lectura_id, pluviometro_id, timestamp, precipitacion_mm_h, "
     "nivel_alerta, esta_lloviendo"],
], [4.4 * cm, 2.6 * cm, 8.5 * cm], encabezado_color=VERDE))
S(p(
    "El frontend <b>lee</b> estas tablas para Consultas, Comparar días y Riesgo Diario, y "
    "puede <b>escribir</b> en las tablas <font face='Courier'>*_batch</font> los datos que se "
    "generan desde la interfaz.", BODY))


# ============================================================ 6. RIESGO
S(p("7. Cómo se calcula el Riesgo Diario", H2))
S(p(
    "El riesgo es la suma de puntos de tres factores; el total se traduce a un nivel "
    "(BAJO &lt; 4, MEDIO 4–7, ALTO ≥ 8):", BODY))
S(bullets([
    "<b>Infraestructura (vibración):</b> porcentaje de anomalías, RMS máximo y fatiga de los sensores.",
    "<b>Clima:</b> precipitación máxima y número de alertas naranja/roja.",
    "<b>Demanda (pasajeros):</b> ocupación estimada y eventos de saturación.",
]))
S(p("Cada factor explica <b>por qué</b> suma puntos, con los datos concretos del día.", BODY))


# ============================================================ 7. EJECUCION Y DESPLIEGUE
S(PageBreak())
S(p("8. Cómo ejecutarlo y desplegarlo", H1))
S(p("8.1 En local", H2))
S(p("Desde la raíz del proyecto:", BODY))
S(p("python -m pip install -r requirements.txt<br/>python Frontend/app.py<br/>"
    "# abre http://localhost:8080", CODE))
S(p("8.2 En la nube (Cloud Run)", H2))
S(p("Despliegue del frontend desde el código fuente (crea el contenedor automáticamente):", BODY))
S(p("gcloud run deploy metrolake-frontend --source . --region us-central1 \\<br/>"
    "&nbsp;&nbsp;--allow-unauthenticated --port 8080 \\<br/>"
    "&nbsp;&nbsp;--set-env-vars BQ_DATASET=project_data \\<br/>"
    "&nbsp;&nbsp;--set-env-vars GCP_PROJECT_ID=terraform-demo-metro", CODE))
S(p("Con la variable <font face='Courier'>BQ_DATASET</font> definida, el frontend usa BigQuery "
    "(datos permanentes). Sin ella, usa archivos locales. La guía completa está en "
    "<font face='Courier'>DESPLIEGUE_GCP.md</font>.", BODY))


# ============================================================ 8. GLOSARIO
S(p("9. Glosario rápido", H2))
S(tabla([
    ["Término", "En palabras simples"],
    ["Pub/Sub", "Servicio de mensajería: alguien publica mensajes y otros los reciben."],
    ["Subscription", "Suscripción que entrega los mensajes de un tema a un destino (aquí, BigQuery)."],
    ["BigQuery", "Base de datos analítica de Google para grandes volúmenes y consultas SQL."],
    ["Cloud Run", "Ejecuta tu app en un contenedor sin administrar servidores; escala a cero."],
    ["Contenedor", "Caja con la app y todo lo que necesita para correr igual en cualquier lado."],
    ["gunicorn", "Servidor que ejecuta la app Flask en producción (más robusto que el de desarrollo)."],
    ["Serverless", "No administras servidores; la nube los enciende/apaga por ti."],
    ["Efímero", "Temporal: el disco de Cloud Run se borra al reiniciar (por eso se usa BigQuery)."],
], [3.6 * cm, 11.9 * cm], encabezado_color=GRIS))
S(Spacer(1, 0.6 * cm))
S(p("Documento generado automáticamente para el proyecto MetroLake · Metro de Medellín.", SMALL))


# ---------------------------------------------------------------- build
def _pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(2 * cm, 1.1 * cm, "MetroLake · Documentación técnica")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, "Página %d" % doc.page)
    canvas.setStrokeColor(colors.HexColor("#dfe5ea"))
    canvas.line(2 * cm, 1.4 * cm, A4[0] - 2 * cm, 1.4 * cm)
    canvas.restoreState()


doc = SimpleDocTemplate(
    SALIDA, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
    title="MetroLake - Documentacion tecnica", author="Samuel Aristizabal",
)
doc.build(historia, onFirstPage=_pie, onLaterPages=_pie)
print("PDF generado en:", SALIDA)
