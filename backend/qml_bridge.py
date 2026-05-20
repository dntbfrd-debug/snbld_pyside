import os
import sys
import time
import hashlib
import webbrowser
import zipfile
import io
import requests
from datetime import datetime
from PySide6.QtCore import Slot

from backend.logger_manager import get_logger
from threads import MouseClickMonitor

logger = get_logger('qml_bridge')


class QMLBridgeMixin:

    def _get_app_dir(self):
        if getattr(sys, 'frozen', False):
            return sys.path[0] if hasattr(sys, 'path') and sys.path else os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @Slot()
    def save_all_settings(self):
        self.save_settings()
        self.notification.emit("Настройки сохранены", "success")

    @Slot(result=str)
    def get_current_version(self):
        return self._get_current_version()

    @Slot(result='QVariant')
    def check_for_updates(self):
        try:
            from packaging import version
            version_url = "https://snbld.ru/version.json"
            resp = requests.get(version_url, timeout=3, verify=True)
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
                    'download_url': data.get('download_zip_url', data.get('download_url', '')),
                    'release_notes': data.get('release_notes', ''),
                    'checksum': data.get('checksum', ''),
                    'current_version': current
                }
            return {'success': False, 'error': 'Сервер не ответил'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @Slot(str)
    def open_url(self, url):
        webbrowser.open(url)
        
    @property
    def window_manager_skip_activation(self):
        return self._settings.get('window_manager_skip_activation', True)

    @Slot(bool)
    def set_window_manager_skip_activation(self, value: bool):
        self._settings['window_manager_skip_activation'] = value
        self.save_settings()
        
        try:
            from backend.window_manager import WindowManager
            wm = WindowManager()
            wm.skip_window_activation = value
        except Exception as e:
            logger.warning(f"[SKIP_ACTIVATION] Не удалось синхронизировать с WindowManager: {e}")
            
        self.settingsChanged.emit()
        
        self.notification.emit(
            f"Активация окна: {'ОТКЛЮЧЕНА' if value else 'ВКЛЮЧЕНА'}", 
            "info"
        )

    @Slot(bool)
    def set_window_message_input(self, value: bool):
        self._settings['use_window_message_input'] = value
        self.save_settings()
        
        try:
            from backend.window_manager import WindowManager
            wm = WindowManager()
            wm.use_window_message_input = value
        except Exception as e:
            logger.warning(f"[WINDOW_INPUT] Не удалось синхронизировать с WindowManager: {e}")
            
        self.settingsChanged.emit()
        
        self.notification.emit(
            f"Режим отправки ввода: {'Напрямую в окно' if value else 'Стандартный'}", 
            "info"
        )

    @Slot(result='QVariant')
    def get_window_manager_diagnostic(self):
        try:
            from backend.window_manager import get_window_manager
            wm = get_window_manager()
            return wm.get_diagnostic_info()
        except Exception as e:
            return {
                'monitors_count': 1,
                'current_dpi': 96,
                'monitor_left': 0,
                'monitor_top': 0,
                'monitor_right': 1920,
                'monitor_bottom': 1080,
                'foreground_title': '',
                'target_title': self._settings.get('target_window_title', ''),
                'last_activation': 0
            }



    @Slot()
    def send_logs_to_telegram(self):
        if getattr(self, '_is_sending_logs', False):
            self.notification.emit("Логи уже отправляются...", "info")
            return

        self._is_sending_logs = True
        self.logSendStatusChanged.emit()
        self.notification.emit("Подготовка логов...", "info")

        import threading
        threading.Thread(target=self._send_logs_worker, daemon=True, name="LogSender").start()

    def _send_logs_worker(self):
        """Асинхронная отправка логов в фоновом потоке."""
        import logging
        _vlogger = logging.getLogger('debug')

        try:
            from backend.logger_manager import LoggerManager
            logs_dir = LoggerManager._log_dir

            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir, exist_ok=True)

            log_files = []
            for f in os.listdir(logs_dir):
                if f.endswith('.log'):
                    log_files.append(os.path.join(logs_dir, f))

            if not log_files:
                self._finish_log_send(False, "Нет файлов логов для отправки")
                return

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for log_file in log_files:
                    filename = os.path.basename(log_file)
                    zf.write(log_file, filename)

                key_hash = hashlib.sha256((self._activation_key or "").encode()).hexdigest()[:8]
                metadata = {
                    "version": self._get_current_version(),
                    "timestamp": datetime.now().isoformat(),
                    "hwid": "",
                    "user_key": key_hash,
                    "is_activated": self._is_activated
                }

                try:
                    from auth import get_hwid
                    metadata['hwid'] = get_hwid()
                except Exception as ex:
                    logger.debug(f"Failed to get HWID for logs: {ex}")

                import json
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))

            zip_buffer.seek(0)

            temp_zip_path = os.path.join(self._get_app_dir(), f"logs_{int(time.time())}.zip")
            with open(temp_zip_path, 'wb') as f:
                f.write(zip_buffer.getvalue())

            url = "https://snbld.ru/upload_logs.php"

            key_hash = hashlib.sha256((self._activation_key or "").encode()).hexdigest()[:8]
            data = {
                "user_key": key_hash,
                "version": self._get_current_version()
            }

            try:
                with open(temp_zip_path, 'rb') as log_file:
                    files = {'log_file': log_file}
                    response = requests.post(url, files=files, data=data, timeout=30)

                if response.status_code == 200:
                    self._finish_log_send(True, "Логи успешно отправлены разработчику")
                else:
                    self._finish_log_send(False, f"Ошибка сервера: {response.status_code}")
            except Exception as e:
                self._finish_log_send(False, f"Ошибка отправки: {str(e)}")

            try:
                os.remove(temp_zip_path)
            except:
                pass

        except Exception as e:
            self._finish_log_send(False, f"Ошибка: {str(e)}")

    def _finish_log_send(self, success, message):
        """Завершение отправки логов (вызывается из фонового потока)."""
        self._is_sending_logs = False
        self.logSendStatusChanged.emit()
        if success:
            self.notification.emit(message, "success")
        else:
            self.notification.emit(message, "error" if "Ошибка" in message else "warning")

    @Slot(str)
    def start_macro(self, name):
        for macro in self._macros:
            if macro.name == name:
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
