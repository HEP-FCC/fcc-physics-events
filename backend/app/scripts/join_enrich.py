#!/usr/bin/env python3
"""Stage 3: join DATASET metadata with aggregated child-FILE statistics.

Usage:
    python3 join_enrich.py --scope winter2023

CHANGES vs the previous version
-------------------------------
1. Aggregates are null when NO child supplied a value, instead of 0. Summing
   991 nulls previously produced total_events=0, which the website then
   displays as a dataset containing zero events -- indistinguishable from a
   genuinely empty sample, and enough to make a physicist filter out 800 GB of
   valid data. "Unknown" and "zero" are different facts.
2. consistency.bytes_match is tri-state (true / false / null) rather than a
   boolean. The old expression returned False whenever the dataset's own bytes
   were null, i.e. on every record, reporting "mismatch" for what is actually
   "nothing to compare against".
3. Replica fields harvested in Stage 1 are carried through explicitly.
4. --workdir and config support; no hardcoded paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rucio_common import (add_common_args, create_session, die, load_config,
                          resolve_scopes, validate_scope_args)


def load_datasets(datasets_file: Path) -> dict[str, dict]:
    if not datasets_file.exists():
        die(f"Missing {datasets_file} (run fetch_rucio.py first)")
    out: dict[str, dict] = {}
    with datasets_file.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            n = row.get("name")
            if n:
                out[n] = row
    return out


def aggregate_edges(edges_file: Path):
    """Single streaming pass over the edge list.

    Dedup key is the (parent, child) PAIR, not the child alone: a file
    legitimately belonging to two datasets must be counted once per parent.
    Deduping on child alone would undercount; not deduping at all would
    double-count the batches replayed after a crash resume.

    Complexity: O(E) time over E edges, O(E) space for the seen-set. The
    seen-set is the memory ceiling here -- for a scope with tens of millions of
    edges this needs replacing with a sort-merge or an on-disk key store.
    Trade-off accepted at winter2023's scale (~1e6 edges); revisit before
    running a campaign an order of magnitude larger.
    """
    agg: dict[str, dict] = {}
    seen: set[tuple] = set()
    missing_parent = 0

    if not edges_file.exists():
        die(f"Missing {edges_file} (run fetch_relationships.py first)")

    with edges_file.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            parent, child = row.get("parent_name"), row.get("name")
            if not parent:
                missing_parent += 1
                continue

            key = (parent, child)
            if key in seen:
                continue
            seen.add(key)

            slot = agg.setdefault(parent, {
                "files": 0,
                # bytes/events start as None and only become numeric once a
                # non-null child value is seen. This is what keeps "no child
                # reported events" distinct from "children reported 0 events".
                "bytes": None, "events": None,
                "null_bytes": 0, "null_events": 0,
                "sample": None,
            })
            slot["files"] += 1

            # min() rather than first-seen: deterministic across resumed or
            # reordered edge fetches, so the derived navigation fields do not
            # change between runs (which would change the upsert UUID).
            if child and (slot["sample"] is None or child < slot["sample"]):
                slot["sample"] = child

            for src, dst, nullc in (("bytes", "bytes", "null_bytes"),
                                    ("events", "events", "null_events")):
                v = row.get(src)
                if v is None:
                    slot[nullc] += 1
                else:
                    slot[dst] = v if slot[dst] is None else slot[dst] + v

    return agg, missing_parent


def bytes_match(own, aggregated) -> bool | None:
    """Tri-state comparison. None means 'no basis for comparison'."""
    if own is None or aggregated is None:
        return None
    return own == aggregated


def build_record(name: str, meta: dict | None, a: dict | None,
                 scope: str) -> dict:
    files = a["files"] if a else 0
    record = dict(meta) if meta else {"name": name, "metadata_present": False}
    record.setdefault("scope", scope)

    record["sample_child_name"] = a["sample"] if a else None
    record["child_aggregates"] = {
        "file_count": files,
        # None, not 0, when nothing was ever summed.
        "total_bytes": a["bytes"] if a else None,
        "total_events": a["events"] if a else None,
        "files_with_null_bytes": a["null_bytes"] if a else 0,
        "files_with_null_events": a["null_events"] if a else 0,
    }

    own_bytes = (meta or {}).get("bytes")
    agg_bytes = record["child_aggregates"]["total_bytes"]
    # Debug/validation only. convert_rucio.py strips this block; it must never
    # reach the website's metadata JSONB.
    record["consistency"] = {
        "dataset_own_bytes": own_bytes,
        "dataset_own_length": (meta or {}).get("length"),
        "aggregated_bytes": agg_bytes,
        "aggregated_file_count": files,
        "bytes_match": bytes_match(own_bytes, agg_bytes),
    }
    record["parent_container"] = None   # dataset -> container not yet fetched
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    validate_scope_args(args)

    # Scope discovery needs a session; explicit --scope values do not. Only
    # pay for the connection when discovery is actually requested.
    if args.all_scopes:
        with create_session(cfg) as session:
            scopes = resolve_scopes(session, cfg, args)
    else:
        scopes = list(dict.fromkeys(args.scope))

    rc = 0
    for scope in scopes:
        try:
            enrich_scope(scope, args.workdir)
        except SystemExit:
            # die() inside a single scope must not kill the whole run.
            print(f"SKIPPED {scope}: missing input files", file=sys.stderr)
            rc = 1
    return rc


def enrich_scope(scope: str, wd) -> None:
    datasets_file = wd / f"{scope}_datasets_with_metadata.ndjson"
    edges_file = wd / f"{scope}_edges.ndjson"
    out_file = wd / f"{scope}_datasets_enriched.ndjson"

    print(f"\n{'=' * 60}\nEnriching {scope}\n{'=' * 60}", file=sys.stderr)

    datasets = load_datasets(datasets_file)
    agg, missing_parent = aggregate_edges(edges_file)

    known, seen_parents = set(datasets), set(agg)
    orphan_parents = seen_parents - known    # in edges, no metadata row
    childless = known - seen_parents         # metadata row, no files

    with out_file.open("w", encoding="utf-8") as out:
        for name, meta in datasets.items():
            out.write(json.dumps(build_record(name, meta, agg.get(name), scope),
                                 ensure_ascii=False) + "\n")
        # Emit orphans too, so nothing is silently dropped between stages.
        for name in sorted(orphan_parents):
            out.write(json.dumps(build_record(name, None, agg[name], scope),
                                 ensure_ascii=False) + "\n")

    for label, val in (("Datasets with metadata", len(datasets)),
                       ("Datasets with >=1 file", len(seen_parents & known)),
                       ("Childless datasets", len(childless)),
                       ("Orphan parents (no metadata)", len(orphan_parents)),
                       ("Edges missing parent_name", missing_parent)):
        print(f"{label:<30}: {val}", file=sys.stderr)
    print(f"Wrote: {out_file}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
