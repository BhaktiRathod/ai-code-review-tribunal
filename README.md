# AI Code Review Tribunal — v0.6 (CrewAI Edition)

Review Python/Java demo ZIPs using four specialist **CrewAI agents**, a **Chief Judge** and an optional independent evidence recheck. **React/Vite** provides the v0.5 Tribunal Studio dashboard; **FastAPI** handles uploads, progress and exports; **Gemini** powers the agent reasoning.

## What changed

- Replaced LangGraph with the real `crewai` framework (`Agent`, `Task`, `Crew`, `Process.sequential`, `LLM`).
- Four specialised roles: Requirements, Code, README and Evaluation. Task outputs are structured Pydantic models; the Chief Judge receives the specialist outputs as CrewAI task context.
- The Chief Judge chooses supported candidate findings and can initiate an independent CrewAI recheck when necessary.
- The established frontend API, progress states, ZIP validation, findings UI, review comparison and PDF/HTML/Markdown exports remain supported.
- Review stages advance upon actual CrewAI task completion, sequentially. This version does **not** claim parallel specialist execution.

## Requirements

Python **3.11–3.13** (use 3.11 or 3.12 for best library compatibility), Node.js 20+, npm and a Gemini API key for live reviews. Install dependencies in a fresh virtual environment; older LangGraph environments must not be reused without reinstalling.

## Run on Ubuntu

**Terminal 1 — backend** (starting from the extracted `ai-code-review-tribunal` folder):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`, then set `GEMINI_API_KEY` to your real secret. The defaults use `GEMINI_MODEL=gemini-2.5-flash`. Start the API:

```bash
uvicorn main:app --reload --port 8000
```

**Terminal 2 — frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`; confirm API health at `http://localhost:8000/api/health`. Stop any older backend running on port 8000 before starting this version.

## Usage

1. Upload a ZIP containing the application source, configuration, README and (optionally) specification files.
2. Enter CTKS/learning objectives and evaluation criteria in the requirements field.
3. Select **Live AI tribunal** for actual CrewAI + Gemini analysis; **Sample demonstration** runs deterministic examples without calling an LLM.
4. Monitor file intake and CrewAI task progress: Requirements → Code → README → Evaluation → Chief Judge → optional Evidence Recheck → Report.
5. Inspect evidence-backed findings, verification checks and the final verdict. Download PDF, HTML or Markdown. To compare reviews, upload an updated ZIP in the same browser tab.

### API endpoints

- `GET /api/health`
- `POST /api/reviews` (multipart `project`, `specification`, `mode`)
- `GET /api/reviews/{review_id}` (job stages, findings, review result)
- `GET /api/reviews/{review_id}/export/pdf|html|md`

## Architecture

```text
frontend/src/             React dashboard, components and styles
backend/main.py           FastAPI, job progress, exports
backend/engine.py         CrewAI agents/tasks, Judge, conditional evidence recheck
backend/file_reader.py    Archive filtering and bounded context
backend/reporting.py      PDF, HTML and Markdown output
samples/sample-demo.zip   Deterministic no-key example
```

## Validation

```bash
python3 -m compileall -q backend
cd frontend && npm install && npm run build
```

Test sample mode, then live mode with a harmless ZIP and a deliberately empty `docker-compose.yml`. Confirm the Chief Judge identifies the defect, the README is detected and each export contains consistent findings. If CrewAI cannot parse a model response, the live job fails explicitly rather than silently fabricating a verdict.

## Production precautions

The project performs **static AI-assisted review only**; it never executes uploaded source. Agent conclusions can be wrong and referenced lines do not prove claims. Source content is transmitted to Gemini during live review: do not upload secrets or confidential projects. Never commit `backend/.env`. Public hosting additionally requires authentication, abuse/rate limits, quotas, persistent job state, retention/deletion controls and cost monitoring. In-memory reviews are lost after backend restart. Before deployment, configure `CORS_ORIGINS` on the backend and `VITE_API_URL` on the frontend. Backend: Render root `backend`, build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`. Frontend: Vercel root `frontend`, output `dist`.

### Framework documentation

- https://docs.crewai.com/
- https://ai.google.dev/gemini-api/docs/crewai-example


## Visual analytics edition (v0.7)

The refreshed React UI includes a blue/violet gradient, improved contrast, review-specific verification donut, and agent-duration bar chart. All charts use the completed API review response: no artificial scoring. The backend continues to use the CrewAI edition and exports PDF, HTML and Markdown.

- Start the API with `uvicorn main:app --reload --port 8000` from `backend` (activate your Python virtual environment and configure `GEMINI_API_KEY`).
- From `frontend`, run `npm install`, `npm run dev`, then browse `http://localhost:5173`.
- Before deployment run `npm run build` and test sample and live review modes plus exports.
- The analytics charts appear once a review completes; initial and upload states deliberately show no invented statistics.

## v0.8 — Consolidated verification and accessible motion

- Specialist checks addressing the same requirement **and source file** are consolidated in `backend/checks.py`. The original individual agent assessments remain visible in an expandable evidence panel.
- When agent assessments disagree, the consolidated check is marked **Needs verification** and flagged as disputed; it is not silently passed or failed.
- **Static Pass** means the AI's source-level assessment only. It does **not** mean project code was executed or runtime behaviour was verified.
- Filter checks by Static Pass, Fail or Needs verification. Charts and PDF/HTML/Markdown reports use the same consolidated backend results.
- Motion shows new results, progress transitions, active agent pulses, hover affordances and evidence disclosure. CSS respects the `prefers-reduced-motion` accessibility preference.
- The original CrewAI + Gemini integration and upload/report endpoints remain unchanged.

### Smoke test for v0.8

1. Start backend and frontend as documented above. Confirm `crewai[google-genai]` is installed and the Gemini key exists only in `backend/.env`.
2. Upload the Sprint 6 demo ZIP with an intentionally empty `docker-compose.yml` and run **Live AI tribunal**.
3. Confirm duplicate Prometheus checks appear once per requirement/source file, with the contributing agents listed.
4. Expand a check and inspect each agent's evidence. Confirm checks are labelled **Static Pass**, not runtime success.
5. Confirm the Chief Judge identifies the empty Compose file, and that PDF/HTML/Markdown exports have the same consolidated checks.
6. Run `npm run build` from `frontend` before deployment. Uploaded code is never executed.
