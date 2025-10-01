from typing import Optional

from src.models import Set
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
