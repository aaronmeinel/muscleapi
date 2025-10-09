from pytest import fixture

from src.events import ExerciseCompleted, ExerciseStarted
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

    assert len(log_repo.all()) == 2  # One set event + one started event
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
    result = service.log_set(
        exercise_name,
        5,
        100,
    )
    assert is_successful(result)

    assert len(repo.all()) == 2  # One set event + one started event

    service.log_set(exercise_name, 5, 100)
    assert len(repo.all()) == 3

    events = repo.all()
    assert all(
        isinstance(event, Set)
        or isinstance(event, ExerciseStarted)
        or isinstance(event, ExerciseCompleted)
        for event in events
    )
    assert len(events) == 3


def test_show_current_day(mock_template_repository):
    repo = MockLogRepository()
    service = LoggingService(
        log_repository=repo, template_repository=mock_template_repository
    )
    service.log_set("Squat", 11, 100)
    service.log_set("Bench press", 12, 100)

    todays_events = repo.all()
    assert len(todays_events) == 4  # 2 sets + 2 started events
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


def test_log_exercise_started(mock_template_repository):
    """When logging a set for an exercise for the first time,
    We need to gather information on how the previous workout went,
    for that exercise (soreness etc.).
    Therefore, we want to log a "started" event for that exercise,
    that indicates that the exercise is now active.
    This event should be logged only once per exercise per workout.
    This event should contain the feedback.

    """

    repo = MockLogRepository()
    service = LoggingService(
        log_repository=repo, template_repository=mock_template_repository
    )

    template = mock_template_repository.get()
    exercises = template.workouts[0].exercises

    for exercise in exercises:  # Log a set for each exercise in the plan
        # Conveniently, we defined the example template to contain
        # one set per exercise.
        service.log_set(exercise.name, 5, 100)

    assert (
        len(repo.all()) == 6
    )  # One set event per exercise (3) + one started event per exercise (3)
    # Since each exercise is logged for the first time,
    # we should also have a "started" event for each exercise
    started_events = [
        event
        for event in repo.all()
        if event.__class__.__name__ == "ExerciseStarted"
    ]
    assert len(started_events) == 3  # One started event per exercise

    # Now log another set for the first exercise
    service.log_set(exercises[0].name, 5, 100)
    assert len(repo.all()) == 7  # Another set event should be logged

    # Now check that no "started" event was logged
    started_events = [
        event
        for event in repo.all()
        if event.__class__.__name__ == "ExerciseStarted"
    ]
    assert (
        len(started_events) == 3
    )  # Still only one started event per exercise


def test_log_exercise_completed(mock_template_repository):
    """We want to allow logging sets above the prescribed amount.
    Therefore, the user can keep logging sets of an exercise, as long as the exercise is active,
    i.e. it has not been logged as completed.
    Once the exercise is completed, no more sets can be logged for that exercise, since the completion
    also contains feedback that we need for future prescriptions.
    Also, we need that information to be able to tell whether the workout is completed or not, which in turn
    is needed to determine the current workout and week.

    So here we expect that after completing an exercise:
        - further sets for that exercise are rejected.
        - we have a completed event in the log repository, that also contains feedback.
    """
    repo = MockLogRepository()
    service = LoggingService(
        log_repository=repo, template_repository=mock_template_repository
    )

    template = mock_template_repository.get()
    exercises = template.workouts[0].exercises

    for exercise in exercises:  # Log a set for each exercise in the plan
        # Conveniently, we defined the example template to contain
        # one set per exercise.
        service.log_set(exercise.name, 5, 100)

    assert (
        len(repo.all()) == 6
    )  # One set event per exercise (3) + one started event per exercise (3)
    exercise_name = exercises[0].name
    completion_result = service.complete_exercise(
        exercise_name, {"soreness": 2}
    )
    assert is_successful(completion_result)
    assert len(repo.all()) == 7  # One completed event should be logged
    completed_event = repo.get()
    assert completed_event is not None
    assert completed_event.name == exercise_name

    log_result = service.log_set(exercise_name, 5, 100)
    assert not is_successful(log_result)
    assert "already completed" in log_result.failure().args[0]


def test_log_workout_completed_happy_path(mock_template_repository):
    """When completing a workout, we need to ensure that all exercises in the workout are completed.
    If not, we should reject the completion request.
    The workout completion should be logged as well.
    Furthermore, a workout completion should trigger the start of the next workout.
    That means that from that point on, the workout index should be incremented,
    and sets should be logged against the new workout.
    """
    repo = MockLogRepository()
    service = LoggingService(
        log_repository=repo, template_repository=mock_template_repository
    )
    template = mock_template_repository.get()
    exercises = template.workouts[0].exercises  # First workout
    for exercise in exercises:  # Log a set for each exercise in the plan
        service.log_set(exercise.name, 5, 100)
    assert (
        len(repo.all()) == 6
    )  # One set event per exercise (3) + one started event per exercise (3)
    # Now complete all exercises
    for exercise in exercises:
        service.complete_exercise(exercise.name, {"soreness": 2})
    assert len(repo.all()) == 9  # 6 + 3 completed events
    workout_completion_result = service.complete_workout()
    assert is_successful(workout_completion_result)
    assert (
        len(repo.all()) == 10
    )  # One workout completed event should be logged


def test_log_workout_completed_reject_incomplete_workout(
    mock_template_repository,
):
    repo = MockLogRepository()
    service = LoggingService(
        log_repository=repo, template_repository=mock_template_repository
    )
    template = mock_template_repository.get()
    exercises = template.workouts[0].exercises  # First workout
    for exercise in exercises:  # Log a set for each exercise in the plan
        service.log_set(exercise.name, 5, 100)
    assert (
        len(repo.all()) == 6
    )  # One set event per exercise (3) + one started event per exercise (3)
    # Now complete only one exercise
    service.complete_exercise(exercises[0].name, {"soreness": 2})
    assert len(repo.all()) == 7  # 6 + 1 completed event
    workout_completion_result = service.complete_workout()
    assert not is_successful(workout_completion_result)
    assert "completed" in workout_completion_result.failure().args[0]
    assert len(repo.all()) == 7  # No workout completed event should be logged


def test_exercises_logged_after_one_workout_completed_will_have_incremented_workout_index(
    mock_template_repository,
):

    repo = MockLogRepository()
    service = LoggingService(
        log_repository=repo, template_repository=mock_template_repository
    )
    template = mock_template_repository.get()
    exercises = template.workouts[0].exercises  # First workout
    for exercise in exercises:  # Log a set for each exercise in the plan
        service.log_set(exercise.name, 5, 100)
    assert (
        len(repo.all()) == 6
    )  # One set event per exercise (3) + one started event per exercise (3)
    # Now complete all exercises
    for exercise in exercises:
        service.complete_exercise(exercise.name, {"soreness": 2})
    assert len(repo.all()) == 9  # 6 + 3 completed events
    # Complete the workout
    completion_result = service.complete_workout()
    assert is_successful(completion_result)

    # Now log a set for the first exercise again
    first_exercise = template.workouts[1].exercises[0]  # Second workout
    exercise = first_exercise.name
    log_result = service.log_set(first_exercise.name, 5, 100)
    assert is_successful(log_result)

    last_event = repo.get()
    assert last_event is not None
    assert last_event.workout_index == 1  # Should be the next workout index
    assert last_event.exercise == first_exercise.name
