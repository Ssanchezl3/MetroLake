# -*- coding: utf-8 -*-
"""Genera la 'Guia del Sistema de Riesgo Diario' de MetroLake.

Documento tecnico, directo y al grano: explica como se calcula el Riesgo Diario
y el sistema de puntos. El contenido es exacto al codigo (Frontend/riesgo.py).

Uso:
    python docs/generar_manual_riesgo.py   # -> docs/MetroLake_Manual_Riesgo.pdf
"""

import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "MetroLake_Manual_Riesgo.pdf")

# Paleta Metro de Medellin
VERDE = colors.HexColor("#00953b")
VERDE_OSC = colors.HexColor("#007a30")
NARANJA = colors.HexColor("#f29100")
ROJO = colors.HexColor("#c0392b")
TEXTO = colors.HexColor("#1f2b33")
GRIS = colors.HexColor("#5a6b76")
SUAVE = colors.HexColor("#f0f3f5")

base = getSampleStyleSheet()
TITULO = ParagraphStyle("Titulo", parent=base["Title"], textColor=VERDE_OSC,
                        fontName="Helvetica-Bold", fontSize=24, leading=30, alignment=TA_CENTER)
SUB = ParagraphStyle("Sub", parent=base["Normal"], textColor=GRIS,
                     fontSize=12, leading=18, alignment=TA_CENTER)
H1 = ParagraphStyle("H1", parent=base["Heading1"], textColor=VERDE_OSC,
                    fontName="Helvetica-Bold", fontSize=16, spaceBefore=6, spaceAfter=10)
H2 = ParagraphStyle("H2", parent=base["Heading2"], textColor=VERDE,
                    fontName="Helvetica-Bold", fontSize=12.5, spaceBefore=10, spaceAfter=6)
BODY = ParagraphStyle("Body", parent=base["BodyText"], textColor=TEXTO,
                      fontSize=10.5, leading=15, alignment=TA_JUSTIFY, spaceAfter=7)
NOTA = ParagraphStyle("Nota", parent=BODY, textColor=GRIS, fontSize=9, leading=13)
LI = ParagraphStyle("LI", parent=BODY, spaceAfter=4)
FIRMA = ParagraphStyle("Firma", parent=BODY, textColor=GRIS, fontSize=9, alignment=TA_LEFT)


def p(t, s=BODY):
    return Paragraph(t, s)


def bullets(items):
    return ListFlowable(
        [ListItem(p(t, LI), value="\u2022") for t in items],
        bulletType="bullet", bulletColor=VERDE, leftIndent=14,
    )


def tabla_puntos(titulo, filas, color=VERDE):
    data = [[titulo, "PUNTOS"]] + filas
    t = Table(data, colWidths=[12.2 * cm, 2.8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXTO),
        ("TEXTCOLOR", (1, 1), (1, -1), VERDE_OSC),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SUAVE]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe5ea")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


H = []
S = H.append

# ===================================================== PORTADA
S(Spacer(1, 2.5 * cm))
S(p("MetroLake", ParagraphStyle("mk", parent=SUB, textColor=VERDE, fontSize=13,
                                fontName="Helvetica-Bold", spaceAfter=2)))
S(p("Metro de Medellín · Monitoreo operacional", ParagraphStyle(
    "mk2", parent=SUB, fontSize=10, spaceAfter=30)))
S(p("Guía del Sistema de<br/>Riesgo Diario", TITULO))
S(Spacer(1, 0.4 * cm))
S(p("Cómo se calcula el nivel de riesgo y el sistema de puntos", SUB))
S(Spacer(1, 1.5 * cm))
S(Table([[p(
    "Este documento explica cómo MetroLake evalúa el <b>riesgo operativo de cada día</b> "
    "a partir de los datos de las tres fuentes del sistema (vibración, clima y pasajeros). "
    "El resultado es un <b>nivel BAJO, MEDIO o ALTO</b> acompañado de un puntaje y de las "
    "razones que lo justifican.<br/><br/>"
    "El sistema de puntos aquí descrito corresponde exactamente a la implementación del "
    "proyecto (módulo <font face='Courier'>Frontend/riesgo.py</font>).", BODY)]],
    colWidths=[15 * cm],
    style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), SUAVE),
                      ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe5ea")),
                      ("TOPPADDING", (0, 0), (-1, -1), 12),
                      ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                      ("LEFTPADDING", (0, 0), (-1, -1), 12),
                      ("RIGHTPADDING", (0, 0), (-1, -1), 12)])))
