[Setup]
AppId={{8F2C8E5A-1B3D-4E6F-9A7C-0D1E2F3A4B5C}}
AppName=snbld resvap
AppVersion=1.4.0
AppVerName=snbld resvap v1.4.0
AppPublisher=snbld
AppPublisherURL=https://snbld.ru
AppSupportURL=https://snbld.ru
AppUpdatesURL=https://snbld.ru
DefaultDirName={pf}\snbld_resvap
DirExistsWarning=no
DefaultGroupName=snbld resvap
AllowNoIcons=yes
OutputDir=dist_installers
OutputBaseFilename=snbld_resvap_v1.4.0_setup
SetupIconFile=123.ico
UninstallDisplayIcon={app}\qml_main.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120,120
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardImageFile=C:\Users\dntbf\AppData\Local\Programs\Inno Setup 6\WizClassicImage-IS.bmp
WizardSmallImageFile=C:\Users\dntbf\AppData\Local\Programs\Inno Setup 6\WizClassicSmallImage-IS.bmp

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"; Flags: checkedonce

[Files]
Source: "dist_standalone\qml_main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist_standalone\qml_main.dist\123.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\snbld resvap"; Filename: "{app}\qml_main.exe"; WorkingDir: "{app}"; IconFilename: "{app}\123.ico"
Name: "{group}\{cm:UninstallProgram,snbld resvap}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\snbld resvap"; Filename: "{app}\qml_main.exe"; WorkingDir: "{app}"; IconFilename: "{app}\123.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\qml_main.exe"; Description: "Запустить snbld resvap"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  SourceKey, DestKey: String;
begin
  if CurStep = ssPostInstall then
  begin
    SourceKey := ExpandConstant('{src}\activation.key');
    DestKey := ExpandConstant('{app}\activation.key');
    if FileExists(SourceKey) then
    begin
      if FileCopy(SourceKey, DestKey, False) then
        Log('Ключ скопирован в папку установки');
    end;
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
