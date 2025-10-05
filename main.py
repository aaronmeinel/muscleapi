import typer
import toolz
from src.models import MesocyclePlan
from src.presentation import current_day_format, text_progress_table
from src.repository import JSONRepository
from src.repository import YAMLTemplateRepository
from src.service import LoggingService
from rich import print
from rich.markdown import Markdown
from rich.table import Table
from datetime import datetime

app = typer.Typer()


repository = JSONRepository("events.json")
logging_service = LoggingService(repository=repository)


@app.command()
def log(exercise: str, reps: int, weight: float):
    logging_service.log_set(exercise, reps, weight)


@app.command()
def history():
    events = repository.all()
    for event in events:
        print(f"{event.exercise}: {event.reps} reps at {event.weight} kg")


@app.command()
def train():
    """Show today's training plan and progress (i.e. logged sets)."""
    logged_exercises = current_day_format(repository.get_by_date(datetime.now()))
    template = YAMLTemplateRepository("template.yaml").get()
    plan: MesocyclePlan = template.to_mesocycle_plan()

    exercises_planned = plan.get_current_workout_prescriptions(
        repository.all(), lambda x: None
    )

    for elem in text_progress_table(logged_exercises, exercises_planned):
        print(elem)


if __name__ == "__main__":
    app()
