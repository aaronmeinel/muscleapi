"""Tests for prescription service."""

from src.service.prescription import (
    get_prescriptions_for_workout,
    static_progression,
    feedback_based_progression,
    Prescription,
)

from src.events import ExerciseCompleted


def test_static_progression_applies_multiplier():
    """Test that static progression applies fixed multiplier."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    result = static_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=[],
        multiplier=1.1,
    )

    assert len(result) == 3
    assert result[0].prescribed_reps == 11  # 10 * 1.1 = 11
    assert result[0].prescribed_weight == 110.0  # 100 * 1.1 = 110


def test_static_progression_with_none_values():
    """Test that static progression handles None values."""
    baseline = [
        Prescription(prescribed_reps=None, prescribed_weight=100.0),
        Prescription(prescribed_reps=10, prescribed_weight=None),
    ]

    result = static_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=[],
        multiplier=1.05,
    )

    assert result[0].prescribed_reps is None
    assert result[0].prescribed_weight == 105.0
    assert result[1].prescribed_reps == 11  # Rounded from 10.5
    assert result[1].prescribed_weight is None


def test_feedback_based_no_history_uses_default():
    """Test that feedback-based uses static when no feedback."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=[],
    )

    # Should use default 1.025 multiplier
    assert result[0].prescribed_weight == 102.5  # 100 * 1.025


def test_feedback_based_high_joint_pain_reduces_weight():
    """Test that high joint pain reduces weight."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 3, "pump": 2, "workload": 2},
        )
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=feedback,
    )

    # High pain (3) -> 0.9 multiplier
    assert result[0].prescribed_weight == 90.0  # 100 * 0.9


def test_feedback_based_workload_too_easy_increases_weight():
    """Test that workload=0 (too easy) increases weight."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 0},
        )
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=feedback,
    )

    # Too easy (0) -> 1.1 multiplier
    assert result[0].prescribed_weight == 110.0  # 100 * 1.1


def test_feedback_based_workload_too_hard_decreases_weight():
    """Test that workload=3 (too hard) decreases weight slightly."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 3},
        )
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=feedback,
    )

    # Too hard (3) -> 0.98 multiplier
    assert result[0].prescribed_weight == 98.0  # 100 * 0.98


def test_feedback_based_good_pump_and_pushed_limits_increases():
    """Test that good pump + pushed limits gives standard progression."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 2},
        )
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=feedback,
    )

    # Good pump (2+) + pushed limits (2) -> 1.05 multiplier
    assert result[0].prescribed_weight == 105.0  # 100 * 1.05


def test_feedback_based_adds_set_when_too_easy():
    """Test that workload=0 adds an extra set."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 0},
        )
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=feedback,
    )

    # Should add 1 set
    assert len(result) == 3
    # Extra set uses last set as template
    assert result[2].prescribed_weight == 110.0


def test_feedback_based_removes_set_when_too_hard():
    """Test that workload=3 removes a set."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 3},
        )
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=feedback,
    )

    # Should remove 1 set
    assert len(result) == 2


def test_feedback_based_uses_latest_feedback():
    """Test that only the latest feedback is used."""
    baseline = [
        Prescription(prescribed_reps=10, prescribed_weight=100.0),
    ]

    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 3, "pump": 0, "workload": 3},
        ),
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=1,
            feedback={"joint_pain": 0, "pump": 3, "workload": 0},  # Latest
        ),
    ]

    result = feedback_based_progression(
        exercise_name="Bench Press",
        baseline_sets=baseline,
        historical_sets=[],
        feedback_history=feedback,
    )

    # Should use latest (workload=0 -> 1.1 multiplier)
    assert result[0].prescribed_weight == 110.0


def test_get_prescriptions_applies_strategy_to_all_exercises():
    """Test that service function applies strategy to workout."""
    workout = {
        "Bench Press": [
            Prescription(prescribed_reps=10, prescribed_weight=100.0),
        ],
        "Squat": [
            Prescription(prescribed_reps=8, prescribed_weight=150.0),
        ],
    }

    # Use positional args in lambda to match function signature
    result = get_prescriptions_for_workout(
        workout_exercises=workout,
        all_sets=[],
        all_feedback=[],
        strategy=lambda exercise_name, baseline_sets, historical_sets, feedback_history, mult=1.1: static_progression(
            exercise_name,
            baseline_sets,
            historical_sets,
            feedback_history,
            multiplier=mult,
        ),
    )

    assert len(result) == 2
    assert "Bench Press" in result
    assert "Squat" in result
    assert result["Bench Press"][0].prescribed_weight == 110.0
    assert result["Squat"][0].prescribed_weight == 165.0


def test_get_prescriptions_filters_exercise_specific_data():
    """Test that service filters sets/feedback per exercise."""
    workout = {
        "Bench Press": [
            Prescription(prescribed_reps=10, prescribed_weight=100.0),
        ],
        "Squat": [
            Prescription(prescribed_reps=8, prescribed_weight=150.0),
        ],
    }

    # Feedback only for bench press
    feedback = [
        ExerciseCompleted(
            exercise="Bench Press",
            week_index=0,
            workout_index=0,
            feedback={"joint_pain": 0, "pump": 2, "workload": 0},
        )
    ]

    result = get_prescriptions_for_workout(
        workout_exercises=workout,
        all_sets=[],
        all_feedback=feedback,
    )

    # Bench press should use feedback (workload=0 -> 1.1x)
    assert result["Bench Press"][0].prescribed_weight == 110.0
    # Squat has no feedback, should use default (1.025x)
    assert result["Squat"][0].prescribed_weight == 153.8  # 150 * 1.025


def test_get_prescriptions_uses_feedback_based_by_default():
    """Test that feedback_based_progression is the default strategy."""
    workout = {
        "Bench Press": [
            Prescription(prescribed_reps=10, prescribed_weight=100.0),
        ],
    }

    # No strategy specified
    result = get_prescriptions_for_workout(
        workout_exercises=workout,
        all_sets=[],
        all_feedback=[],
    )

    # Should use default multiplier (1.025)
    assert result["Bench Press"][0].prescribed_weight == 102.5
