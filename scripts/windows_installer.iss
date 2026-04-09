#ifndef AppName
  #define AppName "ShiqiAutoWin"
#endif

#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

#ifndef ProjectRoot
  #define ProjectRoot ".."
#endif

[Setup]
AppId={{5A2EB8D2-81E7-4A0A-AB00-D43D2432744F}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={localappdata}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#ProjectRoot}\dist\installer
OutputBaseFilename={#AppName}-Setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#ProjectRoot}\dist\{#AppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppName}.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppName}.exe"

[Run]
Filename: "{app}\{#AppName}.exe"; Description: "启动 {#AppName}"; Flags: nowait postinstall skipifsilent
