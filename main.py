import typer

from src.repository import JSONRepository
from src.service import LoggingService
from rich import print

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


if __name__ == "__main__":
    app()
