# High traffic simulation script in PowerShell for Windows
param (
    [string]$TargetUrl = "http://localhost:30005",
    [int]$TotalRequests = 1000,
    [int]$Concurrency = 20
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Simulating High Traffic on: $TargetUrl" -ForegroundColor Cyan
Write-Host "Total Requests: $TotalRequests | Concurrency: $Concurrency" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$scriptBlock = {
    param($url, $workerId, $count)
    for ($i = 0; $i -lt $count; $i++) {
        try {
            if ($i % 2 -eq 0) {
                $body = @{ worker = $workerId; seq = $i; date = (Get-Date).ToString("o") } | ConvertTo-Json
                Invoke-RestMethod -Uri "$url/data" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 3 | Out-Null
            } else {
                Invoke-RestMethod -Uri "$url/" -Method Get -TimeoutSec 3 | Out-Null
            }
        } catch {
            # Ignore individual connection blips during autoscaling
        }
    }
}

$requestsPerJob = [math]::Ceiling($TotalRequests / $Concurrency)
$jobs = @()

Write-Host "Launching $Concurrency background jobs..." -ForegroundColor Yellow
$startTime = Get-Date

for ($j = 1; $j -le $Concurrency; $j++) {
    $jobs += Start-Job -ScriptBlock $scriptBlock -ArgumentList $TargetUrl, $j, $requestsPerJob
}

$jobs | Wait-Job | Out-Null
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

$jobs | Remove-Job

Write-Host "Load test finished in [math]::Round($duration, 2) seconds." -ForegroundColor Green
Write-Host "Check HPA with: kubectl get hpa -n flask-mongo-app -w" -ForegroundColor Green
