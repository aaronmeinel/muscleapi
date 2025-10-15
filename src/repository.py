import json
from datetime import datetime
from pydantic import BaseModel
from src.events import ExerciseCompleted, ExerciseStarted
from src.models import Exercise, Set, SetPrescription, Template, Workout
from src.service import Repository
from pathlib import Path
import yaml

###########################################
# JSON Repository

# Used for logging sets and related events
###########################################


class SetAdapter(BaseModel):
    timestamp: datetime
    data: Set  # noqa
    model_class: str = "Set"

    def to_domain(self):
        return self.data


class ExerciseStartedAdapter(BaseModel):
    timestamp: datetime
    data: ExerciseStarted  # noqa
    model_class: str = "ExerciseStarted"

    def to_domain(self):
        return self.data


class ExerciseCompletedAdapter(BaseModel):
    timestamp: datetime
    data: ExerciseCompleted  # noqa
    model_class: str = "ExerciseCompleted"

    def to_domain(self):
        return self.data


class CompletedWorkoutAdapter(BaseModel):
    timestamp: datetime
    data: ExerciseCompleted  # noqa
    model_class: str = "WorkoutCompleted"

    def to_domain(self):
        return self.data


ADAPTER_MAP = {
    "Set": SetAdapter,
    "ExerciseStarted": ExerciseStartedAdapter,
    "ExerciseCompleted": ExerciseCompletedAdapter,
    "WorkoutCompleted": CompletedWorkoutAdapter,
}


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
                events = []
                for item in data:
                    if isinstance(item, str):
                        item = json.loads(item)

                    adapter = ADAPTER_MAP.get(item.get("model_class"), None)
                    if adapter:
                        events.append(adapter(**item).to_domain())
                    else:
                        raise ValueError(
                            f"Unknown model class: {item.get('model_class')}"
                        )
                return events
        except FileNotFoundError:
            return []

    def _save(self):
        try:
            with open(self.filepath, "w") as f:
                _data = []
                for event in self.events:
                    adapter = ADAPTER_MAP.get(event.__class__.__name__, None)
                    if not adapter:
                        raise ValueError("No adapter for {}")
                    _data.append(
                        adapter(timestamp=datetime.now(), data=event).dict()
                    )
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


#######################################################
# YAML Repository
# Used for storing plan templates and configurations
#######################################################


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
                    ExerciseReadModel(**ex)
                    for ex in getattr(workout, "exercises", [])
                ]
                exercises = tuple(  # Convert list to tuple
                    Exercise(
                        name=ex.name, sets=tuple(ex.sets) if ex.sets else None
                    )  # Convert sets to tuple
                    for ex in exercise_data
                )
                workouts.append(Workout(exercises=exercises))
            templates.append(
                Template(name=read_model.name, workouts=tuple(workouts))
            )  # Convert workouts to tuple
        return templates

    def add(self, template: Template):
        self.templates.append(template)
        with open(self.filepath, "w") as f:
            data = [
                {
                    "name": t.name,
                    "workouts": [
                        {
                            "exercises": [
                                {
                                    "name": ex.name,
                                    "sets": [
                                        {
                                            "prescribed_reps": s.prescribed_reps,  # noqa
                                            "prescribed_weight": s.prescribed_weight,  # noqa
                                        }
                                        for s in (ex.sets if ex.sets else [])
                                    ],
                                }
                                for ex in w.exercises
                            ]
                        }
                        for w in t.workouts
                    ],
                }
                for t in self.templates
            ]
            yaml.dump(data, f)

    def all(self):
        return self.templates

    def get(self):
        return self.templates[0]
