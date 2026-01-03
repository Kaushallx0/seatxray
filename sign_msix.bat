@echo off
setlocal

:: 設定
set "MSIX_PATH=%~dp0build\SeatXray.msix"
set "PFX_PATH=%~dp0build\SeatXray_Key.pfx"
set "PUBLISHER=CN=33D8BA06-78D8-4319-B5F0-45A7789CD09B"
set "PASSWORD=password"

echo ========================================================
echo SeatXray MSIX Signing Tool
echo ========================================================
echo Target MSIX: %MSIX_PATH%
echo Certificate: %PFX_PATH%
echo.

if not exist "%MSIX_PATH%" (
    echo [ERROR] MSIX file not found! Please build the package first.
    pause
    exit /b 1
)

:: PowerShellスクリプトを作成して実行
set "PS_SCRIPT=%temp%\sign_script.ps1"

(
echo $ErrorActionPreference = "Stop"
echo $publisher = "%PUBLISHER%"
echo $pfxPath = "%PFX_PATH%"
echo $msixPath = "%MSIX_PATH%"
echo $password = ConvertTo-SecureString -String "%PASSWORD%" -Force -AsPlainText
echo.
echo # Check if PFX exists
echo if ^(-not ^(Test-Path $pfxPath^)^) {
echo     Write-Host "Creating new Self-Signed Certificate..."
echo     $cert = New-SelfSignedCertificate -Type Custom -Subject $publisher -KeyUsage DigitalSignature -FriendlyName "SeatXray Dev Key" -CertStoreLocation "Cert:\CurrentUser\My" -TextExtension @^("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}"^)
echo     Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password
echo     Write-Host "Certificate created at: $pfxPath"
echo } else {
echo     Write-Host "Using existing certificate: $pfxPath"
echo }
echo.
echo # Find SignTool
echo $signtool = Get-ChildItem -Path "C:\Program Files (x86)\Windows Kits\10\bin" -Filter "signtool.exe" -Recurse -ErrorAction SilentlyContinue ^| Where-Object { $_.FullName -like "*x64*" } ^| Select-Object -First 1
echo if ^(-not $signtool^) {
echo     Write-Error "SignTool.exe not found! Please install Windows SDK."
echo     exit 1
echo }
echo.
echo # Sign
echo Write-Host "Signing with: $($signtool.FullName)"
echo ^& $signtool.FullName sign /fd SHA256 /a /f $pfxPath /p "%PASSWORD%" $msixPath
echo if ^($LASTEXITCODE -eq 0^) {
echo     Write-Host -ForegroundColor Green "SUCCESS: MSIX Signed Successfully!"
echo } else {
echo     Write-Error "Signing Failed."
echo }
) > "%PS_SCRIPT%"

:: PowerShell実行
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"

:: 一時ファイル削除
del "%PS_SCRIPT%"

echo.
pause
