# API Documentation

The backend API is versioned under `/api/v1` by default. Interactive API documentation is provided by FastAPI at `/docs` while the service is running.

| Area | Intended responsibility |
| --- | --- |
| Health | Service readiness and liveness |
| GPS | Ingest and retrieve location updates |
| Bus | List and retrieve bus details |
| ETA | Estimate arrival at a stop |
| Deviation | Compare a bus position with its route |

Endpoint request and response schemas will be documented alongside their implementations.