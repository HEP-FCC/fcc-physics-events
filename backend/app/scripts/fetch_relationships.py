#!/usr/bin/env python3
"""Stage 2: map child FILEs to their parent DATASET via /dids/bulkfiles.

Usage:
    python3 fetch_relationships.py --scope winter2023

CHANGES vs the previous version
-------------------------------
1. Host, token source, batch size and retry policy come from config.
2. The parent DID type is configurable (--parent-type) rather than a module
   constant. It still defaults to DATASET: bulkfiles on a CONTAINER triggers
   recursive expansion that this deployment does not survive, which is
   independent evidence for the "containers can't carry this" observation.
3. Shared session/streaming code moved to rucio_common.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from tqdm import tqdm

from rucio_common import (add_common_args, create_session, die, load_config,
                          resolve_scopes, stream_json, validate_scope_args)

# Resolved once at runtime. The published Rucio spec sends a bare array to
# /dids/bulkfiles; some deployments expect {"dids": [...]}. Probing once and
# caching beats hardcoding either and beats probing on every batch.
_WRAP: bool | None = None


def list_parents(session, cfg: dict, scope: str, did_type: str) -> list[str]:
    host = cfg["rucio"]["host"]
    url = (f"{host}/dids/{urllib.parse.quote(scope, safe='')}/dids/search"
           f"?type={urllib.parse.quote(did_type, safe='')}&long=false")
    retries = cfg["rucio"].get("http_retries", 5)

    for attempt in range(retries):
        try:
            names: list[str] = []
            with session.get(url, stream=True) as r:
                for item in stream_json(r):
                    n = item if isinstance(item, str) else (
                        item.get("name") if isinstance(item, dict) else None)
                    if n:
                        names.append(n)
            return sorted(set(names))
        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt
            print(f"list {did_type} failed ({e}); retry in {wait}s",
                  file=sys.stderr)
            time.sleep(wait)

    die(f"Could not list {did_type}")
    return []


def post_bulkfiles(session, cfg: dict, scope: str,
                   parent_names: list[str]) -> list[dict]:
    global _WRAP
    url = f"{cfg['rucio']['host']}/dids/bulkfiles"
    dids = [{"scope": scope, "name": n} for n in parent_names]

    def send(payload):
        with session.post(url, json=payload, stream=True) as r:
            if r.status_code == 400:
                return None            # wrong body shape for this deployment
            return list(stream_json(r))

    for wrap in ([_WRAP] if _WRAP is not None else [False, True]):
        out = send({"dids": dids} if wrap else dids)
        if out is not None:
            _WRAP = wrap
            return out
    raise RuntimeError("bulkfiles rejected both bare and wrapped bodies (400)")


def load_done(done_file: Path) -> set[str]:
    if not done_file.exists():
        return set()
    return {ln.strip() for ln in done_file.read_text(encoding="utf-8").splitlines()
            if ln.strip()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(ap)
    ap.add_argument("--parent-type", default="DATASET",
                    help="collection DID type to expand (default: DATASET). "
                         "CONTAINER is accepted but this deployment has been "
                         "observed to fail on recursive container expansion.")
    args = ap.parse_args()

    cfg = load_config(args.config)
    validate_scope_args(args)
    args.workdir.mkdir(parents=True, exist_ok=True)

    session = create_session(cfg)
    scopes = resolve_scopes(session, cfg, args)

    failures = []
    for scope in scopes:
        try:
            map_scope(session, cfg, scope, args)
        except Exception as e:
            print(f"\nFAILED {scope}: {type(e).__name__}: {e}", file=sys.stderr)
            failures.append((scope, str(e)))

    if failures:
        print(f"\n{len(failures)} scope(s) failed:", file=sys.stderr)
        for scope, err in failures:
            print(f"  {scope}: {err}", file=sys.stderr)
        return 1
    return 0


def map_scope(session, cfg: dict, scope: str, args) -> None:
    """Map every parent DID in one scope to its child files."""
    batch_size = cfg["rucio"].get("relationship_batch_size", 150)
    pause = cfg["rucio"].get("sleep_between_batches", 0.1)

    edges_file = args.workdir / f"{scope}_edges.ndjson"
    # Checkpoint at PARENT granularity: one parent's file list arrives as a
    # contiguous block, so "this parent is fully written" is the only resume
    # unit that cannot tear a record set in half.
    done_file = args.workdir / f"{scope}_edges.done"

    print(f"\n{'=' * 60}\nMapping {scope}\n{'=' * 60}", file=sys.stderr)

    all_parents = list_parents(session, cfg, scope, args.parent_type)
    done = load_done(done_file)
    remaining = [p for p in all_parents if p not in done]

    print(f"{len(all_parents)} {args.parent_type}s total, {len(done)} mapped, "
          f"{len(remaining)} to do", file=sys.stderr)
    if not remaining:
        print("Nothing to map.", file=sys.stderr)
        return

    with edges_file.open("a", encoding="utf-8") as edges, \
         done_file.open("a", encoding="utf-8") as done_f, \
         tqdm(total=len(remaining), unit=" parent") as bar:

        for start in range(0, len(remaining), batch_size):
            batch = remaining[start:start + batch_size]

            for attempt in range(3):
                try:
                    rows = post_bulkfiles(session, cfg, scope, batch)
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == 2:
                        print(f"\nBatch @{start} failed: {e}", file=sys.stderr)
                        raise
                    time.sleep(2 ** attempt)

            for row in rows:
                edges.write(json.dumps(row, ensure_ascii=False) + "\n")
            edges.flush()

            # Checkpoint AFTER the edges are flushed, never before. A crash in
            # between re-fetches this batch on resume, producing duplicate
            # edges -- which is why join_enrich dedups on (parent, child). The
            # reverse ordering would lose edges silently, which is worse.
            for n in batch:
                done_f.write(n + "\n")
            done_f.flush()

            bar.update(len(batch))
            time.sleep(pause)

    print(f"Saved edges: {edges_file}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
