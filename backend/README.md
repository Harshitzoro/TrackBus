# TrackBus Backend

FastAPI service for health checks, GPS ingestion, bus data, ETA, and route deviation.

## Local development

```bash
python -m venv .venv
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Copy the root or backend `.env.example` to `.env` and provide Firebase settings when configuring persistence. Never commit credentials.