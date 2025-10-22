"""FastAPI backend for MuscleAPI.

Thin API layer over existing domain services.
Exposes REST endpoints for SvelteKit frontend.
"""

from types import MappingProxyType
from returns.pipeline import is_successful
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import rich
import sys


from src.models import Set
from src.events import (
    ExerciseStarted,
    ExerciseCompleted,
    WorkoutCompleted,
)
from src.service.plan_management import 
from src.service.logging import log_set
from src.service.prescription import (
    get_prescriptions_for_workout,
    feedback_based_progression,
    Prescription,
)
from src.storage import append_events, load_events, load_template


app = FastAPI(
    title="MuscleAPI",
    description="Progressive overload tracking API",
    version="0.1.0",
)

# CORS for local development with SvelteKit
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # SvelteKit dev server
        "http://localhost:4173",  # SvelteKit preview
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
        "http://localhost:5174",  # Alternative port
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize repositories and services
# Paths are relative to where the server is run from (project root)
PROJECT_ROOT = Path.cwd()  # Assumes run from project root
EVENTS_PATH = PROJECT_ROOT / "events.json"
TEMPLATE_PATH = PROJECT_ROOT / "template.yaml"


# Request/Response Models
class LogSetRequest(BaseModel):
    """Request to log a set."""

    exercise: str = Field(..., min_length=1, description="Exercise name")
    reps: int = Field(..., gt=0, description="Number of reps performed")
    weight: float = Field(..., ge=0, description="Weight used (kg)")


class ExerciseFeedbackRequest(BaseModel):
    """Request to complete an exercise with feedback."""

    exercise: str = Field(..., min_length=1)
    joint_pain: int = Field(
        ..., ge=0, le=3, description="Joint pain level 0-3"
    )
    pump: int = Field(..., ge=0, le=3, description="Muscle pump level 0-3")
    workload: int = Field(
        ..., ge=0, le=3, description="Perceived workload 0-3"
    )


class ApiResponse(BaseModel):
    """Standard API response."""

    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class LoggedSetInfo(BaseModel):
    """Information about a logged set."""

    reps: int
    weight: float


class ExerciseInfo(BaseModel):
    """Exercise information for current workout."""

    name: str
    prescribed_sets: list[dict]
    logged_sets: list[LoggedSetInfo]
    is_started: bool = False
    is_completed: bool = False


class CurrentWorkoutResponse(BaseModel):
    """Current workout information."""

    week_index: int
    workout_index: int
    exercises: list[ExerciseInfo]


# Health check
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "MuscleAPI is running"}


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "logging": "ok",
            "template": "ok",
            "prescription": "ok",
        },
    }


# Workout endpoints
@app.get("/api/current-workout", response_model=CurrentWorkoutResponse)
async def get_current_workout():
    """Get the current workout with prescriptions and logged sets."""
    try:
        plan = logging_service.plan
        events = log_repo.all()

        week_idx, workout_idx = logging_service._get_current_position()
        current_workout = plan.get_workout(week_idx, workout_idx)

        if not current_workout:
            raise HTTPException(
                status_code=404, detail="No current workout found"
            )

        # Get baseline prescriptions from template
        baseline_prescriptions = {}
        for exercise in current_workout.exercises:
            baseline_prescriptions[exercise.name] = [
                Prescription(
                    prescribed_reps=s.prescribed_reps,
                    prescribed_weight=s.prescribed_weight,
                )
                for s in exercise.sets
            ]

        # Get all sets and feedback for intelligent prescription
        # IMPORTANT: We include ALL historical sets, even from current workout.
        # The prescription service filters to only use COMPLETED exercises,
        # so in-progress sets will be ignored automatically.
        all_sets = [e for e in events if isinstance(e, Set)]
        all_feedback = [e for e in events if isinstance(e, ExerciseCompleted)]

        # Use prescription service to calculate adjusted prescriptions
        # Excludes current workout completions to keep prescriptions stable
        exercises_planned = get_prescriptions_for_workout(
            workout_exercises=baseline_prescriptions,
            all_sets=all_sets,
            all_feedback=all_feedback,
            current_week_idx=week_idx,
            current_workout_idx=workout_idx,
            strategy=feedback_based_progression,
        )

        # Build exercise info with logged sets
        exercise_infos = []
        for exercise_name, prescriptions in exercises_planned.items():
            # Get state for this exercise
            session = ExerciseSession(
                exercise_name=exercise_name,
                week_index=week_idx,
                workout_index=workout_idx,
                events=events,
            )

            # Convert sets to API format
            logged_sets_info = [
                LoggedSetInfo(reps=s.reps, weight=s.weight)
                for s in session.sets
            ]

            # Convert Prescription objects to dicts for API
            prescription_dicts = [
                {
                    "prescribed_reps": p.prescribed_reps,
                    "prescribed_weight": p.prescribed_weight,
                }
                for p in prescriptions
            ]

            exercise_infos.append(
                ExerciseInfo(
                    name=exercise_name,
                    prescribed_sets=prescription_dicts,
                    logged_sets=logged_sets_info,
                    is_started=session.is_started,
                    is_completed=session.is_completed,
                )
            )
        return CurrentWorkoutResponse(
            week_index=week_idx,
            workout_index=workout_idx,
            exercises=exercise_infos,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/log-set", response_model=ApiResponse)
async def log_set_endpoint(request: LogSetRequest):
    """Log a set for an exercise."""
    events = load_events(EVENTS_PATH)
    template = load_template(TEMPLATE_PATH)

    result = log_set(
        events, template, request.exercise, request.reps, request.weight
    )

    if is_successful(result):
        append_events(EVENTS_PATH, result.unwrap())

        return ApiResponse(success=True, message=result.unwrap())
    else:
        return ApiResponse(success=False, error=str(result.failure()))


@app.post("/api/complete-exercise", response_model=ApiResponse)
async def complete_exercise(request: ExerciseFeedbackRequest):
    """Mark an exercise as completed with feedback."""

    feedback = MappingProxyType(
        {
            "joint_pain": request.joint_pain,
            "pump": request.pump,
            "workload": request.workload,
        }
    )

    result = logging_service.complete_exercise(request.exercise, feedback)

    if is_successful(result):
        return ApiResponse(success=True, message=result.unwrap())
    else:
        return ApiResponse(success=False, error=str(result.failure()))


@app.post("/api/complete-workout", response_model=ApiResponse)
async def complete_workout():
    """Mark the current workout as completed."""
    result = logging_service.complete_workout()

    if is_successful(result):
        return ApiResponse(success=True, message=result.unwrap())
    else:
        return ApiResponse(success=False, error=str(result.failure()))


@app.get("/api/history")
async def get_history():
    """Get workout history (all logged events)."""
    events = load_events(EVENTS_PATH)
    return {"events": [e.model_dump() for e in events]}


@app.get("/api/template")
async def get_template():
    """Get the current workout template."""
    try:
        template = logging_service.template

        # Convert to serializable format
        workouts = []
        for workout in template.workouts:
            exercises = []
            for exercise in workout.exercises:
                exercises.append(
                    {
                        "name": exercise.name,
                        "sets": len(exercise.sets) if exercise.sets else 0,
                    }
                )
            workouts.append({"exercises": exercises, "index": workout.index})

        return {"name": template.name, "workouts": workouts}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    rich.print(
        "⚠️  Please use 'python run_server.py' from project root instead"
    )
    rich.print("   or: uv run python run_server.py")
    sys.exit(1)
