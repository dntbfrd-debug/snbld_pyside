import threading
import time
import heapq
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .logger_manager import get_logger
from constants import DEFAULT_CAST_LOCK_MARGIN

logger = get_logger('macros')


@dataclass(order=True)
class QueuedMacro:
    priority: int
    timestamp: float
    macro: Any = field(compare=False)
    timeout: float = field(default=2.0, compare=False)


@dataclass
class MacroStats:
    launches: int = 0
    blocked_cast: int = 0
    blocked_cooldown: int = 0
    blocked_running: int = 0
    queued: int = 0
    queued_launched: int = 0
    queued_expired: int = 0
    last_launch_time: float = 0.0


class MacroDispatcher:

    def __init__(self, backend):
        self.backend = backend
        self.cast_lock_until = 0.0
        self.lock = threading.RLock()
        self.active_macros_lock = threading.Lock()

        self.last_launch_time = 0.0
        self.launch_debounce = 0.08

        self.macro_queue: list = []
        self.queue_lock = threading.Lock()
        self.MAX_QUEUE_SIZE = 100
        self._queue_stop_event = threading.Event()

        self.cooldown_cache: Dict[str, float] = {}
        self.cache_lock = threading.Lock()

        self.macro_stats: Dict[str, MacroStats] = {}
        self.stats_lock = threading.Lock()

        self.stats = {
            'launched': 0,
            'blocked_cast': 0,
            'blocked_cooldown': 0,
            'blocked_running': 0,
        }

        self._macro_last_launch: Dict[str, float] = {}

        # Rate-limit для рестарта обработчика очереди — иначе при сбое потока
        # health_check/restart_queue_processor могут зациклиться и засрать лог.
        self._queue_restart_times: list = []
        self._max_restarts_per_minute = 6
        self._restart_window_sec = 60.0

        self._queue_thread = None
        self._start_queue_processor()

        self.running = True

    def _get_active_macros(self):
        if hasattr(self.backend, 'active_macros'):
            return self.backend.active_macros
        return {}

    def _active_macros_clear(self):
        with self.active_macros_lock:
            if hasattr(self.backend, 'active_macros'):
                self.backend.active_macros.clear()

    def _active_macros_set(self, name, macro):
        with self.active_macros_lock:
            if hasattr(self.backend, 'active_macros'):
                self.backend.active_macros[name] = macro

    def _active_macros_pop(self, name):
        with self.active_macros_lock:
            if hasattr(self.backend, 'active_macros'):
                return self.backend.active_macros.pop(name, None)
        return None

    def _active_macros_items(self):
        with self.active_macros_lock:
            if hasattr(self.backend, 'active_macros'):
                return list(self.backend.active_macros.items())
        return []
    
    def _start_queue_processor(self):
        if self._can_restart_queue_processor():
            self._queue_thread = threading.Thread(target=self._process_queue, daemon=True, name="MacroQueueProcessor")
            self._queue_thread.start()
            logger.info("[DISPATCHER] Обработчик очереди запущен")
        else:
            logger.error("[DISPATCHER] Превышен лимит рестартов обработчика очереди — остановлен")

    def _can_restart_queue_processor(self) -> bool:
        now = time.time()
        with self.lock:
            self._queue_restart_times = [t for t in self._queue_restart_times if now - t < self._restart_window_sec]
            if len(self._queue_restart_times) >= self._max_restarts_per_minute:
                return False
            self._queue_restart_times.append(now)
            return True

    def health_check(self) -> dict:
        status = {
            'queue_processor_alive': self._queue_thread is not None and self._queue_thread.is_alive(),
            'active_macros_count': len(self._get_active_macros()),
            'queue_size': len(self.macro_queue) if hasattr(self, 'macro_queue') else 0,
            'cast_locked': time.time() < self.cast_lock_until,
        }
        if not status['queue_processor_alive'] and self.running:
            logger.warning("[DISPATCHER] Поток обработчика очереди неактивен — перезапуск")
            self._start_queue_processor()
            status['queue_processor_alive'] = (
                self._queue_thread is not None and self._queue_thread.is_alive()
            )
        return status
    
    def request_macro(self, macro, priority=5) -> bool:
        now = time.time()

        cooldown = getattr(macro, 'cooldown', 0)
        should_set_cast = getattr(macro, 'cast_time', 0) > 0

        with self.lock:
            self._ensure_stats_exists(macro.name)

            if now < self.cast_lock_until:
                remaining = self.cast_lock_until - now
                logger.info(f" {macro.name}: ЗАБЛОКИРОВАНО (каст, ост. {remaining:.2f}с)")
                self.stats['blocked_cast'] += 1
                self._update_stats(macro.name, 'blocked_cast')
                return False

            cooldown_margin = self.backend.settings.get("cooldown_margin", 0.3)
            effective_cooldown = cooldown + cooldown_margin

            last_used = getattr(macro, 'last_used', 0)
            if cooldown > 0 and now < last_used + effective_cooldown:
                remaining = (last_used + effective_cooldown) - now
                logger.info(f" {macro.name}: ЗАБЛОКИРОВАНО (КД, ост. {remaining:.2f}с)")
                self.stats['blocked_cooldown'] += 1
                self._update_stats(macro.name, 'blocked_cooldown')
                return False

            any_macro_running = False
            for name, m in self._active_macros_items():
                if m is not macro and hasattr(m, 'running') and m.running.is_set():
                    any_macro_running = True
                    break
            
            if any_macro_running:
                logger.debug(f" {macro.name}: ЗАБЛОКИРОВАНО (выполняется другой макрос)")
                self.stats['blocked_running'] += 1
                self._update_stats(macro.name, 'blocked_running')
                return False
            
            if getattr(macro, 'running', threading.Event()).is_set():
                logger.debug(f" {macro.name}: ЗАБЛОКИРОВАНО (выполняется)")
                self.stats['blocked_running'] += 1
                self._update_stats(macro.name, 'blocked_running')
                return False

            if hasattr(self.backend, 'global_stopped') and self.backend.global_stopped:
                logger.debug(f" {macro.name}: ЗАБЛОКИРОВАНО (макросы остановлены)")
                return False

            macro_last_launch = self._macro_last_launch.get(macro.name, 0.0)
            if now - max(self.last_launch_time, macro_last_launch) < self.launch_debounce:
                remaining = self.launch_debounce - (now - max(self.last_launch_time, macro_last_launch))
                logger.debug(f" {macro.name}: ЗАБЛОКИРОВАНО (debounce, ост. {remaining:.3f}с)")
                return False

            if cooldown > 0 and hasattr(macro, 'last_used'):
                lock = getattr(macro, 'cooldown_lock', None)
                if lock:
                    with lock:
                        macro.last_used = now
                else:
                    macro.last_used = now
                logger.debug(f" {macro.name}: last_used = {now:.2f} (КД {effective_cooldown:.2f}с)")

            if should_set_cast:
                try:
                    self.set_cast_lock(macro)
                except Exception as e:
                    logger.warning(f" {macro.name}: ошибка set_cast_lock: {e}")

            self.stats['launched'] += 1
            self._update_stats_launch(macro.name, now)

            self._active_macros_set(macro.name, macro)

        # Запуск макроса ВНЕ блокировки — start() может блокироваться (join внутри)
        try:
            macro.start()
        except Exception as e:
            logger.error(f" {macro.name}: ОШИБКА при запуске: {str(e)}", exc_info=True)
            with self.lock:
                self._active_macros_pop(macro.name)
                if cooldown > 0 and hasattr(macro, 'last_used'):
                    try:
                        if hasattr(macro, 'cooldown_lock'):
                            with macro.cooldown_lock:
                                macro.last_used = 0
                        else:
                            macro.last_used = 0
                    except Exception:
                        pass
                self.cast_lock_until = 0.0
            return False

        # Записываем время запуска ТОЛЬКО после успешного start() — иначе debounce
        # может блокировать следующие вызовы, хотя макрос ещё не запущен.
        with self.lock:
            self.last_launch_time = time.time()
            self._macro_last_launch[macro.name] = self.last_launch_time
        logger.info(f" {macro.name}: ЗАПУЩЕН")
        return True

    def set_cast_lock(self, macro):
        with self.lock:
            now = time.time()
            cast_time = getattr(macro, 'cast_time', 0)
            if cast_time > 0:
                try:
                    if hasattr(self.backend, 'get_actual_cast_time'):
                        actual_cast_time = self.backend.get_actual_cast_time(cast_time)
                    else:
                        actual_cast_time = 0.5
                except Exception as e:
                    logger.warning(f"[DISPATCHER] get_actual_cast_time failed: {e}")
                    actual_cast_time = 0.5
                
                margin = self.backend.settings.get("cast_lock_margin", DEFAULT_CAST_LOCK_MARGIN)
                lock_duration = actual_cast_time + margin
            else:
                margin = self.backend.settings.get("cast_lock_margin", DEFAULT_CAST_LOCK_MARGIN)
                lock_duration = margin
            
            lock_duration = min(lock_duration, 5.0)
            self.cast_lock_until = now + lock_duration
            logger.debug(f" {macro.name}: блокировка каста установлена на {lock_duration:.2f}с")

    def get_cast_lock_remaining(self) -> float:
        with self.lock:
            now = time.time()
            if now < self.cast_lock_until:
                return self.cast_lock_until - now
            return 0.0

    def on_macro_finished(self, macro_name: str):
        with self.lock:
            finish_delay = self.backend.settings.get("cast_lock_margin", DEFAULT_CAST_LOCK_MARGIN)

            if finish_delay > 0:
                self.cast_lock_until = time.time() + finish_delay
                logger.debug(f" {macro_name}: cast_lock сбросится через {finish_delay}с (из cast_lock_margin)")
            else:
                self.cast_lock_until = 0.0
                logger.debug(f" {macro_name}: cast_lock сброшен (без задержки)")

            self._active_macros_pop(macro_name)

    def _process_queue(self):
        logger.info("[QUEUE] Обработчик очереди запущен")

        while not self._queue_stop_event.is_set():
            self._queue_stop_event.wait(0.005)

            try:
                with self.lock:
                    now = time.time()
                    cast_lock_ok = (now >= self.cast_lock_until)

                with self.queue_lock:
                    if not cast_lock_ok:
                        continue

                    expired_count = 0
                    valid_queue = []

                    while self.macro_queue:
                        queued = heapq.heappop(self.macro_queue)
                        if now - queued.timestamp < queued.timeout:
                            valid_queue.append(queued)
                        else:
                            expired_count += 1
                            self._update_stats(queued.macro.name, 'queued_expired')
                            logger.debug(f" {queued.macro.name}: истёк таймаут в очереди")

                    self.macro_queue = valid_queue
                    heapq.heapify(self.macro_queue)
                    while len(self.macro_queue) > self.MAX_QUEUE_SIZE:
                        dropped = heapq.heappop(self.macro_queue)
                        logger.warning(f" {dropped.macro.name}: удалён из очереди (переполнение)")

                    if expired_count > 0:
                        logger.debug(f"[QUEUE] Истекло {expired_count} макросов")

                    if not self.macro_queue:
                        continue

                    queued = heapq.heappop(self.macro_queue)
                    macro = queued.macro

                    cooldown = getattr(macro, 'cooldown', 0)
                    cooldown_margin = self.backend.settings.get("cooldown_margin", 0.3)
                    effective_cooldown = cooldown + cooldown_margin

                    with self.lock:
                        last_used = getattr(macro, 'last_used', 0)

                        if now < last_used + effective_cooldown:
                            heapq.heappush(self.macro_queue, queued)
                            continue

                        if getattr(macro, 'running', False):
                            heapq.heappush(self.macro_queue, queued)
                            continue

                        if hasattr(self.backend, 'global_stopped') and self.backend.global_stopped:
                            heapq.heappush(self.macro_queue, queued)
                            continue

                        if now - self.last_launch_time < self.launch_debounce:
                            heapq.heappush(self.macro_queue, queued)
                            continue

                        cast_time = getattr(macro, 'cast_time', 0)
                        if cast_time > 0:
                            actual_cast_time = self.backend.get_actual_cast_time(cast_time)
                            margin = self.backend.settings.get("cast_lock_margin", DEFAULT_CAST_LOCK_MARGIN)
                            lock_duration = actual_cast_time + margin
                            self.cast_lock_until = now + lock_duration

                        if cooldown > 0 and hasattr(macro, 'last_used'):
                            if hasattr(macro, 'cooldown_lock'):
                                with macro.cooldown_lock:
                                    macro.last_used = now
                            else:
                                macro.last_used = now

                        if getattr(macro, 'cast_time', 0) > 0:
                            self.set_cast_lock(macro)

                        self.last_launch_time = now
                        self._update_stats_launch(macro.name, now)
                        self._update_stats(macro.name, 'queued_launched')

                        self.stats['launched'] += 1
                        logger.info(f" {macro.name}: запуск из очереди (приоритет {queued.priority}, ждал {now - queued.timestamp:.2f}с)")

                    # Запуск макроса ВНЕ блокировок
                    try:
                        macro.start()
                        logger.info(f" {macro.name}: запущен из очереди")
                    except Exception as e:
                        logger.error(f" {macro.name}: ошибка при запуске из очереди: {e}", exc_info=True)
                        with self.lock:
                            self.cast_lock_until = 0.0

            except Exception as e:
                logger.error(f" Ошибка в обработчике очереди: {str(e)}", exc_info=True)
                with self.lock:
                    self.cast_lock_until = 0.0
                with self.queue_lock:
                    self.macro_queue.clear()
                logger.warning("[QUEUE] Очередь очищена после ошибки")

    def clear_queue(self):
        with self.queue_lock:
            count = len(self.macro_queue)
            self.macro_queue.clear()
            logger.info(f"[QUEUE] Очередь очищена ({count} макросов удалено)")
            return count

    def _ensure_stats_exists(self, macro_name: str):
        with self.stats_lock:
            if macro_name not in self.macro_stats:
                self.macro_stats[macro_name] = MacroStats()

    def _update_stats(self, macro_name: str, field_name: str):
        with self.stats_lock:
            if macro_name not in self.macro_stats:
                self.macro_stats[macro_name] = MacroStats()

            stats = self.macro_stats[macro_name]
            if hasattr(stats, field_name):
                setattr(stats, field_name, getattr(stats, field_name) + 1)

    def _update_stats_launch(self, macro_name: str, now: float):
        with self.stats_lock:
            if macro_name not in self.macro_stats:
                self.macro_stats[macro_name] = MacroStats()

            stats = self.macro_stats[macro_name]
            stats.launches += 1
            stats.last_launch_time = now

            if stats.launches > 1 and stats.last_launch_time > 0:
                pass

    def stop_all_macros(self, timeout: float = 1.0):
        self.running = False
        
        stopped_count = 0
        killed_count = 0
        
        for name, macro in self._active_macros_items():
                macro_thread = getattr(macro, 'thread', None)
                if macro_thread and macro_thread.is_alive():
                    try:
                        if hasattr(macro, 'stop'):
                            macro.stop()
                        macro_thread.join(timeout=timeout)
                        
                        if macro_thread.is_alive():
                            logger.warning(f"Макрос {name} не завершился за {timeout}с, принудительное отключение")
                            killed_count += 1
                        else:
                            stopped_count += 1
                            
                    except Exception as e:
                        logger.error(f"Ошибка при остановке макроса {name}: {e}", exc_info=True)
                        killed_count += 1
        
        self.clear_queue()
        
        with self.lock:
            self.cast_lock_until = 0.0
        
        logger.info(f"Макросы остановлены: {stopped_count} нормально, {killed_count} принудительно")
        return stopped_count, killed_count

    def stop(self):
        self._queue_stop_event.set()
        with self.queue_lock:
            self.macro_queue.clear()
        logger.info("[DISPATCHER] Обработчик очереди остановлен")
        
    def restart_queue_processor(self):
        self._queue_stop_event.clear()
        self._start_queue_processor()
        logger.info("[DISPATCHER] Обработчик очереди перезапущен")
