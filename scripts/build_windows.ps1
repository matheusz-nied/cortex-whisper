$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir
$Version = python -c "import runpy; print(runpy.run_path('src/pulsar_whisper/metadata.py')['APP_VERSION'])"

python scripts/collect_licenses.py
python -m PyInstaller --noconfirm --clean packaging/pulsar-whisper.spec
python scripts/prune_qt_components.py dist/pulsar-whisper
python scripts/collect_native_notices.py `
    --analysis build/pulsar-whisper/Analysis-00.toc `
    --bundle dist/pulsar-whisper `
    --legal build/legal
Copy-Item -Path build/legal/* -Destination dist/pulsar-whisper/_internal/legal -Recurse -Force

$Inno = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $Inno) {
    throw "Inno Setup was not found. Install it and run this script again."
}
& $Inno.Source "/DMyAppVersion=$Version" packaging/windows/installer.iss
