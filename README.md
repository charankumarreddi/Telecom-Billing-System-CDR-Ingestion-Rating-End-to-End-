# Telecom Billing System – CDR Ingestion & Rating (End-to-End)

This project implements a realistic telecom feature: ingesting Call Detail Records (CDRs) and rating them into billable events. It ships with a Python FastAPI backend, tests, Docker image, Jenkins pipeline, and Kubernetes manifests for deployment.

## What’s included

- Python FastAPI backend (app package)
  - Endpoints: health, ingest CDR, get CDR, subscriber usage summary
  - SQLAlchemy models: TariffPlan, Subscriber, CDR, RatedEvent
  - Rating service with simple voice/SMS/data pricing
  - SQLite by default; override with `DATABASE_URL`
- Tests (pytest)
- Dockerfile to containerize the service
- Jenkinsfile (CI/CD): test -> build/push -> deploy to Kubernetes
- Kubernetes manifests (Deployment, Service, ConfigMap)

## Run locally

1. Create a venv and install deps

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

3. Try it

- Health:

```bash
curl http://localhost:8000/health
```

- Ingest a voice call (125 seconds):

```bash
curl -X POST http://localhost:8000/cdrs/ingest \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"911234567890","call_type":"voice","duration_secs":125}'
```

- Usage summary:

```bash
FROM=$(date -u -v-1d +%Y-%m-%dT%H:%M:%SZ)
TO=$(date -u -v+1d +%Y-%m-%dT%H:%M:%SZ)
curl "http://localhost:8000/subscribers/911234567890/usage?from_ts=$FROM&to_ts=$TO"
```

## Docker

Build and run the container:

```bash
# From repo root
docker build -t telecom-billing-cdr -f docker/Dockerfile .
docker run --rm -p 8000:8000 telecom-billing-cdr
```

## Jenkins CI/CD

The pipeline expects these Jenkins credentials:

- `docker-registry-url` (Secret text or username/password with the registry host; used in `docker login`)
- `docker-credentials` (Username/Password for registry)
- `kubeconfig-file` (File credential containing kubeconfig)

Stages:

1. Checkout
2. Setup Python & Install Deps
3. Test (pytest)
4. Docker Build
5. Docker Push
6. Deploy to Kubernetes (`kubectl apply` + `kubectl set image`)

Set environment variables or update the Jenkinsfile as needed:

- `IMAGE_REPO` (defaults to `telecom-billing-cdr`)
- `DOCKER_REGISTRY` (provided by credential)

## Kubernetes

Manifests under `k8s/`:

- `deployment.yaml`: Deployment with readiness/liveness probes
- `service.yaml`: ClusterIP service on port 8000
- `configmap.yaml`: Holds `APP_NAME` and `DATABASE_URL`

Jenkins applies the manifests and then sets the image to the one built in the pipeline. If you deploy manually, update the image in the deployment spec or run:

```bash
kubectl apply -f k8s/
kubectl set image deployment/telecom-cdr telecom-cdr=<your-registry>/telecom-billing-cdr:<tag>
```

## Rating rules (simple demo)

- Voice: rounds up to whole minutes, charges `voice_rate_per_min` (default 0.5 USD/min)
- SMS: flat `sms_rate` (default 0.1 USD)
- Data: per MB at `data_rate_per_mb` (default 0.05 USD/MB)

Tariff plans and a demo subscriber are seeded automatically when the DB is empty. New MSISDNs auto-attach to the first plan.

## Project layout

- `backend/app/main.py` – FastAPI app factory and router wiring
- `backend/app/api/*` – Endpoints for health, cdr, subscribers
- `backend/app/models/cdr.py` – SQLAlchemy models
- `backend/app/services/rating_service.py` – Rating logic and aggregator
- `backend/app/schemas.py` – Pydantic models
- `docker/Dockerfile` – Container build
- `jenkins/Jenkinsfile` – Pipeline
- `k8s/*` – Kubernetes manifests

## Notes

- Default DB is SQLite (`sqlite:///./telecom.db`), stored in container’s working dir; for production, configure a network DB (e.g., Postgres) and set `DATABASE_URL` accordingly.
- The rating logic is simplified for demonstration and can be extended with time bands, roaming, bundles, and discounts.
