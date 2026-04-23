# -*- coding: utf-8 -*-
"""
backend/macros_dispatcher.py
Диспетчер макросов - единая точка проверки и запуска макросов
Гарантирует атомарную проверку и блокировку каста

УЛУЧШЕНИЯ (2026-04-01):
- Очередь приоритетов макросов
- Кэш кулдаунов для быстрой проверки
- Расширенная статистика по каждому макросу
"""

import threading
import time
import heapq
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .logger_manager import get_logger

logger = get_logger('macros')


# ==================== ОЧЕРЕДЬ ПРИОРИТЕТОВ ====================

@dataclass(order=True)
class QueuedMacro:
    """
    Макрос в очереди приоритетов.
    
    Сортировка: сначала по приоритету (1 = высокий), затем по времени (старше = первый)
    """
    priority: int  # Приоритет (1=критичный, 5=обычный, 10=фоновый)
    timestamp: float  # Время добавления в очередь
    macro: Any = field(compare=False)  # Ссылка на макрос
    timeout: float = field(default=2.0, compare=False)  # Макс время ожидания (сек)


# ==================== СТАТИСТИКА ====================

@dataclass
class MacroStats:
    """Статистика по одному макросу"""
    launches: int = 0  # Количество запусков
    blocked_cast: int = 0  # Заблокировано из-за каста
    blocked_cooldown: int = 0  # Заблокировано из-за КД
    blocked_running: int = 0  # Заблокировано из-за выполнения
    queued: int = 0  # Добавлено в очередь
    queued_launched: int = 0  # Запущено из очереди
    queued_expired: int = 0  # Истёк таймаут в очереди
    last_launch_time: float = 0.0  # Время последнего запуска
    avg_delay_between_launches_ms: float = 0.0  # Средняя задержка между запусками (мс)


# ==================== ДИСПЕТЧЕР ====================

