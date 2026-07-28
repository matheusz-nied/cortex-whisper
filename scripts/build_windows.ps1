$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

python scripts/collect_licenses.py
python -m PyInstaller --noconfirm --clean packaging/whisper-ditado.spec
python scripts/prune_qt_components.py dist/whisper-ditado

$Inno = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $Inno) {
    throw "Inno Setup was not found. Install it and run this script again."
}
& $Inno.Source packaging/windows/installer.iss
