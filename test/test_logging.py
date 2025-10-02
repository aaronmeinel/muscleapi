from datetime import datetime
from typing import Optional

from src.models import Set
from src.presentation import current_day_format
from src.service import LoggingService, Repository
from src.repository import JSONRepository


class MockRepository(Repository):
    def __init__(self):
        self.events = []

    def add(self, event):
        self.events.append(event)

    def all(self) -> list:
        return self.events

    def get(self):
        return self.events[-1] if self.events else None

    def get_by_date(self, date) -> list:

        return [e for e in self.events if e.timestamp.date() == date.date()]


def test_log_set():
    repo = MockRepository()
    service = LoggingService(repository=repo)
    service.log_set("squat", 5, 100.0)

    assert len(repo.all()) == 1
    _set = repo.get()
    assert _set.exercise == "squat"
    assert _set.reps == 5
    assert _set.weight == 100.0


def test_json_repository_loads_nonexistent_file(tmp_path):
    repo = JSONRepository(tmp_path / "nonexistent.json")
    assert repo.all() == []


def test_log_set_json(tmp_path):

    repo = JSONRepository(tmp_path / "events.json")
    service = LoggingService(repository=repo)
    service.log_set("squat", 5, 100)
    assert len(repo.all()) == 1

    service.log_set("squat", 5, 100)
    assert len(repo.all()) == 2

    events = repo.all()
    assert all(isinstance(e, Set) for e in events)


def test_show_current_day():
    repo = MockRepository()
    service = LoggingService(repository=repo)
    service.log_set("squat", 11, 100)
    service.log_set("bench press", 10, 80)

    todays_events = repo.get_by_date(date=datetime.now())
    assert len(todays_events) == 2
    logged_exercises = current_day_format(todays_events)
    expected_logged_exercises = {
        "squat": [
            {
                "performed_reps": 11,
                "performed_weight": 100,
                "prescribed_reps": 12,  # Should be the same as in exercises_planned
                "prescribed_weight": 100,  # We store this here for prediction purposes, but this is not used in the UI
            },
        ],
        "bench press": [
            {
                "performed_reps": 9,
                "performed_weight": 82.5,
                "prescribed_reps": 10,
                "prescribed_weight": 80,
            }
        ],
    }
