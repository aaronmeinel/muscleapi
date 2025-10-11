from typing import Protocol
from src.events import ExerciseCompleted, ExerciseStarted, WorkoutCompleted
from src.models import Set, Template
from thefuzz import fuzz

from returns.result import Result, Success, Failure


class Repository(Protocol):
    def add(self, event): ...
    def all(self) -> list: ...
    def get(self) -> object: ...


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
        week_index = self.get_current_week_index()
        workout_index = self.get_current_workout_index()
        log = self.log_repository.all()
        try:
            payload = Set.create_safe(
                log=log,
                exercise=exercise,
                reps=reps,
                weight=weight,
                week_index=week_index,
                workout_index=workout_index,
            )
        except ValueError as e:
            return Failure(e)

        is_first_set = not any(
            map(
                lambda e: isinstance(e, Set)
                and e.workout_index == workout_index
                and e.week_index == week_index
                and e.exercise == exercise,
                log,
            )
        )

        if is_first_set:
            started_event = ExerciseStarted(
                exercise=exercise,
                workout_index=workout_index,
                week_index=week_index,
                feedback={},
            )
            self.log_repository.add(started_event)
        self.log_repository.add(payload)
        return Success(f"Logged set: {exercise} {reps} reps at {weight} kg")

    def get_current_week_index(self) -> int:
        return 0

    def get_current_workout_index(self) -> int:
        workouts_completed = filter(
            lambda e: isinstance(e, WorkoutCompleted),
            self.log_repository.all(),
        )
        return len(list(workouts_completed))

    def show_current_day(self):
        raise NotImplementedError()

    def complete_exercise(
        self, exercise_name: str, feedback: dict
    ) -> Result[str, ValueError]:
        workout_index = self.get_current_workout_index()
        week_index = self.get_current_week_index()
        log = self.log_repository.all()
        sets_performed = set(  # noqa
            [s for s in log if getattr(s, "exercise", None) == exercise_name]
        )
        sets_todo = set(  # noqa
            s
            for s in filter(
                lambda e: e.name == exercise_name,
                self.template.workouts[workout_index].exercises,
            )
        )

        completed_event = ExerciseCompleted(
            exercise=exercise_name,
            workout_index=workout_index,
            week_index=week_index,
            feedback=feedback,
        )
        self.log_repository.add(completed_event)
        return Success(f"Logged completion for exercise: {exercise_name}")

    def complete_workout(self) -> Result[str, ValueError]:
        workout_index = self.get_current_workout_index()
        week_index = self.get_current_week_index()
        log = self.log_repository.all()
        exercises_in_template = [
            ex.name for ex in self.template.workouts[workout_index].exercises
        ]
        completed_exercises = {
            e.exercise
            for e in log
            if isinstance(e, ExerciseCompleted)
            and e.workout_index == workout_index
            and e.week_index == week_index
        }

        missing_exercises = set(exercises_in_template) - completed_exercises
        if missing_exercises:
            return Failure(
                ValueError(
                    f"Cannot complete workout {workout_index} as the\
                     following exercises are not yet completed: \
                     {', '.join(missing_exercises)}"
                )
            )
        completed_event = WorkoutCompleted(
            workout_index=workout_index,
            week_index=week_index,
        )
        self.log_repository.add(completed_event)
        return Success(f"Logged completion for workout: {workout_index}")


class PlanManagementService:
    repository: Repository

    def __init__(self, repository: Repository):
        self.repository = repository

    def create_template(self, name: str, exercises: list[str]):
        self.repository.add({"name": name, "exercises": exercises})

    def get_plan(self, name: str):
        pass

    def list_plans(self):
        pass

    def list_exercises(self):
        pass
