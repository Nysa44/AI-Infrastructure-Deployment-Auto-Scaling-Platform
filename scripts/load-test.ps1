param([int]$Requests = 100, [string]$BaseUrl = "http://localhost:8000")
$ErrorActionPreference = "Stop"
$start = Get-Date
for ($i = 1; $i -le $Requests; $i++) {
  $payload = @{ job_id = "load-$i"; text = "Load test request $i" } | ConvertTo-Json
  Invoke-RestMethod -Uri "$BaseUrl/jobs" -Method Post -ContentType "application/json" -Body $payload | Out-Null
}
$elapsed = (Get-Date) - $start
$rate = [math]::Round($Requests / [math]::Max($elapsed.TotalSeconds, 0.01), 2)
Write-Host "Submitted $Requests jobs in $([math]::Round($elapsed.TotalSeconds,2)) seconds"
Write-Host "Submission rate: $rate jobs/sec (client submission rate, not inference throughput)"
