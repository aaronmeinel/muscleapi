import typer

from src.models import MesocyclePlan
from src.presentation import current_day_format, text_progress_table
from src.repository import JSONRepository
from src.repository import YAMLTemplateRepository
from src.service import LoggingService
import rich


from returns.pipeline import is_successful

app = typer.Typer()


log_repository = JSONRepository("events.json")
template_repository = YAMLTemplateRepository("template.yaml")
logging_service = LoggingService(
    log_repository=log_repository, template_repository=template_repository
)


@app.command()
def log(exercise: str, reps: int, weight: float):
    logging_result = logging_service.log_set(exercise, reps, weight)
    if is_successful(logging_result):
        rich.print(f"[green]{logging_result.unwrap()}[/green]")
    else:
        rich.print(f"[red]{logging_result.failure()}[/red]")


@app.command()
def history():
    events = log_repository.all()
    for event in events:
        rich.print(f"{event.exercise}: {event.reps} reps at {event.weight} kg")


@app.command()
def train():
    """Show today's training plan and progress (i.e. logged sets)."""
    logged_exercises = log_repository.all()

    template = template_repository.get()  # Assume just one template for now
    plan: MesocyclePlan = template.to_mesocycle_plan()

    exercises_planned = plan.get_current_workout_prescriptions(
        logged_exercises, lambda weight_or_reps: None
    )

    for elem in text_progress_table(
        current_day_format(logged_exercises), exercises_planned
    ):
        rich.print(elem)


if __name__ == "__main__":
    app()
