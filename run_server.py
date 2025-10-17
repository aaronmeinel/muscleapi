#!/usr/bin/env python3
"""Development server runner for MuscleAPI backend."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn  # noqa

    # Run the FastAPI app
    uvicorn.run(
        "web.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root / "src"), str(project_root / "web/api")],
    )
