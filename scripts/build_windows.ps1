$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

python -m PyInstaller --noconfirm --clean packaging/whisper-ditado.spec

$Inno = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $Inno) {
    throw "Inno Setup não encontrado. Instale-o e execute o script novamente."
}
& $Inno.Source packaging/windows/installer.iss

