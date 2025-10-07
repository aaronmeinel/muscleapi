from pytest import fixture
from src.models import Exercise, SetPrescription, Workout, Template


@fixture
def sample_template():

    exercises1 = [
        Exercise(ex_name, [SetPrescription()])
        for ex_name in ["Squat", "Bench press", "Deadlift"]
    ]
    exercises2 = [
        Exercise(ex_name, [SetPrescription()])
        for ex_name in ["Squat", "Pushup", "Pullup"]
    ]
    workouts = [Workout(exercises=exercises1), Workout(exercises=exercises2)]
    return Template("twice a week maintenance", workouts=workouts)
