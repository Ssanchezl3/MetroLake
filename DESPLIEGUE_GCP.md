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

### 1.4 Persistencia con BigQuery (recomendado)

Por defecto el frontend guarda en el disco de Cloud Run, que es **efimero**: los
datos se pierden al reiniciar la instancia (por eso las vistas muestran "sin
datos" al rato). Para que **Consultas / Comparar dias / Riesgo Diario** usen
datos permanentes, conecta el frontend a **BigQuery** (dataset `project_data`).

El frontend lee/escribe estas tablas (una "en vivo" y una `_batch` por fuente):

```
clima      / clima_batch
pasajeros  / pasajeros_batch
vibracion  / vibracion_batch
```

El dia se agrupa con `DATE(timestamp)`. Las vistas leen de las 6 tablas.

**Lectura vs escritura:** por defecto el frontend **solo lee** de BigQuery,
porque las tablas las alimenta el pipeline real (Pub/Sub -> subscriptions ->
BigQuery). El boton "Guardar" no escribe en BigQuery salvo que actives la
variable `BQ_PERMITIR_ESCRITURA=1` (entonces inserta en las tablas `*_batch`).

El esquema de las tablas en BigQuery coincide exactamente con los campos de los
eventos de los simuladores (verificado: pasajeros 12 columnas, vibracion 14,
clima 10).

#### Permisos (una sola vez)

La cuenta de servicio de Cloud Run necesita leer y escribir en BigQuery. Usa la
cuenta de computo por defecto del proyecto (NUMERO-compute@developer...):

```bash
PROJ=terraform-demo-metro
NUM=$(gcloud projects describe $PROJ --format='value(projectNumber)')
SA="$NUM-compute@developer.gserviceaccount.com"

# Lectura (suficiente para el modo por defecto, solo lee de BigQuery):
gcloud projects add-iam-policy-binding $PROJ \
  --member="serviceAccount:$SA" --role="roles/bigquery.dataViewer"
gcloud projects add-iam-policy-binding $PROJ \
  --member="serviceAccount:$SA" --role="roles/bigquery.jobUser"

# Solo si vas a activar BQ_PERMITIR_ESCRITURA=1 (para que "Guardar" inserte):
# gcloud projects add-iam-policy-binding $PROJ \
#   --member="serviceAccount:$SA" --role="roles/bigquery.dataEditor"
```

#### Desplegar activando BigQuery

Igual que antes, pero pasando las variables de entorno que activan BigQuery:

```bash
gcloud run deploy metrolake-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars BQ_DATASET=project_data,GCP_PROJECT_ID=terraform-demo-metro
```

Con `BQ_DATASET` definido, el frontend usa BigQuery automaticamente. Si la
variable NO esta, vuelve a usar archivos locales (util para desarrollo local).

### 1.5 Notas importantes

- **Sin BigQuery, los datos son efimeros.** Con BigQuery (seccion 1.4) son
  permanentes y las vistas funcionan siempre.
- **Costo:** con escala a cero, si nadie usa la app no cobra. BigQuery cobra por
  almacenamiento y consultas, pero en volumenes de demo es minimo.

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
