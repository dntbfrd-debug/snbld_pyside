from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPainter, QPixmap, QColor, QCursor
from PySide6.QtCore import Qt, QCoreApplication, QTimer


STATUS_RUNNING = "running"
STATUS_STOPPED = "stopped"
STATUS_ERROR = "error"

_STATUS_COLORS = {
    STATUS_RUNNING: "#22c55e",
    STATUS_STOPPED:  "#ef4444",
    STATUS_ERROR:    "#dc2626",
}


def _create_indicator_pixmap(status, size=16):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    color = _STATUS_COLORS.get(status, "#888888")
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, size - 4, size - 4)
    painter.end()

    return pixmap


class TrayIconManager:

    def __init__(self, backend, app):
        self.backend = backend
        self.app = app
        self._tray = None
        self._current_status = STATUS_STOPPED
        self._menu = None

    def _create_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #50ffffff;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                color: #a2a2a2;
                padding: 8px 30px 8px 20px;
                border-radius: 4px;
                margin: 1px;
            }
            QMenu::item:selected {
                background-color: #404040;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #50ffffff;
                margin: 4px 10px;
            }
        """)

        action_show = QAction("╨Я╨╛╨║╨░╨╖╨░╤В╤М ╨╛╨║╨╜╨╛", menu)
        action_show.triggered.connect(self._on_show_window)
        menu.addAction(action_show)

        menu.addSeparator()

        action_start = QAction(" ╨б╤В╨░╤А╤В ╨╝╨░╨║╤А╨╛╤Б╨╛╨▓", menu)
        action_start.triggered.connect(self._on_start_all)
        menu.addAction(action_start)

        action_stop = QAction("тЦа ╨б╤В╨╛╨┐ ╨╝╨░╨║╤А╨╛╤Б╨╛╨▓", menu)
        action_stop.triggered.connect(self._on_stop_all)
        menu.addAction(action_stop)

        menu.addSeparator()

        action_quit = QAction("╨Т╤Л╤Е╨╛╨┤", menu)
        action_quit.triggered.connect(self._on_quit)
        menu.addAction(action_quit)

        return menu

    def init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self._tray = QSystemTrayIcon()

        pixmap = _create_indicator_pixmap(STATUS_STOPPED)
        icon = QIcon(pixmap)
        self._tray.setIcon(icon)
        self._tray.setToolTip("snbld resvap тАФ ╨Ю╤Б╤В╨░╨╜╨╛╨▓╨╗╨╡╨╜")

        self._menu = self._create_menu()

        self._tray.setContextMenu(None)
        self._tray.activated.connect(self._on_tray_clicked)

        self._show_menu_timer = QTimer()
        self._show_menu_timer.setSingleShot(True)
        self._show_menu_timer.timeout.connect(self._show_context_menu)

        self._tray.show()

    def update_status(self, status, message=None):
        if not self._tray:
            return

        self._current_status = status
        pixmap = _create_indicator_pixmap(status)

        try:
            self._tray.setIcon(QIcon(pixmap))
        except RuntimeError:
            return

        if message:
            try:
                self._tray.setToolTip(f"snbld resvap тАФ {message}")
            except RuntimeError:
                pass
        else:
            labels = {
                STATUS_RUNNING: "╨а╨░╨▒╨╛╤В╨░╨╡╤В",
                STATUS_STOPPED: "╨Ю╤Б╤В╨░╨╜╨╛╨▓╨╗╨╡╨╜",
                STATUS_ERROR: "╨Ю╤И╨╕╨▒╨║╨░",
            }
            try:
                self._tray.setToolTip(f"snbld resvap тАФ {labels.get(status, '╨Э╨╡╨╕╨╖╨▓╨╡╤Б╤В╨╜╨╛')}")
            except RuntimeError:
                pass

    def show_notification(self, title, message, icon=QSystemTrayIcon.Information):
        if not self._tray:
            return
        try:
            self._tray.showMessage(title, message, icon, 3000)
        except RuntimeError:
            pass

    def show_window(self):
        window = getattr(self.backend, '_main_window', None)
        if window:
            window.setVisible(True)
            window.showNormal()
            window.raise_()
            try:
                window.requestActivate()
            except Exception:
                pass

    def _on_tray_clicked(self, reason):
        if reason == QSystemTrayIcon.Context:
            self._show_menu_timer.start(10)
        elif reason == QSystemTrayIcon.DoubleClick:
            self._on_show_window()

    def _show_context_menu(self):
        if self._menu:
            pos = QCursor.pos()
            self._menu.popup(pos)

    def _on_show_window(self):
        window = getattr(self.backend, '_main_window', None)
        if window:
            window.setVisible(True)
            window.showNormal()
            window.raise_()
            try:
                window.requestActivate()
            except Exception:
                pass

    def _on_start_all(self):
        self.backend.start_all_macros()
        self.update_status(STATUS_RUNNING, "╨Ь╨░╨║╤А╨╛╤Б╤Л ╨╖╨░╨┐╤Г╤Й╨╡╨╜╤Л")

    def _on_stop_all(self):
        self.backend.stop_all_macros()
        self.update_status(STATUS_STOPPED, "╨Ь╨░╨║╤А╨╛╤Б╤Л ╨╛╤Б╤В╨░╨╜╨╛╨▓╨╗╨╡╨╜╤Л")

    def disconnect_signals(self):
        try:
            self.backend.startAllPressed.disconnect()
        except (TypeError, RuntimeError):
            pass
        try:
            self.backend.stopAllPressed.disconnect()
        except (TypeError, RuntimeError):
            pass

    def _on_quit(self):
        self.disconnect_signals()
        window = getattr(self.backend, '_main_window', None)
        if window:
            window.close()
        else:
            QCoreApplication.quit()
