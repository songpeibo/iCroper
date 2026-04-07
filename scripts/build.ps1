param(
    [switch]$OneFile,
    [switch]$Clean = $true,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

Write-Host "[iCroper] Project root: $projectRoot"
Write-Host "[iCroper] Python command: $Python"

$pythonCmd = Get-Command $Python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    throw "Python command not found: $Python"
}

# Ensure PyInstaller is available
& $Python -c "import importlib.util,sys;sys.exit(0 if importlib.util.find_spec('PyInstaller') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[iCroper] Installing PyInstaller..."
    & $Python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install PyInstaller."
    }
}

# Ensure runtime dependencies are available in the same interpreter
if (Test-Path "requirements.txt") {
    Write-Host "[iCroper] Installing project requirements..."
    & $Python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install project requirements."
    }
}

if ($Clean) {
    Write-Host "[iCroper] Cleaning build/dist folders..."
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
    if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
}

$mode = if ($OneFile) { "onefile" } else { "onedir" }
Write-Host "[iCroper] Package mode: $mode"
$iconPath = Join-Path $projectRoot "logo.ico"

$pyiArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--windowed",
    "--clean",
    "--name", "iCroper",
    "--collect-submodules", "PySide6.QtSvg",
    "--collect-binaries", "cv2",
    "--add-data", "ui;ui",
    "--add-data", "config;config",
    "--add-data", "core;core",
    "--add-data", "resources;resources"
)

if (Test-Path $iconPath) {
    $pyiArgs += @("--add-data", "logo.ico;.")
    $pyiArgs += @("--icon", $iconPath)
    Write-Host "[iCroper] Using icon: $iconPath"
}

if ($OneFile) {
    $pyiArgs += "--onefile"
} else {
    $pyiArgs += "--onedir"
}

$pyiArgs += "main.py"

Write-Host "[iCroper] Running: $Python $($pyiArgs -join ' ')"
& $Python @pyiArgs

if ($LASTEXITCODE -ne 0) {
    throw "Build failed with exit code: $LASTEXITCODE"
}

if ($OneFile) {
    Write-Host "[iCroper] Build complete: dist/iCroper.exe"
} else {
    Write-Host "[iCroper] Build complete: dist/iCroper/"
}
