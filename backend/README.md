# AquaSculptor — Backend

Python + FastAPI, port 8100.

## Run

```bash
pip install -r requirements.txt
python main.py
```

Server starts on http://localhost:8100 (docs at /docs).

## Test

```bash
python -m pytest tests/ -q
```

## Endpoints

- `GET /api/health` — liveness + version
- `POST /api/brief/validate` — validate a design brief against `schemas/design-brief.schema.json`
- `GET /api/brief/example` — example brief (PLAN.md §3)
- `POST /api/project/save` — save project JSON to `data/projects/`
- `GET /api/project/list` — list saved projects
- `GET /api/project/{name}` — load a project
- `POST /api/geometry/generate` — run the `open_ring` generator on a design brief, returns mesh + engineering quantities
- `POST /api/engineering/run` — full deterministic loop: brief → sculpture + basin geometry → hydraulics → cost tree (one JSON)
- `POST /api/deliverables/package` — same run, returned as a ZIP (STL, GLB, PDF report, XLSX BOM, brief, SHA-256 manifest)
