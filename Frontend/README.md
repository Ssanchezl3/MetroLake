# Frontend · Simulador visual de MetroLake

Interfaz web para **simular y visualizar** lo que hace el proyecto MetroLake.
Reutiliza directamente los simuladores existentes (`SimuladorTorniquetes`,
`SimuladorAcelerometro`, `SimuladorClima`) sin duplicar su lógica.

## Qué ofrece

Un menú lateral con cinco vistas, con el diseño visual del **Metro de Medellín**
(verde institucional y naranja de acento):

- **Panel general** — resumen de las tres fuentes de datos.
- **Simuladores (batch)** — genera un lote histórico eligiendo el **día de la
  semana** (lunes–domingo) y la ventana de tiempo. Los simuladores aplican su
  lógica de fin de semana / horas pico, así que un lunes y un domingo producen
  datos distintos. Botón **Guardar** para persistir el lote bajo la fecha de ese
  día (lo que permite compararlos luego).
- **Streaming en vivo** — emite eventos en tiempo real con los mismos pesos del
  proyecto (50% vibración · 35% pasajeros · 15% clima) y un contador por fuente.
  Botón **Guardar sesión** para persistir los eventos emitidos.
- **Consultas y trazabilidad** (HU H05) — busca por **día** los datos
  almacenados, filtra por **origen** (sintéticos / streaming / guardados) y por
  **fuente**, y los revisa en una **tabla** con buscador de texto.
- **Comparar días** (HU H05) — selecciona **Día A** y **Día B** (guardados) y
  compara sus resúmenes lado a lado (p. ej. lunes vs domingo).
- **Riesgo Diario** — evalúa el nivel de riesgo operativo de un día
  (**BAJO / MEDIO / ALTO**) con un puntaje y la explicación de los criterios:
  infraestructura (anomalías y RMS de vibración, fatiga), clima (precipitación y
  alertas) y demanda (ocupación y volumen de pasajeros).

## Dónde se guardan los datos

- La interfaz guarda en `datos_frontend/YYYY-MM-DD/` (batch y streaming).
- Las consultas también leen los datos que genera el proyecto en
  `datos_sinteticos/YYYY-MM-DD/` y `datos_streaming/streaming_*.json`.

## Cómo ejecutarlo

Desde la raíz del proyecto (`MetroLake/`):

```bash
python -m pip install -r Frontend/requirements.txt
python Frontend/app.py
```

Luego abre <http://localhost:8080> en el navegador.

El puerto por defecto es **8080**. Se puede cambiar con la variable de entorno
`PORT` (por ejemplo si ese puerto ya está en uso):

```bash
# macOS / Linux
PORT=8000 python Frontend/app.py
```

```powershell
# Windows PowerShell
$env:PORT=8000
python Frontend\app.py
```

## Estructura

```text
Frontend/
|-- app.py                 # Servidor Flask + endpoints /api/*
|-- requirements.txt
|-- templates/
|   `-- index.html         # Interfaz de una sola página
`-- static/
    |-- css/styles.css     # Estilos
    `-- js/app.js          # Lógica de la interfaz (menú, batch, streaming, comparar)
```

## Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Interfaz web. |
| GET | `/api/estado` | Configuración (estaciones, tramos, sensores, pluviómetros). |
| GET | `/api/batch?minutos=30` | Genera un lote batch de las tres fuentes con su resumen. |
| GET | `/api/streaming/evento` | Emite un único evento de streaming con `_tipo_fuente`. |
| GET | `/api/batch?minutos=30&dia_semana=lunes` | Lote batch de un día de la semana. |
| POST | `/api/guardar/batch?minutos=30&dia_semana=lunes` | Genera y guarda un lote batch (bajo la fecha de ese día). |
| POST | `/api/guardar/streaming` | Guarda los eventos de streaming acumulados. |
| GET | `/api/consultas/dias` | Lista los días con datos almacenados. |
| GET | `/api/consultas/dia?dia=YYYY-MM-DD&origen=todos&tipo=todos` | Tabla y resumen de un día (origen: `todos` / `batch` / `streaming`). |
| GET | `/api/consultas/comparar?dia_a=...&dia_b=...` | Resúmenes de dos días para comparar. |
| GET | `/api/riesgo/dia?dia=YYYY-MM-DD` | Nivel de riesgo del día (bajo/medio/alto) con criterios. |