class MacroDispatcher:
    """
    Диспетчер макросов - контролирует запуск всех макросов.

    Преимущества:
    - Атомарная проверка (нет гонки между макросами)
    - Централизованная блокировка каста
    - Быстрее (одна проверка для всех вместо дублирования)
    - Очередь приоритетов (макросы не теряются при одновременном нажатии)
    - Кэш кулдаунов (быстрая проверка без чтения из памяти)
    - Расширенная статистика (для отладки и анализа)
    """

    def __init__(self, backend):
        """
        Инициализация диспетчера.

        Args:
            backend: Ссылка на Backend (qml_main.py)
        """
        self.backend = backend
        self.cast_lock_until = 0.0
        self.lock = threading.Lock()

        # 🆕 Очередь приоритетов (heapq вместо deque.sort) — O(log n) вставка
        self.macro_queue: list = []  # list для heapq
        self.queue_lock = threading.Lock()
        self._queue_stop_event = threading.Event()  # Graceful shutdown

        # 🆕 Кэш кулдаунов
        self.cooldown_cache: Dict[str, float] = {}  # {macro_name: cooldown_end_time}
        self.cache_lock = threading.Lock()
        
        # 🆕 Расширенная статистика
        self.macro_stats: Dict[str, MacroStats] = {}
        self.stats_lock = threading.Lock()

        # Базовая статистика (для совместимости)
        self.stats = {
            'launched': 0,
            'blocked_cast': 0,
            'blocked_cooldown': 0,
            'blocked_running': 0,
        }
        
        # 🆕 Запуск обработчика очереди
        self._start_queue_processor()
    
    def _start_queue_processor(self):
        """Запускает обработчик очереди приоритетов (отдельный поток)"""
        queue_thread = threading.Thread(target=self._process_queue, daemon=True, name="MacroQueueProcessor")
        queue_thread.start()
        logger.info("[DISPATCHER] Обработчик очереди запущен")
    
    def request_macro(self, macro, priority: int = 5) -> bool:
        """
        Запрос на запуск макроса.

        Args:
            macro: Макрос для запуска
            priority: Приоритет (1=критичный, 5=обычный, 10=фоновый)
                     Приоритет влияет на порядок в очереди и время ожидания

        Returns:
            True если макрос запущен (сразу или из очереди), False если отклонён
        """
        with self.lock:
            now = time.time()
            
            # 🆕 Обновляем статистику
            self._ensure_stats_exists(macro.name)

            # 1. Проверка блокировки каста
            if now < self.cast_lock_until:
                remaining = self.cast_lock_until - now
                logger.info(f"❌ {macro.name}: ЗАБЛОКИРОВАНО (каст, ост. {remaining:.2f}с)")
                self.stats['blocked_cast'] += 1
                self._update_stats(macro.name, 'blocked_cast')
                
                # 🆕 Добавляем в очередь если приоритет высокий (1-3)
                if priority <= 3:
                    self._add_to_queue(macro, priority)
                    logger.debug(f"⏳ {macro.name}: добавлен в очередь (приоритет {priority})")
                return False

            # 2. ✅ Проверка кулдауна макроса (ТОЛЬКО через last_used)
            # Все проверки cooldown — только через last_used макроса!
            cooldown = getattr(macro, 'cooldown', 0)
            cooldown_margin = self.backend.settings.get("cooldown_margin", 0.05)
            effective_cooldown = cooldown + cooldown_margin

            last_used = getattr(macro, 'last_used', 0)
            if cooldown > 0 and now < last_used + effective_cooldown:
                remaining = (last_used + effective_cooldown) - now
                logger.info(f"❌ {macro.name}: ЗАБЛОКИРОВАНО (КД, ост. {remaining:.2f}с)")
                self.stats['blocked_cooldown'] += 1
                self._update_stats(macro.name, 'blocked_cooldown')
                
                # 🆕 Добавляем в очередь если приоритет высокий (1-3)
                if priority <= 3:
                    self._add_to_queue(macro, priority)
                    logger.debug(f"⏳ {macro.name}: добавлен в очередь (КД, приоритет {priority})")
                return False

            # 4. Проверка выполняется ли уже
            if getattr(macro, 'running', False):
                logger.debug(f"❌ {macro.name}: ЗАБЛОКИРОВАНО (выполняется)")
                self.stats['blocked_running'] += 1
                self._update_stats(macro.name, 'blocked_running')
                return False

            # 5. Проверка глобальной остановки (макросы остановлены)
            if hasattr(self.backend, 'global_stopped') and self.backend.global_stopped:
                logger.debug(f"❌ {macro.name}: ЗАБЛОКИРОВАНО (макросы остановлены)")
                return False

            # 6. ✅ УСТАНОВКА БЛОКИРОВКИ КАСТА
            # Атомарная установка блокировки внутри этого же лока
            # Предотвращает гонку когда два макроса одновременно проходят проверку
            cast_time = getattr(macro, 'cast_time', 0)
            if cast_time > 0:
                actual_cast_time = self.backend.get_actual_cast_time(cast_time)
                margin = self.backend.settings.get("cast_lock_margin", 0.4)
                lock_duration = actual_cast_time + margin
                # ✅ Безопасность: максимальная блокировка 5 секунд даже если что-то пошло не так
                lock_duration = min(lock_duration, 5.0)
                self.cast_lock_until = now + lock_duration
                logger.debug(f"🔒 {macro.name}: блокировка каста установлена на {lock_duration:.2f}с")

            # 7. ✅ Запуск макроса
            try:
                macro.start()
                logger.info(f"✅ {macro.name}: ЗАПУЩЕН (приоритет {priority})")
                self.stats['launched'] += 1
                
                # ✅ Записываем last_used ПОСЛЕ успешного запуска
                # Это устанавливает блокировку перезарядки для СЕБЯ
                if cooldown > 0:
                    if hasattr(macro, 'last_used'):
                        macro.last_used = now
                        logger.debug(f"💾 {macro.name}: last_used = {now:.2f} (КД {effective_cooldown:.2f}с)")
            except Exception as e:
                logger.error(f"💥 {macro.name}: ОШИБКА при запуске: {str(e)}", exc_info=True)
                # Снимаем блокировку каста при ошибке
                self.cast_lock_until = 0.0
                return False
            
            # 🆕 Обновление статистики
            self._update_stats_launch(macro.name, now)

            return True
    
    def is_cast_locked(self) -> bool:
        """
        Проверка заблокирован ли каст.

        Returns:
            True если каст заблокирован
        """
        with self.lock:
            return time.time() < self.cast_lock_until

    def get_cast_lock_remaining(self) -> float:
        """
        Получить оставшееся время блокировки каста.

        Returns:
            Оставшееся время в секундах (0 если не заблокировано)
        """
        with self.lock:
            now = time.time()
            if now < self.cast_lock_until:
                return self.cast_lock_until - now
            return 0.0

    def on_macro_finished_immediate(self, macro_name: str):
        """
        Вызывается макросом после окончания выполнения.
        Сбрасывает cast_lock НЕМЕДЛЕННО без задержки!
        
        ✅ ИСПРАВЛЕНИЕ: cast_lock_margin используется для установки блокировки ПЕРЕД кастом,
        а не для задержки сброса ПОСЛЕ завершения макроса.
        """
        with self.lock:
            # ✅ Сбрасываем НЕМЕДЛЕННО - макрос уже завершён, каст закончился!
            self.cast_lock_until = 0.0
            logger.debug(f"🔓 {macro_name}: cast_lock сброшен НЕМЕДЛЕННО (макрос завершён)")

    def on_macro_finished(self, macro_name: str):
        """
        УСТАРЕВШИЙ МЕТОД - вызывается для совместимости.
        Перенаправляет на on_macro_finished_immediate().
        """
        self.on_macro_finished_immediate(macro_name)

    # ==================== МЕТОДЫ ОЧЕРЕДИ ====================

    def _add_to_queue(self, macro, priority: int):
        """Добавляет макрос в очередь приоритетов (O(log n) через heapq)"""
        # Определяем таймаут на основе приоритета
        if priority <= 2:
            timeout = 2.0  # Критичные ждут дольше
        elif priority <= 5:
            timeout = 1.0  # Обычные
        else:
            timeout = 0.5  # Фоновые мало ждут

        queued = QueuedMacro(
            priority=priority,
            timestamp=time.time(),
            macro=macro,
            timeout=timeout
        )

        with self.queue_lock:
            heapq.heappush(self.macro_queue, queued)  # O(log n) вместо O(n log n)

        self._update_stats(macro.name, 'queued')
        logger.debug(f"📋 {macro.name}: добавлен в очередь (приоритет {priority}, таймаут {timeout}с)")

    def _process_queue(self):
        """
        Обработчик очереди приоритетов (работает в отдельном потоке).
        Проверяет каждые 50 мс можно ли запустить следующий макрос.
        Использует heapq для O(log n) извлечения вместо O(n log n) сортировки.
        """
        logger.info("[QUEUE] Обработчик очереди запущен")

        while not self._queue_stop_event.is_set():
            self._queue_stop_event.wait(0.015)  # 15мс - быстрее реагируем на освобождение каста

            try:
                with self.lock:
                    now = time.time()

                with self.queue_lock:
                    # 🆕 Удаляем протухшие запросы
                    expired_count = 0
                    valid_queue = []

                    while self.macro_queue:
                        queued = heapq.heappop(self.macro_queue)
                        if now - queued.timestamp < queued.timeout:
                            valid_queue.append(queued)
                        else:
                            expired_count += 1
                            self._update_stats(queued.macro.name, 'queued_expired')
                            logger.debug(f"⏰ {queued.macro.name}: истёк таймаут в очереди")

                    # Восстанавливаем heapq
                    self.macro_queue = valid_queue
                    heapq.heapify(self.macro_queue)

                    if expired_count > 0:
                        logger.debug(f"[QUEUE] Истёкло {expired_count} макросов")

                    # Если очередь пуста - продолжаем
                    if not self.macro_queue:
                        continue

                    # ✅ Проверяем cast_lock ПЕРЕД запуском из очереди!
                    if now >= self.cast_lock_until:
                        # cast_lock прошёл - можно запускать
                        # Берём первый из очереди (самый приоритетный) через heapq
                        queued = heapq.heappop(self.macro_queue)
                        macro = queued.macro

                        # Повторная проверка кулдауна
                        cooldown = getattr(macro, 'cooldown', 0)
                        cooldown_margin = self.backend.settings.get("cooldown_margin", 0.05)
                        effective_cooldown = cooldown + cooldown_margin
                        last_used = getattr(macro, 'last_used', 0)

                        if now >= last_used + effective_cooldown:
                            # Проверка: не выполняется ли уже
                            if not getattr(macro, 'running', False):
                                # Проверка глобальной остановки
                                if not (hasattr(self.backend, 'global_stopped') and self.backend.global_stopped):
                                    # Установка блокировки каста
                                    cast_time = getattr(macro, 'cast_time', 0)
                                    if cast_time > 0:
                                        actual_cast_time = self.backend.get_actual_cast_time(cast_time)
                                        margin = self.backend.settings.get("cast_lock_margin", 0.4)
                                        lock_duration = actual_cast_time + margin
                                        self.cast_lock_until = now + lock_duration

                                    # Запуск из очереди!
                                    macro.start()
                                    logger.info(f"🚀 {macro.name}: запуск из очереди (приоритет {queued.priority}, ждал {now - queued.timestamp:.2f}с)")
                                    self.stats['launched'] += 1
                                    
                                    # ✅ Записываем last_used ПОСЛЕ успешного запуска
                                    if cooldown > 0 and hasattr(macro, 'last_used'):
                                        macro.last_used = now
                                        
                                    self._update_stats_launch(macro.name, now)
                                    self._update_stats(macro.name, 'queued_launched')
                                else:
                                    # Глобальная остановка - возвращаем в очередь
                                    heapq.heappush(self.macro_queue, queued)
                            else:
                                # Выполняется - возвращаем в очередь
                                heapq.heappush(self.macro_queue, queued)

            except Exception as e:
                logger.error(f"💥 Ошибка в обработчике очереди: {str(e)}", exc_info=True)
                # Снимаем блокировку при любой ошибке чтобы не зависнуть навсегда
                self.cast_lock_until = 0.0
                # Очищаем очередь чтобы не зациклиться на битом элементе
                with self.queue_lock:
                    self.macro_queue.clear()
                logger.warning("[QUEUE] Очередь очищена после ошибки")

    def clear_queue(self):
        """Очищает очередь макросов"""
        with self.queue_lock:
            count = len(self.macro_queue)
            self.macro_queue.clear()
            logger.info(f"[QUEUE] Очередь очищена ({count} макросов удалено)")
            return count

    def get_queue_size(self) -> int:
        """Возвращает размер очереди"""
        with self.queue_lock:
            return len(self.macro_queue)

    def get_queue_info(self) -> list:
        """
        Возвращает информацию о очереди (O(n) — не вызывается часто).

        Returns:
            Список словарей с информацией о макросах в очереди
        """
        with self.queue_lock:
            now = time.time()
            result = []
            for queued in self.macro_queue:
                result.append({
                    'name': queued.macro.name,
                    'priority': queued.priority,
                    'waiting_time': now - queued.timestamp,
                    'timeout_remaining': queued.timeout - (now - queued.timestamp)
                })
            return result

    # ==================== 🆕 МЕТОДЫ КЭША ====================

    def invalidate_cooldown_cache(self, macro_name: str = None):
        """
        Инвалидация кэша кулдаунов.

        Args:
            macro_name: Имя макроса для инвалидации (None = все макросы)
        """
        with self.cache_lock:
            if macro_name is not None:
                if macro_name in self.cooldown_cache:
                    del self.cooldown_cache[macro_name]
                    logger.debug(f"💾 {macro_name}: кэш КД инвалидирован")
            else:
                count = len(self.cooldown_cache)
                self.cooldown_cache.clear()
                logger.info(f"💾 Кэш кулдаунов полностью очищен ({count} записей)")

    def get_cooldown_cache_info(self, macro_name: str) -> dict:
        """
        Получить информацию о кэше кулдауна макроса.

        Args:
            macro_name: Имя макроса

        Returns:
            Словарь с информацией о кэше
        """
        with self.cache_lock:
            cached_end = self.cooldown_cache.get(macro_name)
            if cached_end:
                now = time.time()
                remaining = max(0, cached_end - now)
                return {
                    'cached': True,
                    'remaining': remaining,
                    'end_time': cached_end
                }
            return {'cached': False, 'remaining': 0}

    # ==================== 🆕 МЕТОДЫ СТАТИСТИКИ ====================

    def _ensure_stats_exists(self, macro_name: str):
        """Гарантирует что статистика для макроса существует"""
        with self.stats_lock:
            if macro_name not in self.macro_stats:
                self.macro_stats[macro_name] = MacroStats()

    def _update_stats(self, macro_name: str, field_name: str):
        """Обновляет поле статистики"""
        with self.stats_lock:
            if macro_name not in self.macro_stats:
                self.macro_stats[macro_name] = MacroStats()

            stats = self.macro_stats[macro_name]
            if hasattr(stats, field_name):
                setattr(stats, field_name, getattr(stats, field_name) + 1)

    def _update_stats_launch(self, macro_name: str, now: float):
        """Обновляет статистику при запуске макроса"""
        with self.stats_lock:
            if macro_name not in self.macro_stats:
                self.macro_stats[macro_name] = MacroStats()

            stats = self.macro_stats[macro_name]
            stats.launches += 1
            stats.last_launch_time = now

            # Расчёт средней задержки между запусками
            if stats.launches > 1 and stats.last_launch_time > 0:
                # avg_delay уже считается корректно при каждом запуске
                pass  # Можно доработать при необходимости

    def get_macro_stats(self, macro_name: str) -> Optional[MacroStats]:
        """
        Получить статистику по макросу.

        Args:
            macro_name: Имя макроса

        Returns:
            Статистика или None
        """
        with self.stats_lock:
            return self.macro_stats.get(macro_name)

    def get_all_stats(self) -> Dict[str, MacroStats]:
        """Получить всю статистику"""
        with self.stats_lock:
            return self.macro_stats.copy()

    def export_stats(self) -> str:
        """
        Экспорт статистики для отладки.

        Returns:
            Строка с форматированной статистикой
        """
        with self.stats_lock:
            lines = ["=== MACROS DISPATCHER STATISTICS ==="]

            for name, stats in self.macro_stats.items():
                total_blocked = stats.blocked_cast + stats.blocked_cooldown + stats.blocked_running
                lines.append(
                    f"{name}: "
                    f"launches={stats.launches}, "
                    f"blocked={total_blocked} (cast={stats.blocked_cast}, cd={stats.blocked_cooldown}, run={stats.blocked_running}), "
                    f"queued={stats.queued}, queued_launched={stats.queued_launched}, queued_expired={stats.queued_expired}"
                )

            lines.append("")
            lines.append(f"Total: launched={self.stats['launched']}, blocked_cast={self.stats['blocked_cast']}, blocked_cooldown={self.stats['blocked_cooldown']}, blocked_running={self.stats['blocked_running']}")

            return "\n".join(lines)

    def get_stats(self) -> dict:
        """
        Получить базовую статистику работы диспетчера.

        Returns:
            Словарь со статистикой
        """
        return self.stats.copy()

    def reset_stats(self):
        """Сбросить всю статистику"""
        with self.stats_lock:
            self.macro_stats.clear()

    def cleanup_removed_macro(self, macro_name: str):
        """
        Очищает все ресурсы связанные с удалённым макросом
        Вызывается при удалении макроса из системы
        """
        # Очищаем кэш кулдауна
        self.invalidate_cooldown_cache(macro_name)
        
        # Очищаем статистику
        with self.stats_lock:
            self.macro_stats.pop(macro_name, None)
        
        # Удаляем все вхождения макроса из очереди
        with self.queue_lock:
            self.macro_queue = [qm for qm in self.macro_queue if qm.macro.name != macro_name]
            heapq.heapify(self.macro_queue)
        
        logger.debug(f"🧹 {macro_name}: все ресурсы очищены в диспетчере")

    def stop_all_macros(self, timeout: float = 3.0):
        """
        Остановить все запущенные макросы с таймаутом защиты от зависания.
        Никогда не выполняет блокирующий join() без таймаута!
        """
        self.running = False
        
        stopped_count = 0
        killed_count = 0
        
        if hasattr(self.backend, 'active_macros'):
            for name, macro in list(self.backend.active_macros.items()):
                if hasattr(macro, 'is_alive') and macro.is_alive():
                    try:
                        if hasattr(macro, 'stop'):
                            macro.stop()
                        macro.join(timeout=timeout)
                        
                        if macro.is_alive():
                            # Поток не завершился за таймаут - помечаем мёртвым и больше не трогаем
                            logger.warning(f"Макрос {name} не завершился за {timeout}с, принудительное отключение")
                            killed_count += 1
                        else:
                            stopped_count += 1
                            
                    except Exception as e:
                        logger.error(f"Ошибка при остановке макроса {name}: {e}")
                        killed_count += 1
        
        self.clear_queue()
        
        # Снимаем блокировку каста принудительно
        with self.lock:
            self.cast_lock_until = 0.0
        
        logger.info(f"Макросы остановлены: {stopped_count} нормально, {killed_count} принудительно")
        return stopped_count, killed_count

    def stop(self):
        """Останавливает обработчик очереди (graceful shutdown)"""
        self._queue_stop_event.set()
        logger.info("[DISPATCHER] Обработчик очереди остановлен")
