"""
Prescription Service - Decoupled prediction/progression logic.

This module provides functions for calculating workout prescriptions
based on historical performance and feedback.

IMPORTANT: Prescriptions are calculated based on COMPLETED workouts only.
The current in-progress workout does not influence prescriptions.
"""

from dataclasses import dataclass
from typing import Optional, Callable
from src.domain import Set
from src.events import ExerciseCompleted


@dataclass(frozen=True)
class Prescription:
    """A prescription for a single set."""

    prescribed_reps: Optional[int]
    prescribed_weight: Optional[float]


# Type alias for prescription strategy functions
PrescriptionStrategy = Callable[
    [str, list[Prescription], list[Set], list[ExerciseCompleted], int, int],
    list[Prescription],
]


def _get_last_completed_performance(
    exercise_name: str,
    historical_sets: list[Set],
    feedback_history: list[ExerciseCompleted],
    current_week_idx: int | None = None,
    current_workout_idx: int | None = None,
) -> tuple[list[Set] | None, ExerciseCompleted | None]:
    """Get the most recent completed performance for an exercise.

    IMPORTANT: Excludes the current workout to maintain invariant that
    prescriptions only apply to NEXT workout occurrence.

    Args:
        exercise_name: Name of the exercise
        historical_sets: All sets logged for this exercise
        feedback_history: All ExerciseCompleted events
        current_week_idx: Current week index
        (to exclude from prescription calculation)
        current_workout_idx: Current workout index
        (to exclude from prescription calculation)

    Returns:
        Tuple of (sets from last completion, feedback event) or (None, None)
    """
    # Get all completions for this exercise, excluding current workout
    completions = [
        f
        for f in feedback_history
        if f.exercise == exercise_name
        and not (
            f.week_index == current_week_idx
            and f.workout_index == current_workout_idx
        )
    ]

    if not completions:
        return None, None

    # Get the most recent completion
    last_completion = completions[-1]

    # Get all sets from that workout
    completion_sets = [
        s
        for s in historical_sets
        if (
            s.exercise == exercise_name
            and s.week_index == last_completion.week_index
            and s.workout_index == last_completion.workout_index
        )
    ]

    return completion_sets, last_completion


def static_progression(
    exercise_name: str,
    baseline_sets: list[Prescription],
    historical_sets: list[Set],
    feedback_history: list[ExerciseCompleted],
    current_week_idx: int,
    current_workout_idx: int,
    multiplier: float = 1.025,
) -> list[Prescription]:
    """Apply a fixed multiplier to last completed performance.

    Args:
        exercise_name: Name of the exercise
        baseline_sets: The template's baseline
        prescriptions (used if no history)
        historical_sets: All sets logged for this exercise
        feedback_history: All ExerciseCompleted events with feedback
        current_week_idx: Current week index (excluded from calculation)
        current_workout_idx: Current workout index (excluded from calculation)
        multiplier: Multiplier to apply (default 2.5% increase)

    Returns:
        List of adjusted prescriptions
    """
    last_sets, _ = _get_last_completed_performance(
        exercise_name,
        historical_sets,
        feedback_history,
        current_week_idx,
        current_workout_idx,
    )

    # No completed history - return template as-is
    if not last_sets:
        return baseline_sets

    # Use last completed performance and apply multiplier
    return [
        Prescription(
            prescribed_reps=int(
                s.reps * multiplier + 0.5
            ),  # Round to nearest int
            prescribed_weight=round(s.weight * multiplier, 1),
        )
        for s in last_sets
    ]


def _calculate_weight_adjustment(
    joint_pain: int, pump: int, workload: int
) -> float:
    """Calculate weight adjustment multiplier based on feedback.

    Feedback scale is 0-3:
    - joint_pain: 0=None, 1=Low, 2=Med, 3=High
    - pump: 0=None, 1=Low, 2=Good, 3=Insane
    - workload: 0=Easy, 1=Pretty good, 2=Pushed limits, 3=Too much
    """

    # High joint pain - reduce weight significantly
    if joint_pain >= 3:
        return 0.90  # -10%
    elif joint_pain == 2:
        return 0.95  # -5%

    # Workload too easy - increase weight
    if workload == 0:
        return 1.10  # +10%

    # Workload too hard - maintain or slight decrease
    if workload == 3:
        return 0.98  # -2%

    # Good pump + pushed limits - standard progression
    if pump >= 2 and workload == 2:
        return 1.05  # +5%

    # Default: small increase
    return 1.025  # +2.5%


