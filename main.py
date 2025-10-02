import typer
import toolz
from src.presentation import current_day_format, text_progress_table
from src.repository import JSONRepository
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

    exercises_planned = {
        "squat": [
            {"prescribed_reps": 12, "prescribed_weight": 100},
            {"prescribed_reps": 10, "prescribed_weight": 105},
        ],
        "bench press": [
            {"prescribed_reps": 10, "prescribed_weight": 80},
            {"prescribed_reps": 8, "prescribed_weight": 85},
            {"prescribed_reps": 6, "prescribed_weight": 90},
        ],
        "deadlift": [
            {"prescribed_reps": 6, "prescribed_weight": 120},
            {"prescribed_reps": 3, "prescribed_weight": 150},
        ],
        "pull ups": [
            {"prescribed_reps": 8, "prescribed_weight": 82},
            {"prescribed_reps": 6, "prescribed_weight": 82},
        ],
    }

    for elem in text_progress_table(logged_exercises, exercises_planned):
        print(elem)


if __name__ == "__main__":
    app()
