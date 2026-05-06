#define AppName "AI Image Layer Extractor"
#define AppExeName "AIImageLayerExtractor"
#define AppVersion "0.1.0"
#define AppPublisher "Personal Tools"
#define AppDescription "AI image layer extraction desktop tool"
#define ProjectRoot "..\.."
#define DistDir ProjectRoot + "\dist\" + AppExeName
#define ReleaseDir ProjectRoot + "\release"

[Setup]
AppId={{9E5D061C-4F52-4B7F-B1DF-47F02B939A81}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#ReleaseDir}
OutputBaseFilename={#AppExeName}_Setup_{#AppVersion}_x64
SetupIconFile=..\assets\app_icon.ico
LicenseFile=..\assets\license.txt
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}.exe
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppDescription}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}.exe"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExeName}.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}.exe"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExeName}.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
