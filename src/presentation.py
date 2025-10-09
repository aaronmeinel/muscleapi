from itertools import zip_longest
from numbers import Number
from typing import Literal
from src.models import Set

import toolz
from rich.markdown import Markdown
from rich.table import Table


def current_day_format(todays_sets: list[Set]) -> dict[str, list[dict]]:
    """Format today's events for display."""

    by_exercise = toolz.groupby(lambda _set: _set.exercise, todays_sets)
    by_type = toolz.valmap(
        toolz.curried.groupby(lambda x: x.__class__.__name__), by_exercise
    )

    return {
        exercise: [
            {
                "performed_reps": set_data.reps,
                "performed_weight": set_data.weight,
                "prescribed_reps": set_data.reps,
                "prescribed_weight": set_data.weight,
                "started": val.get("ExerciseStarted", False) is not False,
            }
            for set_data in val["Set"]
        ]
        for exercise, val in by_type.items()
    }


def _format(num: Number, color: Literal["red", "green"]) -> str:
    return f"[{color}]{num}[/{color}]"


def format_weight(set_data: dict) -> str:
    num = set_data.get("performed_weight") or set_data["prescribed_weight"]
    if "performed_weight" in set_data:
        return _format(num, "green")
    else:
        return _format(num, "red")


def format_reps(set_data: dict) -> str:
    num = set_data.get("performed_reps") or set_data["prescribed_reps"]
    if "performed_reps" in set_data:
        return _format(num, "green")
    else:
        return _format(num, "red")


def join_sets(
    logged: dict[str, list], planned: dict[str, list]
) -> dict[str, list[dict]]:
    """Join logged sets with planned sets.

    This is a bit tricky because we want to show all planned sets,
    even if they are not yet logged.
    We also want to show logged sets that
    are not in the plan (e.g. extra sets).
    We do this by zipping the two lists together,
    filling in an empty dict for missing values.
    Args:
        logged (dict): A dictionary where keys are exercise
            names and values are lists
            of dictionaries containing 'performed_reps', 'performed_weight',
            'prescribed_reps', and 'prescribed_weight'.
            This is basically your training log. You can get the right format
            by calling current_day_format on a list
            of Set objects.
        planned (dict): A dictionary where keys are exercise names
            and values are lists of dictionaries containing
            'prescribed_reps' and 'prescribed_weight'.
            This is basically your training plan for the day.
    Returns:
        dict: A dictionary where keys are exercise names
            and values are lists of
            dictionaries containing 'performed_reps', 'performed_weight',
            'prescribed_reps', and 'prescribed_weight'.
            This is the progress overview for the day.
    """
    # Merge the two dictionaries by exercise name, combining the lists of sets.
    # Use zip_longest to pair sets, filling in with empty dicts if one list
    # is shorter.
    # The result is a dictionary where each exercise maps to a list of sets,
    # each set being a merged dictionary of performed and prescribed data.
    # The merging is done such that if a set has been performed, its data
    # takes precedence.

    return {
        exercise: [
            toolz.merge(*seqs)
            for seqs in list(zip_longest(*set_lists, fillvalue={}))
        ]
        for exercise, set_lists in toolz.merge_with(
            list,
            logged,
            planned,
        ).items()
    }


def construct_exercise_table(exercise: str, sets: list[dict]) -> Table:

    table = Table(title=exercise.capitalize())
    table.add_column("Reps")
    table.add_column("Weight")
    table.add_column("Started")
    table.add_column("Completed")

    for set_data in sets:
        started = set_data.get("started", False)
        table.add_row(
            format_reps(set_data), format_weight(set_data), str(started)
        )
    return table


def text_progress_table(
    logged_exercises: dict[str, list], exercises_planned: dict[str, list]
):
    """Generate an overview of the progress of today's plan.

    This uses data from both the training log (i.e. what has been done)
    and the training plan (i.e. what is supposed to be done) and combines those
    in a way that is useful for display in a CLI.
    It should not be used for anything else.
    Args:
        logged_exercises (dict): A dictionary where keys are exercise names
        and values are lists of
            dictionaries containing 'performed_reps', 'performed_weight',
            'prescribed_reps', and
            'prescribed_weight'.
            This is basically your training log. You can get the right format
            by calling current_day_format on a list
            of Set objects.
        exercises_planned (dict): A dictionary where keys are exercise names
            and values are lists of
            dictionaries containing 'prescribed_reps' and 'prescribed_weight'.
            This is basically your training plan for the day.
    """
    joined = join_sets(logged_exercises, exercises_planned)

    exercise_tables = []
    for exercise, sets in joined.items():
        table = construct_exercise_table(exercise, sets)
        exercise_tables.append(table)

    return [Markdown("### Today's Training Plan")] + exercise_tables
