from pathlib import Path
import json
import yaml
from pydantic import TypeAdapter
from src.events import Event
from src.models import Template

# Pydantic type adapter for automatic serialization
EventAdapter = TypeAdapter(list[Event])


def load_events(path: Path) -> list[Event]:
    """Load all events from JSON file using Pydantic."""
    if not path.exists():
        return []

    with open(path) as f:
        data = json.load(f)

    # Pydantic handles validation + deserialization
    return EventAdapter.validate_python(data)


def save_events(path: Path, events: list[Event]) -> None:
    """Save all events to JSON file (overwrites)."""
    # Pydantic handles serialization
    data = EventAdapter.dump_python(events, mode="json")

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def append_events(path: Path, new_events: list[Event]) -> None:
    """Append new events to existing file."""
    existing = load_events(path)
    all_events = existing + new_events
    save_events(path, all_events)


def load_template(path: Path) -> Template:
    """Load template from YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)

    # Use your existing Template parsing logic
    return (
        Template.from_dict(data)
        if hasattr(Template, "from_dict")
        else Template(**data)
    )
