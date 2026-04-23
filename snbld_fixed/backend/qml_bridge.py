"""
QML Bridge модуль - все методы которые вызываются напрямую из QML интерфейса.
Вынесено из qml_main.py для уменьшения размера основного файла.
ВСЕ МЕТОДЫ ОСТАЮТСЯ С ТЕМИ ЖЕ СИГНАТУРАМИ, ПОЛНАЯ ОБРАТНАЯ СОВМЕСТИМОСТЬ.
"""
import os
import time
import webbrowser
import zipfile
import io
import requests
from datetime import datetime
from PySide6.QtCore import Slot, QObject

from backend.logger_manager import get_logger

logger = get_logger('qml_bridge')


class QMLBridgeMixin:
    """Миксин класс для Backend с QML методами"""

    def _get_app_dir(self):
        """Возвращает путь к папке приложения"""
        import sys
        import os
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__ + "/.."))

    @Slot()
    def save_all_settings(self):
        """Сохраняет все настройки"""
        self.save_settings()
        self.notification.emit("Настройки сохранены", "success")

    @Slot(result=str)
    def get_current_version(self):
        """Возвращает текущую версию программы"""
        return self._get_current_version()

    @Slot(result='QVariant')
    def check_for_updates(self):
        """Проверяет доступность обновлений"""
        try:
            from packaging import version
            version_url = f"https://resvap.snbld.ru/version.json"
            resp = requests.get(version_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                current = self._get_current_version()
                latest = data.get('latest_version', '0.0.0')
                try:
                    is_available = version.parse(latest) > version.parse(current)
                except Exception:
                    is_available = latest != current
                return {
                    'success': True,
                    'available': is_available,
                    'latest_version': latest,
                    'download_url': data.get('download_url', ''),
                    'release_notes': data.get('release_notes', ''),
                    'checksum': data.get('checksum', ''),
                    'current_version': current
                }
            return {'success': False, 'error': 'Сервер не ответил'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @Slot(str)
    def open_url(self, url):
        """Открывает URL в браузере"""
        webbrowser.open(url)

    @Slot()
    def toggle_console(self):
        """Показывает/скрывает консоль (только в EXE)"""
        try:
            import ctypes
            SW_SHOW = 5
            SW_HIDE = 0
            kernel32 = ctypes.WinDLL('kernel32')
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                import win32gui
                if win32gui.IsWindowVisible(hwnd):
                    win32gui.ShowWindow(hwnd, SW_HIDE)
                    self._console_visible = False
                    self.consoleVisibilityChanged.emit()
                    self.notification.emit("Консоль скрыта", "info")
                else:
                    win32gui.ShowWindow(hwnd, SW_SHOW)
                    self._console_visible = True
                    self.consoleVisibilityChanged.emit()
                    self.notification.emit("Консоль показана", "info")
            else:
                self.notification.emit("Консоль не создана (собрано без консоли)", "warning")
        except Exception as e:
            self.notification.emit(f"Ошибка консоли: {e}", "error")

    @Slot()
    def send_logs_to_telegram(self):
        """Отправить логи в Telegram"""
        import logging
        _vlogger = logging.getLogger('debug')

        # Получаем токены из памяти (серверные) или из constants (fallback)
        TELEGRAM_TOKEN = self.get_secret('TELEGRAM_BOT_TOKEN')
        TELEGRAM_CHAT_ID = self.get_secret('TELEGRAM_CHAT_ID')

        _vlogger.info(f"[TELEGRAM] TOKEN={bool(TELEGRAM_TOKEN)}, CHAT_ID={bool(TELEGRAM_CHAT_ID)}")

        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            # Пробуем загрузить токены с сервера (даже без активации)
            from auth import get_server_tokens, load_session
            session_data = load_session()
            if session_data and session_data.get('session_id'):
                result = get_server_tokens(session_id=session_data['session_id'])
                if result and result.get('tokens'):
                    self._secrets = result['tokens']
                    TELEGRAM_TOKEN = self.get_secret('TELEGRAM_BOT_TOKEN')
                    TELEGRAM_CHAT_ID = self.get_secret('TELEGRAM_CHAT_ID')

            if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
                self.notification.emit("⚠ Токены Telegram недоступны", "warning")
                return

        # Логи ХРАНЯТСЯ РЯДОМ С EXE! Используем тот же путь что и logger_manager
        from backend.logger_manager import LoggerManager
        logs_dir = LoggerManager._log_dir
        
        if not os.path.exists(logs_dir):
            try:
                os.makedirs(logs_dir, exist_ok=True)
                _vlogger.info(f"Создана папка логов: {logs_dir}")
            except Exception as e:
                self.notification.emit(f"Не удалось создать папку логов: {e}", "error")
                return

        # Собираем все файлы логов
        log_files = []
        for f in os.listdir(logs_dir):
            if f.endswith('.log'):
                log_files.append(os.path.join(logs_dir, f))

        if not log_files:
            self.notification.emit("Нет файлов логов для отправки", "warning")
            return

        # Создаём ZIP архив в памяти
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for log_file in log_files:
                filename = os.path.basename(log_file)
                zf.write(log_file, filename)

        zip_buffer.seek(0)

        # Отправляем в Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        files = {'document': ('snbld_logs.zip', zip_buffer, 'application/zip')}
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'caption': f"📋 Логи SNBLD от {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }

        try:
            response = requests.post(url, files=files, data=data, timeout=30)
            if response.status_code == 200:
                self.notification.emit("✓ Логи отправлены в Telegram", "success")
            else:
                self.notification.emit(f"Ошибка отправки: {response.status_code}", "error")
        except Exception as e:
            self.notification.emit(f"Ошибка: {str(e)}", "error")

    @Slot(str)
    def start_macro(self, name):
        """Запустить макрос через диспетчер"""
        for macro in self._macros:
            if macro.name == name:
                # Приоритет 5 (обычный) для ручного запуска
                if self.dispatcher.request_macro(macro, priority=5):
                    self._update_macros_dicts()
                    self.notification.emit(f"Макрос '{name}' запущен", "info")
                else:
                    self.notification.emit(f"Макрос '{name}': ЗАБЛОКИРОВАНО", "warning")
                break

    @Slot(str)
    def stop_macro(self, name):
        for macro in self._macros:
            if macro.name == name:
                macro.stop()
                self._update_macros_dicts()
                self.macroStatusChanged.emit()
                self.notification.emit(f"Макрос '{name}' остановлен", "info")
                break

    @Slot()
    def start_all_macros(self):
        """Запустить ВСЕ макросы - разблокировать горячие клавиши"""
        logger.info(f"[START_ALL] Начало запуска всех макросов, global_stopped={self._global_stopped}")
        
        # ✅ Защита от двойного нажатия и гонки состояний
        if not self._global_stopped:
            logger.debug("[START_ALL] Макросы уже запущены, игнорирую повторный вызов")
            return
            
        self._global_stopped = False
        self.globalStoppedChanged.emit()

        # ✅ ЗАПУСКАЕМ MouseClickMonitor (для зональных макросов)
        if self.mouse_click_monitor:
            if not self.mouse_click_monitor.isRunning():
                self.mouse_click_monitor.start()
                logger.info("[START_ALL] MouseClickMonitor запущен")
            else:
                logger.debug("[START_ALL] MouseClickMonitor уже работает")
                
        self.notification.emit("✅ Все макросы запущены", "success")
