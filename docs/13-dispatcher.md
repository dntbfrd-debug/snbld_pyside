# MacroDispatcher — Single Point of Macro Execution Control

**File:** `backend/macros_dispatcher.py`

The `MacroDispatcher` is the central controller for all macro execution in the snbld resvap system. It guarantees atomic checks and prevents race conditions between macros.

## Class Overview

```python
class MacroDispatcher:
    def __init__(self, backend):
        self.cast_lock_until = 0.0              # Cast block end time
        self.lock = threading.Lock()            # Main lock for atomic operations
        self.macro_queue: list = []             # Priority queue (heapq)
        self.cooldown_cache: Dict[str, float]   # Cooldown cache {name: end_time}
        self.macro_stats: Dict[str, MacroStats] # Per-macro statistics
```

**Key features:**
- Atomic priority checks (no race conditions between macros)
- Centralized cast locking
- Priority queue — macros don't get lost on simultaneous key presses
- Cooldown cache — fast checks without memory reads
- Extended statistics for debugging and analysis

## Priority Levels

| Priority | Type | Examples | Queue Timeout |
|----------|------|----------|---------------|
| 1-3 | Critical | Shield, healing | 2.0s |
| 5 | Normal | Attack | 1.0s |
| 10 | Background | Buff | 0.5s |

Macros with priority 1-3 are added to the queue when blocked. Lower-priority macros are simply rejected.

## Cooldown Cache

The cache stores cooldown end times for each macro, enabling extremely fast checks:

| Method | Time | Description |
|--------|------|-------------|
| Cache check | ~0.05 ms | Read from `Dict[str, float]` |
| Full check | ~0.5 ms | Read from macro attribute + settings lookup |

```python
# Cache structure
self.cooldown_cache = {
    "Fireball": 1713024600.123,  # cooldown end timestamp
    "Shield": 1713024605.456,
}
```

- **TTL:** 30 seconds (auto-cleaned)
- **Invalidation:** `invalidate_cooldown_cache(macro_name)` — single or all
- **Thread-safe:** protected by `cache_lock`

## Cast Lock

Prevents starting new macros while a cast is in progress:

```python
# Set before cast begins (in macro step 2)
self.cast_lock_until = time.time() + lock_duration

# Check in request_macro()
if time.time() < self.cast_lock_until:
    # Cast is blocked — reject or queue
```

**Lock duration calculation:**
```python
actual_cast_time = backend.get_actual_cast_time(cast_time)  # accounts for buffs
margin = backend.settings.get("cast_lock_margin", 0.4)
lock_duration = actual_cast_time + margin
```

## request_macro() Method Flow

```
request_macro(macro, priority=5)
    │
    ├─ 1. Check cast_lock
    │     └─ blocked + priority <= 3 → add to queue, return False
    │
    ├─ 2. Check cooldown cache (fast, ~0.05ms)
    │     └─ in CD + priority <= 3 → add to queue, return False
    │
    ├─ 3. Full cooldown check (macro.last_used + cooldown + margin)
    │     └─ in CD + priority <= 3 → add to queue, return False
    │
    ├─ 4. Check macro.running
    │     └─ already running → return False
    │
    ├─ 5. Check backend.global_stopped
    │     └─ macros stopped → return False
    │
    ├─ 6. Update cooldown cache (set end time)
    │
    ├─ 7. Plan cast lock (set in macro at step 2, not here)
    │
    └─ 8. macro.start() — launch!
```

## Priority Queue Processing

A dedicated background thread (`_process_queue`) runs every 50ms:

```python
def _process_queue(self):
    while not stop_event:
        wait(0.05)  # interruptible
        
        # 1. Remove expired entries
        # 2. If queue not empty and cast_lock expired:
        #    3. Pop highest priority macro (heapq.heappop — O(log n))
        #    4. Re-check cooldown, running, global_stopped
        #    5. Set cast_lock_until
        #    6. macro.start()
```

**Queue properties:**
- Uses `heapq` for O(log n) insertion and extraction
- Sorted by `(priority, timestamp)` — highest priority first, oldest first within same priority
- Expired entries are cleaned on each cycle
- Graceful shutdown via `_queue_stop_event`

## Extended Statistics

Each macro tracks detailed statistics via `MacroStats` dataclass:

```python
@dataclass
class MacroStats:
    launches: int = 0                   # Total launches
    blocked_cast: int = 0               # Blocked by cast lock
    blocked_cooldown: int = 0           # Blocked by cooldown
    blocked_running: int = 0            # Blocked (already running)
    queued: int = 0                     # Added to queue
    queued_launched: int = 0            # Launched from queue
    queued_expired: int = 0             # Queue timeout expired
    last_launch_time: float = 0.0       # Last launch timestamp
    avg_delay_between_launches_ms: float = 0.0
```

**Export example:**
```
=== MACROS DISPATCHER STATISTICS ===
Fireball: launches=45, blocked=12 (cast=8, cd=3, run=1), queued=10, queued_launched=7, queued_expired=3
Shield: launches=120, blocked=5 (cast=2, cd=3, run=0), queued=5, queued_launched=5, queued_expired=0
```

## Priority Handling When Cast is Blocked

When `cast_lock` is active, the behavior depends on priority:

| Priority | Cast Blocked | Cooldown Blocked | Already Running |
|----------|-------------|------------------|-----------------|
| 1-3 | → Queue | → Queue | → Reject |
| 5 | → Reject | → Reject | → Reject |
| 10 | → Reject | → Reject | → Reject |

**Rationale:** Critical macros (shield, heal) are too important to lose. They wait in the queue until the cast finishes. Non-critical macros are simply dropped.

## Thread Safety

All shared state is protected by locks:

| Resource | Lock | Type |
|----------|------|------|
| `cast_lock_until`, main flow | `self.lock` | `threading.Lock` |
| `macro_queue` | `self.queue_lock` | `threading.Lock` |
| `cooldown_cache` | `self.cache_lock` | `threading.Lock` |
| `macro_stats` | `self.stats_lock` | `threading.Lock` |

## Public API

| Method | Description |
|--------|-------------|
| `request_macro(macro, priority=5)` | Request macro launch |
| `is_cast_locked()` | Check if cast is blocked |
| `get_cast_lock_remaining()` | Seconds until cast unlock (0 if free) |
| `invalidate_cooldown_cache(name=None)` | Clear cache (single or all) |
| `get_macro_stats(name)` | Get stats for a macro |
| `export_stats()` | Formatted stats string for debugging |
| `clear_queue()` | Clear all queued macros |
| `get_queue_size()` | Number of macros in queue |
| `get_queue_info()` | List of queued macro details |
| `reset_stats()` | Reset all statistics |
| `stop()` | Graceful shutdown of queue processor |
