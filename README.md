# Multi-Container Docker Compose Lab

A Flask API backed by Postgres (data) and Redis (cache) — three services,
one `docker compose` command.

## Run it

```bash
docker compose up --build
```

This builds the `app` image and starts all three containers, networked
together automatically. First boot can take ~10-20s while Postgres
initializes.

Visit:
- http://localhost:5000/              -> service overview
- http://localhost:5000/health        -> health check
- http://localhost:5000/visits        -> GET: list saved visits (empty at first)
- http://localhost:5000/cache-demo    -> increments a Redis counter each hit

Add a visit:
```bash
curl -X POST http://localhost:5000/visits \
  -H "Content-Type: application/json" \
  -d '{"note": "hello from curl"}'
```

Then GET /visits again and you'll see it persisted.

## Things to try, in order

1. **Watch the services start**
   `docker compose ps` -- see all three containers and their status.

2. **Look at the logs of just one service**
   `docker compose logs -f app`
   `docker compose logs -f db`

3. **Prove the database persists data across restarts**
   - POST a visit, confirm it's there with GET /visits
   - `docker compose down` (stops + removes containers, but NOT volumes)
   - `docker compose up` again
   - GET /visits again -- your data is still there, because of the
     named volume `pgdata`

4. **Now prove volumes are what saved you**
   - `docker compose down -v` (the -v also removes volumes this time)
   - `docker compose up`
   - GET /visits -- empty again. The data lived in the volume, not the container.

5. **See container-to-container networking in action**
   Open a shell inside the app container:
   `docker compose exec app sh`
   Then try:
   `ping db`
   `ping cache`
   Notice you can reach other services *by their service name* --
   Compose sets up a private network and DNS automatically.

6. **Edit code without rebuilding**
   Change the message string in app.py, save, then refresh
   http://localhost:5000/ -- no rebuild needed, because of the bind
   mount (`./app:/app`) in compose.yml mapping your local folder
   straight into the container.

7. **Scale a service**
   `docker compose up --scale app=3`
   (Note: this will fail on the fixed port 5000 -- a great real-world
   lesson in why you need a load balancer or dynamic ports to scale
   a service horizontally. Try removing the `ports:` line first, or
   just observe the error.)

8. **Tear everything down cleanly**
   `docker compose down -v`

## What each part of compose.yml is doing

- `build: ./app`      -- builds an image from app/Dockerfile instead of pulling one
- `image: postgres:16-alpine` / `redis:7-alpine` -- pulls prebuilt official images
- `depends_on` with `condition: service_healthy` -- app waits for Postgres
  to actually be ready to accept connections, not just "started"
- `healthcheck`        -- defines how Compose checks if Postgres is ready
- `volumes:` (top-level) -- declares named volumes for persistent data
- `./app:/app` bind mount -- live-syncs your local code into the container
