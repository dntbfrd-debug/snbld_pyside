from PySide6.QtCore import QRunnable, QThreadPool


class _AsyncTask(QRunnable):
    def __init__(self, fn, on_done=None):
        super().__init__()
        self.fn = fn
        self.on_done = on_done
        self._signals = None

    def run(self):
        result = self.fn()
        if self.on_done:
            self.on_done(result)


def run_async(fn, on_done=None):
    QThreadPool.globalInstance().start(_AsyncTask(fn, on_done))
