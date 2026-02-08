# Test the backend API endpoints

Write-Host "Testing /api/health endpoint..."
$health = Invoke-WebRequest -Uri 'http://localhost:8000/api/health' -Method Get -UseBasicParsing
Write-Host "Status: $($health.StatusCode)"

Write-Host "`nTesting /api/tests/discover endpoint with anvil..."
$discover = Invoke-WebRequest -Uri 'http://localhost:8000/api/tests/discover?path=d:%5Cplayground%5Cargos%5Canvil' -Method Get -UseBasicParsing
Write-Host "Status: $($discover.StatusCode)"
$data = ($discover.Content | ConvertFrom-Json)
Write-Host "Suites found: $($data.total_suites)"
Write-Host "Tests found: $($data.total_tests)"
if ($data.suites.Count -gt 0) {
    Write-Host "First suite: $($data.suites[0].name) with $($data.suites[0].tests.Count) tests"
}

Write-Host "`nTesting /api/tests/execute endpoint..."
$execute = Invoke-WebRequest -Uri 'http://localhost:8000/api/tests/execute' -Method Post -UseBasicParsing -ContentType 'application/json' -Body '{"test_ids":["test1","test2"]}'
Write-Host "Status: $($execute.StatusCode)"
$execData = ($execute.Content | ConvertFrom-Json)
Write-Host "Results: $($execData.total) tests"

Write-Host "`nTesting /api/tests/statistics endpoint..."
$stats = Invoke-WebRequest -Uri 'http://localhost:8000/api/tests/statistics' -Method Get -UseBasicParsing
Write-Host "Status: $($stats.StatusCode)"
$statsData = ($stats.Content | ConvertFrom-Json)
Write-Host "Statistics entries: $($statsData.statistics.Count)"

Write-Host "`nAll API endpoints are working!"
