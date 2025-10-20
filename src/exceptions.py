"""Domain-specific exceptions for workout tracking."""


class DomainException(Exception):
    """Base exception for all domain errors."""

    pass


class ExerciseNotInTemplate(DomainException):
    """Raised when trying to log a set
    for an exercise not in the current template."""

    def __init__(self, exercise_name: str, available_exercises: list[str]):
        self.exercise_name = exercise_name
        self.available_exercises = available_exercises
        super().__init__(
            f"Exercise '{exercise_name}' not found in template. "
            f"Available exercises: {', '.join(available_exercises)}"
        )


class ExerciseAlreadyCompleted(DomainException):
    """Raised when trying to log a set for an already completed exercise."""

    def __init__(
        self, exercise_name: str, week_index: int, workout_index: int
    ):
        self.exercise_name = exercise_name
        self.week_index = week_index
        self.workout_index = workout_index
        super().__init__(
            f"Exercise '{exercise_name}' already completed for "
            f"week {week_index}, workout {workout_index}"
        )


class InsufficientSetsLogged(DomainException):
    """Raised when trying to complete an exercise without enough sets."""

    def __init__(
        self, exercise_name: str, sets_logged: int, sets_required: int
    ):
        self.exercise_name = exercise_name
        self.sets_logged = sets_logged
        self.sets_required = sets_required
        super().__init__(
            f"Cannot complete exercise '{exercise_name}'. "
            f"Only {sets_logged} of {sets_required}"
            "required sets have been logged"
        )


class WorkoutNotComplete(DomainException):
    """Raised when trying to complete a workout with incomplete exercises."""

    def __init__(self, workout_index: int, missing_exercises: set[str]):
        self.workout_index = workout_index
        self.missing_exercises = missing_exercises
        super().__init__(
            f"Cannot complete workout {workout_index}. "
            f"Missing exercises: {', '.join(missing_exercises)}"
        )
