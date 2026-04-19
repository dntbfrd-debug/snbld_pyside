# Backend — Ping & Delays

## Ping Calculation & Compensation

The compensation formula converts ICMP ping to an estimated game delay and applies a smoothing factor:

```python
def get_ping_compensation() -> float:
    """Returns ping compensation in seconds."""
    icmp_ping = self._settings.get("average_ping", 30)
    GAME_PING_MULTIPLIER = 2.0          # ICMP -> game ping
    game_ping = icmp_ping * GAME_PING_MULTIPLIER
    compensation = min(game_ping / 1000.0 * 0.7 + 0.02, 0.3)
    return compensation
```

**Formula breakdown:**

| Step | Calculation | Example (37 ms ICMP) |
|------|-------------|----------------------|
| Game ping | `icmp_ping x 2.0` | 74 ms |
| Raw compensation | `game_ping / 1000 x 0.7 + 0.02` | 0.0718 s (~72 ms) |
| Capped value | `min(raw, 0.3)` | 0.072 s |

## Delay Modes

### Auto (ping-based) — `use_ping_delays = True`

| Step | Delay |
|------|-------|
| Step 1 (swap to chant) | `30 + ping_compensation_ms` |
| Steps 2-3 (skill, swap back) | `ping_compensation_ms` |

Example with 37 ms ICMP ping:
- Step 1: 30 + 72 = **102 ms**
- Steps 2-3: **72 ms**

### Fixed delays — `use_ping_delays = False`

| Step | Delay | Default |
|------|-------|---------|
| Step 1 | `first_step_delay` | 90 ms |
| Steps 2-3 | `global_step_delay` | 20 ms |

Switching between modes triggers `recalculate_macro_delays()` which updates all macro step delays.

## Ping Monitoring

- **PingMonitor thread** (`threads.py`) sends ICMP pings to the game server at `ping_check_interval`.
- On each update, `on_ping_updated(ping)` is called:
  1. Updates `self._ping`
  2. Saves `average_ping` to settings
  3. If `use_ping_delays` is enabled — recalculates macro delays

**Signal:** `pingUpdated` (int) — emitted to QML whenever a new ping value is available. QML components bind to `Backend.ping` property.

## Buffs & Cast Time

Buffs provide a `channeling_bonus` (percentage) that reduces effective cast time:

```python
def get_current_channeling_bonus() -> int:
    """Total channeling bonus = base + all active buff bonuses."""
    bonus = self._settings.get("base_channeling", 0)
    with self.buff_lock:
        for buff in self.active_buffs.values():
            bonus += buff["bonus"]
    return bonus

def get_actual_cast_time(base_cast_time: float) -> float:
    """Recalculates cast time with channeling bonuses."""
    bonus_total = self.get_current_channeling_bonus()
    if bonus_total > 0:
        return base_cast_time * 100.0 / (100.0 + bonus_total)
    return base_cast_time
```

**Example:**
- Base channeling: 91%
- Active buff bonus: +20%
- Total: 111%
- Cast time 1.0 s becomes: `1.0 x 100 / 211 = 0.47 s`

### Cast Lock Duration

The cast lock duration is recalculated with the actual cast time:

```
lock_duration = actual_cast_time + cast_lock_margin
# Without buff: 0.52 + 0.4 = 0.92 s
# With buff:    0.47 + 0.4 = 0.87 s
```

A shorter cast lock with buffs allows higher-priority macros to execute sooner.

## Key Settings

| Setting | Type | Description |
|---------|------|-------------|
| `average_ping` | int | Baseline ICMP ping (ms) |
| `ping_check_interval` | int | How often PingMonitor polls (seconds) |
| `use_ping_delays` | bool | Switch between auto and fixed delay modes |
| `base_channeling` | int | Base channeling speed bonus (%) |
| `cast_lock_margin` | float | Extra margin added to cast lock (seconds) |
