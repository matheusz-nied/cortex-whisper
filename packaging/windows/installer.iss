#define MyAppName "Cortex Whisper"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#define MyAppPublisher "Matheus Fernandes da Silva"
#define MyAppExeName "cortex-whisper.exe"

[Setup]
AppId={{B7D20D6B-4368-4D44-9127-11904E17E4A6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Cortex Whisper
DefaultGroupName=Cortex Whisper
OutputDir=..\..\dist
OutputBaseFilename=Cortex-Whisper-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern
LicenseFile=..\..\LICENSE

[Files]
Source: "..\..\dist\cortex-whisper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\build\legal\BUNDLED_COMPONENTS.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\build\legal\NATIVE_COMPONENTS.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\build\legal\licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Cortex Whisper"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\Cortex Whisper"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "startup"; Description: "Start Cortex Whisper with Windows"; GroupDescription: "Startup:"; Flags: checkedonce

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "CortexWhisper"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: startup; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Cortex Whisper"; Flags: nowait postinstall skipifsilent
