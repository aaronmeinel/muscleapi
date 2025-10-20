from src.domain.types import ExerciseState, WorkoutState
from src.events import (
    Event,
    ExerciseStarted,
    ExerciseCompleted,
    SetLogged,
    WorkoutCompleted,
)


def process_exercise_event(
    state: ExerciseState, event: Event
) -> ExerciseState:
    """Reduce single event into exercise state."""
    match event:
        case ExerciseStarted():
            return {**state, "started": True}
        case ExerciseCompleted():
            return {**state, "completed": True}
        case SetLogged():
            return {**state, "sets": [*state["sets"], event]}
        case _:
            return state


def process_workout_event(state: WorkoutState, event: Event) -> WorkoutState:
    """Reduce single event into workout state."""
    match event:
        case WorkoutCompleted():
            return {**state, "completed": True}
        case ExerciseCompleted(exercise=ex):
            return {
                **state,
                "completed_exercises": state["completed_exercises"] | {ex},
                "missing_exercises": state["missing_exercises"] - {ex},
            }
        case _:
            return state
