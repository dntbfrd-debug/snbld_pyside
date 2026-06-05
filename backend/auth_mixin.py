import logging
import os
import sys
import time
import json
import threading
import webbrowser

from PySide6.QtCore import Slot, Signal

from backend.logger_manager import get_logger
from constants import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SELECTEL_ACCESS_KEY, SELECTEL_SECRET_KEY

logger = get_logger('backend')


def _sanitize_error(msg):
    if not msg:
        return ""
    sanitized = msg.replace("\n", " ").replace("\r", " ").strip()
    if len(sanitized) > 200:
        sanitized = sanitized[:200] + "..."
    return sanitized


class AuthMixin:

    activationResult = Signal(str, str)  # status, message ("success"/"error", details)
    def _check_activation_on_startup(self):
        logger.info("[AUTH] Проверка активации...")
        from auth import load_session, check_session, check_key, load_key_from_file, save_key_to_file, get_hwid

        session_data = load_session()
        if session_data and 'session_id' in session_data:
            logger.info(f"[AUTH] Сессия найдена: {session_data['session_id'][:16]}...")
            valid, session_info = check_session(session_data['session_id'])
            if valid and session_info:
                if session_info.get('blocked'):
                    logger.warning(f"[AUTH] Сессия ЗАБЛОКИРОВАНА! Причина: {_sanitize_error(session_info.get('error', ''))}")
                    self._is_activated = False
                    self._activation_status = "error"
                    self._subscription_info = {'blocked': True, 'error': session_info.get('error', '')}
                    self.activationStatusChanged.emit()
                    self.subscriptionChanged.emit()
                    return
                self._activation_key = session_data.get('key', '')
                if self._activation_key:
                    save_key_to_file(self._activation_key)
                key_valid, key_info = check_key(self._activation_key, hwid=get_hwid()) if self._activation_key else (False, None)
                if key_info:
                    logger.info(f"[AUTH] check_key: valid={key_valid}, blocked={key_info.get('blocked')}, error={_sanitize_error(key_info.get('error', ''))}")
                    if key_info.get('blocked') or (not key_valid and 'соединен' not in _sanitize_error(key_info.get('error', '')).lower() and 'таймаут' not in _sanitize_error(key_info.get('error', '')).lower()):
                        reason = _sanitize_error(key_info.get('error', 'Ключ заблокирован или недействителен'))
                        logger.warning(f"[AUTH] Ключ ЗАБЛОКИРОВАН/НЕДЕЙСТВИТЕЛЕН! Причина: {reason}")
                        self._is_activated = False
                        self._activation_status = "error"
                        self._subscription_info = {'blocked': True, 'error': reason}
                        self.activationStatusChanged.emit()
                        self.subscriptionChanged.emit()
                        return
                self._is_activated = True
                self._activation_status = "ok"
                self._subscription_info = {
                    'valid': True,
                    'key_type': session_info.get('key_type', ''),
                    'expires_at': session_info.get('expires_at', ''),
                }
                logger.info("[AUTH] Программа активирована (сессия валидна, ключ подтверждён)")
                self.activationStatusChanged.emit()
                self.subscriptionChanged.emit()
                self._start_heartbeat()
                self._load_server_tokens()
                return

        file_key = load_key_from_file()
        if file_key:
            self._activation_key = file_key
            logger.info(f"[AUTH] Ключ найден в файле: {file_key[:4]}...{file_key[-4:]}")

        if self._activation_key:
            hwid = get_hwid()
            valid, key_data = check_key(self._activation_key, hwid=hwid)
            logger.info(f"[AUTH] check_key результат: valid={valid}, data={key_data}")
            is_blocked = key_data.get('blocked', False)
            if valid:
                server_activated = key_data.get('activated', False)
                if is_blocked:
                    logger.warning(f"[AUTH] Ключ ЗАБЛОКИРОВАН! Причина: {_sanitize_error(key_data.get('error', ''))}")
                    self._is_activated = False
                    self._activation_status = "error"
                    self._subscription_info = {'blocked': True, 'error': key_data.get('error', '')}
                    self.activationStatusChanged.emit()
                    self.subscriptionChanged.emit()
                    return
                if not server_activated:
                    logger.warning("[AUTH] Ключ не активирован на сервере, активирую...")
                    from auth import activate_key
                    success, act_data = activate_key(self._activation_key)
                    if success:
                        valid, key_data = check_key(self._activation_key, hwid=hwid)
                        is_blocked = key_data.get('blocked', False)
                        if is_blocked:
                            logger.warning(f"[AUTH] Ключ остаётся заблокированным после активации")
                            self._is_activated = False
                            self._activation_status = "error"
                            self.activationStatusChanged.emit()
                            self.subscriptionChanged.emit()
                            return
                self._is_activated = True
                self._activation_status = "ok"
                self._subscription_info = {
                    'valid': True,
                    'key_type': key_data.get('key_type', ''),
                    'expires_at': key_data.get('expires_at', ''),
                }
                logger.info("[AUTH] Программа активирована (ключ валиден)")
                self.activationStatusChanged.emit()
                self.subscriptionChanged.emit()
                save_key_to_file(self._activation_key)
                self._start_heartbeat()
                self._load_server_tokens()
                return

        self._is_activated = False
        self._activation_status = "error"
        self._subscription_info = {'valid': False}
        self.activationStatusChanged.emit()
        logger.warning("[AUTH] Ключ не найден, программа не активирована")

    def _start_heartbeat(self):
        from auth import HeartbeatManager, load_session

        session_data = load_session()
        if session_data and 'session_id' in session_data:
            self._heartbeat_manager = HeartbeatManager(check_interval=300)
            self._heartbeat_manager.start(session_data['session_id'])
            # QTimer должен быть создан на главном потоке
            if threading.current_thread() is not threading.main_thread():
                self.createHeartbeatTimerRequested.emit()
            else:
                self._createHeartbeatTimer()
            logger.info("[AUTH] Heartbeat запущен (интервал: 5 мин)")
        else:
            logger.warning("[AUTH] Сессия не найдена, heartbeat НЕ запущен")

    def _createHeartbeatTimer(self):
        """Создаёт QTimer для heartbeat (должен быть на главном потоке)."""
        from PySide6.QtCore import QTimer
        if not hasattr(self, '_heartbeat_timer'):
            self._heartbeat_timer = None
        if self._heartbeat_timer:
            self._heartbeat_timer.stop()
        self._heartbeat_timer = QTimer()
        self._heartbeat_timer.timeout.connect(self._check_heartbeat)
        self._heartbeat_timer.start(300000)

    def _load_server_tokens(self):
        from auth import get_server_tokens, load_session
        session_data = load_session()
        session_id = session_data.get('session_id') if session_data else None
        key = self._activation_key
        result = get_server_tokens(session_id=session_id, key=key)
        if result and 'tokens' in result:
            self._secrets.update(result['tokens'])
            logger.info(f"[AUTH] Загружено {len(result['tokens'])} токенов с сервера")
        else:
            logger.warning("[AUTH] Не удалось загрузить токены с сервера")

    def _check_heartbeat(self):
        logger.debug(f"[AUTH] _check_heartbeat вызван, manager={self._heartbeat_manager}")
        if not self._heartbeat_manager:
            return
        logger.info("[AUTH] Выполняю проверку heartbeat...")
        valid, data = self._heartbeat_manager.check()
        logger.info(f"[AUTH] check_session: valid={valid}, data={data}")
        if not valid and data and 'Session not found' in data.get('error', ''):
            logger.info("[AUTH] Сессия не найдена, проверяю ключ напрямую...")
            from auth import check_key, get_hwid
            if self._activation_key:
                hwid = get_hwid()
                valid, data = check_key(self._activation_key, hwid=hwid)
                logger.info(f"[AUTH] check_key: valid={valid}, data={data}")

        if valid and data:
            is_blocked = data.get('blocked', False)
            if not is_blocked:
                error_msg = data.get('error', '')
                if error_msg:
                    error_lower = error_msg.lower()
                    is_blocked = any(w in error_lower for w in ['blocked', 'disabled', 'inactive', 'no longer active', 'expired', 'not found'])
            if is_blocked:
                logger.warning(f"[AUTH] Ключ заблокирован! Причина: {_sanitize_error(data.get('error', ''))}")
                self._is_activated = False
                self._subscription_info = {}
                self.activationStatusChanged.emit()
                self.subscriptionChanged.emit()
                self.stop_all_macros()
                self.notification.emit("Ключ заблокирован! Обратитесь в поддержку.", "warning")
            else:
                logger.debug("[AUTH] Heartbeat OK")
        elif not valid:
            error_msg = _sanitize_error(data.get('error', '') if data else 'Нет данных')
            logger.warning(f"[AUTH] Ключ НЕВАЛИДЕН! Причина: {error_msg}")
            self._is_activated = False
            self._subscription_info = {}
            self.activationStatusChanged.emit()
            self.subscriptionChanged.emit()
            self.stop_all_macros()
            self.notification.emit("Подписка истекла или заблокирована!", "warning")

    def get_secret(self, key: str) -> str:
        if key in self._secrets:
            return self._secrets[key]
        if key == "TELEGRAM_BOT_TOKEN":
            return TELEGRAM_BOT_TOKEN
        if key == "TELEGRAM_CHAT_ID":
            return TELEGRAM_CHAT_ID
        if key == "SELECTEL_ACCESS_KEY":
            return SELECTEL_ACCESS_KEY
        if key == "SELECTEL_SECRET_KEY":
            return SELECTEL_SECRET_KEY
        return ""

    @Slot(str)
    def activateWithKey(self, key):
        """Запускает активацию в фоновом потоке, UI не блокируется.
        Результат возвращается через сигнал activationResult."""
        key_stripped = key.strip()
        logger.info(f"[AUTH] Запрос асинхронной активации по ключу: {key_stripped[:4]}...{key_stripped[-4:] if len(key_stripped) > 4 else ''}")

        def _activate_worker():
            from auth import activate_key, save_key_to_file
            try:
                success, data = activate_key(key_stripped)
                if success:
                    saved = save_key_to_file(key_stripped)
                    if saved:
                        logger.info(f"[AUTH] Ключ сохранён локально: {key_stripped[:4]}...{key_stripped[-4:]}")
                    else:
                        logger.error("[AUTH] КРИТИЧЕСКАЯ ОШИБКА: Не удалось сохранить ключ!")
                    self._activation_key = key_stripped
                    self._is_activated = True
                    self._subscription_info = {
                        'valid': True,
                        'key_type': data.get('key_type', 'unknown'),
                        'expires_at': data.get('expires_at', '')
                    }
                    self._start_heartbeat()
                    self._load_server_tokens()
                    self.activationStatusChanged.emit()
                    self.subscriptionChanged.emit()
                    logger.info(f"[AUTH] Программа активирована! Тип: {data.get('key_type')}, До: {data.get('expires_at')}")
                    self.activationResult.emit("success", "Программа активирована!")
                else:
                    error_msg = _sanitize_error(data.get('error', 'Неизвестная ошибка'))
                    logger.error(f"[AUTH] Ошибка активации: {error_msg}")
                    self.activationResult.emit("error", error_msg)
            except Exception as e:
                logger.error(f"[AUTH] Критическая ошибка при активации: {e}", exc_info=True)
                self.activationResult.emit("error", str(e))

        threading.Thread(target=_activate_worker, daemon=True, name="ActivateKey").start()

    @Slot(result=str)
    def getHwid(self):
        from auth import get_hwid
        return get_hwid()

    def _get_current_version(self):
        try:
            from constants import CURRENT_VERSION
            return CURRENT_VERSION
        except Exception:
            return "1.0.0"

    def _check_updates_and_notify(self):
        try:
            import requests
            from packaging import version
            version_url = "https://snbld.ru/version.json"
            resp = requests.get(version_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                current = self._get_current_version()
                latest = data.get('latest_version', '0.0.0')
                try:
                    is_available = version.parse(latest) > version.parse(current)
                except Exception:
                    is_available = latest != current
                if is_available:
                    logger.info(f"[UPDATE] Доступно обновление: {current} -> {latest}")
                    self.updateAvailable.emit(data)
                    self.notification.emit(f"Доступно обновление: {latest}\nПерейдите в Диагностика → Обновления", "info")
        except Exception as e:
            logger.debug(f"[UPDATE] Ошибка проверки обновлений: {e}")

    @Slot(str, str)
    def download_update_async(self, download_url, version, expected_checksum=""):
        if not download_url or not version:
            return
        def download_worker():
            try:
                import hashlib
                import requests
                updates_dir = os.path.join(self.app_dir, 'updates')
                os.makedirs(updates_dir, exist_ok=True)
                filename = f"update_{version}.zip"
                filepath = os.path.join(updates_dir, filename)
                if expected_checksum and os.path.exists(filepath) and os.path.getsize(filepath) > 1_000_000:
                    sha256 = hashlib.sha256()
                    with open(filepath, 'rb') as f:
                        for chunk in iter(lambda: f.read(65536), b''):
                            sha256.update(chunk)
                    if sha256.hexdigest() == expected_checksum:
                        logger.info(f"[UPDATE] Обновление уже загружено и проверено: {filepath}")
                        self.updateDownloadComplete.emit(filepath, version)
                        return
                    else:
                        logger.warning(f"[UPDATE] Кэшированный файл не совпадает по checksum, перезагрузка")
                        os.remove(filepath)

                logger.info(f"[UPDATE] Загрузка обновления: {download_url}")
                self.updateDownloadProgress.emit(0, 0)
                resp = requests.get(download_url, timeout=300, stream=True)
                resp.raise_for_status()
                total_size = int(resp.headers.get('content-length', 0))
                downloaded = 0

                tmp_path = filepath + ".tmp"
                sha256 = hashlib.sha256()
                with open(tmp_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            sha256.update(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                self.updateDownloadProgress.emit(downloaded, total_size)

                if expected_checksum:
                    actual_checksum = sha256.hexdigest()
                    if actual_checksum != expected_checksum:
                        logger.error(f"[UPDATE] Контрольная сумма не совпадает! Ожидалось: {expected_checksum}, получено: {actual_checksum}")
                        self.notification.emit("Ошибка: файл обновления повреждён (checksum mismatch)", "error")
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                        return

                file_size = os.path.getsize(tmp_path)
                if file_size < 1_000_000:
                    logger.error(f"[UPDATE] Загруженный файл слишком мал: {file_size} байт")
                    self.notification.emit("Ошибка загрузки: файл повреждён", "error")
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    return

                os.replace(tmp_path, filepath)
                logger.info(f"[UPDATE] Обновление загружено и проверено: {filepath} ({file_size / 1_000_000:.1f}MB)")
                self.updateDownloadProgress.emit(file_size, file_size)
                self.updateDownloadComplete.emit(filepath, version)
            except Exception as e:
                logger.error(f"[UPDATE] Ошибка загрузки обновления: {e}")
                self.notification.emit(f"Ошибка загрузки: {e}", "error")
        threading.Thread(target=download_worker, daemon=True).start()

    @Slot(str, str)
    def install_update(self, update_zip_path, version):
        import subprocess
        if not getattr(sys, 'frozen', False):
            logger.info(f"[UPDATE] Режим разработки — обновление не устанавливается автоматически")
            self.notification.emit("Режим разработки: скачайте обновление вручную из Диагностика → Обновления", "info")
            return
        if not os.path.exists(update_zip_path):
            logger.error(f"[UPDATE] ZIP обновления не найден: {update_zip_path}")
            self.notification.emit("Файл обновления не найден", "error")
            return
        install_dir = _get_app_dir()
        updater_path = os.path.join(install_dir, 'updater.exe')
        if not os.path.exists(updater_path):
            logger.error(f"[UPDATE] updater.exe не найден: {updater_path}")
            self.notification.emit("updater.exe не найден. Обновите вручную.", "error")
            return
        logger.info(f"[UPDATE] Запуск updater.exe: {update_zip_path} → {version}")
        self.notification.emit(f"Установка обновления {version}...", "info")
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            [updater_path, update_zip_path, version],
            cwd=install_dir,
            creationflags=CREATE_NO_WINDOW,
            close_fds=True
        )
        logger.info("[UPDATE] Закрытие программы для установки обновления")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, lambda: self.closeRequested.emit())

    def _is_program_activated(self):
        return self._is_activated

    @Slot()
    def bind_computer(self):
        import auth
        hwid = auth.get_hwid()
        webbrowser.open(f"https://t.me/snbld_bot?start=bind_{hwid}")

    @Slot()
    def buy_subscription(self):
        webbrowser.open("https://boosty.to/snbld")

    @Slot(str)
    def activateProgram(self, key):
        """Асинхронная активация (теперь через сигнал activationResult)."""
        self.activateWithKey(key)

    @Slot(result=bool)
    def isProgramActivated(self):
        return self._is_program_activated()

    @Slot(result='QVariant')
    def getActivationStatus(self):
        from auth import load_session, load_key_from_file, get_hwid, check_subscription_by_hwid
        session = load_session()
        hwid = get_hwid()
        sub_status = check_subscription_by_hwid(hwid)
        return {
            'activated': self._is_activated,
            'has_session': session is not None,
            'session_id': session.get('session_id') if session else None,
            'hwid': hwid,
            'subscription': sub_status
        }

    @Slot()
    def openActivationPage(self):
        self.pageChangeRequested.emit("ActivationPage")
