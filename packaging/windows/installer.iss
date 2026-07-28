#define MyAppName "Whisper Ditado"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Whisper Ditado"
#define MyAppExeName "whisper-ditado.exe"

[Setup]
AppId={{B7D20D6B-4368-4D44-9127-11904E17E4A6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Whisper Ditado
DefaultGroupName=Whisper Ditado
OutputDir=..\..\dist
OutputBaseFilename=Whisper-Ditado-Setup-2.0.0
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern

[Files]
Source: "..\..\dist\whisper-ditado\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Whisper Ditado"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\Whisper Ditado"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "startup"; Description: "Start Whisper Ditado with Windows"; GroupDescription: "Startup:"; Flags: checkedonce

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "WhisperDitado"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: startup; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Whisper Ditado"; Flags: nowait postinstall skipifsilent
