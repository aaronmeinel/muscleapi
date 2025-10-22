# src/service/logging.py (NEW FILE - pure functions)
from returns.result import Result, Success, Failure
from datetime import datetime
from thefuzz import fuzz
from src.domain.state import exercise_state, workout_state
from src.events import (
    Event,
    ExerciseStarted,
    SetLogged,
    ExerciseCompleted,
    WorkoutCompleted,
)
from src.models import Template


def current_position(
    events: list[Event], template: Template
) -> tuple[int, int]:
    """Calculate current (week_index, workout_index) from events."""
    plan = template.to_mesocycle_plan()
    week_idx = plan.current_week_index(events)
    workout_idx = plan.current_workout_index(events)
    return week_idx, workout_idx


def suggest_exercise_name(exercise: str, names: list[str]) -> Result[str, str]:

    match_rank = {fuzz.ratio(exercise, name): name for name in names}
    best_match_score = max(match_rank.keys())
    if best_match_score == max(match_rank.keys()):
        if best_match_score > 80:
            best_match = match_rank[best_match_score]
            return Failure(
                f"Exercise '{exercise}' not in template. Did you mean '{best_match}'?"
            )
        return Failure(f"Unknown exercise: {exercise}")


def log_set(
    events: list[Event],
    template: Template,
    exercise: str,
    reps: int,
    weight: float,
) -> Result[list[Event] | str, str]:
    """
    Pure business logic for logging a set.

    Returns:
        Success(new_events) if valid
        Failure(error_message) if invalid
    """
    # Validate exercise exists
    exercise_names = template.get_exercise_names()
    if exercise not in exercise_names:
        return suggest_exercise_name(exercise, exercise_names)

    # Get current context
    week, workout = current_position(events, template)

    # Get current state
    state = exercise_state(events, exercise, week, workout)

    # Validate can log
    if state["completed"]:
        return Failure(
            f"Cannot log set - exercise '{exercise}' already completed"
        )

    # Build new events
    new_events: list[Event] = []

    if not state["sets"]:  # First set
        new_events.append(
            ExerciseStarted(
                exercise=exercise,
                week_index=week,
                workout_index=workout,
                feedback={},
            )
        )

    new_events.append(
        SetLogged(
            exercise=exercise,
            reps=reps,
            weight=weight,
            timestamp=datetime.now(),
            week_index=week,
            workout_index=workout,
        )
    )

    return Success(new_events)


def complete_exercise(
    events: list[Event],
    template: Template,
    exercise: str,
    feedback: dict[str, int],
) -> Result[list[Event], str]:
    """Pure business logic for completing an exercise."""
    week, workout = current_position(events, template)
    state = exercise_state(events, exercise, week, workout)

    # Get required sets from template
    plan = template.to_mesocycle_plan()
    current_workout = plan.get_workout(week, workout)

    if not current_workout:
        return Failure(f"No workout found at week {week}, workout {workout}")

    current_exercise = next(
        (ex for ex in current_workout.exercises if ex.name == exercise), None
    )

    if not current_exercise:
        return Failure(f"Exercise '{exercise}' not found in workout {workout}")

    required_sets = len(current_exercise.sets) if current_exercise.sets else 1

    if len(state["sets"]) < required_sets:
        return Failure(
            f"Cannot complete '{exercise}' - only {len(state['sets'])} of {required_sets} sets completed"
        )

    if state["completed"]:
        return Failure(f"Exercise '{exercise}' already completed")

    event = ExerciseCompleted(
        exercise=exercise,
        week_index=week,
        workout_index=workout,
        feedback=feedback,
    )

    return Success([event])


def complete_workout(
    events: list[Event], template: Template
) -> Result[list[Event], str]:
    """Pure business logic for completing a workout."""
    week, workout = current_position(events, template)

    plan = template.to_mesocycle_plan()
    current_workout = plan.get_workout(week, workout)

    if not current_workout:
        return Failure(f"No workout found at week {week}, workout {workout}")

    exercise_names = [ex.name for ex in current_workout.exercises]
    state = workout_state(events, exercise_names, week, workout)

    if state["missing_exercises"]:
        missing = ", ".join(state["missing_exercises"])
        return Failure(
            f"Cannot complete workout - missing exercises: {missing}"
        )

    if state["completed"]:
        return Failure(f"Workout {workout} already completed")

    event = WorkoutCompleted(week_index=week, workout_index=workout)

    return Success([event])
