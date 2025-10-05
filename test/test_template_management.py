from datetime import datetime
from numbers import Number
from pathlib import Path
from typing import Optional
from src.repository import YAMLTemplateRepository, TemplateReadModel
from src.models import (
    MesocyclePlan,
    Set,
    SetPrescription,
    Template,
    Exercise,
    Week,
    Workout,
)
from pytest import fixture
import yaml

from src.service import PlanManagementService


@fixture
def sample_template():
    exercises1 = [
        Exercise("Squat", [SetPrescription()]),
        Exercise("Bench press", [SetPrescription()]),
        Exercise("Deadlift", [SetPrescription()]),
    ]
    exercises2 = [
        Exercise("Squat", [SetPrescription()]),
        Exercise("Pushup", [SetPrescription()]),
        Exercise("Pullup", [SetPrescription()]),
    ]
    workouts = [Workout(exercises=exercises1), Workout(exercises=exercises2)]
    return Template("twice a week maintenance", workouts=workouts)


def test_write_sample_template_to_yaml(sample_template):
    data = sample_template.to_yaml()
    path = Path("template.yaml")
    with open(path, "w") as f:
        f.write(data)

    assert path.exists()
    assert path.read_text() == data


def test_yaml_raw_roundtrip(tmp_path, sample_template):

    data = sample_template.to_yaml()
    path = tmp_path / "template.yaml"
    with open(path, "w") as f:
        f.write(data)

    with open(path, "r") as f:
        loaded = yaml.safe_load(f)

    assert loaded == {
        "name": "twice a week maintenance",
        "workouts": [
            {
                "exercises": [
                    {
                        "name": "Squat",
                        "sets": [{"prescribed_reps": None, "prescribed_weight": None}],
                    },
                    {
                        "name": "Bench press",
                        "sets": [{"prescribed_reps": None, "prescribed_weight": None}],
                    },
                    {
                        "name": "Deadlift",
                        "sets": [{"prescribed_reps": None, "prescribed_weight": None}],
                    },
                ],
                "index": None,
            },
            {
                "exercises": [
                    {
                        "name": "Squat",
                        "sets": [{"prescribed_reps": None, "prescribed_weight": None}],
                    },
                    {
                        "name": "Pushup",
                        "sets": [{"prescribed_reps": None, "prescribed_weight": None}],
                    },
                    {
                        "name": "Pullup",
                        "sets": [{"prescribed_reps": None, "prescribed_weight": None}],
                    },
                ],
                "index": None,
            },
        ],
    }


def test_yaml_repository_roundtrip(tmp_path, sample_template):

    data = sample_template.to_yaml()
    assert data
    path = tmp_path / "template.yaml"

    path.write_text(data)

    class MockRepo(YAMLTemplateRepository):
        def _read_file(self):
            return path.read_text()

    repo = MockRepo(tmp_path / "templates.yaml")

    templates = repo.all()
    assert templates
    for template in templates:
        assert isinstance(template, Template)
        for exercise in template.workouts:
            assert isinstance(exercise, Workout)


def test_load_one_workout_from_mesocycleplan_has_correct_format_for_command():
    workouts = [
        Workout(
            exercises=[
                Exercise(name="squat", sets=[SetPrescription()]),
                Exercise(name="bench press", sets=[SetPrescription()]),
            ],
            index=0,
        ),
        Workout(
            exercises=[
                Exercise(name="deadlift", sets=[SetPrescription()]),
                Exercise(name="pull ups", sets=[SetPrescription()]),
            ],
            index=1,
        ),
    ]
    weeks = [Week(index=i, workouts=workouts) for i in range(2)]
    plan = MesocyclePlan(template_name="5/3/1", weeks=weeks)
    # We're in week 0.
    # We've performed workout 0, one set of squat and one set of bench press.
    # Therefore, we want to see workout 1's prescriptions.
    sets = [
        Set(
            exercise="squat",
            reps=5,
            weight=100,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
        Set(
            exercise="bench press",
            reps=5,
            weight=80,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
    ]

    current_workout_prescriptions = plan.get_current_workout_prescriptions(
        sets_performed=sets, progress_function=lambda x: None
    )
    # Since this is the first iteration of this specific workout (deadlift, pull ups),
    # we don't have any prescriptions yet. We might show RIR 3 or something.
    # But for now, just show None.
    # For actual prescriptions, the user would have to complete the first week.
    assert current_workout_prescriptions == {
        "deadlift": [
            {"prescribed_reps": None, "prescribed_weight": None},
        ],
        "pull ups": [
            {"prescribed_reps": None, "prescribed_weight": None},
        ],
    }


def test_second_week_has_prescriptions_after_complete_first_week():
    workouts = [
        Workout(
            exercises=[
                Exercise(name="squat", sets=[SetPrescription()]),
                Exercise(name="bench press", sets=[SetPrescription()]),
            ],
            index=0,
        ),
        Workout(
            exercises=[
                Exercise(name="deadlift", sets=[SetPrescription()]),
                Exercise(name="pull ups", sets=[SetPrescription()]),
            ],
            index=1,
        ),
    ]
    weeks = [Week(index=i, workouts=workouts) for i in range(3)]
    plan = MesocyclePlan(template_name="some plan", weeks=weeks)

    sets = [  # First week, workout 0
        Set(
            exercise="squat",
            reps=5,
            weight=100,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
        Set(
            exercise="bench press",
            reps=5,
            weight=80,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=0,
        ),
        # First week, workout 1
        Set(
            exercise="deadlift",
            reps=5,
            weight=120,
            timestamp=datetime.now(),
            week_index=0,
            workout_index=1,
        ),
        Set(
            exercise="pull ups",
            reps=8,
            weight=80,  # bodyweight + 0 - special treatment for bodyweight exercises not implemented yet
            timestamp=datetime.now(),
            week_index=0,
            workout_index=1,
        ),
    ]
    # Now, we're in week 1, workout 0

    # Since we just want to test that the data is formatted correctly,
    # we'll use a mock progress function that just returns the weights we want to see here.
    # That result doesnt make much sense, but we dont wont to test
    # the progress function here, just the formatting of the output.
    def mock_progress_function(x: Optional[Number]) -> Optional[Number]:
        return 5

    current_workout_prescriptions = plan.get_current_workout_prescriptions(
        sets_performed=sets, progress_function=mock_progress_function
    )
    # We should see prescriptions based on last week's performance.
    assert current_workout_prescriptions == {
        "squat": [
            {"prescribed_reps": 5, "prescribed_weight": 5},
        ],
        "bench press": [
            {"prescribed_reps": 5, "prescribed_weight": 5},
        ],
    }


def test_plan_management_service_create_plan(tmp_path, sample_template):
    class MockRepo(YAMLTemplateRepository):
        def _read_file(self):
            return ""

    repo = MockRepo(tmp_path / "templates.yaml")
    repo.add(sample_template)

    assert len(repo.all()) == 1
    template = repo.get()
    assert template.name == "twice a week maintenance"

    service = PlanManagementService(repository=repo)
    service.create_plan(name="my plan", exercises=["squat", "bench press", "deadlift"])
