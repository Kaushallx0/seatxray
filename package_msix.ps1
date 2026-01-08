# SeatXray MSIX Packaging Script
# Automates: Asset generation, Layout prep, Manifest creation, Packing, Signing

Set-Location $PSScriptRoot
$ErrorActionPreference = "Stop"

Write-Host "=== SeatXray MSIX Packager ===" -ForegroundColor Cyan

# 1. Config
$buildDir = "build\windows"
$sourceIcon = "src\assets\icon.png"
$targetMsix = "build\SeatXray_0.3.0.msix"
$pfxPath = "build\SeatXray_Key.pfx"
$publisher = "CN=33D8BA06-78D8-4319-B5F0-45A7789CD09B"
$certPassword = "password"

if (-not (Test-Path "$buildDir\seatxray.exe")) {
  Write-Error "Build output not found in $buildDir. Did you run 'flet build windows'?"
}

# 2. Generate AppxManifest.xml (Crucial: Flet build wipes this)
Write-Host "Generating AppxManifest.xml..." -ForegroundColor Yellow
$manifestContent = @"
<?xml version="1.0" encoding="utf-8"?>
<Package 
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
  IgnorableNamespaces="uap rescap">

  <Identity
    Name="SeatXray.SeatXray"
    Publisher="$publisher"
    Version="0.3.0.0"
    ProcessorArchitecture="x64" />

  <Properties>
    <DisplayName>SeatXray</DisplayName>
    <PublisherDisplayName>SeatXray</PublisherDisplayName>
    <Logo>Assets\StoreLogo.png</Logo>
  </Properties>

  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.22621.0" />
  </Dependencies>

  <Resources>
    <Resource Language="ja-jp" />
    <Resource Language="en-us" />
  </Resources>

  <Applications>
    <Application Id="App" Executable="seatxray.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements
        DisplayName="SeatXray"
        Description="航空便座席マップ解析ツール"
        BackgroundColor="transparent"
        Square150x150Logo="Assets\Square150x150Logo.png"
        Square44x44Logo="Assets\Square44x44Logo.png">
        <uap:DefaultTile Wide310x150Logo="Assets\Wide310x150Logo.png" Square310x310Logo="Assets\Square310x310Logo.png" />
        <uap:SplashScreen Image="Assets\SplashScreen.png" />
      </uap:VisualElements>
    </Application>
  </Applications>

  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>

</Package>
"@
$manifestContent | Set-Content "$buildDir\AppxManifest.xml" -Encoding UTF8
Write-Host "Manifest created." -ForegroundColor Green


# 3. Find MakeAppx
Write-Host "Locating MakeAppx..." -ForegroundColor Yellow
$kitsRoot = "C:\Program Files (x86)\Windows Kits\10\bin"
$makeappx = Get-ChildItem -Path $kitsRoot -Filter "makeappx.exe" -Recurse -ErrorAction SilentlyContinue | 
Where-Object { $_.FullName -like "*x64*" } | 
Select-Object -First 1

if (-not $makeappx) {
  Write-Error "MakeAppx.exe not found in Windows Kits."
}

# 4. Prepare Assets
Write-Host "Preparing Assets..." -ForegroundColor Yellow
$assetsDir = "$buildDir\Assets"
if (-not (Test-Path $assetsDir)) { New-Item -ItemType Directory -Path $assetsDir | Out-Null }

# Copy/Resize icons (Simple copy for now)
$requiredAssets = @("StoreLogo.png", "Square150x150Logo.png", "Square44x44Logo.png", "Square310x310Logo.png", "Wide310x150Logo.png", "SplashScreen.png")

foreach ($asset in $requiredAssets) {
  Copy-Item $sourceIcon -Destination "$assetsDir\$asset" -Force
}
Write-Host "Assets generated from $sourceIcon" -ForegroundColor Green

# 5. Pack
Write-Host "Packaging MSIX..." -ForegroundColor Yellow
if (Test-Path $targetMsix) { Remove-Item $targetMsix }

& $makeappx.FullName pack /d "$buildDir" /p "$targetMsix" /o
if ($LASTEXITCODE -ne 0) { throw "MakeAppx failed." }

Write-Host "Package created: $targetMsix" -ForegroundColor Green

# 6. Sign using SignTool (Integrated)
Write-Host "Signing..." -ForegroundColor Yellow

# Find SignTool
$signtool = Get-ChildItem -Path $kitsRoot -Filter "signtool.exe" -Recurse -ErrorAction SilentlyContinue | 
Where-Object { $_.FullName -like "*x64*" } | 
Select-Object -First 1

if (-not $signtool) {
  Write-Error "SignTool.exe not found in Windows Kits."
}

# Check/Create PFX
if (-not (Test-Path $pfxPath)) {
  Write-Host "Creating Self-Signed Certificate..." -ForegroundColor Cyan
  # Ensure Cert provider is available
  if (-not (Get-PSDrive Cert -ErrorAction SilentlyContinue)) {
    New-PSDrive -Name Cert -PSProvider Certificate -Root \ | Out-Null
  }
  $cert = New-SelfSignedCertificate -Type Custom -Subject $publisher -KeyUsage DigitalSignature -FriendlyName "SeatXray Dev Key" -CertStoreLocation "Cert:\CurrentUser\My" -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
  $securePass = ConvertTo-SecureString -String $certPassword -Force -AsPlainText
  Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $securePass | Out-Null
  Write-Host "Certificate created: $pfxPath" -ForegroundColor Green
}
else {
  Write-Host "Using existing certificate: $pfxPath" -ForegroundColor Gray
}

# Sign command
& $signtool.FullName sign /fd SHA256 /a /f "$pfxPath" /p "$certPassword" "$targetMsix"

if ($LASTEXITCODE -eq 0) {
  Write-Host "SUCCESS: MSIX Signed Successfully!" -ForegroundColor Green
}
else {
  throw "Signing Failed."
}

Write-Host "`n=== DONE! ===" -ForegroundColor Cyan
Write-Host "Install by double-clicking: $targetMsix"
