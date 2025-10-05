from datetime import datetime
from typing import Protocol
from src.models import Set


class Repository(Protocol):
    def add(self, event): ...
    def all(self): ...
    def get(self): ...


class LoggingService:
    repository: Repository

    def __init__(self, repository: Repository):
        self.repository = repository

    def log_set(self, exercise: str, reps: int, weight: float):
        _set = Set(
            exercise=exercise,
            reps=reps,
            weight=weight,
            timestamp=datetime.now(),
            week_index=self.get_current_week_index(),
            workout_index=self.get_current_workout_index(),
        )

        self.repository.add(_set)

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
