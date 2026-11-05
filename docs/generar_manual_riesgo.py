# -*- coding: utf-8 -*-
"""Genera un 'Manual del Empleado' estilo Five Nights at Freddy's que explica
el sistema de Riesgo Diario de MetroLake con humor corporativo siniestro.

El tono es de broma (la empresa se lava las manos, el empleado "tiene la culpa"),
pero el SISTEMA DE PUNTOS que explica es el real (Frontend/riesgo.py).

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

# --- Paleta "turno nocturno": oscuro con amarillo/rojo de advertencia ---
NEGRO = colors.HexColor("#141210")
CARBON = colors.HexColor("#201c18")
AMARILLO = colors.HexColor("#f2c200")
AMBAR = colors.HexColor("#f29100")
ROJO = colors.HexColor("#c0392b")
CREMA = colors.HexColor("#e8e2d4")
GRIS = colors.HexColor("#9a9283")
VERDE = colors.HexColor("#4e9a3f")

base = getSampleStyleSheet()
TITULO = ParagraphStyle("Titulo", parent=base["Title"], textColor=AMARILLO,
                        fontName="Courier-Bold", fontSize=30, leading=36, alignment=TA_CENTER)
SUB = ParagraphStyle("Sub", parent=base["Normal"], textColor=CREMA,
                     fontName="Courier", fontSize=12, leading=18, alignment=TA_CENTER)
H1 = ParagraphStyle("H1", parent=base["Heading1"], textColor=AMARILLO,
                    fontName="Courier-Bold", fontSize=17, spaceBefore=4, spaceAfter=10)
H2 = ParagraphStyle("H2", parent=base["Heading2"], textColor=AMBAR,
                    fontName="Courier-Bold", fontSize=13, spaceBefore=10, spaceAfter=6)
BODY = ParagraphStyle("Body", parent=base["BodyText"], textColor=CREMA,
                      fontName="Helvetica", fontSize=10.5, leading=15,
                      alignment=TA_JUSTIFY, spaceAfter=7)
NOTA = ParagraphStyle("Nota", parent=BODY, textColor=GRIS, fontSize=9, leading=13)
MONO = ParagraphStyle("Mono", parent=base["Code"], textColor=AMARILLO, fontName="Courier",
                      fontSize=9, leading=13, backColor=CARBON, borderPadding=6,
                      spaceBefore=4, spaceAfter=8)
LI = ParagraphStyle("LI", parent=BODY, spaceAfter=4)
FIRMA = ParagraphStyle("Firma", parent=BODY, textColor=GRIS, fontSize=9,
                       fontName="Courier", alignment=TA_LEFT)


def p(t, s=BODY):
    return Paragraph(t, s)


def bullets(items):
    return ListFlowable(
        [ListItem(p(t, LI), value="\u2756") for t in items],
        bulletType="bullet", bulletColor=AMBAR, leftIndent=14,
    )


def caja_puntos(titulo, filas, color=AMBAR):
    """Tabla de criterios -> puntos, con estetica de advertencia."""
    data = [[titulo, "PUNTOS"]] + filas
    t = Table(data, colWidths=[12.2 * cm, 2.8 * cm])
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), color),
        ("TEXTCOLOR", (0, 0), (-1, 0), NEGRO),
        ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), CREMA),
        ("TEXTCOLOR", (1, 1), (1, -1), AMARILLO),
        ("FONTNAME", (1, 1), (1, -1), "Courier-Bold"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, -1), CARBON),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#3a342c")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]
    t.setStyle(TableStyle(estilo))
    return t


H = []
S = H.append

# ===================================================== PORTADA
S(Spacer(1, 1.6 * cm))
S(p("METRO&nbsp;LAKE&nbsp;INC.", ParagraphStyle("mk", parent=SUB, textColor=AMBAR,
                                                fontSize=13, spaceAfter=2)))
S(p("— Sistemas de Seguridad Operacional —", ParagraphStyle("mk2", parent=SUB,
                                                            textColor=GRIS, fontSize=9)))
S(Spacer(1, 1.1 * cm))
S(p("MANUAL DEL<br/>TECNICO DE TURNO", TITULO))
S(Spacer(1, 0.5 * cm))
S(p("\u2756 Protocolo de Evaluacion de Riesgo Diario \u2756", SUB))
S(Spacer(1, 1.3 * cm))
S(Table([[p(
    "<b>BIENVENIDO/A AL EQUIPO.</b><br/><br/>"
    "Enhorabuena por tu nuevo puesto como <b>Tecnico de Monitoreo del Metro</b>. "
    "Tu labor es sencilla: revisar el <b>Riesgo Diario</b> cada jornada y actuar en "
    "consecuencia.<br/><br/>"
    "Queremos recordarte que, segun la clausula 7.3 de tu contrato, "
    "<b>cualquier incidente durante tu turno es responsabilidad exclusiva del "
    "empleado</b>. Metro Lake Inc. no se hace responsable de vagones, tramos, "
    "pluviometros, ni de cualquier extremidad perdida en el proceso.<br/><br/>"
    "Pero tranquilo. Si lees este manual, probablemente estaras bien.<br/>"
    "<i>Probablemente.</i>", BODY)]],
    colWidths=[15 * cm]))
S(PageBreak())

# ===================================================== COMO FUNCIONA
S(p("1. ¿QUE ES EL RIESGO DIARIO?", H1))
S(p(
    "Cada dia, el sistema revisa los datos de las tres fuentes que vigilan el metro y "
    "calcula un <b>puntaje de riesgo</b>. Tu trabajo es mirar ese numero y decidir si "
    "puedes relajarte... o si deberias empezar a correr.", BODY))
S(p(
    "El puntaje va de <b>0 a 12 puntos</b>. Se obtiene sumando los puntos de "
    "<b>tres factores</b>. Mientras mas alto el numero, mas probable es que algo "
    "salga mal durante TU turno (y ya sabemos de quien seria la culpa).", BODY))

S(p("1.1 Los tres factores que te vigilan", H2))
S(bullets([
    "<b>INFRAESTRUCTURA (vibracion):</b> los sensores de la via. Si tiemblan demasiado, "
    "algo se esta rompiendo. Idealmente, no mientras pasa un tren.",
    "<b>CLIMA (lluvia):</b> los pluviometros. En Medellin llueve. Mucho. A veces demasiado.",
    "<b>DEMANDA (pasajeros):</b> cuanta gente se amontona. Mas gente = mas caos = mas "
    "formularios que llenar si pasa algo.",
]))
S(Spacer(1, 0.3 * cm))

# ===================================================== LA ESCALA
S(p("2. LA ESCALA (memorizala)", H1))
S(Table([
    [p("<b>0 - 3</b>", ParagraphStyle("n", parent=BODY, textColor=NEGRO, alignment=TA_CENTER, fontName="Courier-Bold", fontSize=13)),
     p("<b>BAJO</b><br/>Turno tranquilo. Toma cafe. Agradece.", ParagraphStyle("d1", parent=BODY, textColor=NEGRO))],
    [p("<b>4 - 7</b>", ParagraphStyle("n", parent=BODY, textColor=NEGRO, alignment=TA_CENTER, fontName="Courier-Bold", fontSize=13)),
     p("<b>MEDIO</b><br/>Mantente alerta. Revisa dos veces. No te duermas.", ParagraphStyle("d2", parent=BODY, textColor=NEGRO))],
    [p("<b>8 - 12</b>", ParagraphStyle("n", parent=BODY, textColor=CREMA, alignment=TA_CENTER, fontName="Courier-Bold", fontSize=13)),
     p("<b>ALTO</b><br/>Encomienda tu alma. Avisa a mantenimiento. Y a tu familia.", ParagraphStyle("d3", parent=BODY, textColor=CREMA))],
], colWidths=[3 * cm, 12 * cm], rowHeights=[1.5 * cm, 1.5 * cm, 1.5 * cm],
    style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("BACKGROUND", (0, 1), (-1, 1), AMBAR),
        ("BACKGROUND", (0, 2), (-1, 2), ROJO),
        ("GRID", (0, 0), (-1, -1), 1, NEGRO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ])))
S(Spacer(1, 0.3 * cm))
S(p("Si no sabes sumar hasta 12, este quiza no sea el trabajo para ti. "
    "Pero no te preocupes, el sistema lo hace por ti.", NOTA))
S(PageBreak())

# ===================================================== FACTOR 1
S(p("3. COMO SE REPARTEN LOS PUNTOS", H1))
S(p("Aqui viene lo importante. Lee con atencion, porque despues no digas que "
    "no te avisamos.", BODY))

S(p("3.1 FACTOR: INFRAESTRUCTURA (vibracion) — hasta 5 pts", H2))
S(p("Los acelerometros miden cuanto tiembla la via. Se fijan en tres cosas:", BODY))
S(caja_puntos("Criterio de vibracion", [
    ["Anomalias: menos del 2% de las lecturas", "+1"],
    ["Anomalias: entre 2% y 5%", "+2"],
    ["Anomalias: 5% o mas (esto ya es feo)", "+3"],
    ["Vibracion RMS maxima >= 4.5 mm/s2", "+1"],
    ["Fatiga acumulada >= 0.8 (la via esta cansada)", "+1"],
]))
S(p("Traduccion: si los rieles vibran como gelatina y estan viejos, suma puntos. "
    "No, no puedes arreglarlo con cinta.", NOTA))

S(p("3.2 FACTOR: CLIMA (lluvia) — hasta 4 pts", H2))
S(p("Los pluviometros miden cuanto llueve. En orden de 'me mojé' a 'arca de Noe':", BODY))
S(caja_puntos("Criterio de clima", [
    ["Lluvia moderada: 10 a 30 mm/h", "+1"],
    ["Lluvia fuerte: 30 a 60 mm/h", "+2"],
    ["Lluvia muy fuerte: 60 mm/h o mas", "+3"],
    ["Hay alertas nivel naranja o roja", "+1"],
]))
S(p("Si ves peces nadando en el anden, asume que es nivel ALTO y no esperes al sistema.", NOTA))

S(p("3.3 FACTOR: DEMANDA (pasajeros) — hasta 3 pts", H2))
S(p("Los torniquetes cuentan la gente. Mas gente apretada, mas riesgo:", BODY))
S(caja_puntos("Criterio de demanda", [
    ["Ocupacion alta: entre 50% y 80%", "+1"],
    ["Ocupacion muy alta / saturacion: 80% o mas", "+2"],
    ["Hubo al menos un evento con ocupacion >= 80%", "+1"],
]))
S(p("Recordatorio: los pasajeros NO son responsabilidad tuya... hasta que lo son.", NOTA))
S(PageBreak())

# ===================================================== EJEMPLO
S(p("4. EJEMPLO DE UN TURNO REAL", H1))
S(p("Supongamos que empiezas tu turno y el sistema calcula lo siguiente:", BODY))
S(caja_puntos("Reporte del dia — ejemplo", [
    ["CLIMA: lluvia muy fuerte (71.7 mm/h)  ..............", "+3"],
    ["CLIMA: habia alertas naranja/roja  ................", "+1"],
    ["INFRAESTRUCTURA: sin anomalias  ...................", "0"],
    ["DEMANDA: ocupacion controlada (12%)  ..............", "0"],
], color=AMARILLO))
S(Spacer(1, 0.2 * cm))
S(Table([[p("PUNTAJE TOTAL = 4  \u2192  NIVEL <b>MEDIO</b>", ParagraphStyle(
    "tot", parent=BODY, textColor=NEGRO, fontName="Courier-Bold", fontSize=13,
    alignment=TA_CENTER))]], colWidths=[15 * cm], rowHeights=[1.1 * cm],
    style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), AMBAR),
                      ("VALIGN", (0, 0), (-1, -1), "MIDDLE")])))
S(Spacer(1, 0.3 * cm))
S(p(
    "Interpretacion: llovio como para construir un arca, pero la via estaba bien y "
    "habia poca gente. Resultado: <b>MEDIO</b>. Mantente alerta, revisa los tramos "
    "mojados y reza para que no suba a ALTO. Ese dia, por cierto, el sistema dijo "
    "textualmente: <i>'Lluvia muy fuerte (maxima 71.74 mm/h)'</i>. No era broma.", BODY))

# ===================================================== PROTOCOLO
S(p("5. TU PROTOCOLO SEGUN EL NIVEL", H1))
S(bullets([
    "<b>BAJO (0-3):</b> respira. Haz tu ronda. Finge que trabajas. Todo bien.",
    "<b>MEDIO (4-7):</b> revisa el factor que mas sumo (lo ves en la pantalla). "
    "Vigila de cerca. No es momento de siesta.",
    "<b>ALTO (8-12):</b> activa el protocolo de mantenimiento preventivo, notifica a "
    "tu supervisor y documenta TODO. Recuerda la clausula 7.3.",
]))
S(p(
    "La pantalla de <b>Riesgo Diario</b> siempre te dice el PORQUE de cada punto. "
    "Leelo. Es, literalmente, tu unica defensa en la reunion del lunes.", BODY))

S(Spacer(1, 0.6 * cm))
S(Table([[p(
    "<b>NOTA LEGAL (la parte aburrida pero real):</b><br/>"
    "Este manual es material educativo del proyecto MetroLake. El sistema de puntos "
    "aqui descrito es EXACTO al implementado en el codigo (Frontend/riesgo.py). "
    "Los umbrales son criterios de demostracion y pueden ajustarse. "
    "Metro Lake Inc. es una empresa ficticia. Ninguna extremidad fue perdida en la "
    "elaboracion de este documento.", NOTA)]],
    colWidths=[15 * cm],
    style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), CARBON),
                      ("BOX", (0, 0), (-1, -1), 0.5, GRIS),
                      ("TOPPADDING", (0, 0), (-1, -1), 10),
                      ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                      ("LEFTPADDING", (0, 0), (-1, -1), 10),
                      ("RIGHTPADDING", (0, 0), (-1, -1), 10)])))
S(Spacer(1, 0.5 * cm))
S(p("Firma del empleado: ________________________   Fecha: __________", FIRMA))
S(p("(Al firmar aceptas que leiste esto y que, pase lo que pase, fue tu culpa.)", NOTA))


# --------------------------------------------------- fondo oscuro + pie
def _fondo(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NEGRO)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # marco amarillo de 'precaucion'
    canvas.setStrokeColor(AMARILLO)
    canvas.setLineWidth(2)
    canvas.rect(0.8 * cm, 0.8 * cm, A4[0] - 1.6 * cm, A4[1] - 1.6 * cm, fill=0, stroke=1)
    canvas.setFont("Courier", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(1.4 * cm, 1.0 * cm, "METRO LAKE INC. · CONFIDENCIAL · TURNO NOCTURNO")
    canvas.drawRightString(A4[0] - 1.4 * cm, 1.0 * cm, "Pag. %d" % doc.page)
    canvas.restoreState()


doc = SimpleDocTemplate(
    SALIDA, pagesize=A4,
    leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=1.8 * cm,
    title="MetroLake - Manual del Tecnico (Riesgo Diario)", author="Samuel Aristizabal",
)
doc.build(H, onFirstPage=_fondo, onLaterPages=_fondo)
print("PDF generado en:", SALIDA)
