from functools import reduce
from src.domain.types import ExerciseState, WorkoutState
from src.domain.helpers import filter_by_context
from src.domain.reducers import process_exercise_event, process_workout_event
from src.events import Event


def exercise_state(
    events: list[Event], exercise: str, week: int, workout: int
) -> ExerciseState:
    """Build exercise state from events (pure)."""
    relevant = filter_by_context(
        events, exercise=exercise, week=week, workout=workout
    )

    initial: ExerciseState = {
        "started": False,
        "completed": False,
        "sets": [],
        "exercise": exercise,
        "week_index": week,
        "workout_index": workout,
    }

    return reduce(process_exercise_event, relevant, initial)


def workout_state(
    events: list[Event], exercise_names: list[str], week: int, workout: int
) -> WorkoutState:
    """Build workout state from events (pure)."""
    relevant = filter_by_context(events, week=week, workout=workout)

    initial: WorkoutState = {
        "completed": False,
        "completed_exercises": set(),
        "missing_exercises": set(exercise_names),
        "week_index": week,
        "workout_index": workout,
    }

    return reduce(process_workout_event, relevant, initial)


# Convenience query functions
def can_log_set(state: ExerciseState) -> bool:
    """Check if a set can be logged."""
    return not state["completed"]


def can_complete_exercise(state: ExerciseState, required_sets: int) -> bool:
    """Check if exercise can be completed."""
    return len(state["sets"]) >= required_sets and not state["completed"]


def can_complete_workout(state: WorkoutState) -> bool:
    """Check if workout can be completed."""
    return len(state["missing_exercises"]) == 0 and not state["completed"]
