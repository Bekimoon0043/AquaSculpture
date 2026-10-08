"""AquaSculptor backend — FastAPI entry point (port 8100)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config  # noqa: F401 — loads .env before anything reads os.environ
from api.routes import ai, brief, concepts as concepts_route, copilot, deliverables, engineering, geometry, health, integration, learning as learning_route, optimize as optimize_route, project, review as review_route

app = FastAPI(title="AquaSculptor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(brief.router, prefix="/api")
app.include_router(project.router, prefix="/api")
app.include_router(geometry.router, prefix="/api")
app.include_router(engineering.router, prefix="/api")
app.include_router(deliverables.router, prefix="/api")
app.include_router(integration.router, prefix="/api")
app.include_router(copilot.router, prefix="/api")
app.include_router(optimize_route.router, prefix="/api")
app.include_router(review_route.router, prefix="/api")
app.include_router(learning_route.router, prefix="/api")
app.include_router(concepts_route.router, prefix="/api")

# Single-process mode: serve the built frontend (frontend/dist) at /.
# `npm run build` in frontend/ -> everything under one port, no dev servers.
from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import FRONTEND_DIST as DIST
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404)
        target = DIST / full_path
        return FileResponse(target if target.is_file() else DIST / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8100)
