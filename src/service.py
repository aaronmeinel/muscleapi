from datetime import datetime
from typing import Protocol
from src.models import Set, Template
from thefuzz import fuzz
import toolz
from returns.result import Result, Success, Failure


class Repository(Protocol):
    def add(self, event): ...
    def all(self): ...
    def get(self) -> object: ...


class LoggingService:
    log_repository: Repository
    template_repository: Repository
    # The idea here is that you're going to log against a template - anything else makes no sense,
    # as you need that context to make sense of the logged sets.
    template: Template

    def __init__(self, log_repository: Repository, template_repository: Repository):
        self.log_repository = log_repository
        self.template_repository = template_repository
        self.template = self.template_repository.get()

    def log_set(
        self, exercise: str, reps: int, weight: float
    ) -> Result[str, ValueError]:
        exercise_names = self.template.get_exercise_names()
        if exercise not in exercise_names:
            match_rank = {fuzz.ratio(exercise, name): name for name in exercise_names}
            best_match = match_rank.get(max(match_rank.keys()), None)
            if best_match:
                return Success(
                    f"Exercise {exercise} not in template {self.template.name}. Did you mean {best_match}?"
                )
            else:
                return Failure(
                    ValueError(
                        f"No match for {exercise} found in template {self.template.name}. Known exercises are: {', '.join(exercise_names)}"
                    )
                )

        _set = Set(
            exercise=exercise,
            reps=reps,
            weight=weight,
            timestamp=datetime.now(),
            week_index=self.get_current_week_index(),
            workout_index=self.get_current_workout_index(),
        )

        self.log_repository.add(_set)
        return Success(f"Logged set: {exercise} {reps} reps at {weight} kg")

    def get_current_week_index(self) -> int:
        return 0

    def get_current_workout_index(self) -> int:
        return 0

    def show_current_day(self):
        raise NotImplementedError()


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
