from typing import TypedDict

from src.events import SetLogged


class ExerciseState(TypedDict):
    started: bool
    completed: bool
    sets: list[SetLogged]
    exercise: str
    week_index: int
    workout_index: int


class WorkoutState(TypedDict):
    completed: bool
    completed_exercises: set[str]
    missing_exercises: set[str]
    week_index: int
    workout_index: int
