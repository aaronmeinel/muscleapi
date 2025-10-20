import pytest
from src.domain.reducers import process_exercise_event, process_workout_event
from src.domain.types import ExerciseState, WorkoutState
from src.events import (
    ExerciseStarted,
    ExerciseCompleted,
    SetLogged,
    WorkoutCompleted,
)
from datetime import datetime


def test_process_exercise_event_started():
    state: ExerciseState = {
        "started": False,
        "completed": False,
        "sets": [],
        "exercise": "Squat",
        "week_index": 0,
        "workout_index": 0,
    }
    event = ExerciseStarted(exercise="Squat", week_index=0, workout_index=0)
    result = process_exercise_event(state, event)

    assert result["started"] is True
    assert result["completed"] is False
    assert len(result["sets"]) == 0


def test_process_exercise_event_set_logged():
    state: ExerciseState = {
        "started": True,
        "completed": False,
        "sets": [],
        "exercise": "Squat",
        "week_index": 0,
        "workout_index": 0,
    }
    event = SetLogged(
        exercise="Squat",
        reps=10,
        weight=100,
        week_index=0,
        workout_index=0,
        timestamp=datetime.now(),
    )
    result = process_exercise_event(state, event)

    assert len(result["sets"]) == 1
    assert result["sets"][0].reps == 10
    assert result["started"] is True  # Unchanged


def test_process_exercise_event_completed():
    state: ExerciseState = {
        "started": True,
        "completed": False,
        "sets": [
            SetLogged(
                exercise="Squat",
                reps=10,
                weight=100,
                week_index=0,
                workout_index=0,
                timestamp=datetime.now(),
            )
        ],
        "exercise": "Squat",
        "week_index": 0,
        "workout_index": 0,
    }
    event = ExerciseCompleted(
        exercise="Squat", week_index=0, workout_index=0, feedback={}
    )
    result = process_exercise_event(state, event)

    assert result["completed"] is True
    assert len(result["sets"]) == 1  # Unchanged


@pytest.mark.parametrize(
    "initial_started,initial_completed,event_type,expected_started,expected_completed",
    [
        (False, False, ExerciseStarted, True, False),
        (True, False, ExerciseCompleted, True, True),
        (
            True,
            True,
            ExerciseStarted,
            True,
            True,
        ),  # No change when already completed
    ],
)
def test_process_exercise_event_state_transitions(
    initial_started,
    initial_completed,
    event_type,
    expected_started,
    expected_completed,
):
    state: ExerciseState = {
        "started": initial_started,
        "completed": initial_completed,
        "sets": [],
        "exercise": "Squat",
        "week_index": 0,
        "workout_index": 0,
    }
    event = (
        event_type(exercise="Squat", week_index=0, workout_index=0)
        if event_type != ExerciseCompleted
        else ExerciseCompleted(
            exercise="Squat", week_index=0, workout_index=0, feedback={}
        )
    )
    result = process_exercise_event(state, event)

    assert result["started"] == expected_started
    assert result["completed"] == expected_completed


def test_process_workout_event_exercise_completed():
    state: WorkoutState = {
        "completed": False,
        "completed_exercises": set(),
        "missing_exercises": {"Squat", "Bench"},
        "week_index": 0,
        "workout_index": 0,
    }
    event = ExerciseCompleted(
        exercise="Squat", week_index=0, workout_index=0, feedback={}
    )
    result = process_workout_event(state, event)

    assert "Squat" in result["completed_exercises"]
    assert "Squat" not in result["missing_exercises"]
    assert "Bench" in result["missing_exercises"]
    assert result["completed"] is False


def test_process_workout_event_workout_completed():
    state: WorkoutState = {
        "completed": False,
        "completed_exercises": {"Squat", "Bench"},
        "missing_exercises": set(),
        "week_index": 0,
        "workout_index": 0,
    }
    event = WorkoutCompleted(week_index=0, workout_index=0)
    result = process_workout_event(state, event)

    assert result["completed"] is True
