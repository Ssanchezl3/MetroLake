# Despliegue en Google Cloud Platform (GCP)

Este proyecto tiene **dos partes** que se despliegan de forma distinta:

1. **Frontend web** (`Frontend/app.py`) → se despliega en **Cloud Run** (serverless).
2. **Pipeline de datos** (simuladores → Pub/Sub → BigQuery) → se ejecuta con el
   **publicador** (`Integraciones/publicador_gcp.py`). Los detalles de Pub/Sub y
   BigQuery estan en [`PLAN_CONEXION_GCP.md`](PLAN_CONEXION_GCP.md).

> Diagrama de la arquitectura: ver [`docs/img/arquitectura.png`](docs/img/arquitectura.png).

---

## Parte 1 · Desplegar el frontend en Cloud Run

Cloud Run es la opcion recomendada: es serverless (pagas solo por uso), escala a
cero y construye el contenedor por ti a partir del codigo fuente. La app ya esta
preparada: lee el puerto de la variable `PORT` y escucha en `0.0.0.0`.

Archivos de despliegue incluidos en la raiz:

- `requirements.txt` — dependencias (Flask, requests, **gunicorn**).
- `Procfile` — arranca gunicorn apuntando a `Frontend.app:app`.
- `.gcloudignore` — evita subir datos, entornos virtuales y documentacion.

### 1.1 Requisitos previos (una sola vez)

```bash
# Instalar y autenticar la CLI de gcloud (si no la tienes)
gcloud auth login
gcloud config set project terraform-demo-metro      # tu PROJECT_ID real

# Habilitar las APIs necesarias
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

### 1.2 Desplegar (un solo comando, desde la raiz del proyecto)

```bash
gcloud run deploy metrolake-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

Que hace:

- `--source .` → Cloud Build construye el contenedor automaticamente desde el
  codigo (detecta Python + `requirements.txt` + `Procfile`).
- `--allow-unauthenticated` → la pagina queda publica (quitalo si quieres que
  requiera login de Google).
- Al terminar, imprime la **URL publica** del servicio, por ejemplo:
  `https://metrolake-frontend-xxxxxxxx-uc.a.run.app`

Abre esa URL en el navegador y veras el frontend.

### 1.3 Volver a desplegar (tras cambios)

Repite exactamente el mismo comando `gcloud run deploy ...`. Cloud Run crea una
nueva revision y mueve el trafico a ella.

### 1.4 Notas importantes

- **Datos efimeros:** el disco de Cloud Run es temporal. Lo que se guarde con
  "Guardar" (`datos_frontend/`) se pierde al reiniciar o reescalar la instancia.
  Para persistencia real, monta un bucket de Cloud Storage o escribe en BigQuery
  (ver "Mejoras opcionales").
- **Costo:** con escala a cero, si nadie usa la app no cobra. Ideal para demos.

---

## Parte 2 · Ejecutar el pipeline de datos (Pub/Sub)

El publicador NO es un servidor web; genera eventos y los envia a tres temas de
Pub/Sub. Sigue [`PLAN_CONEXION_GCP.md`](PLAN_CONEXION_GCP.md) para crear temas,
subscriptions a BigQuery y autenticar. En resumen:

```bash
# 1) Habilitar Pub/Sub y crear los 3 temas (una vez)
gcloud services enable pubsub.googleapis.com
gcloud pubsub topics create tema-metro-vibracion
gcloud pubsub topics create tema-metro-pasajeros
gcloud pubsub topics create tema-metro-clima

# 2) Variables que lee el publicador
export GCP_PROJECT_ID=terraform-demo-metro
export GCP_TOPIC_VIBRACION=tema-metro-vibracion
export GCP_TOPIC_PASAJEROS=tema-metro-pasajeros
export GCP_TOPIC_CLIMA=tema-metro-clima

# 3) Ejecutar el publicador (localmente o en una VM)
python -m pip install google-cloud-pubsub
python -m Integraciones.publicador_gcp
```

### Opciones para ejecutar el publicador en la nube

- **Cloud Shell / una VM (Compute Engine):** corre el comando de arriba. Simple
  para demos.
- **Cloud Run Job** (no un servicio web, sino una tarea que corre y termina):
  util para publicar durante X segundos de forma programada.
- **Cloud Scheduler + Cloud Run Job:** para dispararlo periodicamente.

---

## Alternativa al frontend: App Engine

Si prefieres App Engine en lugar de Cloud Run, crea un `app.yaml`:

```yaml
runtime: python312
entrypoint: gunicorn --bind :$PORT Frontend.app:app
```

Y despliega con:

```bash
gcloud app deploy
```

Cloud Run es mas flexible y suele ser mas barato para este caso; App Engine es
igualmente valido.

---

## Mejoras opcionales (para produccion)

- **Persistir "Guardar":** montar un bucket de Cloud Storage como volumen en
  Cloud Run, o cambiar `Frontend/consultas.py` para leer/escribir en BigQuery.
- **Leer datos reales de BigQuery** en las vistas de Consultas/Comparar en vez de
  archivos locales.
- **HTTPS y dominio propio:** Cloud Run ya da HTTPS; puedes mapear un dominio.
- **Autenticacion:** quitar `--allow-unauthenticated` y usar IAM / IAP.

---

## Comprobacion rapida local antes de desplegar

```bash
python -m pip install -r requirements.txt
gunicorn --bind :8080 Frontend.app:app
# abre http://localhost:8080
```

Si funciona con gunicorn en local, funcionara en Cloud Run.
