# LAKI V6 - one interactive launcher (no ADB / flash actions).
$ErrorActionPreference = 'Stop'
$kit = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Write-Host 'LAKI Hybrid V6 FULL AUDIO by DarkoBG - one-step OFFLINE builder' -ForegroundColor Cyan
Write-Host 'Sources: X96 Max Plus 5 ATV 9.20 + Magicsee N5 Max X3 152F ATV 9.20'
Write-Host 'Android model: m6cw4k; brand: LAKI; build: LAKI Hybrid V6 FULL AUDIO by DarkoBG'
Write-Host 'Does NOT flash hardware. A specific V6 image was tested 9/9 on one modified LAKI; new builds require their own verification.' -ForegroundColor Yellow
$x96 = (Read-Host 'Full path to original X96 IMG').Trim('"')
$magic = (Read-Host 'Full path to original Magicsee IMG').Trim('"')
$packer = (Read-Host 'AmlImagePack.exe path [Enter = C:\AmlogicKitchen\bin\windows\AmlImagePack.exe]').Trim('"')
if ([string]::IsNullOrWhiteSpace($packer)) { $packer = 'C:\AmlogicKitchen\bin\windows\AmlImagePack.exe' }
$out = (Read-Host 'NEW output folder [Enter = C:\LakiBox-Backup\LAKI-V6-BUILD]').Trim('"')
if ([string]::IsNullOrWhiteSpace($out)) { $out = 'C:\LakiBox-Backup\LAKI-V6-BUILD' }
if (Test-Path -LiteralPath $out) {
    $base = $out
    do { $out = "$base-RETRY-$([guid]::NewGuid().ToString('N').Substring(0,8))" }
    while (Test-Path -LiteralPath $out)
    Write-Host "Existing output kept. Using a NEW directory: $out" -ForegroundColor Yellow
}

$argsList = @('-3', (Join-Path $kit 'scripts\build_laki_v6.py'), '--x96-img', $x96,
              '--magicsee-img', $magic, '--packer', $packer, '--output-root', $out)
Write-Host "`n[1/2] Read-only preflight" -ForegroundColor Cyan
& py @argsList --check-only
if ($LASTEXITCODE -ne 0) { throw 'Preflight failed. No output created.' }
Write-Host "`nWARNING: FULL includes X96 bootloader and Do not assume new builds are hardware-tested or safe on factory-stock bootloaders." -ForegroundColor Yellow
$approval = Read-Host 'Type BUILD to create a new offline IMG (not to flash)'
if ($approval -cne 'BUILD') { Write-Host 'Cancelled; nothing built.'; exit 0 }
Write-Host "`n[2/2] Build, unpack and independently verify" -ForegroundColor Cyan
& py @argsList
if ($LASTEXITCODE -ne 0) { throw 'Build failed. Do not flash any partial files.' }
Write-Host "`nResult: $out" -ForegroundColor Green
