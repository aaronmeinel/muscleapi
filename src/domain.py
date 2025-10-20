"""Domain aggregates for workout tracking.

This module contains domain models that encapsulate state-building logic
and business rules for exercise sessions and workouts.
"""

from dataclasses import dataclass

from src.models import Set
from src.events import (
    Event,
    ExerciseStarted,
    ExerciseCompleted,
    WorkoutCompleted,
)


from src.domain.state import exercise_state as _exercise_state
from src.domain.state import can_log_set as _can_log_set


@dataclass
class ExerciseSession:
    """Aggregate representing an exercise session.

    Encapsulates the state and business logic for tracking sets
    and completion status of an exercise within a workout.

    Degraded to thin wrapper - will be removed in future.
    """

    exercise_name: str
    week_index: int
    workout_index: int
    events: list[Event]  # All events from the log

    def __post_init__(self):
        state = _exercise_state(
            self.events,
            self.exercise_name,
            self.week_index,
            self.workout_index,
        )
        self._started = state["started"]
        self._completed = state["completed"]
        self._sets = state["sets"]

    @property
    def is_started(self) -> bool:
        """Returns True if the exercise has been started."""
        return self._started

    @property
    def is_completed(self) -> bool:
        """Returns True if the exercise has been completed."""
        return self._completed

    @property
    def sets(self) -> list[Set]:
        """Returns all sets logged for this exercise."""
        return self._sets

    @property
    def is_first_set(self) -> bool:
        """Returns True if no sets have been logged for this exercise yet."""
        return len(self._sets) == 0

    def can_log_set(self) -> bool:
        """Returns True if a set can be logged for this exercise."""
        return not self.is_completed

    def can_complete(self, required_sets: int) -> bool:
        """Returns True if the exercise can be marked as completed.

        Args:
            required_sets: Number of sets required by the template.
        """
        return len(self._sets) >= required_sets and not self.is_completed


@dataclass
class WorkoutSession:
    """Aggregate representing a workout session.

    Encapsulates the state and business logic for tracking exercises
    and completion status of a workout.
    """

    week_index: int
    workout_index: int
    exercise_names: list[str]  # Required exercises from template
    events: list  # All events from the log

    def __post_init__(self):
        """Build state from events after initialization."""
        self._completed = False
        self._completed_exercises = set()

        for event in self.events:
            if isinstance(event, WorkoutCompleted):
                if (
                    event.week_index == self.week_index
                    and event.workout_index == self.workout_index
                ):
                    self._completed = True

            elif isinstance(event, ExerciseCompleted):
                if (
                    event.week_index == self.week_index
                    and event.workout_index == self.workout_index
                ):
                    self._completed_exercises.add(event.exercise)

    @property
    def is_completed(self) -> bool:
        """Returns True if the workout has been completed."""
        return self._completed

    @property
    def completed_exercises(self) -> set[str]:
        """Returns the set of completed exercise names."""
        return self._completed_exercises

    @property
    def missing_exercises(self) -> set[str]:
        """Returns the set of exercises that haven't been completed yet."""
        return set(self.exercise_names) - self._completed_exercises

    def can_complete(self) -> bool:
        """Returns True if the workout can be marked as completed."""
        return len(self.missing_exercises) == 0 and not self.is_completed

    def get_exercise_session(self, exercise_name: str) -> ExerciseSession:
        """Returns an ExerciseSession for the given exercise."""
        return ExerciseSession(
            exercise_name=exercise_name,
            week_index=self.week_index,
            workout_index=self.workout_index,
            events=self.events,
        )
