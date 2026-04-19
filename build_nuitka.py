# -*- coding: utf-8 -*-
"""
build_nuitka.py - Build snbld resvap with Nuitka (Standalone mode)
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

BUILD_DIR = Path("dist_standalone")
VERSION = "1.4.0"

def get_base_dir():
    return Path(__file__).parent

def check_required_files(base_dir):
    print("\n[1/5] Проверка обязательных файлов...")
    required = ["qml_main.py", "qml", "icons", "123.ico"]
    all_ok = True
    for f in required:
        path = base_dir / f
        status = "[OK]" if path.exists() else "[X]"
        print(f"   {status} {f}")
        if not path.exists():
            all_ok = False
    return all_ok

def build_nuitka(base_dir):
    print("\n[2/5] Сборка Nuitka (standalone, ~5-10 минут)...")

    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",  # Single exe file - properly sets sys.frozen and sys._MEIPASS
        f"--output-dir={BUILD_DIR}",
        "--windows-console-mode=hide",
        "--windows-icon-from-ico=123.ico",
        "--enable-plugin=pyside6",
        "--lto=yes",
        "--python-flag=no_site",
        "--quiet",
        "--follow-imports",
        "--include-module=ssl",
        "--include-module=cryptography",
        "--include-qt-plugins=sensible,styles,platforms,imageformats,qml,multimedia",
        "--noinclude-dlls=*webengine*",
        "qml_main.py",
    ]

    python_modules = [
        "macros_core", "tesseract_reader", "threads",
        "skill_database", "low_level_hook", "constants",
        "auth", "utils_qml", "tooltips_qml", "macros",
    ]
    for mod in python_modules:
        cmd.append(f"--include-module={mod}")

    internal_dirs = ["icons", "qml", "tesseract", "profiles"]
    for d in internal_dirs:
        if (base_dir / d).exists():
            cmd.append(f"--include-data-dir={d}={d}")

    root_files = [
        "123.ico", "12.mp4", "logo.png", "asgard_skills.json",
        "app.manifest", "version.json", "qtquickcontrols2.conf",
        "macros_core.py",  # Include macros_core.py (renamed from _macros_original.py)
    ]
    for f in root_files:
        if (base_dir / f).exists():
            cmd.append(f"--include-data-file={f}={f}")

    for d in ["backend", "utils", "macros"]:
        for root, dirs, files in os.walk(d):
            for file in files:
                if file.endswith(".py"):
                    module_path = os.path.join(root, file).replace(os.sep, ".")[:-3]
                    cmd.append(f"--include-module={module_path}")

    print(f"   Команда: {' '.join(cmd[:12])}...")
    print(f"   Всего аргументов: {len(cmd)}")

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=str(base_dir)
    )
    out, _ = proc.communicate(timeout=900)
    print(out)

    if proc.returncode != 0:
        print(f"\n[X] Ошибка сборки: код {proc.returncode}")
        return False
    return True

def create_helper_files(base_dir):
    print("\n[3/5] Создание вспомогательных файлов...")

    # Support both onefile (single exe) and non-onefile (dist folder) modes
    onefile_exe = BUILD_DIR / "qml_main.exe"
    dist_exe = BUILD_DIR / "qml_main.dist" / "qml_main.exe"
    
    exe_path = onefile_exe if onefile_exe.exists() else dist_exe
    
    if not exe_path.exists():
        print("   [X] EXE не найден!")
        return False

    size_mb = exe_path.stat().st_size / 1024 / 1024
    print(f"   [OK] qml_main.exe - {size_mb:.1f} MB")

    # Для onefile - ничего не нужно. Для не-onefile - создаём пустой settings.json
    if not onefile_exe.exists():
        # Создать пустой settings.json для портативного режима (не для onefile)
        import json
        settings_path = BUILD_DIR / "qml_main.dist" / "settings.json"
        
        # Удалить старый settings.json если есть (с настройками пользователя)
        if settings_path.exists():
            settings_path.unlink()
        
        # Создать пустой
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2)
        print("   [OK] settings.json создан (пустой)")

        run_bat = BUILD_DIR / "run.bat"
        run_bat.write_text(
            '@echo off\ncd /d "%~dp0qml_main.dist"\nstart qml_main.exe\n',
            encoding="utf-8"
        )
        print("   [OK] run.bat создан")
    else:
        print("   [INFO] Onefile mode - run.bat не требуется")
        
    return True

def get_inno_setup_path():
    """Находит путь к Inno Setup"""
    possible_paths = [
        Path(r"C:\Users\dntbf\AppData\Local\Programs\Inno Setup 6"),
        Path(r"C:\Program Files (x86)\Inno Setup 6"),
        Path(r"C:\Program Files\Inno Setup 6"),
    ]
    for path in possible_paths:
        if path.exists() and (path / "ISCC.exe").exists():
            return path
    return None

def build_installer(base_dir):
    print("\n[4/5] Подготовка Inno Installer...")

    inno_path = get_inno_setup_path()
    if inno_path:
        wizard_image = str(inno_path / "WizClassicImage-IS.bmp")
        wizard_small = str(inno_path / "WizClassicSmallImage-IS.bmp")
    else:
        wizard_image = r"{pf}\Inno Setup 6\WizModernImage-IS.bmp"
        wizard_small = r"{pf}\Inno Setup 6\WizClassicSmallImage-IS.bmp"

    # Check which mode we're in (onefile or not)
    onefile_exe = BUILD_DIR / "qml_main.exe"
    is_onefile = onefile_exe.exists()
    
    if is_onefile:
        files_section = r'Source: "dist_standalone\qml_main.exe"; DestDir: "{app}"; Flags: ignoreversion' + '\n' + r'Source: "dist_standalone\qml_main.dist\123.ico"; DestDir: "{app}"; Flags: ignoreversion'
    else:
        files_section = r'Source: "dist_standalone\qml_main.dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion'

    iss_content = """[Setup]
