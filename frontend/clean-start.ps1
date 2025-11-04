# Clean Start Script for Frontend

Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow

# Kill any existing Next.js processes on port 3000
Write-Host "🔍 Checking for processes on port 3000..." -ForegroundColor Cyan
$processes = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($processes) {
    foreach ($processId in $processes) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Killed process $processId" -ForegroundColor Green
    }
}

# Remove .next directory
if (Test-Path ".next") {
    Remove-Item -Recurse -Force ".next"
    Write-Host "✅ Removed .next" -ForegroundColor Green
}

# Remove .turbo directory
if (Test-Path ".turbo") {
    Remove-Item -Recurse -Force ".turbo"
    Write-Host "✅ Removed .turbo" -ForegroundColor Green
}

# Remove node_modules cache
if (Test-Path "node_modules\.cache") {
    Remove-Item -Recurse -Force "node_modules\.cache"
    Write-Host "✅ Removed node_modules\.cache" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 Starting Next.js development server..." -ForegroundColor Cyan
Write-Host ""

# Start the dev server
npm run dev
