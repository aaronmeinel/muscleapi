from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel


@dataclass(frozen=True)
class Set:
    exercise: str
    reps: int
    weight: float
