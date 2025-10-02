import json
from datetime import datetime
from pydantic import BaseModel
from src.models import Set
from src.service import Repository


class SetAdapter(BaseModel):
    timestamp: datetime
    data: Set

    def to_domain(self):
        return self.data


class JSONRepository(Repository):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.events = self._load()

    def _load(self) -> list[Set]:
        try:
            with open(self.filepath, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    return []
                sets = []
                for item in data:
                    if isinstance(item, str):
                        item = json.loads(item)
                    sets.append(SetAdapter(**item).to_domain())
                return sets
        except FileNotFoundError:
            return []

    def _save(self):
        try:
            with open(self.filepath, "w") as f:
                _data = [
                    SetAdapter(timestamp=datetime.now(), data=s).dict()
                    for s in self.events
                ]
                json.dump(_data, f, indent=2, default=str)
        except FileNotFoundError as e:
            raise e

    def add(self, _set: Set):
        self.events.append(_set)
        self._save()

    def all(self):
        return self.events

    def get(self):
        raise ValueError("Whatever")

    def get_by_date(self, date) -> list[Set]:
        return [e for e in self.events if e.timestamp.date() == date.date()]