S(PageBreak())

# ===================================================== 1. QUE ES
S(p("1. Qué es el Riesgo Diario", H1))
S(p(
    "Cada día, el sistema analiza los datos almacenados de esa jornada y calcula un "
    "<b>puntaje de riesgo entre 0 y 12</b>. Ese puntaje es la suma de los puntos de "
    "<b>tres factores</b>. A mayor puntaje, mayor probabilidad de un incidente operativo.", BODY))
S(p("No es un modelo de aprendizaje automático: es un <b>sistema de reglas</b> "
    "transparente, en el que cada criterio suma una cantidad fija de puntos. Esto permite "
    "explicar siempre por qué un día obtuvo determinado nivel.", BODY))

S(p("1.1 Los tres factores", H2))
S(bullets([
    "<b>Infraestructura (vibración):</b> telemetría de los acelerómetros de la vía "
    "(anomalías, vibración RMS y fatiga de los tramos).",
    "<b>Clima (lluvia):</b> lecturas de los pluviómetros (precipitación y niveles de alerta).",
    "<b>Demanda (pasajeros):</b> afluencia en las estaciones (ocupación estimada y saturación).",
]))

# ===================================================== 2. ESCALA
S(p("2. La escala de niveles", H1))
S(p("El puntaje total se traduce a un nivel según estos rangos:", BODY))
S(Table([
    [p("<b>0 – 3</b>", ParagraphStyle("n", parent=BODY, textColor=colors.white, alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=13)),
     p("<b>BAJO</b>  ·  operación normal, sin acciones especiales.", ParagraphStyle("d1", parent=BODY, textColor=colors.white))],
    [p("<b>4 – 7</b>", ParagraphStyle("n", parent=BODY, textColor=colors.white, alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=13)),
     p("<b>MEDIO</b>  ·  vigilancia reforzada; revisar el factor dominante.", ParagraphStyle("d2", parent=BODY, textColor=colors.white))],
    [p("<b>8 – 12</b>", ParagraphStyle("n", parent=BODY, textColor=colors.white, alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=13)),
     p("<b>ALTO</b>  ·  activar mantenimiento preventivo y notificar al supervisor.", ParagraphStyle("d3", parent=BODY, textColor=colors.white))],
], colWidths=[3 * cm, 12 * cm], rowHeights=[1.3 * cm, 1.3 * cm, 1.3 * cm],
    style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("BACKGROUND", (0, 1), (-1, 1), NARANJA),
        ("BACKGROUND", (0, 2), (-1, 2), ROJO),
        ("GRID", (0, 0), (-1, -1), 1, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ])))
S(Spacer(1, 0.2 * cm))
S(p("El máximo teórico es 12 puntos. El sistema calcula el total automáticamente.", NOTA))
S(PageBreak())

# ===================================================== 3. PUNTOS
S(p("3. Sistema de puntos por factor", H1))

S(p("3.1 Infraestructura (vibración) — hasta 5 puntos", H2))
S(p("Se evalúan tres aspectos de la telemetría de vibración:", BODY))
S(tabla_puntos("Criterio de vibración", [
    ["Anomalías: menos del 2% de las lecturas", "+1"],
    ["Anomalías: entre 2% y 5%", "+2"],
    ["Anomalías: 5% o más", "+3"],
    ["Vibración RMS máxima ≥ 4.5 mm/s²", "+1"],
    ["Fatiga acumulada ≥ 0.8", "+1"],
]))
S(p("El criterio de anomalías es excluyente (aplica un solo rango). Los de RMS y fatiga "
    "se suman de forma independiente.", NOTA))

S(p("3.2 Clima (lluvia) — hasta 4 puntos", H2))
S(p("Se evalúa la precipitación de los pluviómetros y las alertas:", BODY))
S(tabla_puntos("Criterio de clima", [
    ["Lluvia moderada: 10 a 30 mm/h", "+1"],
    ["Lluvia fuerte: 30 a 60 mm/h", "+2"],
    ["Lluvia muy fuerte: 60 mm/h o más", "+3"],
    ["Hay lecturas con alerta naranja o roja", "+1"],
]))
S(p("El criterio de precipitación es excluyente (aplica un solo rango). La alerta suma aparte.", NOTA))

