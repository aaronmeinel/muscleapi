from pathlib import Path
import typer


from src.service import logging as logging_service
from src import storage
import rich


from returns.pipeline import is_successful

app = typer.Typer()
EVENTS_PATH = Path("events.json")


@app.command()
def log(exercise: str, reps: int, weight: float):
    events = storage.load_events(EVENTS_PATH)
    template = storage.load_template(Path("template.json"))
    logging_result = logging_service.log_set(
        events, template=template, exercise=exercise, reps=reps, weight=weight
    )
    if is_successful(logging_result):
        rich.print(f"[green]{logging_result.unwrap()}[/green]")
    else:
        rich.print(f"[red]{logging_result.failure()}[/red]")


@app.command()
def complete(exercise: str, joint_pain: int, pump: int, workload: int):
    """Mark an exercise as completed for today."""
    events = storage.load_events(EVENTS_PATH)
    template = storage.load_template(Path("template.json"))
    feedback = {"joint_pain": joint_pain, "pump": pump, "workload": workload}
    completion_result = logging_service.complete_exercise(
        events, template=template, exercise=exercise, feedback=feedback
    )
    if is_successful(completion_result):
        rich.print(f"[green]{completion_result.unwrap()}[/green]")
    else:
        rich.print(f"[red]{completion_result.failure()}[/red]")


@app.command()
def history():
    events = storage.load_events(EVENTS_PATH)
    rich.print("[bold underline]Exercise Log History[/bold underline]")
    for event in events:
        rich.print(f"{event.exercise}: {event.reps} reps at {event.weight} kg")


@app.command()
def train():
    """Show today's training plan and progress (i.e. logged sets)."""
    rich.print("FIXME")


@app.command()
def finish_workout():
    """Mark the current workout as completed."""
    finish_result = logging_service.complete_workout()
    if is_successful(finish_result):
        rich.print(f"[green]{finish_result.unwrap()}[/green]")
    else:
        rich.print(f"[red]{finish_result.failure()}[/red]")


if __name__ == "__main__":
    app()
