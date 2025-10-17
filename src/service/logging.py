from types import MappingProxyType

from datetime import datetime
from src.events import ExerciseCompleted, ExerciseStarted, WorkoutCompleted
from src.models import Set, Template, MesocyclePlan
from src.domain import ExerciseSession, WorkoutSession
from thefuzz import fuzz

from returns.result import Result, Success, Failure
from src.protocols import Repository


class LoggingService:
    log_repository: Repository
    template_repository: Repository
    # The idea here is that you're going to log against a template
    # - anything else makes no sense,
    # as you need that context to make sense of the logged sets.
    template: Template

    def __init__(
        self, log_repository: Repository, template_repository: Repository
    ):
        self.log_repository = log_repository
        self.template_repository = template_repository
        self.template = self.template_repository.get()
        self._plan = None

    @property
    def plan(self) -> MesocyclePlan:
        """Lazy-load and cache the mesocycle plan."""
        if self._plan is None:
            self._plan = self.template.to_mesocycle_plan()
        return self._plan

    def log_set(
        self, exercise: str, reps: int, weight: float
    ) -> Result[str, ValueError]:
        exercise_names = self.template.get_exercise_names()
        if exercise not in exercise_names:
            match_rank = {
                fuzz.ratio(exercise, name): name for name in exercise_names
            }
            best_match = match_rank.get(max(match_rank.keys()), None)
            if best_match:
                return Success(
                    f"Exercise {exercise} not in {self.template.name}.\
                    Did you mean {best_match}?"
                )
            else:
                return Failure(
                    ValueError(
                        f"No match for {exercise} found in template\
                          {self.template.name}.\
                          Known exercises are: {', '.join(exercise_names)}"
                    )
                )

        week_index, workout_index = self._get_current_position()
        log = self.log_repository.all()

        # Use domain aggregate to encapsulate state logic
        exercise_session = ExerciseSession(
            exercise_name=exercise,
            week_index=week_index,
            workout_index=workout_index,
            events=log,
        )

        # Check if we can log a set
        if not exercise_session.can_log_set():
            return Failure(
                ValueError(
                    f"Cannot log set for exercise {exercise} in workout\
                {workout_index} week {week_index} - exercise already completed"
                )
            )

        # If this is the first set, log an ExerciseStarted event
        if exercise_session.is_first_set:
            started_event = ExerciseStarted(
                exercise=exercise,
                workout_index=workout_index,
                week_index=week_index,
                feedback={},
            )
            self.log_repository.add(started_event)

        # Create and log the set
        payload = Set(
            exercise=exercise,
            reps=reps,
            weight=weight,
            timestamp=datetime.now(),
            week_index=week_index,
            workout_index=workout_index,
        )
        self.log_repository.add(payload)
        return Success(f"Logged set: {exercise} {reps} reps at {weight} kg")

    def get_current_week_index(self) -> int:
        """Get current week index from domain model."""
        plan = self.template.to_mesocycle_plan()
        return plan.current_week_index(self.log_repository.all())

    def get_current_workout_index(self) -> int:
        """Get current workout index from domain model."""
        plan = self.template.to_mesocycle_plan()
        return plan.current_workout_index(self.log_repository.all())

    def show_current_day(self):
        raise NotImplementedError()

    def complete_exercise(
        self, exercise_name: str, feedback: MappingProxyType
    ) -> Result[str, ValueError]:

        week_index, workout_index = self._get_current_position()
        log = self.log_repository.all()

        # Use domain aggregate to check if exercise can be completed
        exercise_session = ExerciseSession(
            exercise_name=exercise_name,
            week_index=week_index,
            workout_index=workout_index,
            events=log,
        )

        # Get required sets from template
        current_workout = self.plan.get_workout(week_index, workout_index)
        current_exercise = next(
            (
                ex
                for ex in current_workout.exercises
                if ex.name == exercise_name
            ),
            None,
        )

        if not current_exercise:
            return Failure(
                ValueError(
                    f"Exercise {exercise_name} not found in workout {workout_index}"  # noqa
                )
            )

        required_sets = (
            len(current_exercise.sets) if current_exercise.sets else 1
        )

        if not exercise_session.can_complete(required_sets):
            sets_performed = len(exercise_session.sets)
            return Failure(
                ValueError(
                    f"Cannot complete exercise {exercise_name} as only\
                     {sets_performed} of {required_sets} sets have been completed"  # noqa
                )
            )

        completed_event = ExerciseCompleted(
            exercise=exercise_name,
            workout_index=workout_index,
            week_index=week_index,
            feedback=dict(feedback),
        )
        self.log_repository.add(completed_event)
        return Success(f"Logged completion for exercise: {exercise_name}")

    def complete_workout(self) -> Result[str, ValueError]:

        week_index, workout_index = self._get_current_position()
        log = self.log_repository.all()

        current_workout = self.plan.get_workout(week_index, workout_index)
        if not current_workout:
            return Failure(
                ValueError(
                    f"No workout found at week {week_index},"
                    f"workout {workout_index}"
                )
            )

        exercises_in_template = [ex.name for ex in current_workout.exercises]

        # Use domain aggregate to check if workout can be completed
        workout_session = WorkoutSession(
            week_index=week_index,
            workout_index=workout_index,
            exercise_names=exercises_in_template,
            events=log,
        )

        if not workout_session.can_complete():
            missing = workout_session.missing_exercises
            return Failure(
                ValueError(
                    f"Cannot complete workout {workout_index} as the\
                     following exercises are not yet completed: \
                     {', '.join(missing)}"
                )
            )

        completed_event = WorkoutCompleted(
            workout_index=workout_index,
            week_index=week_index,
        )
        self.log_repository.add(completed_event)
        return Success(f"Logged completion for workout: {workout_index}")

    def _get_current_position(self) -> tuple[int, int]:
        """Get current (week_index, workout_index) from domain."""
        events = self.log_repository.all()
        week_idx = self.plan.current_week_index(events)
        workout_idx = self.plan.current_workout_index(events)
        return week_idx, workout_idx
