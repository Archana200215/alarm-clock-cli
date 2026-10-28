# Alarm Clock CLI

A dependency-free Python command-line alarm clock built with the standard library.

## Requirements and scope

- Create an alarm using local 24-hour time (`HH:MM`) and an optional label.
- Schedule the next occurrence of a time; if that time has already passed today, schedule it for tomorrow.
- List pending alarms and cancel an alarm by ID.
- Notify when an alarm is due using a terminal message and best-effort terminal bell.
- Support multiple alarms, graceful shutdown, and clear input errors.
- No web UI, database, or third-party packages. Alarms exist only for the current process.

## Run

Requires Python 3.10 or newer.

```bash
python alarm_clock.py
```

Example session:

```text
Alarm Clock CLI
Commands: add HH:MM [label] | list | cancel ID | help | quit
alarm> add 23:59 Review PR
Created alarm #1: Review PR at 2026-10-28 23:59
alarm> list
#1  2026-10-28 23:59  Review PR
alarm> cancel 1
Alarm cancelled.
alarm> quit
Goodbye.
```

Commands:
- `add HH:MM [label]` — create an alarm for the next occurrence.
- `list` — list pending alarms.
- `cancel ID` — cancel a pending alarm.
- `help` — show command help.
- `quit` / `exit` — stop the monitor and exit.

## Tests

Run from the project root:

```bash
python -m unittest discover -s tests -v
```

The tests cover time parsing, midnight rollover, invalid input, one-time firing, and cancellation.

## Design decisions

- **Standard library only:** keeps setup friction low and respects the CLI-only constraint.
- **Separate domain logic from CLI parsing:** `AlarmClock` and `parse_alarm_time` can be tested without interactive input.
- **One monitor thread:** checks pending alarms at a short interval, rather than creating one thread per alarm.
- **One-shot alarms:** fired alarms are not repeated; recurring alarms were left out to keep behavior predictable within the exercise.
- **In-memory state:** no persistence because a database is explicitly out of scope.
- **Terminal notification:** portable fallback with a terminal bell; actual audible behavior depends on terminal settings.

## Known limitations

- The process must remain running for alarms to trigger.
- Alarms are not persisted across restarts.
- Notification sound is terminal-dependent.
- Times use the machine's local timezone; daylight-saving and timezone selection are not configurable.
