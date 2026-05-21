import os
import sys
import time
import subprocess
import zipfile
import tempfile


LOG_FILE = None


def log(msg):
    print(f"[UPDATER] {msg}")
    if LOG_FILE:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        except Exception:
            pass


def find_main_exe():
    updater_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    candidates = [
        os.path.join(updater_dir, "snbld.exe"),
    ]
    for f in os.listdir(updater_dir):
        if f.endswith(".exe") and (f.startswith("qml_main") or f.startswith("snbld_qml_")):
            candidates.append(os.path.join(updater_dir, f))
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def find_processes_by_name(exe_name):
    procs = []
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.strip('"').split('","')
            if len(parts) >= 2 and parts[0].strip('"').lower() == exe_name.lower():
                try:
                    procs.append(int(parts[1].strip('"')))
                except ValueError:
                    pass
    except Exception as e:
        log(f"Ошибка tasklist: {e}")
    return procs


def wait_for_process_close(exe_path, timeout=30):
    exe_name = os.path.basename(exe_path)
    log(f"Ожидание закрытия {exe_name} (до {timeout}с)...")
    for _ in range(timeout * 10):
        procs = find_processes_by_name(exe_name)
        if not procs:
            log(f"{exe_name} закрыт")
            return True
        time.sleep(0.1)
    log(f"Таймаут ожидания {exe_name}, принудительное завершение...")
    try:
        subprocess.run(["taskkill", "/F", "/IM", exe_name], capture_output=True, timeout=5)
        time.sleep(1)
    except Exception as e:
        log(f"Ошибка taskkill: {e}")
    return True


def extract_with_retry(zf, item, dst, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            src = zf.read(item)
            tmp = dst + ".tmp"
            with open(tmp, "wb") as f:
                f.write(src)
            os.replace(tmp, dst)
            return True
        except PermissionError:
            if attempt < retries - 1:
                log(f"   {item} заблокирован, повтор через {delay}с...")
                time.sleep(delay)
            else:
                log(f"   [X] {item} не удалось записать (заблокирован)")
                return False
        except Exception as e:
            log(f"   [X] {item}: {e}")
            return False
    return False


def apply_update(install_dir, update_zip_path):
    log(f"Распаковка обновления: {update_zip_path}")

    if not os.path.exists(update_zip_path):
        log(f"  [X] Файл обновления не найден: {update_zip_path}")
        return False

    try:
        with zipfile.ZipFile(update_zip_path, "r") as zf:
            items = [item for item in zf.namelist() if item not in ("activation.key",) and os.path.basename(item) != "updater.exe"]
            log(f"  Файлов в ZIP: {len(items)}")
            errors = 0
            for item in items:
                dst = os.path.join(install_dir, item)
                if not extract_with_retry(zf, item, dst):
                    errors += 1
            if errors:
                log(f"  [X] {errors} файлов не удалось обновить")
                return False
    except zipfile.BadZipFile:
        log(f"  [X] ZIP-файл повреждён")
        return False
    except Exception as e:
        log(f"  [X] Ошибка распаковки: {e}")
        return False

    log("  Обновление применено!")
    return True


def main():
    global LOG_FILE

    if len(sys.argv) < 3:
        log("Использование: updater.exe <update_zip_path> <version>")
        sys.exit(1)

    update_zip = sys.argv[1]
    new_version = sys.argv[2]
    install_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    LOG_FILE = os.path.join(install_dir, "updater.log")

    log(f"=== ОБНОВЛЕНИЕ ДО v{new_version} ===")
    log(f"Папка установки: {install_dir}")
    log(f"ZIP: {update_zip}")

    main_exe = find_main_exe()
    if not main_exe:
        log("  [X] ОСНОВНОЙ EXE НЕ НАЙДЕН!")
        sys.exit(1)

    log(f"Основной EXE: {os.path.basename(main_exe)}")

    wait_for_process_close(main_exe, timeout=30)

    if not apply_update(install_dir, update_zip):
        log("  [X] Обновление не удалось")
        sys.exit(1)

    log("Запуск обновлённой программы...")
    try:
        subprocess.Popen([main_exe], cwd=install_dir)
    except Exception as e:
        log(f"  [X] Ошибка запуска: {e}")
        sys.exit(1)

    time.sleep(2)
    try:
        if os.path.exists(update_zip):
            os.remove(update_zip)
    except Exception:
        pass

    log(f"=== ОБНОВЛЕНИЕ ДО v{new_version} ЗАВЕРШЕНО ===")


if __name__ == "__main__":
    main()
