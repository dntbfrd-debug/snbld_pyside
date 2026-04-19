# -*- coding: utf-8 -*-
"""
updater_main.py
Маленький апдейтер для snbld resvap
Заменяет файлы в папке установки и перезапускает программу
"""

import os
import sys
import time
import shutil
import subprocess
import zipfile


def log(msg):
    print(f"[UPDATER] {msg}")


def find_main_exe():
    """Находит основной EXE в папке установки"""
    updater_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Сначала ищем новое стандартное имя
    standard_path = os.path.join(updater_dir, 'snbld.exe')
    if os.path.exists(standard_path):
        return standard_path
    
    # Обратная совместимость со старыми версиями
    for f in os.listdir(updater_dir):
        if f.startswith('qml_main') and f.endswith('.exe') or f.startswith('snbld_qml_') and f.endswith('.exe'):
            return os.path.join(updater_dir, f)
    return None


def wait_for_process_close(exe_path, timeout=30):
    """Ждёт пока процесс закроется"""
    import psutil
    exe_name = os.path.basename(exe_path)

    for _ in range(timeout * 10):
        found = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == exe_name:
                found = True
                break
        if not found:
            return True
        time.sleep(0.1)

    # Принудительное закрытие
    try:
        subprocess.run(['taskkill', '/F', '/IM', exe_name],
                       capture_output=True, timeout=5)
    except Exception:
        pass
    return True


def apply_update(install_dir, update_zip_path):
    """Применяет обновление из ZIP"""
    log(f"Распаковка обновления: {update_zip_path}")

    with zipfile.ZipFile(update_zip_path, 'r') as zf:
        for item in zf.namelist():
            # Пропускаем activation.key
            if item == 'activation.key':
                continue

            # Пропускаем сам updater.exe
            if os.path.basename(item) == 'updater.exe':
                continue

            src = zf.read(item)
            dst = os.path.join(install_dir, item)

            # Создаём директории
            os.makedirs(os.path.dirname(dst), exist_ok=True)

            # Записываем файл
            with open(dst, 'wb') as f:
                f.write(src)
            log(f"  ✓ {item}")


def main():
    if len(sys.argv) < 3:
        log("Использование: updater.exe <update_zip_path> <version>")
        sys.exit(1)

    update_zip = sys.argv[1]
    new_version = sys.argv[2]

    install_dir = os.path.dirname(os.path.abspath(__file__))
    main_exe = find_main_exe()

    if not main_exe:
        log("❌ Основной EXE не найден!")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

    log(f"Папка установки: {install_dir}")
    log(f"Основной EXE: {os.path.basename(main_exe)}")
    log(f"Версия обновления: {new_version}")

    # Ждём закрытия основной программы
    log("Ожидание закрытия программы...")
    wait_for_process_close(main_exe, timeout=30)

    # Применяем обновление
    try:
        apply_update(install_dir, update_zip)
        log("✅ Обновление применено!")
    except Exception as e:
        log(f"❌ Ошибка применения: {e}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

    # Запускаем обновлённую программу
    log("Запуск обновлённой программы...")
    try:
        subprocess.Popen([main_exe], cwd=install_dir)
    except Exception as e:
        log(f"❌ Ошибка запуска: {e}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

    # Удаляем временные файлы
    time.sleep(2)
    try:
        if os.path.exists(update_zip):
            os.remove(update_zip)
            log(f"🗑️ Временный ZIP удалён")
    except Exception:
        pass

    log(f"🎉 Обновление до {new_version} завершено!")


if __name__ == "__main__":
    main()
