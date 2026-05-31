import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

from utils.wizard_bmp import generate_dark_wizard_bmp

BUILD_DIR = Path("dist_standalone")
VERSION = "1.3.56"

def get_base_dir():
    return Path(__file__).parent

def check_required_files(base_dir):
    print("\n[1/5] Проверка обязательных файлов...")
    required = ["run.pyw", "qml_main.py", "qml", "icons", "123.ico", "asgard_skills.json"]
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

    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    jobs = max(1, cpu_count - 1)
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        f"--output-dir={BUILD_DIR}",
        f"--jobs={jobs}",
        "--windows-console-mode=disable",
        "--windows-icon-from-ico=123.ico",
        "--enable-plugin=pyside6",
        "--lto=yes",
        "--no-prefer-source",
        "--python-flag=-O",
        "--python-flag=no_site",
        "--remove-output",
        "--no-deployment-flag=self-execution",
        "--follow-imports",
        "--include-module=ssl",
        "--include-module=cryptography",
        f"--include-qt-plugins=sensible,styles,platforms,imageformats,qml,multimedia",
        "--noinclude-dlls=*webengine*",
        "qml_main.py",
    ]

    python_modules = [
        "macros_core", "tesseract_reader", "threads",
        "skill_database", "low_level_hook", "mouse_detector", "constants",
        "auth", "utils_qml", "tooltips_qml",
        "updater_main",
        "input_blocker",
        "backend.input_system", "backend.logger_manager",
        "backend.macros_dispatcher", "backend.qml_bridge",
        "backend.session_log",
        "backend.settings_manager",
        "backend.window_manager",
        "backend.keyboard_shim",
        "backend.win32_api",
        "backend.auth_mixin",
        "backend.macro_mixin",
        "backend.ocr_mixin",
        "backend.castbar_mixin",
        "backend.window_mixin",
        "backend.settings_mixin",
        "backend.hooks_guard",
        "backend.attach_thread",
        "utils.file_utils",
        "utils.resource_utils", "utils.sound_alert", "utils.tray_icon",
        "macros.steps_executor",
    ]
    for mod in python_modules:
        cmd.append(f"--include-module={mod}")

    internal_dirs = ["icons", "qml", "fonts", "profiles"]
    for d in internal_dirs:
        if (base_dir / d).exists():
            cmd.append(f"--include-data-dir={d}={d}")

    tesseract_dir = base_dir / "tesseract"
    if tesseract_dir.exists():
        for root, dirs, files in os.walk(tesseract_dir):
            rel_root = os.path.relpath(root, base_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(rel_root, file)
                cmd.append(f"--include-data-file={src_file}={dest_file}")

    root_files = [
        "123.ico", "logo.png", "asgard_skills.json",
        "version.json", "qtquickcontrols2.conf",
        "macros.json", "requirements.txt",
        "12.mp4",
        "onn.mp3", "off.mp3"
    ]
    for f in root_files:
        if (base_dir / f).exists():
            cmd.append(f"--include-data-file={f}={f}")

    for d in ["backend", "utils", "macros"]:
        if (base_dir / d).exists():
            for root, dirs, files in os.walk(base_dir / d):
                for file in files:
                    if file.endswith(".py") and file != "__init__.py":
                        rel_path = os.path.relpath(os.path.join(root, file), base_dir)
                        module_path = rel_path.replace(os.sep, ".")[:-3]
                        if module_path not in python_modules:
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

    dist_exe = BUILD_DIR / "qml_main.dist" / "qml_main.exe"
    
    if not dist_exe.exists():
        print("   [X] EXE не найден в qml_main.dist!")
        return False

    size_mb = dist_exe.stat().st_size / 1024 / 1024
    print(f"   [OK] qml_main.exe - {size_mb:.1f} MB")

    dist_dir = BUILD_DIR / "qml_main.dist"
    
    print("\n   [ОЧИСТКА] Удаление исходного кода из билда...")
    py_count = 0
    for root, dirs, files in os.walk(dist_dir):
        for file in files:
            if file == "macros_core.py":
                continue
            if file.endswith(".py") or file.endswith(".pyc") or file.endswith(".pyo"):
                file_path = Path(root) / file
                try:
                    file_path.unlink()
                    py_count += 1
                except Exception as e:
                    print(f"    Не удалось удалить {file}: {e}")
    print(f"   [OK] Удалено исходных файлов: {py_count}")
    print("   [OK] macros_core.py СОХРАНЁН!")
    
    print("\n   [ОЧИСТКА DLL] Удаление неиспользуемых Qt DLL...")
    dll_remove_patterns = [
        "*qt6quick3d*",
        "*qt63d*",
        "*qt6datavisualization*",
        "*qt6charts*",
        "*qt6location*",
        "*qt6virtualkeyboard*",
        "*qt6remoteobjects*",
        "*qt6scxml*",
        "*qt6texttospeech*",
        "*qt6sensors*",
        "*qt6spatialaudio*",
        "*qt6webchannel*",
        "*qt6webview*",
        "*qt6test*",
        "*qt6concurrent*",
    ]
    
    dll_removed = 0
    dll_saved_mb = 0
    for pattern in dll_remove_patterns:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                import fnmatch
                if fnmatch.fnmatch(file.lower(), pattern.lower()):
                    file_path = Path(root) / file
                    try:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        dll_removed += 1
                        dll_saved_mb += size / 1024 / 1024
                        print(f"    Удалён: {file} ({size/1024/1024:.1f} MB)")
                    except Exception as e:
                        print(f"    Не удалось удалить {file}: {e}")
    print(f"   [OK] Удалено DLL: {dll_removed} шт, сэкономлено ~{dll_saved_mb:.0f} MB")
    
    tess_doc = dist_dir / "tesseract" / "doc"
    if tess_doc.exists():
        try:
            shutil.rmtree(tess_doc)
            print("   [OK] Удалена tesseract/doc (документация)")
        except Exception as e:
            print(f"    Не удалось удалить tesseract/doc: {e}")
    
    pdf_ttf = dist_dir / "tesseract" / "tessdata" / "pdf.ttf"
    if pdf_ttf.exists():
        try:
            sz = pdf_ttf.stat().st_size
            pdf_ttf.unlink()
            print(f"   [OK] Удалён pdf.ttf ({sz/1024:.0f} KB)")
        except Exception as e:
            print(f"    Не удалось удалить pdf.ttf: {e}")

    import json
    sys.path.insert(0, str(base_dir))
    from backend.settings_manager import SettingsManager
    
    settings_path = BUILD_DIR / "qml_main.dist" / "settings.json"
    if settings_path.exists():
        settings_path.unlink()
    
    sm = SettingsManager()
    defaults = sm.DEFAULTS
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(defaults, f, indent=2, ensure_ascii=False)
    print("   [OK] settings.json создан (с настройками по умолчанию)")

    for folder_name in ["logs", "cache", "cache/icons"]:
        folder_path = BUILD_DIR / "qml_main.dist" / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"   [OK] Папка {folder_name} создана")

    run_bat = BUILD_DIR / "run.bat"
    run_bat.write_text(
        '@echo off\ncd /d "%~dp0qml_main.dist"\nstart qml_main.exe\n',
        encoding="utf-8"
    )
    print("   [OK] run.bat создан")
        
    return True