S(p("3.3 Demanda (pasajeros) — hasta 3 puntos", H2))
S(p("Se evalúa la ocupación estimada a partir de los torniquetes:", BODY))
S(tabla_puntos("Criterio de demanda", [
    ["Ocupación alta: entre 50% y 80%", "+1"],
    ["Ocupación muy alta / saturación: 80% o más", "+2"],
    ["Hubo al menos un evento con ocupación ≥ 80%", "+1"],
]))
S(PageBreak())

# ===================================================== 4. EJEMPLO
S(p("4. Ejemplo de cálculo", H1))
S(p("Supongamos que en un día el sistema registra lo siguiente:", BODY))
S(tabla_puntos("Reporte del día (ejemplo)", [
    ["Clima: lluvia muy fuerte (máxima 71.7 mm/h)", "+3"],
    ["Clima: había alertas naranja/roja", "+1"],
    ["Infraestructura: sin anomalías", "0"],
    ["Demanda: ocupación controlada (12%)", "0"],
], color=NARANJA))
S(Spacer(1, 0.2 * cm))
S(Table([[p("Puntaje total = 4  →  Nivel MEDIO", ParagraphStyle(
    "tot", parent=BODY, textColor=colors.white, fontName="Helvetica-Bold", fontSize=13,
    alignment=TA_CENTER))]], colWidths=[15 * cm], rowHeights=[1.1 * cm],
    style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), NARANJA),
                      ("VALIGN", (0, 0), (-1, -1), "MIDDLE")])))
S(Spacer(1, 0.3 * cm))
S(p(
    "Interpretación: la precipitación fue muy alta (+3) y hubo alertas serias (+1), pero la "
    "vía no presentó anomalías y la ocupación fue baja. El total de 4 puntos cae en el rango "
    "4–7, por lo que el nivel del día es <b>MEDIO</b>.", BODY))

# ===================================================== 5. INTERPRETACION
S(p("5. Cómo interpretar el resultado", H1))
S(bullets([
    "<b>BAJO (0–3):</b> operación normal. No se requieren acciones especiales.",
    "<b>MEDIO (4–7):</b> vigilancia reforzada. Revisar el factor que más aportó al puntaje "
    "(visible en la pantalla de Riesgo Diario).",
    "<b>ALTO (8–12):</b> activar el protocolo de mantenimiento preventivo y notificar al "
    "supervisor; documentar la jornada.",
]))
S(p(
    "La vista de <b>Riesgo Diario</b> en la interfaz muestra, además del nivel y el puntaje, "
    "la razón de cada punto asignado, de modo que la evaluación siempre es trazable.", BODY))

S(Spacer(1, 0.6 * cm))
S(Table([[p(
    "<b>Nota técnica:</b> los umbrales (porcentaje de anomalías, RMS, precipitación, "
    "ocupación y los cortes de nivel) son criterios de configuración definidos en el código y "
    "pueden ajustarse según los estándares operativos del Metro. El sistema de puntos descrito "
    "coincide con el módulo <font face='Courier'>Frontend/riesgo.py</font>.", NOTA)]],
    colWidths=[15 * cm],
    style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), SUAVE),
                      ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe5ea")),
                      ("TOPPADDING", (0, 0), (-1, -1), 10),
                      ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                      ("LEFTPADDING", (0, 0), (-1, -1), 10),
                      ("RIGHTPADDING", (0, 0), (-1, -1), 10)])))


# --------------------------------------------------- pie de pagina
def _pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(2 * cm, 1.1 * cm, "MetroLake · Guía del Sistema de Riesgo Diario")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, "Página %d" % doc.page)
    canvas.setStrokeColor(colors.HexColor("#dfe5ea"))
    canvas.line(2 * cm, 1.4 * cm, A4[0] - 2 * cm, 1.4 * cm)
    canvas.restoreState()


doc = SimpleDocTemplate(
    SALIDA, pagesize=A4,
    leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=1.8 * cm,
    title="MetroLake - Guia del Sistema de Riesgo Diario", author="Samuel Aristizabal",
)
doc.build(H, onFirstPage=_pie, onLaterPages=_pie)
print("PDF generado en:", SALIDA)
