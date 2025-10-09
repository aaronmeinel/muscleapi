from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class ExerciseStarted:
    name: str
    workout_index: int
    week_index: int
    feedback: dict


@dataclass(frozen=True)
class ExerciseCompleted:
    name: str
    workout_index: int
    week_index: int
    feedback: dict


@dataclass(frozen=True)
class WorkoutCompleted:
    workout_index: int
    week_index: int
