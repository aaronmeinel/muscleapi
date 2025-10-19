from pydantic import Field
from pydantic.dataclasses import dataclass
from typing import Literal, Union
from datetime import datetime


@dataclass(frozen=True)
class ExerciseStarted:
    exercise: str
    week_index: int
    workout_index: int
    feedback: dict[str, int] = Field(default_factory=dict)
    type: Literal["exercise_started"] = "exercise_started"


@dataclass(frozen=True)
class SetLogged:
    exercise: str
    timestamp: datetime
    week_index: int
    workout_index: int
    reps: int = Field(gt=0)
    weight: float = Field(gt=0)
    type: Literal["set"] = "set"


@dataclass(frozen=True)
class ExerciseCompleted:
    exercise: str
    workout_index: int
    week_index: int
    feedback: dict[str, int]
    type: Literal["exercise_completed"] = "exercise_completed"


@dataclass(frozen=True)
class WorkoutCompleted:
    workout_index: int
    week_index: int
    type: Literal["workout_completed"] = "workout_completed"


Event = Union[ExerciseStarted, ExerciseCompleted, SetLogged, WorkoutCompleted]
