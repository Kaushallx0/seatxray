# SeatXray Windows Build Script (Auto-Fix)
# Based on build-guide.md

Set-Location $PSScriptRoot

Write-Host "=== SeatXray Windows Build System ===" -ForegroundColor Cyan
Write-Host "Target: Windows (MSIX/EXE)"
Write-Host "Hack Level: High (Flet 0.80.1 fixes enabled)"

# 0. Cleanup (Optional but recommended to ensure clean state)
# Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue

# 1. First Build Run (Expect Failure or Partial Success)
Write-Host "`n[Phase 1] Initial Build (Triggers plugin extraction)..." -ForegroundColor Yellow
# We ignore errors here because the CMakeLists.txt bug usually fails the build first time
flet build windows --verbose 2>&1 | Out-Null

# 2. Hack 1: Fix serious_python_windows CMakeLists.txt
Write-Host "[Phase 2] Applying Fixes..." -ForegroundColor Yellow
$pluginFile = ".\build\flutter\windows\flutter\ephemeral\.plugin_symlinks\serious_python_windows\windows\CMakeLists.txt"

if (Test-Path $pluginFile) {
    $content = Get-Content $pluginFile
    # Remove lines containing system32 dlls which cause MSB3073 error
    $newContent = $content | Where-Object { $_ -notmatch 'system32/(msvcp140|vcruntime140|vcruntime140_1)\.dll' }
    
    if ($content.Count -ne $newContent.Count) {
        $newContent | Set-Content $pluginFile
        Write-Host "  [OK] Removed broken System32 DLL references." -ForegroundColor Green
    }
    else {
        Write-Host "  [SKIP] CMakeLists.txt already clean or pattern not found." -ForegroundColor Gray
    }
}
else {
    Write-Host "  [WARN] Plugin directory not found. Is this the first run?" -ForegroundColor Red
}

# 3. Hack 2 moved to after final build to prevent overwrite

# 4. Final Flet Build
Write-Host "`n[Phase 3] Final Flet Build..." -ForegroundColor Yellow
flet build windows --verbose

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild Complete! Output in build\windows" -ForegroundColor Green
}
else {
    Write-Host "`nBuild Failed. Check output above." -ForegroundColor Red
}
