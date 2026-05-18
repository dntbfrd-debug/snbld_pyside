import os
import sys
import re
import json
import io
import shutil
import subprocess
import threading
import warnings
import zipfile
from pathlib import Path
from datetime import date

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QCheckBox,
    QGroupBox, QMessageBox, QProgressBar,
)
from PySide6.QtCore import QProcess, QProcessEnvironment, Signal, Qt

BASE_DIR = Path(__file__).parent
BUILD_NUITKA = BASE_DIR / "build_nuitka.py"
VERSION_JSON = BASE_DIR / "version.json"
DIST_DIR = BASE_DIR / "dist_standalone" / "qml_main.dist"
DIST_INSTALLERS = BASE_DIR / "dist_installers"
ISS_FILE = BASE_DIR / "snbld_resvap.iss"
ENV_FILE = BASE_DIR / ".env"

BEGET_REMOTE = "/home/s/snbld/snbld.beget.tech/public_html"
CDN_BASE = "https://snbld.ru"


def read_current_version():
    text = BUILD_NUITKA.read_text("utf-8")
    m = re.search(r'^VERSION\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1) if m else "0.0.0"


def write_version(version):
    text = BUILD_NUITKA.read_text("utf-8")
    text = re.sub(
        r'^VERSION\s*=\s*"[^"]+"',
        f'VERSION = "{version}"',
        text, count=1, flags=re.MULTILINE
    )
    BUILD_NUITKA.write_text(text, "utf-8")


def bump_patch(version):
    parts = version.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def load_env():
    if not ENV_FILE.exists():
        return {}
    env = {}
    for line in ENV_FILE.read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env


def find_iscc():
    iscc = shutil.which("ISCC.exe")
    if iscc:
        return iscc
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


class ReleaseTool(QWidget):
    log_signal = Signal(str)
    deploy_done_signal = Signal()
    deploy_error_signal = Signal(str)
    installer_done_signal = Signal()
    beget_done_signal = Signal()

    def __init__(self):
        super().__init__()
        self.process = None
        self.build_ok = False
        self.current_version = read_current_version()
        self.new_version = bump_patch(self.current_version)
        self.setup_ui()
        self.load_version_json_notes()

        self.log_signal.connect(self._on_log)
        self.deploy_done_signal.connect(self._on_deploy_done)
        self.deploy_error_signal.connect(self._on_deploy_error)
        self.installer_done_signal.connect(self._on_installer_done)
        self.beget_done_signal.connect(self._on_beget_done)

    def setup_ui(self):
        self.setWindowTitle("SNBLD Release Tool")
        self.setMinimumSize(800, 700)
        self.setStyleSheet("""
            QWidget { font-size: 10pt; }
            QTextEdit#log { font-family: Consolas; font-size: 9pt;
                background: #1e1e1e; color: #d4d4d4; }
            QPushButton { padding: 6px 16px; }
            QPushButton:disabled { color: #888; }
        """)

        layout = QVBoxLayout(self)
        vbox = QVBoxLayout()

        row = QHBoxLayout()
        row.addWidget(QLabel("Текущая:"))
        self.lbl_current = QLabel(self.current_version)
        self.lbl_current.setStyleSheet("font-weight: bold;")
        row.addWidget(self.lbl_current)
        row.addSpacing(20)
        row.addWidget(QLabel("Новая версия:"))
        self.edit_version = QLineEdit(self.new_version)
        self.edit_version.setMaximumWidth(120)
        row.addWidget(self.edit_version)
        row.addStretch()
        vbox.addLayout(row)

        gb_notes = QGroupBox("Release Notes")
        gb_notes.setLayout(QVBoxLayout())
        self.notes_edit = QTextEdit()
        self.notes_edit.setMinimumHeight(120)
        gb_notes.layout().addWidget(self.notes_edit)
        vbox.addWidget(gb_notes)

        main_btn = QHBoxLayout()
        self.btn_build = QPushButton("Собрать")
        self.btn_build.clicked.connect(self.do_build)
        main_btn.addWidget(self.btn_build)

        self.btn_deploy = QPushButton("Деплоить обнову")
        self.btn_deploy.clicked.connect(self.do_deploy)
        main_btn.addWidget(self.btn_deploy)

        self.btn_build_deploy = QPushButton("Собрать и деплоить")
        self.btn_build_deploy.setStyleSheet("font-weight: bold;")
        self.btn_build_deploy.clicked.connect(self.do_build_deploy)
        main_btn.addWidget(self.btn_build_deploy)

        main_btn.addStretch()
        vbox.addLayout(main_btn)

        inst_btn = QHBoxLayout()
        self.btn_installer = QPushButton("Собрать установщик")
        self.btn_installer.clicked.connect(self.do_build_installer)
        inst_btn.addWidget(self.btn_installer)

        self.btn_beget = QPushButton("Залить установщик на Beget")
        self.btn_beget.clicked.connect(self.do_upload_beget)
        inst_btn.addWidget(self.btn_beget)

        self.cb_skip_iscc = QCheckBox("Пропустить ISCC при сборке")
        inst_btn.addWidget(self.cb_skip_iscc)
        inst_btn.addStretch()
        vbox.addLayout(inst_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        vbox.addWidget(self.progress)

        gb_log = QGroupBox("Лог")
        gb_log.setLayout(QVBoxLayout())
        self.log_edit = QTextEdit()
        self.log_edit.setObjectName("log")
        self.log_edit.setReadOnly(True)
        self.log_edit.setMinimumHeight(200)
        gb_log.layout().addWidget(self.log_edit)
        vbox.addWidget(gb_log, stretch=1)

        status_row = QHBoxLayout()
        self.lbl_status = QLabel("Готов")
        status_row.addWidget(self.lbl_status, stretch=1)
        self.btn_clear = QPushButton("Очистить лог")
        self.btn_clear.clicked.connect(lambda: self.log_edit.clear())
        status_row.addWidget(self.btn_clear)
        vbox.addLayout(status_row)

        layout.addLayout(vbox)

    def load_version_json_notes(self):
        if VERSION_JSON.exists():
            try:
                data = json.loads(VERSION_JSON.read_text("utf-8"))
                notes = data.get("release_notes", "")
                self.notes_edit.setPlainText(notes)
            except Exception:
                pass

    def _on_log(self, text):
        self.log_edit.append(text)
        self.log_edit.verticalScrollBar().setValue(
            self.log_edit.verticalScrollBar().maximum()
        )

    def _on_deploy_error(self, msg):
        self.lbl_status.setText(f"Ошибка: {msg}")
        self.set_busy(False)
        QMessageBox.critical(self, "Ошибка", msg)

    def _on_deploy_done(self):
        self.lbl_status.setText("Деплой завершён")
        self.set_busy(False)
        QMessageBox.information(self, "Успех", "Обновление разослано пользователям!")

    def _on_installer_done(self):
        self.lbl_status.setText("Установщик собран")
        self.set_busy(False)
        QMessageBox.information(self, "Успех", "Установщик собран в dist_installers/")

    def _on_beget_done(self):
        self.lbl_status.setText("Залито на Beget")
        self.set_busy(False)
        QMessageBox.information(self, "Успех", "Установщик загружен на Beget!")

    def log(self, text):
        self.log_signal.emit(text)

    def set_busy(self, busy):
        for btn in [self.btn_build, self.btn_deploy, self.btn_build_deploy,
                     self.btn_installer, self.btn_beget]:
            btn.setDisabled(busy)
        self.edit_version.setReadOnly(busy)
        self.progress.setVisible(busy)
        if busy:
            self.progress.setRange(0, 0)

    def save_version(self):
        version = self.edit_version.text().strip()
        if not re.match(r"^\d+\.\d+\.\d+$", version):
            QMessageBox.warning(self, "Ошибка", "Неверный формат версии (X.Y.Z)")
            return None
        write_version(version)
        return version

    def do_build(self):
        version = self.save_version()
        if not version:
            return
        self.log(f"=== СБОРКА v{version} ===")
        self.build_ok = False
        self.run_build(version, deploy_after=False)

    def do_build_deploy(self):
        version = self.save_version()
        if not version:
            return
        self.log(f"=== СБОРКА + ДЕПЛОЙ v{version} ===")
        self.build_ok = False
        self.run_build(version, deploy_after=True)

    def run_build(self, version, deploy_after=False):
        self.set_busy(True)
        self.lbl_status.setText("Сборка...")

        qenv = QProcessEnvironment.systemEnvironment()
        qenv.insert("PYTHONUNBUFFERED", "1")
        if self.cb_skip_iscc.isChecked():
            qenv.insert("SNBLD_SKIP_ISCC", "1")

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.setWorkingDirectory(str(BASE_DIR))
        self.process.setProcessEnvironment(qenv)

        self._build_version = version
        self._deploy_after = deploy_after

        self.process.readyReadStandardOutput.connect(self._on_build_stdout)
        self.process.finished.connect(self._on_build_finished)
        self.process.errorOccurred.connect(self._on_build_error)
        self.process.start(sys.executable, ["-u", "build_nuitka.py"])

    def _on_build_stdout(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            self.log(line)

    def _on_build_error(self, error):
        self.log(f"[PROCESS ERROR] {self.process.errorString()}")

    def _on_build_finished(self, code):
        if code == 0:
            self.log("=== СБОРКА УСПЕШНА ===")
            self.build_ok = True
            self.lbl_status.setText("Сборка завершена")
            if self._deploy_after:
                self.do_deploy()
            else:
                self.set_busy(False)
        else:
            self.log(f"=== СБОРКА НЕУДАЧА (код {code}) ===")
            self.build_ok = False
            self.lbl_status.setText("Ошибка сборки")
            self.set_busy(False)
            QMessageBox.critical(self, "Ошибка", f"Сборка завершилась с кодом {code}")

    def do_deploy(self):
        version = self.edit_version.text().strip()
        if not re.match(r"^\d+\.\d+\.\d+$", version):
            QMessageBox.warning(self, "Ошибка", "Неверный формат версии")
            return

        self.set_busy(True)
        self.lbl_status.setText("Деплой...")
        self.log(f"=== ДЕПЛОЙ v{version} ===")

        thread = threading.Thread(
            target=self._deploy_thread, args=(version,), daemon=True
        )
        thread.start()

    def _deploy_thread(self, version):
        def emit(msg):
            self.log_signal.emit(msg)

        try:
            emit("[1/5] Проверка файлов...")
            if not DIST_DIR.exists():
                emit("[X] dist_standalone/qml_main.dist не найден! Соберите сначала.")
                self.deploy_error_signal.emit("Не найден dist_standalone/qml_main.dist")
                return

            if not (DIST_DIR / "qml_main.exe").exists():
                emit("[X] qml_main.exe не найден!")
                self.deploy_error_signal.emit("Не найден qml_main.exe")
                return

            if not (DIST_DIR / "updater.exe").exists():
                emit("[WARN] updater.exe не найден! Автообновление не будет работать.")

            emit("[2/5] Создание update.zip...")
            zip_path = BASE_DIR / "update.zip"
            if zip_path.exists():
                zip_path.unlink()

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                for root, dirs, files in os.walk(str(DIST_DIR)):
                    for f in files:
                        fp = os.path.join(root, f)
                        arcname = os.path.relpath(fp, str(DIST_DIR))
                        z.write(fp, arcname)
            size = os.path.getsize(zip_path)
            emit(f"ZIP created: {size} bytes")
            emit(f"[OK] update.zip ({size/1024:.0f} KB)")

            emit("[3/5] Загрузка на Beget...")
            env_data = load_env()
            host = env_data.get("BEGET_SSH_HOST", "")
            user = env_data.get("BEGET_SSH_USER", "")
            password = env_data.get("BEGET_SSH_PASSWORD", "")
            if not host or not user or not password:
                emit("[X] Beget credentials не найдены в .env")
                self.deploy_error_signal.emit("Нет Beget credentials")
                return

            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=30)
            sftp = ssh.open_sftp()

            remote_zip = f"{BEGET_REMOTE}/downloads/update_{version}.zip"
            emit(f"   Загрузка update_{version}.zip ({size/1024:.0f} KB)...")
            sftp.put(str(zip_path), remote_zip)
            emit("[OK] update.zip загружен")

            emit("   Создание download_update.php...")
            php_script = f"""<?php
$file = isset($_GET['file']) ? basename($_GET['file']) : '';
if (!$file || !preg_match('/^update_\\d+\\.\\d+\\.\\d+\\.zip$/', $file)) {{
    http_response_code(404);
    die('File not found');
}}
$path = __DIR__ . '/' . $file;
if (!file_exists($path) || filesize($path) === 0) {{
    http_response_code(404);
    die('File not found');
}}
header('Content-Description: File Transfer');
header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="' . $file . '"');
header('Content-Length: ' . filesize($path));
header('Cache-Control: must-revalidate');
header('Pragma: public');
if (ob_get_level()) ob_end_clean();
readfile($path);
exit;
?>"""
            remote_php = f"{BEGET_REMOTE}/downloads/download_update.php"
            buf = io.BytesIO(php_script.encode("utf-8"))
            sftp.putfo(buf, remote_php)
            emit("[OK] download_update.php создан")

            emit("[5/5] Обновление version.json...")
            upload_url = f"{CDN_BASE}/downloads/download_update.php?file=update_{version}.zip"
            notes = self.notes_edit.toPlainText().strip()
            vj_data = json.loads(VERSION_JSON.read_text("utf-8")) if VERSION_JSON.exists() else {}
            vj_data.update(latest_version=version, download_url=upload_url,
                           download_zip_url=upload_url, release_notes=notes,
                           release_date=date.today().isoformat())
            VERSION_JSON.write_text(json.dumps(vj_data, ensure_ascii=False, indent=2), "utf-8")
            emit("[OK] version.json обновлён")

            emit("[5/5] Загрузка version.json на Beget...")
            sftp.put(str(VERSION_JSON), f"{BEGET_REMOTE}/version.json")
            sftp.close()
            ssh.close()
            emit("[OK] version.json загружен")

            if zip_path.exists():
                zip_path.unlink()

            emit("")
            emit("=" * 50)
            emit(f"ДЕПЛОЙ v{version} УСПЕШНО ЗАВЕРШЁН")
            emit("=" * 50)
            emit("Все пользователи получат обновление при следующем запуске")
            self.deploy_done_signal.emit()

        except Exception as e:
            emit(f"[X] Ошибка: {e}")
            self.deploy_error_signal.emit(str(e))

    def do_build_installer(self):
        version = self.edit_version.text().strip()
        if not ISS_FILE.exists():
            QMessageBox.warning(self, "Ошибка", "Сначала собери проект (нужен snbld_resvap.iss)")
            return

        iscc = find_iscc()
        if not iscc:
            QMessageBox.critical(self, "Ошибка", "ISCC.exe не найден. Установи Inno Setup 6.")
            return

        self.set_busy(True)
        self.lbl_status.setText("Сборка установщика...")
        self.log(f"=== СБОРКА УСТАНОВЩИКА ===")

        thread = threading.Thread(
            target=self._build_installer_thread, args=(iscc, version), daemon=True
        )
        thread.start()

    def _generate_dark_bmps(self, version):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            return None, None

        out_dir = BASE_DIR / "dist_installers"
        out_dir.mkdir(parents=True, exist_ok=True)

        sidebar_path = out_dir / "wizard_sidebar.bmp"
        small_path = out_dir / "wizard_small.bmp"
        bg_dark = (18, 18, 30)
        accent = (80, 140, 255)

        img = Image.new("RGB", (164, 314), bg_dark)
        draw = ImageDraw.Draw(img)
        for y in range(314):
            t = y / 314
            r = int(bg_dark[0] + (30 - bg_dark[0]) * t)
            g = int(bg_dark[1] + (40 - bg_dark[1]) * t)
            b = int(bg_dark[2] + (60 - bg_dark[2]) * t)
            draw.line([(0, y), (163, y)], fill=(r, g, b))
        logo_path = BASE_DIR / "logo.png"
        if logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((80, 80), Image.LANCZOS)
            lx = (164 - logo.width) // 2
            ly = 30
            if logo.mode == "RGBA":
                img.paste(logo, (lx, ly), logo)
            else:
                img.paste(logo, (lx, ly))
        try:
            font = ImageFont.truetype("arial.ttf", 11)
            draw.text((82, 160), "snbld resvap", fill=(180, 180, 200), font=font, anchor="mt")
            font_small = ImageFont.truetype("arial.ttf", 9)
            draw.text((82, 175), "v" + version, fill=(120, 120, 140), font=font_small, anchor="mt")
        except Exception:
            pass
        img.save(sidebar_path, "BMP")
        self.log_signal.emit(f"   [OK] {sidebar_path.name} ({img.size[0]}x{img.size[1]})")

        small = Image.new("RGB", (55, 55), bg_dark)
        sdraw = ImageDraw.Draw(small)
        for y in range(55):
            t = y / 55
            r = int(bg_dark[0] + (accent[0] * 0.3 - bg_dark[0]) * t)
            g = int(bg_dark[1] + (accent[1] * 0.3 - bg_dark[1]) * t)
            b = int(bg_dark[2] + (accent[2] * 0.3 - bg_dark[2]) * t)
            sdraw.line([(0, y), (54, y)], fill=(r, g, b))
        if logo_path.exists():
            logo_small = Image.open(logo_path).convert("RGBA")
            logo_small.thumbnail((40, 40), Image.LANCZOS)
            slx = (55 - logo_small.width) // 2
            sly = (55 - logo_small.height) // 2
            if logo_small.mode == "RGBA":
                small.paste(logo_small, (slx, sly), logo_small)
            else:
                small.paste(logo_small, (slx, sly))
        small.save(small_path, "BMP")
        self.log_signal.emit(f"   [OK] {small_path.name} ({small.size[0]}x{small.size[1]})")
        return str(sidebar_path), str(small_path)

    def _build_installer_thread(self, iscc, version):
        def emit(msg):
            self.log_signal.emit(msg)

        try:
            emit(f"ISCC: {iscc}")

            if DIST_INSTALLERS.exists():
                for f in DIST_INSTALLERS.iterdir():
                    if f.suffix == ".exe":
                        try:
                            f.unlink()
                            emit(f"   [DEL] {f.name}")
                        except Exception as e:
                            emit(f"   [WARN] Не удалось удалить {f.name}: {e}")

            sidebar, small = self._generate_dark_bmps(version)
            if sidebar and small:
                iss_text = ISS_FILE.read_text("utf-8")
                iss_text = iss_text.replace("WizardStyle=modern", "WizardStyle=modern dark includetitlebar")
                iss_text = re.sub(
                    r'WizardImageFile=.*$',
                    f'WizardImageFile={sidebar}',
                    iss_text,
                    flags=re.MULTILINE
                )
                iss_text = re.sub(
                    r'WizardSmallImageFile=.*$',
                    f'WizardSmallImageFile={small}',
                    iss_text,
                    flags=re.MULTILINE
                )
                ISS_FILE.write_text(iss_text, "utf-8")
                emit("   [OK] ISS обновлён (тёмная тема + кастомные BMP)")
            else:
                emit("   [SKIP] Pillow не найден, ISS без изменений")

            proc = subprocess.Popen(
                [iscc, str(ISS_FILE)],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=str(BASE_DIR)
            )
            for line in proc.stdout:
                emit(f"   {line.rstrip()}")
            proc.wait(timeout=300)

            if proc.returncode != 0:
                emit("[X] Ошибка компиляции установщика")
                self.deploy_error_signal.emit("ISCC ошибка")
                return

            installers = sorted(DIST_INSTALLERS.glob("snbldsetup*.exe"), key=os.path.getmtime)
            if installers:
                size_mb = installers[-1].stat().st_size / 1024 / 1024
                emit(f"[OK] {installers[-1].name} ({size_mb:.1f} MB)")
            else:
                emit("[WARN] Установщик не найден в dist_installers/")

            self.installer_done_signal.emit()
        except Exception as e:
            emit(f"[X] Ошибка: {e}")
            self.deploy_error_signal.emit(str(e))

    def do_upload_beget(self):
        installers = sorted(DIST_INSTALLERS.glob("snbldsetup*.exe"), key=os.path.getmtime)
        if not installers:
            QMessageBox.warning(self, "Ошибка", "Нет установщика в dist_installers/")
            return

        env = load_env()
        host = env.get("BEGET_SSH_HOST")
        user = env.get("BEGET_SSH_USER")
        password = env.get("BEGET_SSH_PASSWORD")
        if not host or not user or not password:
            QMessageBox.critical(self, "Ошибка", "Нет Beget credentials в .env")
            return

        self.set_busy(True)
        self.lbl_status.setText("Загрузка на Beget...")
        self.log("=== ЗАГРУЗКА УСТАНОВЩИКА НА BEGET ===")

        thread = threading.Thread(
            target=self._upload_beget_thread,
            args=(installers[-1], host, user, password), daemon=True
        )
        thread.start()

    def _upload_beget_thread(self, installer_path, host, user, password):
        def emit(msg):
            self.log_signal.emit(msg)

        try:
            emit(f"Файл: {installer_path.name} ({installer_path.stat().st_size/1024/1024:.1f} MB)")
            emit(f"Хост: {host}")

            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, password=password, timeout=30)
            sftp = ssh.open_sftp()

            remote = f"/home/s/snbld/snbld.beget.tech/public_html/downloads/{installer_path.name}"
            emit(f"Загрузка -> {remote}...")
            sftp.put(str(installer_path), remote)
            sftp.close()
            ssh.close()
            emit("[OK] Установщик загружен на Beget")
            self.beget_done_signal.emit()
        except Exception as e:
            emit(f"[X] Ошибка: {e}")
            self.deploy_error_signal.emit(str(e))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = ReleaseTool()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
