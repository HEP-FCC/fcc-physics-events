# Rucio → fcc-physics-events ingestion pipeline

## Step 0: find out what scopes exist

```bash
export RUCIO_AUTH_TOKEN="$(cat /tmp/rucio_oauth.token)"

python3 discover_scopes.py                 # list every visible scope
python3 discover_scopes.py --count         # + DID census per scope (slow)
```

Run this first. Nothing else knows the scope names until you do.

## Step 1-4: harvest

```bash
# all scopes, auto-discovered
python3 fetch_rucio.py         --all-scopes
python3 fetch_relationships.py --all-scopes
python3 join_enrich.py         --all-scopes
python3 convert_rucio.py --scope winter2023 --scope spring2021 \
        --granularity process --out ./out

# or explicit, repeatable
python3 fetch_rucio.py --scope winter2023 --scope spring2021
```

Filter noise scopes (`user.*`, `mock`, `tests`) with `--scope-regex`:

```bash
python3 fetch_rucio.py --all-scopes --scope-regex '^(winter|spring|summer)\d{4}$'
```

Every intermediate file is named `<scope>_*.ndjson`, so scopes never collide
and a failed scope is re-runnable alone. A scope that errors is reported and
skipped; the run continues.

## Configuration

All vocabulary, endpoints and layout rules live in `rucio_pipeline.json`.
Nothing is hardcoded in Python — not the host, token path, scope, batch sizes,
stage tokens, extensions, detector aliases, or path layouts.

## Open design questions

1. **Layout A names cannot be matched to the website.** The site keys entities
   on the canonical process name (`wzp6_ee_ww_4q_Vcb_Vcb_ecm163`). Layout C
   DIDs carry that form; Layout A DIDs (`91.19gev/ee_Zbb/idea/delphes/...`)
   carry no generator and no `ecm` token, so they cannot be joined to existing
   entities. Is there an EventProducer manifest mapping job IDs to canonical
   names?
2. **The harvester's job is probably enrichment, not import.** Existing site
   entities already have `n-events` and cross-sections from EventProducer.
   Rucio uniquely knows `replicas` / `replica_count` / `rse_names`. Confirm the
   goal is attaching replica location to existing entities.
3. **Entity granularity.** `granularity.mode` — `did` vs `process`. The upsert
   UUID is `uuid5(name + navigation FK ids)`, so switching after a production
   import orphans every row. Decide before the first import.
4. **Token lifetime.** Rucio tokens expire; a value read once into an
   application global goes stale. The backend needs a refresh path on 401.