def get_inno_setup_path():
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

    wizard_image, wizard_small = generate_dark_wizard_bmp(base_dir, VERSION)
    if not wizard_image:
        inno_path = get_inno_setup_path()
        if inno_path:
            wizard_image = str(inno_path / "WizClassicImage-IS.bmp")
            wizard_small = str(inno_path / "WizClassicSmallImage-IS.bmp")
        else:
            wizard_image = r"{pf}\Inno Setup 6\WizClassicImage-IS.bmp"
            wizard_small = r"{pf}\Inno Setup 6\WizClassicSmallImage-IS.bmp"

    DATA_DIR = r"{localappdata}\snbld_resvap\data"
    DATA_EXE = DATA_DIR + r"\qml_main.exe"

    files_section = 'Source: "dist_standalone\\qml_main.dist\\*"; DestDir: "' + DATA_DIR + '"; Flags: recursesubdirs createallsubdirs ignoreversion'

    dirs_section = """[Dirs]
Name: "{app}\\logs"
Name: "{app}\\profiles"
"""

    iss_content = """[Setup]
AppId={{8F2C8E5A-1B3D-4E6F-9A7C-0D1E2F3A4B5C}}
AppName=snbld resvap
AppVersion=VERSION
AppVerName=snbld resvap vVERSION
AppPublisher=snbld
AppPublisherURL=https://snbld.ru
AppSupportURL=https://snbld.ru
AppUpdatesURL=https://snbld.ru
DefaultDirName={commonpf}\\snbld_resvap
DirExistsWarning=no
DefaultGroupName=snbld resvap
AllowNoIcons=yes
OutputDir=dist_installers
OutputBaseFilename=snbldsetup
SetupIconFile=123.ico
UninstallDisplayIcon=DATAEXE
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern dark includetitlebar
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

DIRS_SECTION

[Icons]
Name: "{app}\\snbld resvap"; Filename: "DATAEXE"; WorkingDir: "{app}"
Name: "{group}\\snbld resvap"; Filename: "DATAEXE"; WorkingDir: "{app}"
Name: "{group}\\{cm:UninstallProgram,snbld resvap}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\snbld resvap"; Filename: "DATAEXE"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\\snbld_resvap"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
Filename: "DATAEXE"; Description: "Запустить snbld resvap"; Flags: nowait postinstall skipifsilent runasoriginaluser; WorkingDir: "{app}"

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
      if CopyFile(SourceKey, DestKey, False) then
        Log('Ключ скопирован в папку установки');
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataPath: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    DataPath := ExpandConstant('{localappdata}\\snbld_resvap');
    if DirExists(DataPath) then
    begin
      if DelTree(DataPath, True, True, True) then
        Log('Данные приложения удалены: ' + DataPath)
      else
        Log('Ошибка удаления данных: ' + DataPath);
    end;
  end;
end;
"""
    data_exe = DATA_DIR + r"\qml_main.exe"
    iss_content = iss_content.replace("VERSION", VERSION)
    iss_content = iss_content.replace("WIZIMAGE", wizard_image)
    iss_content = iss_content.replace("WIZSMALL", wizard_small)
    iss_content = iss_content.replace("FILESECTION", files_section)
    iss_content = iss_content.replace("DIRS_SECTION", dirs_section)
    iss_content = iss_content.replace("DATAEXE", data_exe)

    iss_file = base_dir / "snbld_resvap.iss"
    iss_file.write_text(iss_content, encoding="utf-8")
    print(f"   [OK] snbld_resvap.iss создан")

    if os.environ.get("SNBLD_SKIP_ISCC") == "1":
        print("   [SKIP] SNBLD_SKIP_ISCC=1, пропуск компиляции ISCC")
        return True

    iscc = shutil.which("ISCC.exe")
    if not iscc:
        iscc = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if not os.path.exists(iscc):
        print(f"   [X] ISCC.exe не найден: {iscc}")
        print(f"   [INFO] Запустите вручную: iscc.exe snbld_resvap.iss")
        return True

    dist_installers = base_dir / "dist_installers"
    if dist_installers.exists():
        for f in dist_installers.iterdir():
            if f.suffix == ".exe":
                try:
                    f.unlink()
                    print(f"   [DEL] {f.name} (старый установщик)")
                except Exception as e:
                    print(f"   [WARN] Не удалось удалить {f.name}: {e}")

    print(f"   [5/5] Компиляция Inno Setup...")
    for attempt in range(1, 4):
        proc = subprocess.Popen(
            [iscc, "snbld_resvap.iss"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, cwd=str(base_dir)
        )
        out, _ = proc.communicate(timeout=300)
        print(out)

        if proc.returncode == 0:
            break

        if attempt < 3:
            print(f"   [RETRY] Попытка {attempt} не удалась, жду 3с...")
            time.sleep(3)
    else:
        print(f"\n[X] Ошибка ISCC после 3 попыток")
        return False

    print(f"   [OK] Установщик собран")
    return True

def build_updater(base_dir):
    print("\n[EXTRA] Сборка updater.exe...")
    dist_updater = Path("dist_updater")
    if dist_updater.exists():
        shutil.rmtree(dist_updater)

    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--windows-console-mode=disable",
        f"--output-dir={dist_updater}",
        "updater_main.py",
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=str(base_dir)
    )
    out, _ = proc.communicate(timeout=600)
    print(out)

    if proc.returncode != 0:
        print(f"\n[X] Ошибка сборки updater.exe: код {proc.returncode}")
        return False

    updater_exe = dist_updater / "updater_main.exe"
    if updater_exe.exists():
        dest = BUILD_DIR / "qml_main.dist" / "updater.exe"
        shutil.copy(str(updater_exe), str(dest))
        size_mb = dest.stat().st_size / 1024 / 1024
        print(f"   [OK] updater.exe скопирован в qml_main.dist ({size_mb:.1f} MB)")
        return True
    print("   [X] updater_main.exe не найден в dist_updater!")
    return False


