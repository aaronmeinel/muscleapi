"""
Prescription Service - Decoupled prediction/progression logic.

This module provides functions for calculating workout prescriptions
based on historical performance and feedback.
"""

from dataclasses import dataclass
from typing import Optional, Callable
from src.models import Set
from src.events import ExerciseCompleted


@dataclass(frozen=True)
class Prescription:
    """A prescription for a single set."""

    prescribed_reps: Optional[int]
    prescribed_weight: Optional[float]


# Type alias for prescription strategy functions
PrescriptionStrategy = Callable[
    [str, list[Prescription], list[Set], list[ExerciseCompleted]],
    list[Prescription],
]


def static_progression(
    exercise_name: str,
    baseline_sets: list[Prescription],
    historical_sets: list[Set],
    feedback_history: list[ExerciseCompleted],
    multiplier: float = 1.025,
) -> list[Prescription]:
    """Apply a fixed multiplier to baseline prescriptions.

    Args:
        exercise_name: Name of the exercise
        baseline_sets: The template's baseline prescriptions
        historical_sets: All sets logged for this exercise
        feedback_history: All ExerciseCompleted events with feedback
        multiplier: Multiplier to apply (default 2.5% increase)

    Returns:
        List of adjusted prescriptions
    """
    return [
        Prescription(
            prescribed_reps=(
                round(
                    s.prescribed_reps * multiplier + 0.0001
                )  # Add tiny value to fix rounding
                if s.prescribed_reps
                else None
            ),
            prescribed_weight=(
                round(s.prescribed_weight * multiplier, 1)
                if s.prescribed_weight
                else None
            ),
        )
        for s in baseline_sets
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
) -> list[Prescription]:
    """Calculate prescriptions based on latest feedback.

    Uses feedback (joint pain, pump, workload) to adjust prescriptions:
    - High joint pain → reduce weight
    - Low pump → increase intensity
    - Workload too easy → increase weight & add set
    - Workload too hard → reduce sets or maintain weight

    Args:
        exercise_name: Name of the exercise
        baseline_sets: The template's baseline prescriptions
        historical_sets: All sets logged for this exercise
        feedback_history: All ExerciseCompleted events with feedback

    Returns:
        List of adjusted prescriptions
    """

    # Get the most recent feedback for this exercise
    relevant_feedback = [
        f for f in feedback_history if f.exercise == exercise_name
    ]

    if not relevant_feedback:
        # No feedback yet, use static progression
        return static_progression(
            exercise_name, baseline_sets, historical_sets, feedback_history
        )

    latest_feedback = relevant_feedback[-1]

    # Extract feedback values (dict from event)
    joint_pain = latest_feedback.feedback.get("joint_pain", 0)
    pump = latest_feedback.feedback.get("pump", 2)
    workload = latest_feedback.feedback.get("workload", 2)

    # Calculate adjustment factors based on feedback
    weight_adjustment = _calculate_weight_adjustment(
        joint_pain, pump, workload
    )
    set_adjustment = _calculate_set_adjustment(workload)

    # Apply adjustments to baseline
    adjusted_sets = []
    num_sets = max(1, len(baseline_sets) + set_adjustment)  # At least 1 set

    for i in range(num_sets):
        if i < len(baseline_sets):
            base = baseline_sets[i]
        else:
            # Adding extra sets - use last set as template
            base = baseline_sets[-1]

        adjusted_sets.append(
            Prescription(
                prescribed_reps=base.prescribed_reps,
                prescribed_weight=(
                    round(base.prescribed_weight * weight_adjustment, 1)
                    if base.prescribed_weight
                    else None
                ),
            )
        )

    return adjusted_sets


def get_prescriptions_for_workout(
    workout_exercises: dict[str, list[Prescription]],
    all_sets: list[Set],
    all_feedback: list[ExerciseCompleted],
    strategy: PrescriptionStrategy = feedback_based_progression,
) -> dict[str, list[Prescription]]:
    """Get prescriptions for all exercises in a workout.

    Args:
        workout_exercises: Dict of exercise_name -> baseline prescriptions
        all_sets: All historical sets
        all_feedback: All historical exercise feedback
        strategy: Function to calculate prescriptions
        (default: feedback_based_progression)

    Returns:
        Dict of exercise_name -> adjusted prescriptions
    """
    prescriptions = {}

    for exercise_name, baseline_sets in workout_exercises.items():
        # Filter historical data for this exercise
        exercise_sets = [s for s in all_sets if s.exercise == exercise_name]

        prescriptions[exercise_name] = strategy(
            exercise_name=exercise_name,
            baseline_sets=baseline_sets,
            historical_sets=exercise_sets,
            feedback_history=all_feedback,
        )

    return prescriptions
