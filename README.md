# AI Infrastructure Deployment & Auto-Scaling Platform

A portfolio-ready DevOps project: a queue-driven AI inference API and worker, packaged with Docker, deployable to Kubernetes, managed with Terraform, and monitored with Prometheus/Grafana.

## Capabilities
- FastAPI inference API and Redis Streams worker
- Idempotent job submission, bounded retries and dead-letter stream
- Docker Compose local stack
- Kubernetes Deployments, Services, ConfigMaps, Secret, probes, resource limits and HPAs
- Terraform-managed Kubernetes resources on an existing cluster
- Prometheus metrics, alert rules and provisioned Grafana dashboard
- GitHub Actions tests, container build and Trivy vulnerability scan
- Kind local-cluster configuration and smoke/load-test scripts

The inference adapter is deterministic demo logic, not a hosted LLM. HPA targets and replica ranges are configured policies, not claims of measured scaling performance. This is a portfolio implementation, not a production-certified service.

## Prerequisites
Docker Desktop with its engine running. For Kubernetes: kubectl, Kind and Terraform 1.6+. Python 3.11+ for tests.

## Run locally (Windows PowerShell)
```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```
Open API docs at http://localhost:8000/docs, Prometheus at http://localhost:9090 and Grafana at http://localhost:3000 (local default admin/admin; change before any shared deployment).

Submit a job:
```powershell
$body = @{ job_id = "demo-001"; text = "Explain reliable AI infrastructure" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/jobs" -Method Post -ContentType "application/json" -Body $body
Invoke-RestMethod -Uri "http://localhost:8000/jobs/demo-001"
```
Linux/macOS:
```bash
cp .env.example .env
docker compose up --build -d
curl -X POST http://localhost:8000/jobs -H "Content-Type: application/json" -d '{"job_id":"demo-001","text":"hello"}'
```
Stop with `docker compose down`. `docker compose down -v` also deletes local data.

## Kubernetes with Kind
```bash
docker build -t ai-inference-platform:1.0.0 .
kind create cluster --name ai-platform --config kind/kind-config.yaml
kind load docker-image ai-inference-platform:1.0.0 --name ai-platform
kubectl apply -f k8s/00-namespace.yaml -f k8s/01-config.yaml -f k8s/02-redis.yaml -f k8s/03-api.yaml -f k8s/04-worker.yaml -f k8s/05-monitoring.yaml
kubectl get pods -n ai-platform
```
For CPU-based HPA metrics, install metrics-server:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
kubectl rollout status deployment/metrics-server -n kube-system
kubectl top nodes
kubectl get hpa -n ai-platform
```
The insecure TLS flag is a local Kind workaround; do not copy it into production clusters.

## Terraform
Create the Kind cluster and load the image first. Then:
```bash
cd terraform
terraform init
terraform plan
terraform apply
```
Terraform uses `~/.kube/config` by default. Override with `-var="kubeconfig_path=C:/Users/you/.kube/config"` on Windows. Terraform and `kubectl apply -f k8s/00-namespace.yaml -f k8s/01-config.yaml -f k8s/02-redis.yaml -f k8s/03-api.yaml -f k8s/04-worker.yaml -f k8s/05-monitoring.yaml` manage overlapping resources: use one deployment method, not both at once. `terraform destroy` removes Terraform-managed application resources. `kind delete cluster --name ai-platform` removes the local cluster.

## API
- `GET /health` liveness
- `GET /ready` Redis readiness
- `GET /metrics` Prometheus metrics
- `POST /jobs` submit `{"job_id":"demo-001","text":"..."}`
- `GET /jobs/{job_id}` status/result

Job IDs are idempotency keys. Inputs are 1–5,000 characters. Redis is used for queueing and result storage in this demo.

## Metrics
`inference_jobs_submitted_total`, `inference_jobs_processed_total`, `inference_jobs_failed_total`, `inference_worker_retries_total`, `inference_dead_letter_total`, `inference_queue_depth`, and `inference_job_processing_seconds`.

## Tests
```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```
Unit tests validate request schemas, inference determinism and retry decision logic. Run Docker Compose and Kind smoke tests separately for integration validation.

## Security
`.env` is ignored by Git. Never commit real credentials. The Kubernetes Secret and Grafana credentials are local demo placeholders. Production needs TLS, managed secret storage, RBAC review, network policies, hardened images, image signing and security/compliance validation.
