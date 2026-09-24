# Frontend · Simulador visual de MetroLake

Interfaz web para **simular y visualizar** lo que hace el proyecto MetroLake.
Reutiliza directamente los simuladores existentes (`SimuladorTorniquetes`,
`SimuladorAcelerometro`, `SimuladorClima`) sin duplicar su lógica.

## Qué ofrece

Un menú lateral con cuatro vistas:

- **Panel general** — resumen de las tres fuentes de datos.
- **Simuladores (batch)** — genera un lote histórico por ventana de tiempo y
  muestra métricas y las últimas muestras generadas.
- **Streaming en vivo** — emite eventos en tiempo real con los mismos pesos del
  proyecto (50% vibración · 35% pasajeros · 15% clima) y un contador por fuente.
- **Comparar** — coloca el modo batch y el modo streaming lado a lado.

## Cómo ejecutarlo

Desde la raíz del proyecto (`MetroLake/`):

```bash
python -m pip install -r Frontend/requirements.txt
python Frontend/app.py
```

Luego abre <http://localhost:5000> en el navegador.

El puerto se puede cambiar con la variable de entorno `PORT`:

```bash
PORT=8080 python Frontend/app.py
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
