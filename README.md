# SkyCompare - flight aggregator prototype

Searches **100 mock flight providers** (each with its own response schema) in parallel, normalises
everything into one canonical schema, then tags the **Cheapest**, **Fastest** and **Recommended** flights.

- **Backend:** Django 6 + Django REST Framework (`/backend`)
- **Frontend:** React + TypeScript + Tailwind CSS, built with Vite (`/frontend`)

```
React (Vercel) --GET /api/search--> Django API (Render)
                                      |-- cache hit? return
                                      |-- ThreadPoolExecutor: 100 provider.fetch() in parallel, 1.5s deadline
                                      |-- adapter registry: 7 schema adapters -> canonical Flight
                                      |-- ranking: score + cheapest/fastest/recommended tags
                                      '-- cache result, return {query, meta, flights}
```

Interview prep: [docs/SkyCompare-Project-Guide.pdf](docs/SkyCompare-Project-Guide.pdf) (how it works, CV bullets, 40 Q&A).

## Run locally

Two terminals.

**Backend** (Python 3.12+)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py runserver      # http://localhost:8000
```

**Frontend** (Node 20+)
```bash
cd frontend
npm install
npm run start                   # http://localhost:5173  (proxies /api to :8000)
```

Open http://localhost:5173. A default JFK to LHR search runs on load.

## Tests
```bash
cd backend && pytest
```

## API
`GET /api/search/?origin=JFK&destination=LHR&date=2026-10-15`

```jsonc
{
  "query": { "origin": "JFK", "destination": "LHR", "date": "2026-10-15" },
  "meta":  { "total_flights": 277, "providers_total": 100, "providers_ok": 95, "providers_failed": 5,
             "failures": [{ "provider_id": "provider_072", "reason": "timeout" }],
             "cached": false, "took_ms": 1534 },
  "flights": [{ "id": "...", "provider_id": "provider_048", "airline": "Qatar Airways", "flight_number": "QR363",
                "origin": "JFK", "destination": "LHR",
                "departure_time": "2026-10-15T08:45-04:00", "arrival_time": "2026-10-15T20:46+01:00",
                "duration_minutes": 421, "stops": 0, "price_usd": 393.4, "currency": "GBP",
                "score": 87.2, "tags": ["recommended"] }]
}
```
Also: `GET /api/airports/`, `GET /api/health/`.

Five providers misbehave on purpose (3 return errors, 2 hang), so every search shows graceful
degradation: 95 of 100 providers succeed. Set `MOCK_CHAOS_ENABLED=0` to turn that off.

## Configuration (environment variables, backend)

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_DEBUG` | `1` | set `0` in production |
| `DJANGO_SECRET_KEY` | dev key | required when `DJANGO_DEBUG=0` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Render's hostname is added automatically |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | comma-separated frontend origins |
| `PROVIDER_TIMEOUT_SECONDS` | `1.5` | overall deadline for the provider fan-out |
| `SEARCH_CACHE_TTL` / `SEARCH_CACHE_TTL_PARTIAL` | `300` / `60` | cache seconds (full / partial results) |
| `SEARCH_RATE_LIMIT` | `60/min` | per-IP throttle |
| `MOCK_CHAOS_ENABLED` | `1` | make 5 mock providers fail/hang |

Frontend: `VITE_API_URL` (empty in dev; the Render URL in production).

## Deploy (free tier)

**1. Push to GitHub.**

**2. Backend on Render**
- New > Blueprint > pick the repo. Render reads `render.yaml`.
- After the first deploy, set `CORS_ALLOWED_ORIGINS` to your Vercel URL (no trailing slash) and redeploy.
- Check `https://<your-service>.onrender.com/api/health/`.
- Free services sleep after ~15 min idle; the first request then takes up to a minute.
  The UI shows a "server is waking up" message. An uptime ping (e.g. UptimeRobot on `/api/health/`) keeps it warm.
- If Render rejects `PYTHON_VERSION`, use any 3.12+ version it lists (Django 6 needs Python 3.12+).

**3. Frontend on Vercel**
- New Project > pick the repo > **Root Directory: `frontend`** (framework preset: Vite).
- Environment variable: `VITE_API_URL=https://<your-service>.onrender.com`
- Deploy.

## Project layout
```
backend/
  config/                 settings, urls, wsgi
  flights/
    domain.py             canonical Flight + query/result types
    reference.py          airports, airlines, FX rates
    adapters/             BaseAdapter, registry, 7 schema adapters
    providers/            mock generator: itineraries, per-schema renderers, 100 providers
    services/             aggregator (fan-out, cache), ranking (score + tags)
    serializers.py views.py urls.py
    tests/
frontend/src/
  components/             SearchForm, HighlightBadges, FlightCard, ResultsList, FilterSidebar, States
  hooks/useFlightSearch.ts  api.ts  types.ts  lib/format.ts
```
