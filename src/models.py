from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from numbers import Number
from typing import Optional

import yaml
from dataclasses import asdict
from pydantic import BaseModel, Field

from src.events import WorkoutCompleted, ExerciseCompleted


class ExerciseFeedback(BaseModel):
    """Feedback collected after completing an exercise."""

    joint_pain: int = Field(ge=0, le=10, description="Joint pain level (0-10)")
    pump: int = Field(ge=0, le=10, description="Muscle pump level (0-10)")
    workload: int = Field(ge=0, le=10, description="Perceived workload (0-10)")

    class Config:
        frozen = True


class WorkoutFeedback(BaseModel):
    """Feedback collected after completing a workout."""

    difficulty: int = Field(
        ge=0, le=10, description="Overall difficulty (0-10)"
    )
    energy_level: int = Field(ge=0, le=10, description="Energy level (0-10)")
    notes: Optional[str] = Field(
        None, max_length=500, description="Optional notes"
    )

    class Config:
        frozen = True


@dataclass(frozen=True, eq=True)
class Set:
    """Represents a set of an exercise.

    Since we're building a very specialized system here,
    this serves as an event at the same time.
    We make a deliberate choice for coupling here for prototyping.
    """

    exercise: str
    reps: int
    weight: float
    timestamp: datetime
    week_index: int
    workout_index: int

    @classmethod
    def create_safe(
        cls,
        log: Iterable,
        exercise: str,
        reps: int,
        weight: float,
        week_index: int,
        workout_index: int,
    ) -> "Set":
        """Factory method that checks if the set
        can be created in the given context.
        This means that we need to check
        if the exercise has already been completed
        in the given workout and week.
        """

        completed = filter(
            lambda e: isinstance(e, ExerciseCompleted)
            and e.workout_index == workout_index
            and e.week_index == week_index
            and e.exercise == exercise,
            log,
        )
        if any(completed):
            raise ValueError(
                f"Cannot log set for exercise {exercise} in workout\
                {workout_index} week {week_index} - exercise already completed"
            )
        return cls(
            exercise=exercise,
            reps=reps,
            weight=weight,
            timestamp=datetime.now(),
            week_index=week_index,
            workout_index=workout_index,
        )


@dataclass(frozen=True)
class SetPrescription:
    prescribed_reps: Optional[int] = None
    prescribed_weight: Optional[float] = None


@dataclass(frozen=True)
class Exercise:
    name: str
    sets: Optional[tuple[SetPrescription, ...]]

    # Default to one set. Because an exercise without sets makes no sense.
    # Why would you add it to the template in the first place?


@dataclass(frozen=True)
class Workout:

    exercises: tuple[Exercise, ...]
    index: Optional[int] = None

    def is_complete(self, sets_performed: list[Set], week_index: int) -> bool:
        """Returns True if all exercises in this workout
        have been performed in the given week."""
        performed_exercises = {
            s.exercise
            for s in sets_performed
            if s.week_index == week_index and s.workout_index == self.index
        }
        required_exercises = {exercise.name for exercise in self.exercises}
        return required_exercises.issubset(performed_exercises)


@dataclass(frozen=True)
class Template:
    name: str
    workouts: tuple[Workout, ...]

    def to_yaml(self):
        """Convert template to YAML,
        converting tuples to lists for compatibility."""

        def convert_tuples_to_lists(obj):
            """Recursively convert tuples to lists in nested structures."""
            if isinstance(obj, tuple):
                return [convert_tuples_to_lists(item) for item in obj]
            elif isinstance(obj, dict):
                return {
                    key: convert_tuples_to_lists(value)
                    for key, value in obj.items()
                }
            elif isinstance(obj, list):
                return [convert_tuples_to_lists(item) for item in obj]
            else:
                return obj

        data = asdict(self)
        data_with_lists = convert_tuples_to_lists(data)
        return yaml.dump(data_with_lists)

    def to_mesocycle_plan(self) -> "MesocyclePlan":
        weeks = [
            Week(index=i, workouts=self.workouts)
            for i in range(4)  # 4 weeks by default
        ]
        return MesocyclePlan(template_name=self.name, weeks=weeks)

    def get_exercise_names(self) -> list[str]:
        """Returns a list of all exercise names in this template.

        This is useful for validation and suggestion/autocomplete purposes when
        logging sets.
        The idea is that logging a set only makes
        sense if the exercise is part of the plan.
        Replacing an exercise in the plan is a
        different operation that should be handled
        separately.
        """
        return list(
            {
                exercise.name
                for workout in self.workouts
                for exercise in workout.exercises
            }
        )


