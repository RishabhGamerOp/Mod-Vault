[Setup]
AppId={{A3D89E71-5E21-4B12-9A2E-88F3C7E1B0A1}
AppName=ModVault
AppVersion=1.0.0
AppPublisher=ModVault Team
DefaultDirName={autopf}\ModVault
DefaultGroupName=ModVault
UninstallDisplayIcon={app}\ModVault.exe
OutputDir=Output
OutputBaseFilename=ModVault_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\ModVault\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\ModVault"; Filename: "{app}\ModVault.exe"
Name: "{autodesktop}\ModVault"; Filename: "{app}\ModVault.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ModVault.exe"; Description: "Launch ModVault"; Flags: nowait postinstall skipifsilent