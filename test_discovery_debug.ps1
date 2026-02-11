# Test discovery debug script

$ErrorActionPreference = "Stop"

# Get list of projects from backend
Write-Host "Getting projects list..." -ForegroundColor Cyan
$projectsResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/projects" -Method Get
$projects = $projectsResponse.Content | ConvertFrom-Json

Write-Host "Found $($projects.projects.Count) projects:" -ForegroundColor Green
foreach ($project in $projects.projects) {
    Write-Host "  - $($project.name) at $($project.local_folder)"
}

# Test discovery for each project
foreach ($project in $projects.projects) {
    Write-Host "`nTesting discovery for: $($project.name)" -ForegroundColor Cyan
    $encodedPath = [System.Web.HttpUtility]::UrlEncode($project.local_folder)
    Write-Host "  Path: $($project.local_folder)"
    Write-Host "  Encoded URL: /api/tests/discover?path=$encodedPath"

    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/tests/discover?path=$encodedPath" -Method Get
        $data = $response.Content | ConvertFrom-Json
        Write-Host "  ✓ Suites found: $($data.total_suites)" -ForegroundColor Green
        Write-Host "  ✓ Tests found: $($data.total_tests)" -ForegroundColor Green

        if ($data.suites.Count -gt 0) {
            Write-Host "  First suite: $($data.suites[0].name) with $($data.suites[0].tests.Count) tests"
        }
    }
    catch {
        Write-Host "  ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}
