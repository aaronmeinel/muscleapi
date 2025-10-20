import pytest
from src.domain.helpers import filter_by_context, filter_events_by_type
from src.events import Event, SetLogged, ExerciseStarted, ExerciseCompleted
from datetime import datetime


def test_filter_by_context_exercise():
    events = [
        SetLogged(
            exercise="Squat",
            week_index=0,
            workout_index=0,
            reps=10,
            weight=100,
            timestamp=datetime.now(),
        ),
        SetLogged(
            exercise="Bench",
            week_index=0,
            workout_index=0,
            reps=8,
            weight=60,
            timestamp=datetime.now(),
        ),
    ]
    result = filter_by_context(events, exercise="Squat")
    assert len(result) == 1
    assert result[0].exercise == "Squat"


def test_filter_by_context_week_and_workout():
    events = [
        SetLogged(
            exercise="Squat",
            week_index=0,
            workout_index=0,
            reps=10,
            weight=100,
            timestamp=datetime.now(),
        ),
        SetLogged(
            exercise="Squat",
            week_index=1,
            workout_index=0,
            reps=10,
            weight=100,
            timestamp=datetime.now(),
        ),
    ]
    result = filter_by_context(events, week=0, workout=0)
    assert len(result) == 1


@pytest.mark.parametrize(
    "exercise,week,workout,expected_count",
    [
        ("Squat", None, None, 2),
        (None, 0, None, 2),
        ("Squat", 0, 0, 1),
        ("Bench", 1, 1, 0),
    ],
)
def test_filter_by_context_combinations(
    exercise: str | None,
    week: int | None,
    workout: int | None,
    expected_count: int,
):
    events: list[Event] = [
        SetLogged(
            exercise="Squat",
            week_index=0,
            workout_index=0,
            reps=10,
            weight=100,
            timestamp=datetime.now(),
        ),
        SetLogged(
            exercise="Squat",
            week_index=1,
            workout_index=0,
            reps=10,
            weight=100,
            timestamp=datetime.now(),
        ),
        ExerciseStarted(exercise="Bench", week_index=0, workout_index=0),
    ]
    result = filter_by_context(
        events, exercise=exercise, week=week, workout=workout
    )
    assert len(result) == expected_count


def test_filter_events_by_type():
    events = [
        SetLogged(
            exercise="Squat",
            reps=10,
            weight=100,
            week_index=0,
            workout_index=0,
            timestamp=datetime.now(),
        ),
        ExerciseStarted(exercise="Squat", week_index=0, workout_index=0),
        ExerciseCompleted(
            exercise="Squat", week_index=0, workout_index=0, feedback={}
        ),
    ]
    sets = filter_events_by_type(events, SetLogged)
    assert len(sets) == 1
    assert isinstance(sets[0], SetLogged)
