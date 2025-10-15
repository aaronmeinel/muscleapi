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
def complete(exercise: str, joint_pain: int, pump: int, workload: int):
    """Mark an exercise as completed for today."""
    feedback = {"joint_pain": joint_pain, "pump": pump, "workload": workload}
    result = logging_service.complete_exercise(exercise, feedback)
    if is_successful(result):
        rich.print(f"[green]{result.unwrap()}[/green]")
    else:
        rich.print(f"[red]{result.failure()}[/red]")


@app.command()
def history():
    events = log_repository.all()
    for event in events:
        rich.print(f"{event.exercise}: {event.reps} reps at {event.weight} kg")


@app.command()
def train():
    """Show today's training plan and progress (i.e. logged sets)."""
    all_events = log_repository.all()

    # Filter to only exercise-level events (exclude WorkoutCompleted)
    from src.events import ExerciseStarted, ExerciseCompleted
    from src.models import Set

    logged_exercises = [
        e
        for e in all_events
        if isinstance(e, (Set, ExerciseStarted, ExerciseCompleted))
    ]

    template = template_repository.get()
    plan: MesocyclePlan = template.to_mesocycle_plan()

    # Use domain methods to get current position
    current_week_idx = plan.current_week_index(all_events)
    current_workout_idx = plan.current_workout_index(all_events)

    # Filter logged exercises to current week/workout only
    todays_exercises = [
        e
        for e in logged_exercises
        if e.week_index == current_week_idx
        and e.workout_index == current_workout_idx
    ]

    # Get current workout prescriptions
    current_workout = plan.current_workout(all_events)
    if not current_workout:
        rich.print("[yellow]No more workouts in plan![/yellow]")
        return

    exercises_planned = plan.get_current_workout_prescriptions(
        all_events,
        lambda weight_or_reps: (
            weight_or_reps * 1.025 if weight_or_reps else "?"
        ),
    )

    for elem in text_progress_table(
        current_day_format(todays_exercises), exercises_planned
    ):
        rich.print(elem)


@app.command()
def finish_workout():
    """Mark the current workout as completed."""
    result = logging_service.complete_workout()
    if is_successful(result):
        rich.print(f"[green]{result.unwrap()}[/green]")
    else:
        rich.print(f"[red]{result.failure()}[/red]")


if __name__ == "__main__":
    app()
