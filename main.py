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
from returns.pipeline import is_successful

app = typer.Typer()


log_repository = JSONRepository("events.json")
template_repository = YAMLTemplateRepository("template.yaml")
logging_service = LoggingService(
    log_repository=log_repository, template_repository=template_repository
)


@app.command()
def log(exercise: str, reps: int, weight: float):
    result = logging_service.log_set(exercise, reps, weight)
    if is_successful(result):
        print(f"[green]{result.unwrap()}[/green]")
    else:
        print(f"[red]{result.failure()}[/red]")


@app.command()
def history():
    events = log_repository.all()
    for event in events:
        print(f"{event.exercise}: {event.reps} reps at {event.weight} kg")


@app.command()
def train():
    """Show today's training plan and progress (i.e. logged sets)."""
    logged_exercises = current_day_format(log_repository.get_by_date(datetime.now()))
    template = template_repository.get()  # Assume just one template for now
    plan: MesocyclePlan = template.to_mesocycle_plan()

    exercises_planned = plan.get_current_workout_prescriptions(
        log_repository.all(), lambda x: None
    )

    for elem in text_progress_table(logged_exercises, exercises_planned):
        print(elem)


if __name__ == "__main__":
    app()
