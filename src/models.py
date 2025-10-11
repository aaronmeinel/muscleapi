from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from numbers import Number
from typing import Optional
from toolz import first
import yaml
from dataclasses import asdict

from src.events import ExerciseCompleted


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
    sets: Optional[list[SetPrescription]]

    # Default to one set. Because an exercise without sets makes no sense.
    # Why would you add it to the template in the first place?


@dataclass(frozen=True)
class Workout:

    exercises: list[Exercise]
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
    workouts: list[Workout]

    def to_yaml(self):

        return yaml.dump(asdict(self))

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
    workouts: list[Workout]
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

        current_week = first(
            w for w in self.weeks if w.is_complete(sets_performed) is False
        )
        current_workout = first(
            wo
            for wo in current_week.workouts
            if wo.is_complete(sets_performed, current_week.index) is False
        )

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