@dataclass(frozen=True)
class Week:
    workouts: tuple[Workout, ...]
    index: int

    def is_complete(self, sets_performed: list[Set]) -> bool:
        """Returns True if all workouts in this week have been completed."""
        return all(
            workout.is_complete(sets_performed, self.index)
            for workout in self.workouts
        )


@dataclass(frozen=True)
class MesocyclePlan:
    template_name: str
    weeks: list[Week]

    def get_n_workouts_per_week(self) -> int:
        """Returns the number of workouts per week in this plan."""
        if not self.weeks:
            return 0
        return len(self.weeks[0].workouts)

    def get_current_week_index(self, sets_performed: list[Set]) -> int:
        """Returns the index of the current week based on sets performed.

        The current week is the closest week that contains incomplete workouts.
        These again are identified by the 'missing' sets.
        Because the set events carry an index
        of the week and workout they belong to,
        we can use that to determine the current week.
        So if the last set has week_index 0
        and the week plan is completed with that,
        we're in week 1 now.

        """
        return max((s.week_index for s in sets_performed), default=-1) + 1

    def get_current_workout_index(self, sets_performed: list[Set]) -> int:
        """Returns the index of the current workout based on sets performed.

        The current workout is the closest
        workout that contains incomplete exercises
        """
        current_week_index = self.get_current_week_index(sets_performed)
        return max(
            (
                s.workout_index
                for s in sets_performed
                if s.week_index == current_week_index
            ),
            default=-1,
        )

    def get_current_workout_prescriptions(
        self,
        sets_performed: list[Set],
        progress_function: Callable[[Optional[Number]], Optional[Number]],
    ) -> dict[str, list[dict]]:
        """Get prescriptions for the current
        workout based on progression function."""
        # Use the new navigation methods instead of the old first() logic
        current_workout = self.current_workout(sets_performed)

        if not current_workout:
            return {}

        return {
            exercise.name: [
                {
                    "prescribed_reps": progress_function(s.prescribed_reps),
                    "prescribed_weight": progress_function(
                        s.prescribed_weight
                    ),
                }
                for s in exercise.sets
            ]
            for exercise in current_workout.exercises
        }

    def get_week(self, index: int) -> Optional[Week]:
        """Get a specific week by index."""
        if 0 <= index < len(self.weeks):
            return self.weeks[index]
        return None

    def get_workout(
        self, week_index: int, workout_index: int
    ) -> Optional[Workout]:
        """Get a specific workout by week and workout index."""
        week = self.get_week(week_index)
        if week and 0 <= workout_index < len(week.workouts):
            return week.workouts[workout_index]
        return None

    def current_week_index(self, events: list) -> int:
        """Calculate current week index from events.

        Looks for the most recent week that has activity.
        If all workouts in a week are complete, moves to next week.
        """
        if not events:
            return 0

        # Find all workout completions
        completed_workouts = [
            e for e in events if isinstance(e, WorkoutCompleted)
        ]

        if not completed_workouts:
            # No workouts completed yet, we're in week 0
            return 0

        # Get the highest week index from completed workouts
        max_week = max(w.week_index for w in completed_workouts)

        # Check if all workouts in that week are complete
        workouts_in_week = (
            len(self.weeks[max_week].workouts)
            if max_week < len(self.weeks)
            else 0
        )
        completed_in_week = sum(
            1 for w in completed_workouts if w.week_index == max_week
        )

        if completed_in_week >= workouts_in_week:
            # All workouts in this week done, move to next
            return min(max_week + 1, len(self.weeks) - 1)

        return max_week

    def current_workout_index(self, events: list) -> int:
        """Calculate current workout index within the current week.

        Returns the index of the next incomplete workout.
        """
        current_week = self.current_week_index(events)

        # Find completed workouts in current week
        completed_workouts = [
            e
            for e in events
            if isinstance(e, WorkoutCompleted) and e.week_index == current_week
        ]

        if not completed_workouts:
            return 0

        # Get the highest completed workout index in current week
        max_workout = max(w.workout_index for w in completed_workouts)

        # Next workout is max + 1
        week = self.get_week(current_week)
        if week:
            next_index = max_workout + 1
            return min(next_index, len(week.workouts) - 1)

        return 0

    def current_workout(self, events: list) -> Optional[Workout]:
        """Get the current workout based on event history."""
        week_idx = self.current_week_index(events)
        workout_idx = self.current_workout_index(events)
        return self.get_workout(week_idx, workout_idx)
