from pytest import fixture

from src.models import Set
from src.presentation import current_day_format
from src.service import LoggingService, Repository
from src.repository import JSONRepository
from returns.pipeline import is_successful


class MockLogRepository(Repository):
    def __init__(self):
        self.events = []

    def add(self, event):
        self.events.append(event)

    def all(self) -> list:
        return self.events

    def get(self):
        return self.events[-1] if self.events else None

    def get_by_date(self, date) -> list:

        return [
            log_event
            for log_event in self.events
            if log_event.timestamp.date() == date.date()
        ]


@fixture
def mock_template_repository(sample_template):
    class MockTemplateRepository(Repository):
        def get(self) -> object:
            return sample_template

        def add(self):
            raise NotImplementedError

        def all(self):
            raise NotImplementedError

    return MockTemplateRepository()


def test_log_set(mock_template_repository):
    log_repo = MockLogRepository()
    service = LoggingService(
        log_repository=log_repo, template_repository=mock_template_repository
    )
    exercise_name = "Squat"
    log_result = service.log_set(exercise_name, 5, 100.0)
    assert is_successful(log_result)

    assert len(log_repo.all()) == 1
    _set = log_repo.get()
    assert _set.exercise == exercise_name
    assert _set.reps == 5
    assert _set.weight == 100.0


def test_log_set_json(tmp_path, mock_template_repository):

    repo = JSONRepository(tmp_path / "events.json")
    service = LoggingService(
        log_repository=repo, template_repository=mock_template_repository
    )
    exercise_name = "Squat"
    result = service.log_set(exercise_name, 5, 100)
    assert is_successful(result)

    assert len(repo.all()) == 1

    service.log_set(exercise_name, 5, 100)
    assert len(repo.all()) == 2

    events = repo.all()
    assert all(isinstance(event, Set) for event in events)
    assert len(events) == 2


def test_show_current_day(mock_template_repository):
    repo = MockLogRepository()
    service = LoggingService(
        log_repository=repo, template_repository=mock_template_repository
    )
    service.log_set("Squat", 11, 100)
    service.log_set("Bench press", 12, 100)

    todays_events = repo.all()
    assert len(todays_events) == 2
    logged_exercises = current_day_format(todays_events)
    expected_logged_exercises = {
        "Squat": [
            {
                "performed_reps": 11,
                "performed_weight": 100,
                "prescribed_reps": 11,  # Should be the same as in exercises_planned
                "prescribed_weight": 100,  # We store this here for prediction purposes, but this is not used in the UI
            },
        ],
        "Bench press": [
            {
                "performed_reps": 12,
                "performed_weight": 100,
                "prescribed_reps": 12,
                "prescribed_weight": 100,
            }
        ],
    }
    assert logged_exercises == expected_logged_exercises
