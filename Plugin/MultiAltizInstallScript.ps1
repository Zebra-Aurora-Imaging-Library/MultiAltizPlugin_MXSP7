# Check whether Python is installed by running the command "python --version".
$pythonVersionOutput = (python --version 2>&1)

if ($LASTEXITCODE -ne 0) {
    Write-Host "Python is not installed. Please install Python before running this script. Only Python 3.7. 3.9 and 3.11 are supported" -ForegroundColor Red
    Exit
}

# Check if python version is supported.
$pythonVersion = $pythonVersionOutput.Split()[1]

# Split the version into components
$versionParts = $pythonVersion -split '\.'
$major = [int]$versionParts[0]
$minor = [int]$versionParts[1]

# Only allow versions 3.7, 3.9, or 3.11
if ($major -eq 3 -and ($minor -eq 7 -or $minor -eq 9 -or $minor -eq 11)) {
    Write-Host "Python is installed. Version : $pythonVersion"
} else {
    Write-Host "Python is installed but is not one of the acceptable versions (3.7, 3.9, or 3.11). Please install a compatible version." -ForegroundColor Red
    Exit
}

# Check whether pip is installed by running the command "pip --version".
$pythonVersion = (pip --version 2>&1)

if ($LASTEXITCODE -eq 0) {
    Write-Host "pip is installed. Version : $pythonVersion"
} else {
    Write-Host "pip is not installed. Please install pip package before running this script." -ForegroundColor Red
    Exit
}

# Checking installation of the Python MIL package.
$packageCheckCommand = "python -m pip show mil"

$packageCheckOutput = Invoke-Expression $packageCheckCommand -ErrorAction SilentlyContinue

if (-not $packageCheckOutput) {
    Write-Host "The Python MIL package is not installed. Installation in progress..." -ForegroundColor DarkYellow

    # Installation du package Python avec pip
    $packageInstallCommand = "python -m pip install mil --no-index --find-links=""C:\Program Files\Matrox Imaging\MIL\Scripting\pythonwrapper\dist"""
    Invoke-Expression $packageInstallCommand
} else {
    Write-Host "The Python MIL package is already installed" -ForegroundColor Green
}

# Get script directory
$scriptDirectory = $PSScriptRoot

$sourceFolder = Join-Path -Path $scriptDirectory -ChildPath "multi_altiz"

$destinationFolder = "C:\ProgramData\Matrox Imaging\CaptureWorksPlugins"

# Check if destination folder exist
if (-not (Test-Path $destinationFolder -PathType Container)) {
    Write-Host "The destination folder does not exist. Folder creation..." -ForegroundColor Red
    New-Item -Path $destinationFolder -ItemType Directory | Out-Null
}

# Check if source folder exist
if (Test-Path $sourceFolder -PathType Container) {  
    Copy-Item $sourceFolder $destinationFolder -Recurse -Force
    Write-Host "The folder has been copied successfully."
} else {
    Write-Host "Source folder doesn't exist so it can't be copied." -ForegroundColor Red
}

