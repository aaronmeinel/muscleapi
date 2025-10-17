"""Tests for prescription service - comprehensive coverage."""

from src.service.prescription import (
    get_prescriptions_for_workout,
    static_progression,
    feedback_based_progression,
    Prescription,
)
from src.domain import Set
from src.events import ExerciseCompleted
from datetime import datetime


def test_no_history_returns_template_as_is():
    """First time doing exercise - return template unchanged."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=[],
        current_week_idx=0,
        current_workout_idx=0,
    )

    # Should return template exactly as-is
    assert len(result) == 1
    assert result[0].prescribed_reps == 10
    assert result[0].prescribed_weight == 100.0


def test_no_history_with_null_template():
    """First time with null template - return null."""
    baseline = [
        Prescription(prescribed_reps=None, prescribed_weight=None),
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=[],
        current_week_idx=0,
        current_workout_idx=0,
    )

    # Should return template as-is (nulls)
    assert len(result) == 1
    assert result[0].prescribed_reps is None
    assert result[0].prescribed_weight is None


def test_incomplete_exercise_does_not_affect_prescription():
    """Sets logged but exercise not completed - should not affect prescription."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    # Logged sets but no ExerciseCompleted event
    historical_sets = [
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=historical_sets,
        feedback_history=[],  # No completion!
        current_week_idx=1,  # Next workout
        current_workout_idx=0,
    )

    # Should still return template as-is because exercise wasn't completed
    assert len(result) == 1
    assert result[0].prescribed_reps == 10
    assert result[0].prescribed_weight == 100.0


def test_completed_exercise_affects_next_workout():
    """Completed exercise with feedback - affects NEXT workout only."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    # Completed workout with 1 set
    historical_sets = [
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={
                "joint_pain": 0,
                "pump": 2,
                "workload": 2,
            },  # Pushed limits
        )
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=historical_sets,
        feedback_history=feedback,
        current_week_idx=1,  # Next week - will see progression
        current_workout_idx=0,
    )

    # Should use last completed performance (100kg) and apply 5% increase
    assert len(result) == 1
    assert result[0].prescribed_reps == 10  # Same reps
    assert result[0].prescribed_weight == 105.0  # 100 * 1.05


def test_workload_too_easy_adds_set_next_workout():
    """Workload=0 (too easy) should add set to NEXT workout, not current."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    # Completed workout with 1 set, rated as too easy
    historical_sets = [
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 0},  # Too easy!
        )
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=historical_sets,
        feedback_history=feedback,
        current_week_idx=1,  # Next week - will see +1 set
        current_workout_idx=0,
    )

    # Should prescribe 2 sets for next workout (1 + 1 adjustment)
    assert len(result) == 2
    # Weight increased by 10% because too easy
    assert result[0].prescribed_weight == 110.0  # 100 * 1.1
    assert result[1].prescribed_weight == 110.0


def test_workload_too_hard_removes_set_next_workout():
    """Workload=3 (too hard) should remove set from NEXT workout."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    # Completed workout with 3 sets, rated as too hard
    historical_sets = [
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 3},  # Too hard!
        )
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=historical_sets,
        feedback_history=feedback,
        current_week_idx=1,  # Next week
        current_workout_idx=0,
    )

    # Should prescribe 2 sets for next workout (3 - 1 adjustment)
    assert len(result) == 2
    # Weight decreased by 2% because too hard
    assert result[0].prescribed_weight == 98.0  # 100 * 0.98


def test_high_joint_pain_reduces_weight():
    """High joint pain should reduce weight for next workout."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    historical_sets = [
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 3, "pump": 2, "workload": 2},  # High pain!
        )
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=historical_sets,
        feedback_history=feedback,
        current_week_idx=1,
        current_workout_idx=0,
    )

    # Should reduce weight by 10%
    assert result[0].prescribed_weight == 90.0  # 100 * 0.9


def test_multiple_completions_uses_latest():
    """Multiple completed workouts - use most recent feedback."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    # First workout - too easy
    historical_sets = [
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
        # Second workout - pushed limits
        Set(
            exercise="Bench Press",
            reps=10,
            weight=110.0,
            timestamp=datetime.now(),
            week_index=1,
            workout_index=0,
        ),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 0},  # Too easy
        ),
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=1,
            workout_index=0,
            feedback={
                "joint_pain": 0,
                "pump": 2,
                "workload": 2,
            },  # Pushed limits (latest)
        ),
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=historical_sets,
        feedback_history=feedback,
        current_week_idx=2,  # Week 2 - will use week 1 completion
        current_workout_idx=0,
    )

    # Should use latest workout (110kg) with 5% increase
    assert len(result) == 1  # Latest had 1 set
    assert result[0].prescribed_weight == 115.5  # 110 * 1.05


def test_current_workout_in_progress_ignored():
    """Current in-progress workout should not affect prescriptions."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    # Last completed workout
    historical_sets = [
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
        # Current workout (in progress) - should be ignored!
        Set(
            exercise="Bench Press",
            reps=12,
            weight=120.0,
            timestamp=datetime.now(),
            week_index=1,
            workout_index=0,
        ),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 2},
        ),
        # Completed current workout too - should be excluded!
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=1,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 3, "workload": 0},
        ),
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=historical_sets,
        feedback_history=feedback,
        current_week_idx=1,  # Currently in week 1, workout 0
        current_workout_idx=0,
    )

    # Should use LAST COMPLETED (week 0), not current week 1
    assert result[0].prescribed_weight == 105.0  # 100 * 1.05, NOT 120


def test_different_exercises_independent():
    """Different exercises should not affect each other."""
    workout = {
        "Bench Press": [
            Prescription(prescribed_reps=10, prescribed_weight=100.0)
        ],
        "Squat": [Prescription(prescribed_reps=8, prescribed_weight=150.0)],
    }

    # Only Bench Press has history
    historical_sets = [
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 0},  # Too easy
        )
    ]

    result = get_prescriptions_for_workout(
        workout_exercises=workout,
        all_sets=historical_sets,
        all_feedback=feedback,
        current_week_idx=1,  # Next week
        current_workout_idx=0,
        strategy=feedback_based_progression,
    )

    # Bench Press should progress
    assert result["Bench Press"][0].prescribed_weight == 110.0  # 100 * 1.1
    # Squat should stay as template (no history)
    assert result["Squat"][0].prescribed_weight == 150.0


def test_static_progression_no_history():
    """Static progression with no history returns template."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    result = static_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=[],
        current_week_idx=0,
        current_workout_idx=0,
        multiplier=1.1,
    )

    # No history - return template as-is
    assert result[0].prescribed_weight == 100.0


def test_static_progression_with_history():
    """Static progression applies multiplier to last completed."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    historical_sets = [
        Set(
            exercise="Bench Press",
            reps=10,
            weight=100.0,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press", week_index=0, workout_index=0, feedback={}
        )
    ]

    result = static_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=historical_sets,
        feedback_history=feedback,
        current_week_idx=1,  # Next week
        current_workout_idx=0,
        multiplier=1.1,
    )

    # Should apply 10% increase to last completed
    assert result[0].prescribed_weight == 110.0  # 100 * 1.1
