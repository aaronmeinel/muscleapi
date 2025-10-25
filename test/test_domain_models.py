"""Tests for domain models: MesocyclePlan, Week, Workout navigation."""

import pytest
from datetime import datetime
import rich
from src.models import (
    MesocyclePlan,
    Week,
    Workout,
    Exercise,
    SetPrescription,
    Set,
)
from src.events import SetLogged, WorkoutCompleted, ExerciseStarted


@pytest.fixture
def simple_plan():
    """A 2-week plan with 2 workouts per week, 2 exercises per workout."""
    exercises_a = (
        Exercise("Squat", (SetPrescription(),)),
        Exercise("Bench", (SetPrescription(),)),
    )
    exercises_b = (
        Exercise("Deadlift", (SetPrescription(),)),
        Exercise("Pullup", (SetPrescription(),)),
    )

    workouts = (
        Workout(exercises=exercises_a, index=0),
        Workout(exercises=exercises_b, index=1),
    )

    weeks = [
        Week(index=0, workouts=workouts),
        Week(index=1, workouts=workouts),
    ]

    return MesocyclePlan(template_name="Test Plan", weeks=weeks)


class TestMesocyclePlanNavigation:
    """Test navigation methods on MesocyclePlan."""

    def test_get_week_valid_index(self, simple_plan):
        week = simple_plan.get_week(0)
        assert week is not None
        assert week.index == 0

    def test_get_week_invalid_index(self, simple_plan):
        assert simple_plan.get_week(-1) is None
        assert simple_plan.get_week(10) is None

    def test_get_workout_valid_indices(self, simple_plan):
        workout = simple_plan.get_workout(0, 0)
        assert workout is not None
        assert isinstance(workout, Workout)
        assert len(workout.exercises) == 2
        assert workout.exercises[0].name == "Squat"

    def test_get_workout_invalid_indices(self, simple_plan):
        assert simple_plan.get_workout(-1, 0) is None
        assert simple_plan.get_workout(0, -1) is None
        assert simple_plan.get_workout(10, 0) is None

    def test_get_curent_workout_prescriptions_no_events(self, simple_plan):
        prescriptions = simple_plan.get_current_workout_prescriptions(
            sets_performed=[],
            progress_function=lambda x: x,
        )
        assert "Squat" in prescriptions
        assert "Bench" in prescriptions

    def test_get_current_workout_prescriptions_with_events(
        self, simple_plan: MesocyclePlan
    ):
        events = [
            ExerciseStarted("Bench", 0, 0, {}),
            SetLogged("Bench", datetime.now(), 0, 0, 5, 200),
        ]
        prescriptions = simple_plan.get_current_workout_prescriptions(
            sets_performed=events,
            progress_function=lambda x: x,
        )

        assert False, prescriptions


class TestCurrentWeekCalculation:
    """Test current_week_index calculation from events."""

    def test_no_events_returns_week_zero(self, simple_plan):
        assert simple_plan.current_week_index([]) == 0

    def test_no_completed_workouts_returns_week_zero(self, simple_plan):
        events = [
            ExerciseStarted("Squat", 0, 0, {}),
            Set("Squat", 5, 100.0, datetime.now(), 0, 0),
        ]
        assert simple_plan.current_week_index(events) == 0

    def test_one_workout_completed_stays_in_same_week(self, simple_plan):
        events = [WorkoutCompleted(workout_index=0, week_index=0)]
        # Still in week 0 because there are 2 workouts per week
        assert simple_plan.current_week_index(events) == 0

    def test_all_workouts_in_week_completed_moves_to_next_week(
        self, simple_plan
    ):
        events = [
            WorkoutCompleted(workout_index=0, week_index=0),
            WorkoutCompleted(workout_index=1, week_index=0),
        ]
        # Both workouts done, move to week 1
        assert simple_plan.current_week_index(events) == 1


class TestCurrentWorkoutCalculation:
    """Test current_workout_index calculation from events."""

    def test_no_events_returns_workout_zero(self, simple_plan):
        assert simple_plan.current_workout_index([]) == 0

    def test_no_completed_workouts_returns_workout_zero(self, simple_plan):
        events = [
            ExerciseStarted("Squat", 0, 0, {}),
            Set("Squat", 5, 100.0, datetime.now(), 0, 0),
        ]
        assert simple_plan.current_workout_index(events) == 0

    def test_first_workout_completed_returns_second_workout(self, simple_plan):
        events = [WorkoutCompleted(workout_index=0, week_index=0)]
        assert simple_plan.current_workout_index(events) == 1

    def test_ignores_completed_workouts_from_previous_weeks(self, simple_plan):
        events = [
            WorkoutCompleted(workout_index=0, week_index=0),
            WorkoutCompleted(workout_index=1, week_index=0),
            # Now in week 1, no workouts completed yet
        ]
        assert simple_plan.current_workout_index(events) == 0


class TestCurrentWorkout:
    """Test current_workout() which combines week and workout logic."""

    def test_returns_first_workout_with_no_events(self, simple_plan):
        workout = simple_plan.current_workout([])
        assert workout is not None
        assert workout.exercises[0].name == "Squat"

    def test_returns_second_workout_after_first_completed(self, simple_plan):
        events = [WorkoutCompleted(workout_index=0, week_index=0)]
        workout = simple_plan.current_workout(events)
        assert workout is not None
        assert workout.exercises[0].name == "Deadlift"

    def test_returns_first_workout_of_second_week(self, simple_plan):
        events = [
            WorkoutCompleted(workout_index=0, week_index=0),
            WorkoutCompleted(workout_index=1, week_index=0),
        ]
        workout = simple_plan.current_workout(events)
        assert workout is not None
        assert (
            workout.exercises[0].name == "Squat"
        )  # Back to first workout type


class TestWeekCompletion:
    """Test Week.is_complete() method."""

    def test_week_not_complete_with_no_sets(self, simple_plan):
        week = simple_plan.get_week(0)
        assert not week.is_complete([])

    def test_week_not_complete_with_partial_sets(self, simple_plan):
        week = simple_plan.get_week(0)
        sets = [Set("Squat", 5, 100.0, datetime.now(), 0, 0)]
        assert not week.is_complete(sets)


class TestWorkoutCompletion:
    """Test Workout.is_complete() method."""

    def test_workout_not_complete_with_no_sets(self, simple_plan):
        workout = simple_plan.get_workout(0, 0)
        assert not workout.is_complete([], week_index=0)

    def test_workout_not_complete_with_partial_exercises(self, simple_plan):
        workout = simple_plan.get_workout(0, 0)
        sets = [Set("Squat", 5, 100.0, datetime.now(), 0, 0)]
        # Only Squat logged, Bench missing
        assert not workout.is_complete(sets, week_index=0)

    def test_workout_complete_with_all_exercises(self, simple_plan):
        workout = simple_plan.get_workout(0, 0)
        sets = [
            Set("Squat", 5, 100.0, datetime.now(), 0, 0),
            Set("Bench", 5, 80.0, datetime.now(), 0, 0),
        ]
        assert workout.is_complete(sets, week_index=0)
