# Kill Next.js Dev Server Script

Write-Host "🔍 Finding Next.js processes..." -ForegroundColor Yellow

# Find and kill processes on port 3000
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($port3000) {
    foreach ($processId in $port3000) {
        $processName = (Get-Process -Id $processId -ErrorAction SilentlyContinue).ProcessName
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Killed $processName (PID: $processId) on port 3000" -ForegroundColor Green
    }
} else {
    Write-Host "ℹ️  No process found on port 3000" -ForegroundColor Cyan
}

# Find and kill processes on port 3001
$port3001 = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($port3001) {
    foreach ($processId in $port3001) {
        $processName = (Get-Process -Id $processId -ErrorAction SilentlyContinue).ProcessName
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Killed $processName (PID: $processId) on port 3001" -ForegroundColor Green
    }
} else {
    Write-Host "ℹ️  No process found on port 3001" -ForegroundColor Cyan
}

# Remove lock file
$lockFile = ".next\dev\lock"
if (Test-Path $lockFile) {
    Remove-Item -Force $lockFile
    Write-Host "✅ Removed lock file" -ForegroundColor Green
}

Write-Host ""
Write-Host "✨ Done! You can now run: npm run dev" -ForegroundColor Green
