# Comments service
## Running
1. Copy `.env.example` to `.env` and fill in the required values.
```bash
cp .env.example .env
```
2. Run docker compose to start the service.
```bash
docker compose up
```

For local development use local docker file:
```bash
docker compose -f compose.local.yaml up
```
And you can run the backend with 
```bash
uv run granian config.asgi:application --interface asgi --host 0.0.0.0 --port 8000
```
And the frontend with
```bash
cd frontend
npm run dev -- --host
```
