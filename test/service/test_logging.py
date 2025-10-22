import pytest
from datetime import datetime
from returns.pipeline import is_successful
from src.service.logging import log_set, complete_exercise, complete_workout
from src.events import ExerciseStarted, SetLogged, ExerciseCompleted
from src.models import Template, Workout, Exercise, SetPrescription


@pytest.fixture(scope="module")
def sample_template():
    return Template(
        name="Test",
        workouts=(
            Workout(
                index=0,
                exercises=(
                    Exercise(
                        "Squat",
                        sets=(
                            SetPrescription(
                                prescribed_reps=10, prescribed_weight=100
                            ),
                            SetPrescription(
                                prescribed_reps=10, prescribed_weight=100
                            ),
                        ),
                    ),
                    Exercise(
                        "Bench",
                        sets=(
                            SetPrescription(
                                prescribed_reps=8, prescribed_weight=60
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def test_log_set_success(sample_template):
    events = []
    result = log_set(events, sample_template, "Squat", 10, 100)

    assert is_successful(result)
    new_events = result.unwrap()
    assert len(new_events) == 2  # Started + Set
    assert isinstance(new_events[0], ExerciseStarted)
    assert isinstance(new_events[1], SetLogged)


def test_log_set_second_set_no_started_event(sample_template):
    events = [
        ExerciseStarted(exercise="Squat", week_index=0, workout_index=0),
        SetLogged(
            exercise="Squat",
            reps=10,
            weight=100,
            week_index=0,
            workout_index=0,
            timestamp=datetime.now(),
        ),
    ]

    result = log_set(events, sample_template, "Squat", 9, 100)

    assert is_successful(result)
    new_events = result.unwrap()
    assert len(new_events) == 1  # Just Set, no Started


def test_log_set_unknown_exercise(sample_template):
    events = []
    result = log_set(events, sample_template, "InvalidExercise", 10, 100)

    assert not is_successful(result)
    assert "Unknown exercise" in result.failure()


def test_log_set_exercise_already_completed(sample_template):
    events = [
        ExerciseStarted(exercise="Squat", week_index=0, workout_index=0),
        SetLogged(
            exercise="Squat",
            reps=10,
            weight=100,
            week_index=0,
            workout_index=0,
            timestamp=datetime.now(),
        ),
        ExerciseCompleted(
            exercise="Squat", week_index=0, workout_index=0, feedback={}
        ),
    ]

    result = log_set(events, sample_template, "Squat", 10, 100)

    assert not is_successful(result)
    assert "already completed" in result.failure()


def test_complete_exercise_success(sample_template):
    events = [
        ExerciseStarted(exercise="Squat", week_index=0, workout_index=0),
        SetLogged(
            exercise="Squat",
            reps=10,
            weight=100,
            week_index=0,
            workout_index=0,
            timestamp=datetime.now(),
        ),
        SetLogged(
            exercise="Squat",
            reps=10,
            weight=100,
            week_index=0,
            workout_index=0,
            timestamp=datetime.now(),
        ),
    ]

    result = complete_exercise(
        events, sample_template, "Squat", {"pump": 3, "pain": 0, "workload": 2}
    )

    assert is_successful(result)
    new_events = result.unwrap()
    assert len(new_events) == 1
    assert isinstance(new_events[0], ExerciseCompleted)


def test_complete_exercise_not_enough_sets(sample_template):
    events = [
        ExerciseStarted(exercise="Squat", week_index=0, workout_index=0),
        SetLogged(
            exercise="Squat",
            reps=10,
            weight=100,
            week_index=0,
            workout_index=0,
            timestamp=datetime.now(),
        ),
    ]

    result = complete_exercise(
        events, sample_template, "Squat", {"pump": 3, "pain": 0, "workload": 2}
    )

    assert not is_successful(result)
    assert "only 1 of 2 sets" in result.failure()


# Property-based tests (NEW)
from hypothesis import given, strategies as st


@given(
    reps=st.integers(min_value=1, max_value=50),
    weight=st.floats(
        min_value=1.25, max_value=500.0, allow_nan=False, allow_infinity=False
    ),
)
def test_log_set_valid_ranges(sample_template, reps, weight):
    events = []
    result = log_set(events, sample_template, "Squat", reps, weight)

    assert is_successful(result)
    new_events = result.unwrap()
    assert new_events[1].reps == reps
    assert new_events[1].weight == weight
