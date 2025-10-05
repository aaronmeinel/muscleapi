import json
from datetime import datetime
from pydantic import BaseModel
from src.models import Exercise, Set, SetPrescription, Template, Workout
from src.service import Repository
from pathlib import Path
import yaml


class SetAdapter(BaseModel):
    timestamp: datetime
    data: Set

    def to_domain(self):
        return self.data


class JSONRepository(Repository):
    """A simple JSON file-based repository for storing Sets.
    In fact, this is right now used only for storing set data.
    We might not need anything else after all.
    """

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


class ExerciseReadModel(BaseModel):
    name: str
    sets: list[SetPrescription]


class WorkoutReadModel(BaseModel):
    exercises: list[dict]


class TemplateReadModel(BaseModel):
    name: str
    workouts: list[WorkoutReadModel]


class YAMLTemplateRepository(Repository):
    """A simple YAML file-based repository for storing plan templates"""

    def __init__(self, filepath: str = "./template.yaml"):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            self.filepath.touch()
        self.templates = self._load()

    def _read_file(self):
        """Read the YAML file and return the raw data.

        This allows for easier testing by overriding this method.
        """
        with open(self.filepath, "r") as f:
            data = yaml.safe_load(f)
        return data

    def _load(self):
        data = self._read_file()
        if not data:
            return []
        if isinstance(data, str):
            data = yaml.safe_load(data)
        if isinstance(data, dict):
            data = [data]
        templates = []
        for item in data:
            read_model = TemplateReadModel(**item)
            workouts = []
            for workout in read_model.workouts:
                exercise_data = [
                    ExerciseReadModel(**ex) for ex in getattr(workout, "exercises", [])
                ]
                exercises = [
                    Exercise(name=ex.name, sets=ex.sets) for ex in exercise_data
                ]
                workouts.append(Workout(exercises=exercises))
            templates.append(Template(name=read_model.name, workouts=workouts))
        return templates

    def add(self, template: Template):
        self.templates.append(template)
        with open(self.filepath, "w") as f:
            data = [
                TemplateReadModel(
                    name=t.name,
                    workouts=[
                        WorkoutReadModel(
                            exercises=[{"name": ex.name} for ex in w.exercises]
                        )
                        for w in t.workouts
                    ],
                ).dict()
                for t in self.templates
            ]
            yaml.dump(data, f)

    def all(self):
        return self.templates

    def get(self):
        return self.templates[0]
