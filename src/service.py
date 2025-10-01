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
        _set = Set(exercise=exercise, reps=reps, weight=weight)

        self.repository.add(_set)
