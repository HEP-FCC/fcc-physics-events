#!/usr/bin/env python3
"""Stage 1: fetch DID metadata and replica information for a Rucio scope.

Usage:
    export RUCIO_AUTH_TOKEN="$(cat /tmp/rucio_oauth.token)"
    python3 fetch_rucio.py --scope winter2023
    python3 fetch_rucio.py --scope winter2023 --types DATASET

CHANGES vs the previous version
-------------------------------
1. Replicas are now fetched for the DID types listed in
   rucio.replica_did_types (default: DATASET), not hardcoded to FILE. This is
   the specific change requested: replicas / replica_count / rse_names are
   wanted at dataset level, and the old `if did_type == "FILE"` guard meant
   /replicas/list was never called for a DATASET at all.
2. rse_names is extracted as a first-class sorted list. It was previously
   buried inside the discarded all_replica_metadata blob.
3. Absent replica information is written as null, not as 0. The website's
   import layer drops nulls (_filter_empty_metadata_values) but happily stores
   a fabricated 0, which renders as "this dataset has no replicas" and is
   indistinguishable from a real zero.
4. Replica fetch uses POST /replicas/datasets_bulk, which returns one small
   row per (dataset, RSE) with byte/length/state summaries -- NOT
   /replicas/list, which expands every dataset into all of its child files
   and made the first version hang for minutes per batch.
5. Scope, host, token source, batch sizes and DID types all come from config
   or CLI.
6. NEW: optional per-dataset sample PFNs and parent containers, gated by
   rucio.fetch_sample_pfns / rucio.fetch_parents in the config.

   sample_pfns uses POST /replicas/list with nrandom (verified against
   rucio/rucio master, lib/rucio/web/rest/flaskapi/v1/replicas.py: 'nrandom:
   The maximum number of replicas to return'). nrandom bounds the response to
   N child files, which is what makes /replicas/list safe to reintroduce
   after it was removed for expanding whole collections. A /replicas/list row
   carries the FILE's own scope/name and nothing identifying the requested
   collection, so attribution forces ONE DATASET PER REQUEST -- this is a
   correctness constraint, not a style choice. Do not "optimise" it back
   into multi-dataset batches.

   parent_containers uses GET /dids/{scope}/{name}/parents (verified against
   lib/rucio/web/rest/flaskapi/v1/dids.py, class Parents, route
   '/<path:scope_name>/parents'), one GET per DID, name fully URL-quoted
   including slashes, matching the official client's quote_plus behaviour.

   COST: both features together add ~2 requests per DATASET (~1,900 for
   winter2023, roughly 2-4 minutes). Fine at 1e3 datasets; at 1e4+ move PFN
   sampling back to a post-join stage keyed on sample_child_name, which
   needs ~N/200 requests instead of N.

   RESUME CAVEAT: rows already present in the output NDJSON are skipped by
   the resume logic and will NOT gain the new fields. Delete the per-scope
   output file (or use a fresh --workdir) when enabling these flags on a
   previously-harvested scope.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from tqdm import tqdm

from rucio_common import (add_common_args, create_session, die, load_config,
                          resolve_scopes, stream_json, validate_scope_args)


def list_dids(session, cfg: dict, scope: str, did_type: str) -> list[str]:
    """Enumerate every DID name of one type in the scope."""
    host = cfg["rucio"]["host"]
    url = (f"{host}/dids/{urllib.parse.quote(scope, safe='')}/dids/search"
           f"?type={urllib.parse.quote(did_type, safe='')}&long=false")

    max_retries = cfg["rucio"].get("http_retries", 5)
    for attempt in range(max_retries):
        names: list[str] = []
        print(f"\nSearching {did_type} DIDs (attempt {attempt + 1}/{max_retries})",
              file=sys.stderr)
        try:
            with session.get(url, stream=True) as resp:
                for item in tqdm(stream_json(resp),
                                 desc=f"Finding {did_type}", unit=" did"):
                    name = item if isinstance(item, str) else (
                        item.get("name") if isinstance(item, dict) else None)
                    if name:
                        names.append(name)
            # sorted(set(...)) gives a deterministic order, which is what makes
            # the resume logic below correct across runs.
            return sorted(set(names))
        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt
            print(f"\n{type(e).__name__}: {e}. Retrying in {wait}s...",
                  file=sys.stderr)
            time.sleep(wait)

    die(f"Failed to list {did_type} after {max_retries} attempts.")
    return []


def fetch_metadata_batch(session, cfg, scope: str, names: list[str]) -> list[dict]:
    url = f"{cfg['rucio']['host']}/dids/bulkmeta"
    payload = {"dids": [{"scope": scope, "name": n} for n in names],
               "inherit": True, "plugin": "ALL"}
    with session.post(url, json=payload, stream=True) as resp:
        return list(stream_json(resp))


def fetch_dataset_replicas_bulk(session, cfg, scope: str,
                                names: list[str]) -> list[dict]:
    """POST /replicas/datasets_bulk -- dataset-LEVEL replica summary.

    Verified against rucio/rucio master, lib/rucio/web/rest/flaskapi/v1/
    replicas.py (DatasetReplicasBulk, route '/datasets_bulk'): returns one row
    per (dataset, RSE) with rse / bytes / length / available_bytes /
    available_length / state, WITHOUT expanding the dataset into its files.

    This replaces the earlier use of POST /replicas/list, which resolves every
    collection into its constituent FILEs server-side: a batch of 100 datasets
    at ~1000 files each meant a ~100k-row response with PFN URLs, materialised
    in memory -- the observed multi-minute hang at 0%. datasets_bulk returns
    ~1-2 small rows per dataset instead, so the whole scope costs seconds.

    Each returned row carries the dataset's own scope/name, so attribution is
    direct; no 'parents' resolution needed.
    """
    url = f"{cfg['rucio']['host']}/replicas/datasets_bulk"
    payload = {"dids": [{"scope": scope, "name": n} for n in names]}
    with session.post(url, json=payload, stream=True) as resp:
        return list(stream_json(resp))


def summarise_dataset_replicas(rows: list[dict]) -> dict[str, dict]:
    """Group datasets_bulk rows by dataset name.

    Returns {name: {"rse_names": [...], "replica_count": int,
                    "replicas": {rse: {...}},
                    "unavailable_rse_names": [...]}}.

    STATE FILTERING (verified against rucio/rucio master,
    lib/rucio/db/sqla/constants.py, class ReplicaState):
        AVAILABLE, UNAVAILABLE, COPYING, BEING_DELETED, BAD,
        TEMPORARY_UNAVAILABLE

    Only AVAILABLE means the data can actually be fetched right now. Observed
    in production winter2023 data: datasets_bulk can return
    state="UNAVAILABLE" with bytes=0 and available_bytes=0 for an RSE that is
    registered but holds nothing retrievable. Counting that row into
    replica_count / rse_names would tell a physicist "this data lives at
    INFN_CNAF_DISK" when it does not -- worse than the earlier null-vs-0 bug,
    because it is not just missing information, it is an active wrong claim
    about where the data is.

    replica_count / rse_names now report ONLY available replicas.
    unavailable_rse_names preserves the rest (still worth knowing -- it means
    the data existed and something happened to it) without it appearing
    interchangeable with a live copy. The full per-RSE detail, including
    state, stays in 'replicas' for anyone who wants to see everything.

    O(R) time and space over R returned rows.
    """
    by_name: dict[str, dict] = {}
    for row in rows:
        name, rse = row.get("name"), row.get("rse")
        if not name or not rse:
            continue
        slot = by_name.setdefault(name, {})
        slot[rse] = {
            "state": row.get("state"),
            "bytes": row.get("bytes"),
            "length": row.get("length"),
            "available_bytes": row.get("available_bytes"),
            "available_length": row.get("available_length"),
        }

    result = {}
    for name, rses in by_name.items():
        available = sorted(r for r, info in rses.items()
                           if info.get("state") == "AVAILABLE")
        unavailable = sorted(r for r in rses if r not in available)
        result[name] = {
            "rse_names": available,
            "replica_count": len(available),
            "unavailable_rse_names": unavailable or None,
            "replicas": rses,   # full detail, all states, for anyone who needs it
        }
    return result


def iter_file_replicas(session, cfg, scope: str, name: str,
                       nrandom: int | None):
    """Yield one normalised row per CHILD FILE of one collection DID.

    nrandom=None means NO SAMPLING: every child file is returned. That is the
    full expansion that made the original /replicas/list use hang, so this
    function is a GENERATOR and the caller streams it straight to disk --
    nothing accumulates a 194k-row list in memory. Pass an int to bound it.

    Each yielded row:
        lfn      "<scope>:<name>" -- the LFN, which in Rucio IS the scope:name
                 pair (verified: lib/rucio/web/rest/flaskapi/v1/rses.py,
                 LFNS2PFNS parses its input with lfn.split(':', 1) into
                 {'scope','name'}). There is no separate LFN attribute to
                 fetch; it is composed, not looked up.
        scope, name, bytes, md5, adler32
        rses     {rse: [pfn, ...]}
        states   {rse: state} when the deployment reports per-RSE states

    all_states=True: an UNAVAILABLE replica's PFN is still provenance ("the
    data lived here"). Dataset-level availability truth stays in rse_names /
    unavailable_rse_names from datasets_bulk; filtering here would let the
    two disagree.
    """
    url = f"{cfg['rucio']['host']}/replicas/list"
    payload: dict = {"dids": [{"scope": scope, "name": name}],
                     "all_states": True}
    if nrandom is not None:
        payload["nrandom"] = nrandom

    with session.post(url, json=payload, stream=True) as resp:
        for row in stream_json(resp):
            fscope, fname = row.get("scope"), row.get("name")
            if not fname:
                continue

            rses = row.get("rses")
            if not isinstance(rses, dict):
                # Fallback shape: 'pfns' dict keyed by PFN carrying per-PFN
                # info including the owning RSE.
                rses = {}
                for pfn, info in (row.get("pfns") or {}).items():
                    rse = (info or {}).get("rse")
                    if rse:
                        rses.setdefault(rse, []).append(pfn)

            states = {}
            for pfn, info in (row.get("pfns") or {}).items():
                rse, st = (info or {}).get("rse"), (info or {}).get("state")
                if rse and st:
                    states[rse] = st

            yield {
                "lfn": f"{fscope}:{fname}",
                "scope": fscope,
                "name": fname,
                "parent_scope": scope,
                "parent_name": name,
                "bytes": row.get("bytes"),
                "md5": row.get("md5"),
                "adler32": row.get("adler32"),
                "rses": {r: sorted(set(p or [])) for r, p in rses.items()},
                "states": states or None,
            }


def fetch_parents(session, cfg, scope: str, name: str) -> list | None:
    """Parent DIDs of one dataset via GET /dids/{scope}/{name}/parents.

    Returns a sorted list of {"scope","name","type"} rows. [] is a fact
    ("top-level DID, no parent container") and is kept distinct from None,
    which callers use for "request failed / not attempted". The DID name is
    quoted with safe='' so embedded slashes become %2F, matching the
    official Rucio client's quote_plus() treatment of names on this route.
    """
    host = cfg["rucio"]["host"]
    url = (f"{host}/dids/{urllib.parse.quote(scope, safe='')}/"
           f"{urllib.parse.quote(name, safe='')}/parents")
    rows = []
    with session.get(url, stream=True) as resp:
        if resp.status_code == 404:      # DID vanished between list and fetch
            return None
        for row in stream_json(resp):
            rows.append({"scope": row.get("scope"),
                         "name": row.get("name"),
                         "type": row.get("type")})
    return sorted(rows, key=lambda r: (r["name"] or ""))


_RULE_FIELDS = ("id", "state", "rse_expression", "account", "copies",
                "locks_ok_cnt", "locks_replicating_cnt", "locks_stuck_cnt",
                "expires_at", "created_at")


def fetch_rules(session, cfg, scope: str, name: str) -> list | None:
    """Replication rules on one DID.

    ROUTE (verified against rucio/rucio master): GET
    /dids/{scope}/{name}/rules -- dids.py, class Rules (line ~1915),
    registered at '/<path:scope_name>/rules'. NOT /rules/{scope}/{name}:
    the rules blueprint only serves /{rule_id} and /. (That wrong URL was
    produced by an LLM tool; kept here as a reminder to verify routes
    against source, whatever generated them.)

    Rows are trimmed to _RULE_FIELDS: the full rule dict carries ~30 keys of
    scheduler internals that would bloat the metadata JSONB for no display
    value. [] means "queried, no rules" -- meaningfully different from None
    ("query failed"), same tri-state convention as parent_containers.
    """
    host = cfg["rucio"]["host"]
    url = (f"{host}/dids/{urllib.parse.quote(scope, safe='')}/"
           f"{urllib.parse.quote(name, safe='')}/rules")
    rows = []
    with session.get(url, stream=True) as resp:
        if resp.status_code == 404:
            return []                     # no rules for this DID
        for row in stream_json(resp):
            rows.append({k: row.get(k) for k in _RULE_FIELDS})
    return sorted(rows, key=lambda r: (r.get("id") or ""))


def fetch_parent_rules(session, cfg, parents: list | None,
                       cache: dict) -> list | None:
    """Rules inherited from parent containers, cached per parent DID.

    Observed in this deployment: the dataset
    'IDEA/p8_ee_WW_mumu_ecm240/' carries no direct rule while its container
    'IDEA/p8_ee_WW_mumu_ecm240' (no trailing slash) does. A dataset showing
    replication_rules=[] with no parent check would therefore misread as
    "nothing manages this data". Each entry is tagged with the parent DID it
    came from so the provenance is explicit.

    The cache matters: containers are shared across few datasets here
    (~1:1), but in a scope where one container holds many datasets this
    collapses N rule queries into one per container.
    """
    if not parents:
        return [] if parents == [] else None
    out = []
    for p in parents:
        key = f"{p.get('scope')}:{p.get('name')}"
        if key not in cache:
            try:
                cache[key] = fetch_rules(session, cfg,
                                         p.get("scope"), p.get("name"))
            except requests.exceptions.RequestException:
                cache[key] = None
        rules = cache[key]
        if rules:
            for r in rules:
                out.append({"parent_did": key, **r})
        elif rules is None:
            return None                   # a parent query failed: unknown
    return out


def output_filename(workdir: Path, scope: str, did_type: str) -> Path:
    return workdir / f"{scope}_{did_type.lower()}s_with_metadata.ndjson"


def completed_dids(outfile: Path) -> set[str]:
    """Names already written, for crash resume."""
    done: set[str] = set()
    if not outfile.exists():
        return done
    with outfile.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue          # truncated final line from a killed run
            if "name" in row:
                done.add(row["name"])
    return done


def process_type(session, cfg: dict, scope: str, did_type: str,
                 workdir: Path) -> None:
    rc = cfg["rucio"]
    want_replicas = did_type in rc.get("replica_did_types", ["DATASET"])
    # Per-DID enrichment only makes sense where replicas do (DATASET level);
    # gating on want_replicas keeps FILE/CONTAINER passes cheap.
    want_pfns = want_replicas and rc.get("fetch_sample_pfns", False)
    want_parents = want_replicas and rc.get("fetch_parents", False)
    # Rules inheritance needs the parents; force-fetch them when rules are on.
    want_rules = want_replicas and rc.get("fetch_rules", False)
    want_parents = want_parents or want_rules
    parent_rule_cache: dict = {}
    # null / 0 / absent => no sampling, every child file is fetched.
    nrandom = rc.get("pfn_sample_count") or None
    # One file instead of two: per-file replica rows are nested under the
    # dataset as "file_replicas" rather than streamed to a side file.
    # Memory stays bounded because accumulation is PER DATASET (~200 rows),
    # never the whole 194k-row scope. "file_replicas" is deliberately absent
    # from output.metadata_whitelist, so convert_rucio.py still drops it and
    # the website receives only pfn_file_count / pfn_prefixes.
    embed_files = rc.get("embed_file_replicas", True)
    # null / 0 => no batching: send every DID in one request and let the
    # server decide what it can return. Falls back to 500 only if the key
    # is absent entirely. If this 413s or times out, set an integer.
    meta_batch = rc.get("metadata_batch_size", 500) or None
    pause = rc.get("sleep_between_batches", 0.1)

    outfile = output_filename(workdir, scope, did_type)
    print(f"\n{'=' * 60}\n{did_type} (scope={scope}, replicas="
          f"{'yes' if want_replicas else 'no'})\n{'=' * 60}", file=sys.stderr)

    all_dids = list_dids(session, cfg, scope, did_type)
    done = completed_dids(outfile)
    if done:
        print(f"Resume: {len(done)} already fetched", file=sys.stderr)
    remaining = [d for d in all_dids if d not in done]
    if not remaining:
        print("Nothing to fetch.", file=sys.stderr)
        return

    unattributed = 0
    pfn_failures = 0
    parent_failures = 0
    rule_failures = 0

    # Per-file replica rows go to their own NDJSON, never into the dataset
    # row. At winter2023 scale that is ~194k rows / hundreds of MB; it is
    # harvest output for whoever needs file-level detail, not website
    # metadata. Opened unconditionally (cheap) so the `with` block stays flat.
    replica_file = workdir / f"{scope}_{did_type.lower()}_file_replicas.ndjson"

    with outfile.open("a", encoding="utf-8") as out, \
         (contextlib.nullcontext(None) if embed_files
          else replica_file.open("a", encoding="utf-8")) as replica_out, \
         tqdm(total=len(remaining), desc=f"Fetching {did_type}", unit=" did") as bar:

        step = meta_batch or len(remaining)
        for start in range(0, len(remaining), step):
            batch = remaining[start:start + step]

            for attempt in range(3):
                try:
                    meta_rows = fetch_metadata_batch(session, cfg, scope, batch)
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == 2:
                        print(f"\nFatal on metadata batch @{start}: {e}",
                              file=sys.stderr)
                        raise
                    time.sleep(2 ** attempt)

            replica_summary: dict[str, dict] = {}
            replica_query_ok = False
            if want_replicas:
                for attempt in range(3):
                    try:
                        rows = fetch_dataset_replicas_bulk(
                            session, cfg, scope, batch)
                        replica_summary = summarise_dataset_replicas(rows)
                        replica_query_ok = True
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt == 2:
                            # Non-fatal: metadata is still worth keeping. The
                            # affected DIDs get null replica fields (honest),
                            # not 0 (fabricated).
                            print(f"\ndatasets_bulk failed for batch @{start} "
                                  f"({e}); continuing without replicas",
                                  file=sys.stderr)
                            break
                        time.sleep(2 ** attempt)
                unattributed += len([n for n in batch
                                     if n not in replica_summary
                                     and n.rstrip("/") not in replica_summary])

            for row in meta_rows:
                name = row.get("name")
                summary = replica_summary.get(name)
                if summary is None and name:
                    summary = replica_summary.get(name.rstrip("/")) \
                        or replica_summary.get(f"{name}/")

                if summary:
                    row["rse_names"] = summary["rse_names"]
                    row["replica_count"] = summary["replica_count"]
                    row["unavailable_rse_names"] = summary.get("unavailable_rse_names")
                    row["replicas"] = summary["replicas"]
                    row["replica_query_status"] = "ok"
                elif want_replicas and replica_query_ok:
                    # datasets_bulk answered for this batch and returned no
                    # row for this DID (trailing-slash variants already
                    # checked above): Rucio holds NO dataset-replica entry.
                    # That is a known zero, not an unknown -- the case the
                    # old null-only convention could not express. The status
                    # field is what makes storing 0 honest: a consumer can
                    # tell "ok, 0" from "failed, null".
                    row["rse_names"] = []
                    row["replica_count"] = 0
                    row["unavailable_rse_names"] = None
                    row["replicas"] = None
                    row["replica_query_status"] = "ok"
                elif want_replicas:
                    # Query failed after retries: unknown, so null, never 0.
                    row["rse_names"] = None
                    row["replica_count"] = None
                    row["unavailable_rse_names"] = None
                    row["replicas"] = None
                    row["replica_query_status"] = "failed"
                else:
                    row["rse_names"] = None
                    row["replica_count"] = None
                    row["unavailable_rse_names"] = None
                    row["replicas"] = None
                    row["replica_query_status"] = "not_applicable"

                # Per-DID enrichment. Failures are isolated per DID and per
                # feature: a broken /parents route must not cost the PFNs,
                # and neither must cost the metadata row itself.
                if want_pfns and name:
                    try:
                        # Stream per-file rows straight to the side file. The
                        # dataset row keeps only a bounded rollup: embedding
                        # ~200 files x N PFNs per dataset would produce a
                        # metadata JSONB blob the website cannot usefully
                        # index or display, and would defeat the whitelist's
                        # whole purpose.
                        n_files, prefixes = 0, {}
                        embedded: list = []
                        for frow in iter_file_replicas(
                                session, cfg, scope, name, nrandom):
                            if embed_files:
                                # parent_scope/parent_name are the enclosing
                                # dataset's own scope/name once nested, so drop
                                # them: ~19 MB of pure redundancy at scope scale.
                                frow.pop("parent_scope", None)
                                frow.pop("parent_name", None)
                                embedded.append(frow)
                            else:
                                replica_out.write(
                                    json.dumps(frow, ensure_ascii=False) + "\n")
                            n_files += 1
                            for rse, pfns in frow["rses"].items():
                                if pfns and rse not in prefixes:
                                    # Directory part of the first PFN seen at
                                    # this RSE. Truncating at the last '/' is
                                    # a display convenience only; it is NOT a
                                    # reconstructable path rule, because
                                    # non-deterministic RSEs may place files
                                    # from one dataset under different paths.
                                    prefixes[rse] = pfns[0].rsplit("/", 1)[0]
                        if embed_files:
                            row["file_replicas"] = embedded or None
                        else:
                            replica_out.flush()
                        row["pfn_file_count"] = n_files
                        row["pfn_prefixes"] = prefixes or None
                    except requests.exceptions.RequestException:
                        pfn_failures += 1
                        row["file_replicas"] = None
                        row["pfn_file_count"] = None
                        row["pfn_prefixes"] = None
                elif want_pfns:
                    row["file_replicas"] = None
                    row["pfn_file_count"] = None
                    row["pfn_prefixes"] = None

                if want_parents and name:
                    try:
                        row["parent_containers"] = fetch_parents(
                            session, cfg, scope, name)
                    except requests.exceptions.RequestException:
                        parent_failures += 1
                        row["parent_containers"] = None
                elif want_parents:
                    row["parent_containers"] = None

                if want_rules and name:
                    try:
                        row["replication_rules"] = fetch_rules(
                            session, cfg, scope, name)
                    except requests.exceptions.RequestException:
                        rule_failures += 1
                        row["replication_rules"] = None
                    row["parent_rules"] = fetch_parent_rules(
                        session, cfg, row.get("parent_containers"),
                        parent_rule_cache)
                elif want_rules:
                    row["replication_rules"] = None
                    row["parent_rules"] = None

                out.write(json.dumps(row, ensure_ascii=False) + "\n")

            out.flush()
            bar.update(len(batch))
            time.sleep(pause)

    if pfn_failures or parent_failures or rule_failures:
        print(f"NOTE: per-DID enrichment failures -- sample_pfns: "
              f"{pfn_failures}, parent_containers: {parent_failures}, "
              f"replication_rules: {rule_failures}. Those "
              f"rows carry null for the affected field only.", file=sys.stderr)

    if want_replicas and unattributed:
        print(f"NOTE: {unattributed}/{len(remaining)} {did_type}s returned no "
              f"row from /replicas/datasets_bulk. For those, Rucio holds no "
              f"dataset-replica entry (or the name spelling differs by a "
              f"trailing slash). They carry null replica fields, not 0.",
              file=sys.stderr)

    print(f"Saved: {outfile}", file=sys.stderr)
    if want_pfns and not embed_files:
        print(f"Saved per-file replicas (LFN + PFNs): {replica_file}",
              file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(ap)
    ap.add_argument("--types", nargs="*", default=None,
                    help="DID types to fetch (default: rucio.did_types from config)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    validate_scope_args(args)
    did_types = ([t.upper() for t in args.types] if args.types
                 else cfg["rucio"]["did_types"])
    args.workdir.mkdir(parents=True, exist_ok=True)

    failures: list[tuple[str, str, str]] = []
    with create_session(cfg) as session:
        scopes = resolve_scopes(session, cfg, args)
        for scope in scopes:
            for did_type in did_types:
                try:
                    process_type(session, cfg, scope, did_type, args.workdir)
                except Exception as e:
                    # One bad scope must not abandon the rest of a multi-scope
                    # run. Record and continue: output files are per-scope, so
                    # a failed scope is re-runnable on its own afterwards.
                    print(f"\nFAILED {scope}/{did_type}: "
                          f"{type(e).__name__}: {e}", file=sys.stderr)
                    failures.append((scope, did_type, str(e)))

    if failures:
        print(f"\n{len(failures)} scope/type combination(s) failed:",
              file=sys.stderr)
        for scope, did_type, err in failures:
            print(f"  {scope}/{did_type}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
