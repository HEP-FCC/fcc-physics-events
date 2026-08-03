#!/usr/bin/env python3
"""Shared helpers for the Rucio -> fcc-physics-events pipeline.

Exists because token reading, session construction and NDJSON streaming were
duplicated verbatim across three scripts. Duplicated code drifts: a retry
policy fixed in one fetcher and not the others is a silent inconsistency, and
the token-source change requested for the backend integration would otherwise
need three edits.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_CONFIG = Path(__file__).with_name("rucio_pipeline.json")


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

def _strip_comments(obj: Any) -> Any:
    """Recursively drop keys beginning with '_'.

    JSON has no comment syntax. Underscore keys let the config file carry the
    reasoning for each value (which matters far more than the values, since a
    physicist editing 'stage_tokens' needs to know where the vocabulary comes
    from) without those strings reaching any consumer.
    """
    if isinstance(obj, dict):
        return {k: _strip_comments(v) for k, v in obj.items()
                if not k.startswith("_")}
    if isinstance(obj, list):
        return [_strip_comments(v) for v in obj]
    return obj


def load_config(path: Path | None = None) -> dict:
    """Load and validate the pipeline configuration."""
    path = path or DEFAULT_CONFIG
    if not path.exists():
        die(f"Config not found: {path}\n"
            f"Pass --config, or place rucio_pipeline.json beside the scripts.")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"Config {path} is not valid JSON: {e}")

    cfg = _strip_comments(raw)

    # Fail loudly at startup rather than with a KeyError 40 minutes into a
    # 900-dataset fetch. Cheap check, expensive omission.
    for section in ("rucio", "vocabulary", "layouts", "granularity", "output"):
        if section not in cfg:
            die(f"Config {path} is missing required section '{section}'")

    mode = cfg["granularity"].get("mode")
    if mode not in ("did", "process"):
        die(f"granularity.mode must be 'did' or 'process', got {mode!r}")

    return cfg


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------

def read_token(cfg: dict) -> str:
    """Resolve the Rucio auth token: environment variable first, then file.

    Environment first is deliberate: in the fcc-physics-events backend the
    token comes from application config held in app state, not from a file
    under /tmp. Reading the env var first means the same code path works
    unmodified in both places; the file is the interactive lxplus fallback.

    NOTE (unresolved): Rucio auth tokens expire. Whatever holds this value in
    the backend needs a refresh path on 401, not a read-once-at-startup global.
    
    """
    rc = cfg["rucio"]

    env_name = rc.get("token_env")
    if env_name:
        tok = os.environ.get(env_name, "").strip()
        if tok:
            return tok

    token_file = rc.get("token_file")
    if token_file:
        p = Path(token_file)
        if p.exists():
            tok = p.read_text(encoding="utf-8").strip()
            if tok:
                return tok

    die(f"No Rucio token. Set ${env_name} or write one to {token_file}.")
    return ""  # unreachable; keeps type checkers quiet


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def create_session(cfg: dict) -> requests.Session:
    """Session with urllib3-level retry on transient failures.

    POST is in allowed_methods because every POST this pipeline issues
    (bulkmeta, bulkfiles, replicas/list) is a read-only listing despite the
    verb, so replaying one is idempotent. Do not extend this to a Rucio
    endpoint that mutates state.
    """
    rc = cfg["rucio"]
    session = requests.Session()
    retries = Retry(
        total=rc.get("http_retries", 5),
        backoff_factor=rc.get("http_backoff_factor", 1.0),
        status_forcelist=rc.get("retry_status", [429, 500, 502, 503, 504]),
        allowed_methods=["GET", "POST"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries,
                                          pool_connections=5, pool_maxsize=10))
    session.headers.update({
        "X-Rucio-Auth-Token": read_token(cfg),
        "Accept": "application/x-json-stream",
    })
    return session


def stream_json(response: requests.Response) -> Iterator[Any]:
    """Yield records from either an x-json-stream body or a plain JSON array.

    Rucio is inconsistent about which it returns depending on endpoint and
    deployment, so both are handled. raise_for_status() before reading: a 2xx
    check here also passes the 201 that bulkfiles returns.
    """
    response.raise_for_status()
    if "json-stream" in response.headers.get("Content-Type", ""):
        for line in response.iter_lines():
            if line:
                yield json.loads(line.decode("utf-8"))
    else:
        data = response.json()
        if isinstance(data, list):
            yield from data
        else:
            yield data


def list_scopes(session: requests.Session, cfg: dict) -> list[str]:
    """Every scope the token can see, via GET /scopes/.

    Verified against rucio/rucio master, lib/rucio/web/rest/flaskapi/v1/
    scopes.py: the blueprint registers url_prefix='/scopes' with a GET on '/',
    and the handler returns jsonify(list_scopes(...)) -- a flat JSON array of
    scope-name strings.

    IMPORTANT: that handler is wrapped in
    @check_accept_header_wrapper_flask(['application/json']), so it accepts
    ONLY application/json. The session-wide
    'Accept: application/x-json-stream' used by every other endpoint here
    would make this return 406 Not Acceptable, hence the per-request override
    below. Do not remove it.
    """
    url = f"{cfg['rucio']['host']}/scopes/"
    resp = session.get(url, headers={"Accept": "application/json"})
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        die(f"Unexpected /scopes/ response type {type(data).__name__}; "
            f"expected a JSON array of scope names.")
    return sorted(str(s) for s in data)


def resolve_scopes(session: requests.Session, cfg: dict, args) -> list[str]:
    """Turn --scope / --all-scopes / --scope-regex into a concrete scope list.

    Kept separate from list_scopes() so the network call only happens when
    discovery is actually requested: passing explicit --scope values must not
    require the /scopes/ endpoint to be reachable or permitted.
    """
    if args.scope:
        return list(dict.fromkeys(args.scope))   # de-dup, preserve order

    scopes = list_scopes(session, cfg)
    print(f"Discovered {len(scopes)} scope(s): {scopes}", file=sys.stderr)

    pattern = args.scope_regex or cfg["rucio"].get("scope_regex")
    if pattern:
        rx = re.compile(pattern)
        kept = [s for s in scopes if rx.search(s)]
        skipped = [s for s in scopes if s not in kept]
        print(f"Filter {pattern!r} kept {len(kept)}, skipped {len(skipped)}: "
              f"{skipped}", file=sys.stderr)
        scopes = kept

    if not scopes:
        die("No scopes left after filtering. Check --scope-regex.")
    return scopes


def add_common_args(ap) -> None:
    """CLI flags shared by every stage."""
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                    help=f"pipeline config JSON (default: {DEFAULT_CONFIG.name})")
    ap.add_argument("--scope", action="append", default=[],
                    help="Rucio scope, repeatable (--scope winter2023 --scope "
                         "spring2021). Omit entirely to use --all-scopes.")
    ap.add_argument("--all-scopes", action="store_true",
                    help="discover every scope via GET /scopes/ and process "
                         "each one. Mutually exclusive with --scope.")
    ap.add_argument("--scope-regex", default=None,
                    help="regex filter applied to discovered scopes, e.g. "
                         r"'^(winter|spring|summer)\d{4}$' to exclude user.* "
                         "and mock scopes. Only meaningful with --all-scopes.")
    ap.add_argument("--workdir", type=Path, default=Path.cwd(),
                    help="directory for intermediate NDJSON (default: cwd)")


def validate_scope_args(args) -> None:
    """Reject the ambiguous combinations up front."""
    if args.scope and args.all_scopes:
        die("--scope and --all-scopes are mutually exclusive.")
    if not args.scope and not args.all_scopes:
        die("Specify at least one --scope, or --all-scopes to discover them. "
            "Run discover_scopes.py first if you want to see the list before "
            "committing to a full run.")