def print_summary():
    print("\n" + "=" * 50)
    print(f"СБОРКА ЗАВЕРШЕНА v{VERSION}")
    print("=" * 50)
    print("\n[5/5] Результат:")
    print(f"   Папка: {BUILD_DIR}/")
    print("   - qml_main.dist/qml_main.exe  (запуск)")
    print("   - qml_main.dist/updater.exe    (автообновление)")
    print("   - qml_main.dist/ (все DLL внутри)")
    print("   - run.bat               (ярлык)")
    print(f"   - snbld_resvap.iss      (Inno Setup)")
    print(f"   - dist_installers/snbldsetup.exe  (установщик)")

def main():
    base_dir = get_base_dir()
    os.chdir(base_dir)

    print("=" * 50)
    print(f"СБОРКА SNBLD RESVAP v{VERSION} (Standalone)")
    print("=" * 50)

    update_zip = base_dir / "update.zip"
    if update_zip.exists():
        update_zip.unlink()
        print(f"\n[DEL] {update_zip.name} (старый архив обновления)")

    build_artifacts = [BUILD_DIR, Path("dist_updater"), Path("qml_main.build"), Path(".nuitka")]
    for artifact in build_artifacts:
        if artifact.exists():
            print(f"\n[DEL] Удаление {artifact}...")
            try:
                shutil.rmtree(artifact)
            except PermissionError:
                print(f"   [WARN] {artifact} заблокирован, пробую убить qml_main.exe...")
                subprocess.run(['taskkill', '/F', '/IM', 'qml_main.exe'], capture_output=True)
                time.sleep(2)
                try:
                    shutil.rmtree(artifact)
                except:
                    print(f"   [WARN] Ручное удаление {artifact} требуется. Закройте приложение и удалите папку вручную.")
                    return 1

    if not check_required_files(base_dir):
        print("\n[X] Отсутствуют обязательные файлы!")
        return 1

    if not build_nuitka(base_dir):
        return 1

    if not create_helper_files(base_dir):
        return 1

    if not build_updater(base_dir):
        return 1

    if not build_installer(base_dir):
        return 1

    print_summary()
    return 0

if __name__ == "__main__":
    sys.exit(main())