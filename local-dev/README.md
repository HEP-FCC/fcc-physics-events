# Local development

Runs Postgres in a Podman container; backend and frontend run natively for
fast hot-reload.

## 1. Start Postgres (once; leave it running across sessions)

```bash
podman run -d \
  --name dami-local-db \
  -e POSTGRES_USER=dami_local \
  -e POSTGRES_PASSWORD=dami_local \
  -e POSTGRES_DB=dami_local \
  -p 5432:5432 \
  -v dami-local-db-data:/var/lib/postgresql/data \
  docker.io/library/postgres:17-alpine3.22
```

A named volume (not a host bind mount) is required here -- rootless Podman
can't `chown` a plain host directory to match Postgres's internal container
user, and the container crash-loops on startup if you try.

Stop it later with `podman stop dami-local-db`, restart with `podman start dami-local-db`.
Remove it entirely (including the data) with `podman rm -f dami-local-db && podman volume rm dami-local-db-data`.

## 2. Start the backend

```bash
cp local-dev/backend.env.example local-dev/backend.env
# fill in METADATA_BROWSER_APPLICATION_SECRET_KEY in local-dev/backend.env

cd backend
uv run --env-file ../local-dev/backend.env uvicorn app.main:app --reload --no-access-log
```

## 3. Start the frontend

```bash
cd frontend
yarn dev
```

No env file needed here -- `nuxt.config.ts`'s default `apiBaseUrl`
(`http://localhost:8000`) already matches the backend above.

Open http://localhost:3000.

## Notes

- Quote any env value containing spaces in `local-dev/backend.env`
  (`uv run --env-file` silently stops parsing the rest of the file on an
  unquoted multi-word value, which also makes everything after that line
  fall back to hardcoded config defaults).
- If port 8000 or 3000 is already taken on your machine, run the backend
  with `--port <other>` and the frontend with `yarn dev --port <other>`,
  setting `METADATA_BROWSER_BACKEND_URL=http://localhost:<backend-port>`
  when starting the frontend so it points at the right place.
