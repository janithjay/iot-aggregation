$ErrorActionPreference = 'Stop'

$health = Invoke-RestMethod -Uri 'http://localhost:5000/health' -Method Get
if ($health.status -ne 'ok') {
    throw 'API health check failed'
}

$payload = @{
    sensor_id = 'sensor-lead-01'
    values = @(11, 17, 9, 23, 15)
} | ConvertTo-Json

$post = Invoke-RestMethod -Uri 'http://localhost:5000/data' -Method Post -ContentType 'application/json' -Body $payload
$id = $post.data_id
if (-not $id) {
    throw 'POST /data did not return data_id'
}

$maxAttempts = 15
$attempt = 0
$summary = $null

while ($attempt -lt $maxAttempts) {
    $summary = Invoke-RestMethod -Uri ("http://localhost:5000/summary?id=" + $id) -Method Get
    if ($summary.status -eq 'done' -or $summary.status -eq 'failed') {
        break
    }
    Start-Sleep -Seconds 1
    $attempt++
}

if (-not $summary) {
    throw 'Summary polling failed'
}

"HEALTH=$($health | ConvertTo-Json -Compress)"
"POST=$($post | ConvertTo-Json -Compress)"
"FINAL_SUMMARY=$($summary | ConvertTo-Json -Compress)"
"ATTEMPTS=$attempt"
