from src.domain.state import (
    exercise_state,
    workout_state,
    can_log_set,
    can_complete_exercise,
    can_complete_workout,
)
from src.events import (
    ExerciseStarted,
    SetLogged,
    ExerciseCompleted,
    WorkoutCompleted,
)
from datetime import datetime


def test_exercise_state_initial():
    """Port from test_exercise_session_initial"""
    events = []
    state = exercise_state(events, "Squat", 0, 0)

    assert state["started"] is False
    assert state["completed"] is False
    assert len(state["sets"]) == 0
    assert state["exercise"] == "Squat"
    assert state["week_index"] == 0
    assert state["workout_index"] == 0


def test_exercise_state_with_started_event():
    """Port from test_exercise_session_started"""
    events = [ExerciseStarted(exercise="Squat", week_index=0, workout_index=0)]
    state = exercise_state(events, "Squat", 0, 0)

    assert state["started"] is True
    assert state["completed"] is False


def test_exercise_state_with_sets():
    """Port from test_exercise_session_with_sets"""
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
            reps=8,
            weight=100,
            week_index=0,
            workout_index=0,
            timestamp=datetime.now(),
        ),
    ]
    state = exercise_state(events, "Squat", 0, 0)

    assert state["started"] is True
    assert len(state["sets"]) == 2
    assert state["sets"][0].reps == 10
    assert state["sets"][1].reps == 8


def test_exercise_state_filters_other_exercises():
    """Port from existing test"""
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
    state = exercise_state(events, "Squat", 0, 0)

    assert len(state["sets"]) == 1
    assert state["sets"][0].exercise == "Squat"


def test_exercise_state_filters_other_weeks():
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
            reps=12,
            weight=100,
            timestamp=datetime.now(),
        ),
    ]
    state = exercise_state(events, "Squat", 0, 0)

    assert len(state["sets"]) == 1
    assert state["sets"][0].reps == 10


def test_exercise_state_completed():
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
    state = exercise_state(events, "Squat", 0, 0)

    assert state["started"] is True
    assert state["completed"] is True
    assert len(state["sets"]) == 1


# PORT WorkoutSession tests


def test_workout_state_initial():
    events = []
    state = workout_state(events, ["Squat", "Bench"], 0, 0)

    assert state["completed"] is False
    assert len(state["completed_exercises"]) == 0
    assert state["missing_exercises"] == {"Squat", "Bench"}


def test_workout_state_one_exercise_completed():
    events = [
        ExerciseCompleted(
            exercise="Squat", week_index=0, workout_index=0, feedback={}
        )
    ]
    state = workout_state(events, ["Squat", "Bench"], 0, 0)

    assert "Squat" in state["completed_exercises"]
    assert "Squat" not in state["missing_exercises"]
    assert "Bench" in state["missing_exercises"]
    assert state["completed"] is False


def test_workout_state_all_exercises_completed():
    events = [
        ExerciseCompleted(
            exercise="Squat", week_index=0, workout_index=0, feedback={}
        ),
        ExerciseCompleted(
            exercise="Bench", week_index=0, workout_index=0, feedback={}
        ),
        WorkoutCompleted(week_index=0, workout_index=0),
    ]
    state = workout_state(events, ["Squat", "Bench"], 0, 0)

    assert state["completed"] is True
    assert len(state["missing_exercises"]) == 0


# Test query functions


def test_can_log_set_when_not_completed():
    state = exercise_state([], "Squat", 0, 0)
    assert can_log_set(state) is True


def test_can_log_set_when_completed():
    events = [
        ExerciseCompleted(
            exercise="Squat", week_index=0, workout_index=0, feedback={}
        )
    ]
    state = exercise_state(events, "Squat", 0, 0)
    assert can_log_set(state) is False


def test_can_complete_exercise_enough_sets():
    events = [
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
    state = exercise_state(events, "Squat", 0, 0)
    assert can_complete_exercise(state, required_sets=2) is True


def test_can_complete_exercise_not_enough_sets():
    events = [
        SetLogged(
            exercise="Squat",
            reps=10,
            weight=100,
            week_index=0,
            workout_index=0,
            timestamp=datetime.now(),
        ),
    ]
    state = exercise_state(events, "Squat", 0, 0)
    assert can_complete_exercise(state, required_sets=2) is False


def test_can_complete_workout_when_all_done():
    events = [
        ExerciseCompleted(
            exercise="Squat", week_index=0, workout_index=0, feedback={}
        ),
        ExerciseCompleted(
            exercise="Bench", week_index=0, workout_index=0, feedback={}
        ),
    ]
    state = workout_state(events, ["Squat", "Bench"], 0, 0)
    assert can_complete_workout(state) is True


def test_can_complete_workout_when_missing():
    events = [
        ExerciseCompleted(
            exercise="Squat", week_index=0, workout_index=0, feedback={}
        ),
    ]
    state = workout_state(events, ["Squat", "Bench"], 0, 0)
    assert can_complete_workout(state) is False
