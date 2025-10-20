# A simple workout tracker

## MVP
- Log a set
- Create a plan
- See your plans
- See todays workout and your progress (which implicitly tells you what sets are left to do)
- Simple progression -> if last target was met, increase reps or weight by about 2.5%, if target was drastically exceeded (>2 reps +), 5%

## Roadmap
- Predictive analytics (more elaborate progression prediction)
- Adjust plan on the go (differentiate between template and plan?)


# Refactoring Plan: OOP → Pure Functions (SHORT VERSION)

**Goal:** Transform to pure functional architecture with full type safety
**Timeline:** 13-19 hours (2-3 weekends)
**Result:** ~20% less code, >85% coverage, no classes/repositories

---

## Phase 1: Foundation (2-3h)

**Setup types without breaking anything**

1. Create `src/domain/types.py` with TypedDict definitions
2. Convert events to Pydantic models with `type: Literal[...]` and `frozen=True`
3. Move `Set` to `events.py` as `SetLogged`

**Checkpoint:** `pytest tests/` passes

---

## Phase 2: Pure Functions (4-6h)

**Create functional equivalents alongside classes**

### 2.1 Helpers
- Create `src/domain/helpers.py`
- Add `filter_by_context()`, `filter_events_by_type()`
- Write 10-15 tests

### 2.2 Reducers
- Create `src/domain/reducers.py`
- Add `process_exercise_event()`, `process_workout_event()`
- Write 15-20 tests

### 2.3 State Builders
- Create `src/domain/state.py`
- Add `exercise_state()`, `workout_state()`, `can_log_set()`, etc.
- Port all existing ExerciseSession/WorkoutSession tests (20+)

**Checkpoint:** All new tests pass, coverage ≥ baseline

---

## Phase 2.5: Storage (1-2h)

**Replace repositories with pure I/O**

1. Create `src/storage.py`:
```python
from pydantic import TypeAdapter
EventAdapter = TypeAdapter(list[Event])

def load_events(path: Path) -> list[Event]:
    return EventAdapter.validate_python(json.load(path))

def append_events(path: Path, new_events: list[Event]):
    # Load, append, save
```

2. Write 10-12 storage tests (round-trip, validation)
3. Delete `repository.py` and `protocols.py`

**Checkpoint:** Storage tests pass

---

## Phase 3: Service Layer (3-4h)

**Replace service classes with pure functions**

### 3.1 Bridge (Temporary)
- Update ExerciseSession/WorkoutSession to delegate to pure functions
- Existing tests still pass

### 3.2 Pure Services
- Create `src/service/logging.py` with:
  - `log_set(events, template, ...) -> Result[list[Event], str]`
  - `complete_exercise(events, template, ...) -> Result[...str]`
  - `complete_workout(events, template) -> Result[...str]`
- Port all LoggingService tests (30+)
- Add property-based tests with Hypothesis

**Checkpoint:** Service tests pass, coverage increased

---

## Phase 4: API Layer (1-2h)

**Use storage + pure functions directly**
```python
@app.post("/api/log-set")
async def log_set_endpoint(request: LogSetRequest):
    # Load
    events = load_events(EVENTS_PATH)
    template = load_template(TEMPLATE_PATH)
    
    # Process (pure)
    result = log_set(events, template, request.exercise, request.reps, request.weight)
    
    # Save
    if is_successful(result):
        append_events(EVENTS_PATH, result.unwrap())
        return ApiResponse(success=True)
    else:
        return ApiResponse(success=False, error=result.failure())
```

Simplify history endpoint:
```python
@app.get("/api/history")
async def get_history():
    events = load_events(EVENTS_PATH)
    return {"events": [e.model_dump() for e in events]}  # Pydantic auto-serialization
```

**Checkpoint:** API tests pass

---

## Phase 5: Clean Up (2-3h)

1. **Delete old code:**
   - ExerciseSession class
   - WorkoutSession class
   - LoggingService class
   - repository.py
   - protocols.py

2. **Add event validation tests** (8 tests)

3. **Create ARCHITECTURE.md** documenting:
   - Structure
   - Data flow
   - Key patterns
   - Examples

**Checkpoint:** `pytest tests/` and `pyright src/` pass

---

## Phase 6: Type Safety (1h)

1. **Configure pyproject.toml:**
```toml
[tool.pyright]
typeCheckingMode = "basic"
reportUndefinedVariable = "error"

[tool.mypy]
warn_return_any = true
check_untyped_defs = true
```

2. **Run:** `pyright src/` and fix errors

3. **Optional:** Add pre-commit hooks and GitHub Actions CI

**Checkpoint:** Zero type errors

---

## Quick Checklist
```
□ Phase 1: TypedDict + Pydantic events
□ Phase 2.1: Helpers + tests
□ Phase 2.2: Reducers + tests
□ Phase 2.3: State builders + tests
□ Phase 2.5: Storage + delete repos
□ Phase 3.1: Bridge classes
□ Phase 3.2: Pure services + tests
□ Phase 4: Refactor API
□ Phase 5: Delete old code + docs
□ Phase 6: Type checking

Final:
□ pytest tests/ -v (all pass)
□ pyright src/ (zero errors)
□ pytest --cov (>85%)
□ Manual API test
```

---

## Key Patterns

**TypedDict for internal state:**
```python
class ExerciseState(TypedDict):
    started: bool
    completed: bool
    sets: list[SetLogged]
```

**Pydantic for events (boundaries):**
```python
class SetLogged(BaseModel):
    type: Literal["set"] = "set"
    reps: int = Field(gt=0)
    class Config:
        frozen = True
```

**Pure functions:**
```python
def exercise_state(events, exercise, week, workout) -> ExerciseState:
    relevant = filter_by_context(events, exercise, week, workout)
    return reduce(process_exercise_event, relevant, initial_state)
```

**Result types:**
```python
def log_set(...) -> Result[list[Event], str]:
    if invalid:
        return Failure("error message")
    return Success([new_events])
```

---

## Expected Outcome

| Metric | Before | After |
|--------|--------|-------|
| Lines of code | ~720 | ~580 |
| Test count | ~80 | ~130 |
| Coverage | ~81% | ~92% |
| Classes for behavior | 5+ | 0 |
| Repositories | Yes | No |
| Type safety | Partial | Full |

🎉 **Done!**