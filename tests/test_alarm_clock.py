import unittest
from datetime import datetime

from alarm_clock import AlarmClock, parse_alarm_time


class AlarmClockTests(unittest.TestCase):
    def test_parse_future_time_today(self):
        now = datetime(2026, 1, 1, 8, 0, 0)
        self.assertEqual(parse_alarm_time("09:30", now), datetime(2026, 1, 1, 9, 30))

    def test_parse_past_time_rolls_to_tomorrow(self):
        now = datetime(2026, 1, 1, 20, 0, 0)
        self.assertEqual(parse_alarm_time("07:15", now), datetime(2026, 1, 2, 7, 15))

    def test_invalid_time_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_alarm_time("25:99", datetime(2026, 1, 1, 8, 0))

    def test_due_alarm_fires_once(self):
        notified = []
        clock = AlarmClock(notify=notified.append)
        alarm = clock.add_alarm(datetime(2026, 1, 1, 9, 0), "standup")
        self.assertEqual(clock.check_due(datetime(2026, 1, 1, 9, 0)), [alarm])
        self.assertEqual(clock.check_due(datetime(2026, 1, 1, 9, 1)), [])
        self.assertEqual(notified, [alarm])

    def test_cancel_prevents_firing(self):
        notified = []
        clock = AlarmClock(notify=notified.append)
        alarm = clock.add_alarm(datetime(2026, 1, 1, 9, 0), "cancel me")
        self.assertTrue(clock.cancel_alarm(alarm.alarm_id))
        self.assertEqual(clock.check_due(datetime(2026, 1, 1, 10, 0)), [])
        self.assertEqual(notified, [])

    def test_cancel_unknown_or_fired_alarm_returns_false(self):
        clock = AlarmClock(notify=lambda alarm: None)
        self.assertFalse(clock.cancel_alarm(99))
        alarm = clock.add_alarm(datetime(2026, 1, 1, 9, 0))
        clock.check_due(datetime(2026, 1, 1, 9, 0))
        self.assertFalse(clock.cancel_alarm(alarm.alarm_id))


if __name__ == "__main__":
    unittest.main()
