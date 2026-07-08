[Setup]
AppName=DupeClear Pro
AppVersion=1.0.0
AppPublisher=DupeClear
AppPublisherURL=https://dupeclearpro.com
DefaultDirName={autopf}\DupeClear Pro
DefaultGroupName=DupeClear Pro
OutputBaseFilename=DupeClearPro_Setup_v1.0.0
OutputDir=installer\output
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\DupeClearPro.exe
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "..\dist\DupeClearPro.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DupeClear Pro"; Filename: "{app}\DupeClearPro.exe"
Name: "{autodesktop}\DupeClear Pro"; Filename: "{app}\DupeClearPro.exe"

[Run]
Filename: "{app}\DupeClearPro.exe"; Description: "Launch DupeClear Pro"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\DupeClearPro"
