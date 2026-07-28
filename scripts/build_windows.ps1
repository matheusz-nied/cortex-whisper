$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

python scripts/collect_licenses.py
python -m PyInstaller --noconfirm --clean packaging/whisper-ditado.spec
python scripts/prune_qt_components.py dist/whisper-ditado
python scripts/collect_native_notices.py `
    --analysis build/whisper-ditado/Analysis-00.toc `
    --bundle dist/whisper-ditado `
    --legal build/legal
Copy-Item -Path build/legal/* -Destination dist/whisper-ditado/_internal/legal -Recurse -Force

$Inno = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $Inno) {
    throw "Inno Setup was not found. Install it and run this script again."
}
& $Inno.Source packaging/windows/installer.iss
