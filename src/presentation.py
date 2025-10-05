from src.models import Set
from typing import TypedDict
import toolz
from rich.markdown import Markdown
from rich.table import Table


def current_day_format(todays_sets: list[Set]) -> dict[str, list[dict]]:
    """Format today's events for display."""
    return {
        e.exercise: [
            {
                "performed_reps": e.reps,
                "performed_weight": e.weight,
                "prescribed_reps": e.reps,
                "prescribed_weight": e.weight,
            }
        ]
        for e in todays_sets
    }


def text_progress_table(logged_exercises, exercises_planned):
    """Generate a list of rich renderables showing the progress of today's training plan.

    Args:
        logged_exercises (dict): A dictionary where keys are exercise names and values are lists of
            dictionaries containing 'performed_reps', 'performed_weight', 'prescribed_reps', and
            'prescribed_weight'.
            This is basically your training log. You can get the right format by calling current_day_format on a list
            of Set objects.
        exercises_planned (dict): A dictionary where keys are exercise names and values are lists of
            dictionaries containing 'prescribed_reps' and 'prescribed_weight'.
            This is basically your training plan for the day.
    """

    joined = toolz.merge_with(
        toolz.compose(list, toolz.concat),
        logged_exercises,
        exercises_planned,
    )
    exercise_tables = []
    for exercise, sets in joined.items():
        table = Table(title=exercise.capitalize())
        table.add_column("Reps")
        table.add_column("Weight")
        for s in sets:
            is_done = "performed_reps" in s
            format_ = lambda num, s=s: (
                f"[green]{num}[/green]" if is_done else f"[red]{num}[/red]"
            )
            table.add_row(
                format_(s.get("performed_reps", s["prescribed_reps"])),
                format_(s.get("performed_weight", s["prescribed_weight"])),
            )
        exercise_tables.append(table)
    md = Markdown("### Today's Training Plan")
    return [md] + exercise_tables
