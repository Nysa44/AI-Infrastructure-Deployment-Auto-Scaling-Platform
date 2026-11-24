$ErrorActionPreference = "Stop"
if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env" }
docker compose up --build -d
docker compose ps
Write-Host "API docs: http://localhost:8000/docs"
Write-Host "Grafana: http://localhost:3000"
Write-Host "Prometheus: http://localhost:9090"
