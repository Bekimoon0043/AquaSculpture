"""SculptFlow Studio backend — FastAPI entry point (port 8100)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config  # noqa: F401 — loads .env before anything reads os.environ
from api.routes import ai, brief, copilot, deliverables, engineering, geometry, health, integration, learning as learning_route, optimize as optimize_route, project, review as review_route

app = FastAPI(title="SculptFlow Studio API", version="0.1.0")

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8100)
