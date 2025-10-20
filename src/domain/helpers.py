from src.events import Event


def filter_by_context(
    events: list[Event],
    exercise: str | None = None,
    week: int | None = None,
    workout: int | None = None,
) -> list[Event]:
    """Reusable context filter."""

    def matches(e: Event) -> bool:
        return (
            (exercise is None or getattr(e, "exercise", None) == exercise)
            and (week is None or e.week_index == week)
            and (workout is None or e.workout_index == workout)
        )

    return list(filter(matches, events))


def filter_events_by_type(
    events: list[Event], event_type: type
) -> list[Event]:
    """Filter events by their type."""
    return [e for e in events if isinstance(e, event_type)]