def _calculate_set_adjustment(workload: int) -> int:
    """Calculate how many sets to add/remove.

    Args:
        workload: Workload feedback (0=easy, 3=too hard)

    Returns:
        -1, 0, or +1 set adjustment
    """
    if workload == 0:  # Too easy
        return 1  # Add a set
    elif workload == 3:  # Too much
        return -1  # Remove a set
    else:
        return 0  # Keep same number


def feedback_based_progression(
    exercise_name: str,
    baseline_sets: list[Prescription],
    historical_sets: list[Set],
    feedback_history: list[ExerciseCompleted],
    current_week_idx: int,
    current_workout_idx: int,
) -> list[Prescription]:
    """Calculate prescriptions based on last
    completed performance and feedback.

    EXCLUDES the current workout from
    prescription calculation, so prescriptions
    remain stable throughout the workout even as you complete exercises.

    Args:
        exercise_name: Name of the exercise
        baseline_sets: The template's baseline
        prescriptions (used if no history)
        historical_sets: All sets logged for this exercise
        feedback_history: All ExerciseCompleted events with feedback
        current_week_idx: Current week index (excluded from calculation)
        current_workout_idx: Current workout index (excluded from calculation)

    Returns:
        List of adjusted prescriptions
        (can have different length than baseline)
    """
    last_sets, last_feedback = _get_last_completed_performance(
        exercise_name,
        historical_sets,
        feedback_history,
        current_week_idx,
        current_workout_idx,
    )

    # No completed history - return template as-is
    if not last_sets or not last_feedback:
        return baseline_sets

    # Extract feedback values (dict from event)
    joint_pain = last_feedback.feedback.get("joint_pain", 0)
    pump = last_feedback.feedback.get("pump", 2)
    workload = last_feedback.feedback.get("workload", 2)

    # Calculate adjustment factors based on feedback
    weight_adjustment = _calculate_weight_adjustment(
        joint_pain, pump, workload
    )
    set_adjustment = _calculate_set_adjustment(workload)

    # Apply adjustments to last completed performance
    num_sets = max(1, len(last_sets) + set_adjustment)  # At least 1 set

    adjusted_sets = []
    for i in range(num_sets):
        if i < len(last_sets):
            base_set = last_sets[i]
        else:
            # Adding extra sets - use last set as template
            base_set = last_sets[-1]

        adjusted_sets.append(
            Prescription(
                prescribed_reps=base_set.reps,  # Keep same reps
                prescribed_weight=round(
                    base_set.weight * weight_adjustment, 1
                ),
            )
        )

    return adjusted_sets


def get_prescriptions_for_workout(
    workout_exercises: dict[str, list[Prescription]],
    all_sets: list[Set],
    all_feedback: list[ExerciseCompleted],
    current_week_idx: int,
    current_workout_idx: int,
    strategy: PrescriptionStrategy = feedback_based_progression,
) -> dict[str, list[Prescription]]:
    """Get prescriptions for all exercises in a workout.

    Args:
        workout_exercises: Dict of exercise name -> baseline prescriptions
        all_sets: All historical sets
        all_feedback: All exercise completion events
        current_week_idx: Current week index (excluded from calculation)
        current_workout_idx: Current workout index (excluded from calculation)
        strategy: Prescription strategy function to use

    Returns:
        Dict of exercise name -> adjusted prescriptions
    """
    result = {}
    for exercise_name, baseline_prescriptions in workout_exercises.items():
        result[exercise_name] = strategy(
            exercise_name,
            baseline_prescriptions,
            all_sets,
            all_feedback,
            current_week_idx,
            current_workout_idx,
        )
    return result
