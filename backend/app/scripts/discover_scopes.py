#!/usr/bin/env python3
"""Discover every Rucio scope the token can see, with an optional DID census.

Usage:
    export RUCIO_AUTH_TOKEN="$(cat /tmp/rucio_oauth.token)"

    python3 discover_scopes.py                    # just list scope names
    python3 discover_scopes.py --count            # + DID counts per scope
    python3 discover_scopes.py --count --regex '^(winter|spring|summer)\\d{4}$'

Run this BEFORE a full harvest. Listing scopes is one cheap request; counting
DIDs walks every scope and is the expensive part, so it is opt-in.

Endpoint provenance (rucio/rucio master,
lib/rucio/web/rest/flaskapi/v1/scopes.py): the blueprint is registered with
url_prefix='/scopes' and a GET on '/', whose handler returns a flat JSON array
of scope-name strings. The handler is decorated with
check_accept_header_wrapper_flask(['application/json']), so it will answer 406
to the 'application/x-json-stream' Accept header the rest of this pipeline
uses. rucio_common.list_scopes overrides the header for exactly that reason.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

import requests

from rucio_common import (DEFAULT_CONFIG, create_session, die, list_scopes,
                          load_config, stream_json)


def count_dids(session, cfg: dict, scope: str, did_type: str) -> int | None:
    """Number of DIDs of one type in a scope, or None if the query failed.

    Returns None rather than 0 on error: a scope that could not be queried and
    a scope that is genuinely empty are different facts, and collapsing them
    would silently hide a permissions problem.

    Uses long=false so the server returns bare names instead of full metadata
    dicts -- roughly an order of magnitude less data for a count.
    """
    host = cfg["rucio"]["host"]
    url = (f"{host}/dids/{urllib.parse.quote(scope, safe='')}/dids/search"
           f"?type={urllib.parse.quote(did_type, safe='')}&long=false")
    try:
        n = 0
        with session.get(url, stream=True) as r:
            for _ in stream_json(r):
                n += 1
        return n
    except requests.exceptions.RequestException as e:
        print(f"  ! {scope}/{did_type}: {type(e).__name__}: {e}",
              file=sys.stderr)
        return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--regex", default=None,
                    help="filter scope names, e.g. "
                         r"'^(winter|spring|summer)\d{4}$'")
    ap.add_argument("--count", action="store_true",
                    help="also count DIDs per scope (slow: walks every scope)")
    ap.add_argument("--types", nargs="*", default=None,
                    help="DID types to count (default: rucio.did_types)")
    ap.add_argument("--json-out", type=Path, default=None,
                    help="write the census to this JSON file")
    args = ap.parse_args()

    cfg = load_config(args.config)
    session = create_session(cfg)

    scopes = list_scopes(session, cfg)
    print(f"{len(scopes)} scope(s) visible to this token:\n", file=sys.stderr)

    if args.regex:
        rx = re.compile(args.regex)
        matched = [s for s in scopes if rx.search(s)]
        for s in scopes:
            print(f"  {'KEEP' if s in matched else 'skip'}  {s}",
                  file=sys.stderr)
        scopes = matched
        print(f"\n{len(scopes)} scope(s) matched {args.regex!r}\n",
              file=sys.stderr)
    else:
        for s in scopes:
            print(f"  {s}", file=sys.stderr)
        print(file=sys.stderr)

    census: dict = {"scopes": scopes}

    if args.count:
        did_types = ([t.upper() for t in args.types] if args.types
                     else cfg["rucio"]["did_types"])
        counts: dict[str, dict] = {}
        width = max((len(s) for s in scopes), default=10)

        header = f"{'scope':<{width}}  " + "  ".join(
            f"{t:>10}" for t in did_types)
        print(header, file=sys.stderr)
        print("-" * len(header), file=sys.stderr)

        for scope in scopes:
            row = {t: count_dids(session, cfg, scope, t) for t in did_types}
            counts[scope] = row
            cells = "  ".join(
                f"{('ERR' if row[t] is None else row[t]):>10}"
                for t in did_types)
            print(f"{scope:<{width}}  {cells}", file=sys.stderr)

        census["counts"] = counts

        # A scope with containers/datasets but zero files, or one that errored
        # on every type, is worth knowing about before a multi-hour harvest.
        empty = [s for s, r in counts.items()
                 if all(v in (0, None) for v in r.values())]
        if empty:
            print(f"\nNOTE: {len(empty)} scope(s) returned no DIDs or errored "
                  f"on every type: {empty}", file=sys.stderr)

    if args.json_out:
        args.json_out.write_text(json.dumps(census, indent=2), encoding="utf-8")
        print(f"\nWrote census: {args.json_out}", file=sys.stderr)

    # Scope names to stdout, one per line, so this composes with a shell loop:
    #   for s in $(python3 discover_scopes.py --regex '...'); do ... done
    for s in scopes:
        print(s)

    return 0


if __name__ == "__main__":
    sys.exit(main())