AppId={{8F2C8E5A-1B3D-4E6F-9A7C-0D1E2F3A4B5C}}
AppName=snbld resvap
AppVersion=VERSION
AppVerName=snbld resvap vVERSION
AppPublisher=snbld
AppPublisherURL=https://snbld.ru
AppSupportURL=https://snbld.ru
AppUpdatesURL=https://snbld.ru
DefaultDirName={pf}\\snbld_resvap
DirExistsWarning=no
DefaultGroupName=snbld resvap
AllowNoIcons=yes
OutputDir=dist_installers
OutputBaseFilename=snbld_resvap_vVERSION_setup
SetupIconFile=123.ico
UninstallDisplayIcon={app}\\qml_main.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120,120
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardImageFile=WIZIMAGE
WizardSmallImageFile=WIZSMALL

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"; Flags: checkedonce

[Files]
FILESECTION

[Icons]
Name: "{group}\\snbld resvap"; Filename: "{app}\\qml_main.exe"; WorkingDir: "{app}"; IconFilename: "{app}\\123.ico"
Name: "{group}\\{cm:UninstallProgram,snbld resvap}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\snbld resvap"; Filename: "{app}\\qml_main.exe"; WorkingDir: "{app}"; IconFilename: "{app}\\123.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\\qml_main.exe"; Description: "Запустить snbld resvap"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  SourceKey, DestKey: String;
begin
  if CurStep = ssPostInstall then
  begin
    SourceKey := ExpandConstant('{src}\\activation.key');
    DestKey := ExpandConstant('{app}\\activation.key');
    if FileExists(SourceKey) then
    begin
      if FileCopy(SourceKey, DestKey, False) then
        Log('Ключ скопирован в папку установки');
    end;
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
"""
    iss_content = iss_content.replace("VERSION", VERSION)
    iss_content = iss_content.replace("WIZIMAGE", wizard_image)
    iss_content = iss_content.replace("WIZSMALL", wizard_small)
    # activation.key добавляется сервером в ZIP (рядом с setup.exe)
    iss_content = iss_content.replace("FILESECTION", files_section)

    iss_file = base_dir / "snbld_resvap.iss"
    iss_file.write_text(iss_content, encoding="utf-8")
    print(f"   [OK] snbld_resvap.iss создан (mode: {'onefile' if is_onefile else 'standalone'})")
    print(f"   [INFO] Для сборки запустите: iscc.exe snbld_resvap.iss")
    return True
    return True

def print_summary():
    print("\n" + "=" * 50)
    print(f"СБОРКА ЗАВЕРШЕНА v{VERSION}")
    print("=" * 50)
    print("\n[5/5] Результат:")
    print(f"   Папка: {BUILD_DIR}/")
    print("   - qml_main.dist/qml_main.exe  (запуск)")
    print("   - qml_main.dist/ (все DLL внутри)")
    print("   - run.bat               (ярлык)")
    print(f"   - snbld_resvap.iss      (Inno Setup)")
    print("\n[СЛЕДУЮЩИЙ ШАГ] Сборка Inno Installer:")
    print("   iscc.exe snbld_resvap.iss")

def main():
    base_dir = get_base_dir()
    os.chdir(base_dir)

    print("=" * 50)
    print(f"СБОРКА SNBLD RESVAP v{VERSION} (Standalone)")
    print("=" * 50)

    if BUILD_DIR.exists():
        print(f"\n[DEL] Удаление старой сборки {BUILD_DIR}...")
        shutil.rmtree(BUILD_DIR)

    if not check_required_files(base_dir):
        print("\n[X] Отсутствуют обязательные файлы!")
        return 1

    if not build_nuitka(base_dir):
        return 1

    if not create_helper_files(base_dir):
        return 1

    if not build_installer(base_dir):
        return 1

    print_summary()
    return 0

if __name__ == "__main__":
    sys.exit(main())