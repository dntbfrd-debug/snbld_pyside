import os
import sys
import time
import subprocess
import zipfile


def log(msg):
    print(f"[UPDATER] {msg}")


def find_main_exe():
    updater_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    standard_path = os.path.join(updater_dir, 'snbld.exe')
    if os.path.exists(standard_path):
        return standard_path

    for f in os.listdir(updater_dir):
        if f.startswith('qml_main') and f.endswith('.exe') or f.startswith('snbld_qml_') and f.endswith('.exe'):
            return os.path.join(updater_dir, f)
    return None


def find_processes_by_name(exe_name):
    procs = []
    try:
        result = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {exe_name}', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = line.strip('"').split('","')
            if len(parts) >= 2 and parts[0].strip('"').lower() == exe_name.lower():
                try:
                    procs.append(int(parts[1].strip('"')))
                except ValueError:
                    pass
    except Exception:
        pass
    return procs


def wait_for_process_close(exe_path, timeout=30):
    exe_name = os.path.basename(exe_path)

    for _ in range(timeout * 10):
        procs = find_processes_by_name(exe_name)
        if not procs:
            return True
        time.sleep(0.1)

    try:
        subprocess.run(['taskkill', '/F', '/IM', exe_name],
                       capture_output=True, timeout=5)
    except Exception:
        pass
    return True


def apply_update(install_dir, update_zip_path):
    log(f"Распаковка обновления: {update_zip_path}")

    with zipfile.ZipFile(update_zip_path, 'r') as zf:
        for item in zf.namelist():
            if item == 'activation.key':
                continue

            if os.path.basename(item) == 'updater.exe':
                continue

            src = zf.read(item)
            dst = os.path.join(install_dir, item)

            os.makedirs(os.path.dirname(dst), exist_ok=True)

            with open(dst, 'wb') as f:
                f.write(src)
            log(f"   {item}")


def main():
    if len(sys.argv) < 3:
        log("Использование: updater.exe <update_zip_path> <version>")
        sys.exit(1)

    update_zip = sys.argv[1]
    new_version = sys.argv[2]

    install_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    main_exe = find_main_exe()

    if not main_exe:
        log(" ОСНОВНОЙ EXE НЕ НАЙДЕН!")
        sys.exit(1)

    log(f"Папка установки: {install_dir}")
    log(f"Основной EXE: {os.path.basename(main_exe)}")
    log(f"Версия обновления: {new_version}")

    log("Ожидание закрытия программы...")
    wait_for_process_close(main_exe, timeout=30)

    try:
        apply_update(install_dir, update_zip)
        log(" Обновление применено!")
    except Exception as e:
        log(f" Ошибка применения: {e}")
        sys.exit(1)

    log("Запуск обновлённой программы...")
    try:
        subprocess.Popen([main_exe], cwd=install_dir)
    except Exception as e:
        log(f" Ошибка запуска: {e}")
        sys.exit(1)

    time.sleep(2)
    try:
        if os.path.exists(update_zip):
            os.remove(update_zip)
            log(f" Временный ZIP удалён")
    except Exception:
        pass

    log(f" Обновление до {new_version} завершено!")


if __name__ == "__main__":
    main()
