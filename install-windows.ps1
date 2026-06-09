$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoOwner = "lmaertin"
$RepoName = "python-pooldose"
$RepoRef = if ($env:POOLDOSE_REPO_REF) { $env:POOLDOSE_REPO_REF } else { "main" }
$ArchiveUrl = "https://github.com/$RepoOwner/$RepoName/archive/refs/heads/$RepoRef.zip"

$DefaultInstallRoot = Join-Path $env:LOCALAPPDATA "python-pooldose"
$InstallRoot = if ($env:POOLDOSE_INSTALL_ROOT) {
    $env:POOLDOSE_INSTALL_ROOT
} else {
    $DefaultInstallRoot
}
$SourceDir = Join-Path $InstallRoot "source"
$VenvDir = Join-Path $InstallRoot ".venv"
$DefaultLauncherPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "PoolDose.cmd"
$LauncherPath = if ($env:POOLDOSE_LAUNCHER_PATH) {
    $env:POOLDOSE_LAUNCHER_PATH
} else {
    $DefaultLauncherPath
}

function Show-PythonInstallInstructions {
    Write-Host "Python 3.11+ was not found in PATH." -ForegroundColor Yellow
    Write-Host "Install Python first, then run this installer again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 1 (recommended):" -ForegroundColor Cyan
    Write-Host "  Download from https://www.python.org/downloads/windows/"
    Write-Host "  During setup, enable: Add python.exe to PATH"
    Write-Host ""
    Write-Host "Option 2 (winget):" -ForegroundColor Cyan
    Write-Host "  winget install -e --id Python.Python.3.13"
}

function Get-PythonRunner {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return {
            param([string[]]$PythonArgs)
            & python @PythonArgs
        }
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        return {
            param([string[]]$PythonArgs)
            & py -3 @PythonArgs
        }
    }

    return $null
}

function New-Launcher {
    param(
        [string]$TargetPath,
        [string]$VirtualEnvPath
    )

    $launcherDir = Split-Path -Path $TargetPath -Parent
    if (-not (Test-Path -Path $launcherDir)) {
        New-Item -ItemType Directory -Path $launcherDir | Out-Null
    }

    $launcherContent = @"
@echo off
setlocal
set "VENV_DIR=$VirtualEnvPath"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo python-pooldose is not installed yet.
    echo Please run install-windows.ps1 again.
    pause
    exit /b 1
)

if not "%~1"=="" (
    "%VENV_DIR%\Scripts\python.exe" -m pooldose %*
    exit /b %errorlevel%
)

echo python-pooldose launcher
echo.
echo 1^) Connect to a device
echo 2^) Analyze a device
echo 3^) Use a mock JSON file
echo 4^) Show help
echo.
set /p choice=Choose an option [1-4]: 

if "%choice%"=="1" goto connect
if "%choice%"=="2" goto analyze
if "%choice%"=="3" goto mock
if "%choice%"=="4" goto help

echo Unknown option: %choice%
pause
exit /b 1

:connect
set /p host=Device IP address or hostname [kommspot]: 
if "%host%"=="" set "host=kommspot"
set "sslArg="
set /p sslReply=Use HTTPS? [y/N]: 
if /I "%sslReply%"=="y" set "sslArg=--ssl"
if /I "%sslReply%"=="yes" set "sslArg=--ssl"
set "portArg="
set /p port=Custom port (optional): 
if not "%port%"=="" set "portArg=--port \"%port%\""
"%VENV_DIR%\Scripts\python.exe" -m pooldose --host "%host%" %sslArg% %portArg%
pause
exit /b %errorlevel%

:analyze
set /p host=Device IP address or hostname [kommspot]: 
if "%host%"=="" set "host=kommspot"
set "sslArg="
set /p sslReply=Use HTTPS? [y/N]: 
if /I "%sslReply%"=="y" set "sslArg=--ssl"
if /I "%sslReply%"=="yes" set "sslArg=--ssl"
set "portArg="
set /p port=Custom port (optional): 
if not "%port%"=="" set "portArg=--port \"%port%\""
set "analyzeArg=--analyze"
set /p allWidgets=Include hidden widgets? [y/N]: 
if /I "%allWidgets%"=="y" set "analyzeArg=--analyze-all"
if /I "%allWidgets%"=="yes" set "analyzeArg=--analyze-all"
"%VENV_DIR%\Scripts\python.exe" -m pooldose --host "%host%" %sslArg% %portArg% %analyzeArg%
pause
exit /b %errorlevel%

:mock
set /p mockPath=Path to mock JSON file: 
if "%mockPath%"=="" (
    echo A JSON file path is required.
    pause
    exit /b 1
)
"%VENV_DIR%\Scripts\python.exe" -m pooldose --mock "%mockPath%"
pause
exit /b %errorlevel%

:help
"%VENV_DIR%\Scripts\python.exe" -m pooldose --help
pause
exit /b %errorlevel%
"@

    Set-Content -Path $TargetPath -Value $launcherContent -Encoding Ascii
}

$runPython = Get-PythonRunner
if (-not $runPython) {
    Show-PythonInstallInstructions
    exit 1
}

$workDir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString())
$archivePath = Join-Path $workDir "source.zip"

try {
    New-Item -ItemType Directory -Path $workDir | Out-Null

    Write-Host "Downloading latest source from GitHub..."
    Invoke-WebRequest -Uri $ArchiveUrl -OutFile $archivePath

    Write-Host "Preparing installation directories..."
    New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
    if (Test-Path -Path $SourceDir) {
        Remove-Item -Path $SourceDir -Recurse -Force
    }

    Write-Host "Extracting source archive..."
    Expand-Archive -Path $archivePath -DestinationPath $workDir -Force
    $extractedDir = Get-ChildItem -Path $workDir -Directory |
        Where-Object { $_.Name -like "$RepoName-*" } |
        Select-Object -First 1

    if (-not $extractedDir) {
        throw "Could not detect extracted source directory."
    }

    Move-Item -Path $extractedDir.FullName -Destination $SourceDir -Force

    Write-Host "Creating virtual environment..."
    & $runPython @("-m", "venv", $VenvDir)

    Write-Host "Installing python-pooldose..."
    & "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
    & "$VenvDir\Scripts\python.exe" -m pip install --upgrade $SourceDir

    Write-Host "Creating launcher..."
    New-Launcher -TargetPath $LauncherPath -VirtualEnvPath $VenvDir

    Write-Host ""
    Write-Host "Installation completed."
    Write-Host "Source: $SourceDir"
    Write-Host "Launcher: $LauncherPath"
    Write-Host ""
    Write-Host "Network access hint:"
    Write-Host "  If Windows Firewall prompts for Python/Terminal network access, click Allow."
    Write-Host ""
    Write-Host "You can now double-click the launcher or run:"
    Write-Host "  $LauncherPath"
}
finally {
    if (Test-Path -Path $workDir) {
        Remove-Item -Path $workDir -Recurse -Force
    }
}
