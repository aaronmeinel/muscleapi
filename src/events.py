from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class ExerciseStarted:
    exercise: str
    workout_index: int
    week_index: int
    feedback: dict

    def __hash__(self):
        return hash((self.exercise, self.workout_index, self.week_index))


@dataclass(frozen=True)
class ExerciseCompleted:
    exercise: str
    workout_index: int
    week_index: int
    feedback: dict

    def __hash__(self):
        return hash((self.exercise, self.workout_index, self.week_index))


@dataclass(frozen=True)
class WorkoutCompleted:
    workout_index: int
    week_index: int
