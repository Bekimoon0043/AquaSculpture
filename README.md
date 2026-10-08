# SculptFlow Studio

Prompt-to-engineering design software for sculptures and fountains.
See `PLAN.md` for the master plan. Status: Phase 0 skeleton + Phase 1 `open_ring` seed.

## Layout

- `schemas/` — design-brief JSON Schema (the AI ↔ engineering contract)
- `backend/` — Python + FastAPI engine (port 8100)
- `frontend/` — React 18 + Vite + Three.js + Zustand UI (port 5173)
- `desktop/` — Electron shell

## Run the backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

API at http://localhost:8100 — `GET /api/health`, `GET /api/brief/example`,
`POST /api/brief/validate`, `POST /api/geometry/generate`,
`POST /api/engineering/run` (brief → geometry + hydraulics + cost),
`POST /api/deliverables/package` (ZIP with STL/GLB/PDF/XLSX + manifest),
project save/load under `/api/project/`. Interactive docs at `/docs`.

Tests:

```bash
cd backend
python -m pytest tests/ -q
```

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

UI at http://localhost:5173 (start the backend first so Generate works).

Production build: `npm run build` → `frontend/dist/`.

## Desktop (Electron)

```bash
cd desktop
npm install   # skipped in Phase 0 — heavy download
npm start     # dev: loads http://localhost:5173; packaged: loads frontend/dist
```

## Run as a single app (no dev servers)

1. `cd frontend && npm run build` (once, or after UI changes)
2. Double-click **LuxuryForm Studio.bat** — opens http://localhost:8100

The backend serves the built UI + API on one port. Dev mode (hot reload):
backend `python main.py` (:8100), frontend `npm run dev` (:5173).
