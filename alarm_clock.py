"""A small, dependency-free CLI alarm clock."""
from __future__ import annotations

import argparse
import itertools
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable


@dataclass
class Alarm:
    alarm_id: int
    when: datetime
    label: str = "Alarm"
    fired: bool = False
    cancelled: bool = False


def parse_alarm_time(value: str, now: datetime | None = None) -> datetime:
    """Parse HH:MM into the next local occurrence of that time."""
    try:
        parsed = datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise ValueError("Time must use 24-hour HH:MM format, e.g. 07:30 or 18:45.") from exc

    current = now or datetime.now()
    target = current.replace(
        hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
    )
    if target <= current:
        target += timedelta(days=1)
    return target


@dataclass
class AlarmClock:
    notify: Callable[[Alarm], None] | None = None
    poll_interval: float = 0.25
    _alarms: dict[int, Alarm] = field(default_factory=dict)
    _ids: itertools.count = field(default_factory=lambda: itertools.count(1))
    _stop_event: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = None

    def __post_init__(self) -> None:
        if self.notify is None:
            self.notify = print_notification

    def add_alarm(self, when: datetime, label: str = "Alarm") -> Alarm:
        label = label.strip() or "Alarm"
        alarm = Alarm(next(self._ids), when, label)
        self._alarms[alarm.alarm_id] = alarm
        return alarm

    def list_alarms(self) -> list[Alarm]:
        return sorted(
            (a for a in self._alarms.values() if not a.cancelled and not a.fired),
            key=lambda a: (a.when, a.alarm_id),
        )

    def cancel_alarm(self, alarm_id: int) -> bool:
        alarm = self._alarms.get(alarm_id)
        if alarm is None or alarm.cancelled or alarm.fired:
            return False
        alarm.cancelled = True
        return True

    def check_due(self, now: datetime | None = None) -> list[Alarm]:
        current = now or datetime.now()
        due = []
        for alarm in self._alarms.values():
            if not alarm.cancelled and not alarm.fired and alarm.when <= current:
                alarm.fired = True
                due.append(alarm)
                assert self.notify is not None
                self.notify(alarm)
        return due

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="alarm-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=max(1.0, self.poll_interval * 4))

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self.check_due()
            self._stop_event.wait(self.poll_interval)


def print_notification(alarm: Alarm) -> None:
    print(f"\n\n⏰ ALARM: {alarm.label} — {alarm.when.strftime('%H:%M')}\n", flush=True)
    # Terminal bell is best-effort; some terminals mute it.
    print("\a", end="", flush=True)


def run_cli() -> int:
    parser = argparse.ArgumentParser(description="Simple Python CLI alarm clock")
    parser.add_argument("--check-only", action="store_true",
                        help="run one due-alarm check and exit (useful for scripting)")
    args = parser.parse_args()

    clock = AlarmClock()
    if args.check_only:
        clock.check_due()
        return 0

    clock.start()
    print("Alarm Clock CLI")
    print("Commands: add HH:MM [label] | list | cancel ID | help | quit")
    print("Times use local 24-hour time. Alarms are kept in memory for this session.")

    try:
        while True:
            try:
                command = input("alarm> ").strip()
            except EOFError:
                break
            if not command:
                continue

            parts = command.split()
            action = parts[0].lower()

            if action in {"quit", "exit"}:
                break
            if action == "help":
                print("add HH:MM [label]  Create an alarm for the next occurrence.")
                print("list               Show pending alarms.")
                print("cancel ID          Cancel a pending alarm.")
                print("quit               Exit the application.")
            elif action == "add":
                if len(parts) < 2:
                    print("Usage: add HH:MM [label]")
                    continue
                try:
                    when = parse_alarm_time(parts[1])
                except ValueError as exc:
                    print(f"Invalid time: {exc}")
                    continue
                label = " ".join(parts[2:]) or "Alarm"
                alarm = clock.add_alarm(when, label)
                print(f"Created alarm #{alarm.alarm_id}: {alarm.label} at {when:%Y-%m-%d %H:%M}")
            elif action == "list":
                alarms = clock.list_alarms()
                if not alarms:
                    print("No pending alarms.")
                else:
                    for alarm in alarms:
                        print(f"#{alarm.alarm_id}  {alarm.when:%Y-%m-%d %H:%M}  {alarm.label}")
            elif action == "cancel":
                if len(parts) != 2:
                    print("Usage: cancel ID")
                    continue
                try:
                    alarm_id = int(parts[1])
                except ValueError:
                    print("Alarm ID must be an integer.")
                    continue
                print("Alarm cancelled." if clock.cancel_alarm(alarm_id)
                      else f"No pending alarm found with ID {alarm_id}.")
            else:
                print("Unknown command. Type 'help' to see available commands.")
    except KeyboardInterrupt:
        print("\nInterrupted; shutting down.")
    finally:
        clock.stop()
    print("Goodbye.")
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
