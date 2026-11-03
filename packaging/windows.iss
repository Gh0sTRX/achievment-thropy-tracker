#define AppVersion "0.12.0"
[Setup]
AppId={{36A259D0-55AD-4B8F-83E4-D716F3955AAF}
AppName=Achievement Atlas
AppVersion={#AppVersion}
AppPublisher=Achievement Atlas Community
AppPublisherURL=https://github.com/Gh0sTRX/achievment-thropy-tracker
DefaultDirName={localappdata}\Programs\AchievementAtlas
DefaultGroupName=Achievement Atlas
PrivilegesRequired=lowest
AppMutex=Local\AchievementAtlas.Running
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installer
OutputBaseFilename=AchievementAtlas-0.12.0-Windows-x64-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=..\LICENSE
InfoBeforeFile=..\KURULUM.txt
UninstallDisplayIcon={app}\AchievementAtlas.exe
SetupIconFile=..\assets\achievement-atlas.ico
[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Kısayollar:"
[Files]
Source: "..\dist\AchievementAtlas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\KURULUM.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\PUBLIC_PROFILES_TR.md"; DestDir: "{app}\docs"; Flags: ignoreversion
[Icons]
Name: "{group}\Achievement Atlas"; Filename: "{app}\AchievementAtlas.exe"
Name: "{group}\Kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Achievement Atlas"; Filename: "{app}\AchievementAtlas.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\AchievementAtlas.exe"; Description: "Achievement Atlas'ı başlat"; Flags: nowait postinstall skipifsilent
