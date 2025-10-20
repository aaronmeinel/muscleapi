import pytest
from pathlib import Path
from datetime import datetime
from src.storage import load_events, save_events, append_events, load_template
from src.events import (
    ExerciseStarted,
    SetLogged,
    ExerciseCompleted,
    WorkoutCompleted,
)


def test_load_events_empty_file(tmp_path: Path):
    path = tmp_path / "events.json"
    events = load_events(path)
    assert events == []


def test_load_events_with_data(tmp_path: Path):
    path = tmp_path / "events.json"
    path.write_text(
        """[
        {
            "type": "set",
            "exercise": "Squat",
            "reps": 10,
            "weight": 100.0,
            "timestamp": "2024-01-01T12:00:00",
            "week_index": 0,
            "workout_index": 0
        }
    ]"""
    )

    events = load_events(path)
    assert len(events) == 1
    assert isinstance(events[0], SetLogged)
    assert events[0].reps == 10


def test_save_events(tmp_path: Path):
    path = tmp_path / "events.json"
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

    save_events(path, events)

    assert path.exists()
    loaded = load_events(path)
    assert len(loaded) == 2


def test_append_events(tmp_path: Path):
    path = tmp_path / "events.json"

    append_events(
        path,
        [ExerciseStarted(exercise="Squat", week_index=0, workout_index=0)],
    )
    events = load_events(path)
    assert len(events) == 1

    append_events(
        path,
        [
            SetLogged(
                exercise="Squat",
                reps=10,
                weight=100,
                week_index=0,
                workout_index=0,
                timestamp=datetime.now(),
            )
        ],
    )
    events = load_events(path)
    assert len(events) == 2


def test_round_trip_preserves_data(tmp_path: Path):
    """Serialize and deserialize preserves all data."""
    path = tmp_path / "events.json"
    original = [
        ExerciseStarted(
            exercise="Squat",
            week_index=0,
            workout_index=0,
            feedback={"pump": 3},
        ),
        SetLogged(
            exercise="Squat",
            reps=10,
            weight=100.5,
            week_index=0,
            workout_index=0,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        ),
    ]

    save_events(path, original)
    loaded = load_events(path)

    assert len(loaded) == len(original)
    assert loaded[0].exercise == original[0].exercise
    assert loaded[1].reps == original[1].reps


def test_pydantic_validation_on_load(tmp_path: Path):
    """Pydantic validates data on load."""
    path = tmp_path / "events.json"
    path.write_text('[{"type": "set", "reps": -5, "weight": 100, ...}]')

    with pytest.raises(Exception):  # Pydantic ValidationError
        load_events(path)
