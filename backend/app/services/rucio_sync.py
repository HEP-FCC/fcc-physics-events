"""
Rucio synchronization service.

Pulls REPLICA LOCATION ONLY -- dataset-level RSE summaries and, optionally,
child-file PFNs -- from a Rucio server and upserts it into the entities
database by reusing the existing import path (data_import_module.import_data).
No intermediate files, no file watcher.

Deliberately does NOT call /dids/bulkmeta. Physics metadata (events, bytes,
cross-sections) belongs to EventProducer; fetching it here would cost one
extra request per batch to produce fields this service is forbidden to write.
Replica location is the thing Rucio uniquely knows, and it is all this
service carries.

IDENTITY (verified against uuid_utils.generate_entity_uuid and _upsert_entity)
    uuid5(ns, f"{name},{accelerator_id},{campaign_id},{detector_id},"
              f"{file_type_id},{stage_id}")
The entity NAME is part of the key alongside the five navigation ids, so this
service emits process-level names, never DID paths. A DID-shaped name produces
a different UUID and therefore a duplicate row rather than an update.

FIELD OWNERSHIP
Metadata keys use the website's own vocabulary; nothing is namespaced. Because
_merge_metadata_respecting_locks overwrites any key present in the new
payload, the set of keys this service may write is an explicit whitelist in
config (rucio_sync.emit_fields). Default: only what Rucio uniquely knows --
replica location and file counts. Adding 'n-events' or 'size' means Rucio
starts overwriting EventProducer values on every cycle. That is a policy
decision, made in one config line, not an accident.

Per-field locks (__<key>__lock__) set in the UI are honoured by the existing
upsert, so a manually corrected field survives this sync.
"""

import asyncio
import glob
import json
import os
import re
import urllib.parse
from pathlib import Path
from typing import Any

import httpx

from app.storage.database import Database
from app.storage.database_modules.data_import_module import import_data
from app.utils.config_utils import get_config
from app.utils.logging_utils import get_logger

logger = get_logger()


def _as_bool(value: Any, default: bool) -> bool:
    """Coerce a config value to bool, tolerating strings.

    pyhocon returns environment-variable substitutions as STRINGS, so a config
    value overridden by ${?VAR} arrives as "false", and bool("false") is True.
    Passing that straight to bool() means setting the env var to false ENABLES
    the thing it was meant to disable -- a silent, inverted failure.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true", "yes", "on", "1"):
            return True
        if v in ("false", "no", "off", "0"):
            return False
        logger.warning(f"Uninterpretable boolean {value!r}; using {default}")
        return default
    return bool(value)

# Written when nothing is configured. Replica location and PFNs only.
# n-events / size / path are EventProducer's and are never fetched, let alone
# written.
DEFAULT_EMIT_FIELDS = [
    "rucio_datasets",
    "replicas",
    "replica_count",
]


class RucioSyncService:
    """Pull-based Rucio -> PostgreSQL synchronizer."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.config = get_config()
        cfg = self.config.get("rucio_sync", {})

        self.enabled: bool = _as_bool(cfg.get("enabled"), False)
        self.host: str = str(cfg.get("host", "")).rstrip("/")

        self.token_env: str = cfg.get("token_env", "RUCIO_AUTH_TOKEN")
        self.token_file: str | None = cfg.get("token_file", None)
        # Glob for the token the rucio CLI writes after `rucio whoami` + SSO.
        # See _resolve_token for why this is a glob and not a fixed path.
        self.token_glob: str = cfg.get("token_glob", "/tmp/*/.rucio_*/auth_token_*")

        # Matches both the dot form Rucio conventionally uses (user.jsmiesko)
        # and the slash form, since I have not verified which this deployment
        # emits. Check your own /scopes/ output and tighten if you can.
        self.scope_exclude: str | None = cfg.get(
            "scope_exclude_regex", r"^(user|group)[./]")
        self.scope_include: str | None = cfg.get("scope_include_regex", None)

        self.interval_seconds: int = int(cfg.get("interval_seconds", 21600))
        self.batch_size: int = int(cfg.get("batch_size", 100))
        self.request_timeout: float = float(cfg.get("request_timeout", 60.0))

        emit = cfg.get("emit_fields", None)
        self.emit_fields: set[str] = set(emit) if emit else set(DEFAULT_EMIT_FIELDS)

        # Per-campaign navigation vocabulary. Nothing here can be read from a
        # Rucio DID: Rucio knows the path, not which accelerator produced the
        # sample or whether it is generator- or reconstruction-level.
        #
        # A campaign NOT listed here is skipped entirely, not defaulted. These
        # three values feed the entity UUID, so a wrong guess does not produce
        # a visibly wrong field -- it produces a duplicate row alongside the
        # real one, silently. winter2023 happens to be all rec/edm4hep-root,
        # but a campaign mixing generator and reconstruction output would
        # break that assumption, and a global default would hide it.
        self.campaigns: dict[str, dict[str, Any]] = {
            name: dict(vals) for name, vals in (cfg.get("campaigns", {}) or {}).items()
        }
        self.max_path_segments: int = int(cfg.get("max_path_segments", 2))
        self.detector_aliases: dict[str, str] = dict(
            cfg.get("detector_aliases", {"idea": "IDEA"})
        )

        self.is_running = False
        self._token: str | None = None
        self._task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------
    # Lifecycle (mirrors FileWatcherService)
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if not self.enabled:
            logger.info("Rucio sync disabled in configuration")
            return
        if not self.host:
            logger.error("rucio_sync.host not configured; sync not started")
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Rucio sync started (host={self.host}, "
                    f"interval={self.interval_seconds}s, "
                    f"emits={sorted(self.emit_fields)})")

    async def stop(self) -> None:
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Rucio sync stopped")

    async def _loop(self) -> None:
        while self.is_running:
            try:
                await self.sync_once()
            except Exception as e:
                logger.error(f"Rucio sync cycle failed: {e}")
            await asyncio.sleep(self.interval_seconds)

    # ------------------------------------------------------------------
    # Token resolution
    # ------------------------------------------------------------------

    def _resolve_token(self, force_reload: bool = False) -> str:
        """Find a Rucio auth token: env var, explicit file, then CLI glob.

        The CLI path is a glob on purpose. The rucio client writes its token
        under a directory derived from the OS user and RUCIO_ACCOUNT, and the
        exact template varies between client versions; I do not have verified
        data on the layout for your deployment. Confirm yours once with

            find /tmp -name 'auth_token*' -user "$USER" 2>/dev/null

        then pin rucio_sync.token_file to the result so the service is not
        relying on a wildcard.

        Newest match wins: after a re-auth the CLI writes a fresh file, and
        picking a stale one fails the whole cycle on 401.
        """
        if self._token and not force_reload:
            return self._token

        tok = os.environ.get(self.token_env, "").strip()
        if tok:
            self._token = tok
            return tok

        if self.token_file:
            p = Path(self.token_file)
            if p.exists():
                tok = p.read_text(encoding="utf-8").strip()
                if tok:
                    self._token = tok
                    return tok

        for m in sorted(glob.glob(self.token_glob),
                        key=os.path.getmtime, reverse=True):
            try:
                tok = Path(m).read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if tok:
                logger.info(f"Using Rucio token from {m}")
                self._token = tok
                return tok

        raise RuntimeError(
            f"No Rucio token found. Set ${self.token_env}, set "
            f"rucio_sync.token_file, or run `rucio whoami` and complete the "
            f"CERN SSO login so the client writes one "
            f"(searched: {self.token_glob})."
        )

    async def _request(self, client: httpx.AsyncClient, method: str,
                       url: str, **kw: Any) -> httpx.Response:
        """Issue a request, re-reading the token once on 401.

        Rucio tokens expire. A cycle that starts valid can hit 401 partway
        through a large scope; re-reading covers the case where the CLI has
        since refreshed the file. If it is still 401 the message states
        exactly what a human must do, because under interactive SSO no code
        can recover from this on its own.
        """
        headers = {"X-Rucio-Auth-Token": self._resolve_token()}
        headers.update(kw.pop("headers", {}))
        r = await client.request(method, url, headers=headers, **kw)
        if r.status_code == 401:
            logger.warning("Rucio returned 401; re-reading token")
            headers["X-Rucio-Auth-Token"] = self._resolve_token(force_reload=True)
            r = await client.request(method, url, headers=headers, **kw)
            if r.status_code == 401:
                raise RuntimeError(
                    "Rucio token rejected after reload. Run `rucio whoami`, "
                    "complete the CERN SSO login, then re-run the sync."
                )
        r.raise_for_status()
        return r

    async def _stream(self, client: httpx.AsyncClient, method: str,
                      url: str, **kw: Any) -> list[Any]:
        """Same 401 handling, for x-json-stream endpoints."""
        headers = {"X-Rucio-Auth-Token": self._resolve_token(),
                   "Accept": "application/x-json-stream"}
        headers.update(kw.pop("headers", {}))
        for attempt in (0, 1):
            rows: list[Any] = []
            async with client.stream(method, url, headers=headers, **kw) as r:
                if r.status_code == 401 and attempt == 0:
                    await r.aread()
                    logger.warning("Rucio returned 401; re-reading token")
                    headers["X-Rucio-Auth-Token"] = self._resolve_token(
                        force_reload=True)
                    continue
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if line:
                        rows.append(json.loads(line))
            return rows
        raise RuntimeError(
            "Rucio token rejected after reload. Run `rucio whoami`, complete "
            "the CERN SSO login, then re-run the sync."
        )

    # ------------------------------------------------------------------
    # One cycle
    # ------------------------------------------------------------------

    async def sync_once(self, dry_run: bool = False) -> dict[str, Any]:
        stats: dict[str, Any] = {}
        async with httpx.AsyncClient(timeout=self.request_timeout) as client:
            scopes = await self._list_scopes(client)
            kept = self._filter_scopes(scopes)
            logger.info(f"Rucio scopes: {len(scopes)} visible, "
                        f"{len(kept)} kept: {kept}")
            for scope in kept:
                try:
                    stats[scope] = await self._sync_scope(client, scope, dry_run)
                except Exception as e:
                    # Scope isolation: one broken scope must not abort the rest.
                    logger.error(f"Sync failed for scope {scope}: {e}")
                    stats[scope] = {"error": str(e)}
        return stats

    async def _sync_scope(self, client: httpx.AsyncClient, scope: str,
                          dry_run: bool) -> dict[str, int]:
        names = await self._list_datasets(client, scope)
        logger.info(f"{scope}: {len(names)} DATASET DIDs")

        processes: dict[tuple, dict[str, Any]] = {}
        skipped = 0

        for start in range(0, len(names), self.batch_size):
            batch = names[start:start + self.batch_size]

            # Dataset-level replica summary: ONE request per batch.
            repl = self._summarise_replicas(
                await self._dataset_replicas(client, scope, batch))

            for n in batch:
                rec = self._did_to_process(scope, n, repl.get(n, {}))
                if rec is None:
                    skipped += 1
                    continue
                self._collapse(processes, rec)

        payload = {"processes": [self._project(p) for p in processes.values()]}
        result = {"dids": len(names), "processes": len(processes),
                  "unmappable": skipped}

        if dry_run:
            logger.info(f"[dry-run] {scope}: {len(processes)} processes, no writes")
            print(json.dumps(payload, indent=2))
            return result

        if payload["processes"]:
            # Reuse the backend's import path in full: FK get-or-create,
            # deterministic UUID, lock-respecting merge, upsert.
            await import_data(self.database, json.dumps(payload).encode("utf-8"))
        return result

    # ------------------------------------------------------------------
    # Rucio calls
    # ------------------------------------------------------------------

    async def _list_scopes(self, client: httpx.AsyncClient) -> list[str]:
        # /scopes/ answers only Accept: application/json (406 on x-json-stream).
        r = await self._request(client, "GET", f"{self.host}/scopes/",
                                headers={"Accept": "application/json"})
        data = r.json()
        if not isinstance(data, list):
            raise RuntimeError(
                f"/scopes/ returned {type(data).__name__}, expected list")
        return sorted(str(s) for s in data)

    def _filter_scopes(self, scopes: list[str]) -> list[str]:
        kept = scopes
        if self.scope_exclude:
            rx = re.compile(self.scope_exclude)
            kept = [s for s in kept if not rx.search(s)]
        if self.scope_include:
            rx = re.compile(self.scope_include)
            kept = [s for s in kept if rx.search(s)]
        return kept

    async def _list_datasets(self, client: httpx.AsyncClient,
                             scope: str) -> list[str]:
        url = (f"{self.host}/dids/{urllib.parse.quote(scope, safe='')}"
               f"/dids/search?type=DATASET&long=false")
        names: list[str] = []
        for item in await self._stream(client, "GET", url):
            n = item if isinstance(item, str) else (
                item.get("name") if isinstance(item, dict) else None)
            if n:
                names.append(n)
        return sorted(set(names))

    async def _dataset_replicas(self, client: httpx.AsyncClient, scope: str,
                                names: list[str]) -> list[dict[str, Any]]:
        """POST /replicas/datasets_bulk: one row per (dataset, RSE).

        Not /replicas/list: that expands every dataset into its child FILEs
        server-side, which produced the multi-minute hang in the offline
        pipeline. datasets_bulk returns ~1-2 small rows per dataset.
        """
        body = {"dids": [{"scope": scope, "name": n} for n in names]}
        rows = await self._stream(client, "POST",
                                  f"{self.host}/replicas/datasets_bulk", json=body)
        return [r for r in rows if isinstance(r, dict)]

    @staticmethod
    def _summarise_replicas(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Group datasets_bulk rows by dataset, keeping only COMPLETE replicas.

        A replica is complete when the RSE holds every file the dataset has:
        state AVAILABLE and available_length == length, with length > 0.

        Checking availability alone is not enough. Real winter2023 data has
        rows like INFN_BARI_DISK reporting state=AVAILABLE with
        available_length=0 against a dataset of 12 files -- registered at the
        site but holding nothing. Listing that as a replica tells a physicist
        their data is retrievable somewhere it is not.

        Returns a flat list of RSE names, which is what the site displays; the
        per-site byte and file detail was accurate but unreadable in the UI.
        """
        by_name: dict[str, dict[str, Any]] = {}
        for row in rows:
            name, rse = row.get("name"), row.get("rse")
            if not name or not rse:
                continue
            length = row.get("length")
            avail = row.get("available_length")
            complete = (str(row.get("state", "")).upper() == "AVAILABLE"
                        and length is not None and length > 0
                        and avail is not None and avail >= length)
            slot = by_name.setdefault(name, {"complete": set(), "incomplete": set()})
            slot["complete" if complete else "incomplete"].add(rse)

        return {name: {"complete_rses": sorted(v["complete"]),
                       "incomplete_rses": sorted(v["incomplete"])}
                for name, v in by_name.items()}

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    def _did_to_process(self, scope: str, name: str,
                        repl: dict[str, Any]) -> dict[str, Any] | None:
        """Layout C DID (detector/process/...) -> one process-level record.

        Carries identity fields plus replica/PFN facts only. Nothing here is
        physics metadata, by design.
        """
        segments = [s for s in name.split("/") if s]
        if len(segments) < 2:
            logger.warning(f"Unmappable DID (need detector/process): {scope}:{name}")
            return None
        if self.max_path_segments and len(segments) > self.max_path_segments:
            # Rejected, not best-guessed. Mapping segments[0:2] of a deeper
            # path silently produces a plausible-looking entity under a
            # fictional detector, which is worse than no entity at all.
            logger.warning(
                f"Skipping non-Layout-C DID ({len(segments)} path segments, "
                f"expected {self.max_path_segments}): {scope}:{name}")
            return None

        vocab = self.campaigns.get(scope)
        if not vocab:
            logger.warning(
                f"Skipping {scope}:{name} -- campaign '{scope}' is not in "
                f"rucio_sync.campaigns. accelerator/stage/file-type cannot be "
                f"derived from a Rucio DID and are part of the entity UUID, "
                f"so guessing them would create duplicate rows.")
            return None

        detector_raw, process = segments[0], segments[1]
        detector = self.detector_aliases.get(detector_raw, detector_raw)
        return {
            # Identity: name plus the five navigation values.
            #
            # process-name is the BARE process, no detector prefix. Verified
            # against this deployment's data on 2026-08-06: datasets carrying
            # EventProducer's n-events/cross-section are named bare
            # ("kkmcp8_ee_mumu_ecm87p9"). A parallel set of 924 rows named
            # "IDEA/<process>" exists but carries did-layout/source instead,
            # i.e. it is residue from an earlier import of the offline
            # pipeline's output, not authoritative. entity.name is a plain
            # alias of this key (json_data_model.py:83, no composition
            # anywhere in _generate_entity_name), so emitting the prefixed
            # form would target the duplicates rather than the real rows.
            "process-name": process,
            "campaign": scope,
            "accelerator": vocab.get("accelerator"),
            "detector": detector,
            "stage": vocab.get("stage"),
            "file-type": vocab.get("file-type"),
            # Replica facts. _project decides what actually ships.
            # 'replicas' is the list of RSEs holding a COMPLETE copy; the
            # count is derived from it so the two can never disagree.
            "replicas": repl.get("complete_rses") or None,
            "replica_count": len(repl.get("complete_rses") or []) or None,
            "incomplete_rses": repl.get("incomplete_rses") or None,
            # The dataset's Rucio identifier, "scope:name". This is what
            # locates the data in Rucio and needs no extra request -- it comes
            # from the DID listing already done. Replaces the PFN prefixes,
            # which described physical storage paths the site does not need.
            # Key name chosen so the frontend's title-casing renders it as
            # "Rucio Datasets"; plural because a process can span several DIDs.
            "rucio_datasets": [f"{scope}:{name}"],
        }

    def _collapse(self, acc: dict[tuple, dict[str, Any]],
                  rec: dict[str, Any]) -> None:
        """Fold multiple DIDs onto one process entity.

        For Layout C (campaign:<Detector>/<process>/) the key below is exactly
        the DID's own identity, so one DID maps to one entity and this branch
        rarely fires. It exists because nothing in Rucio enforces that, and a
        silently dropped second DID would be worse than a merged one -- the
        warning makes the case visible if it ever occurs.
        """
        key = (rec["process-name"], rec["campaign"], rec["accelerator"],
               rec["detector"], rec["stage"], rec["file-type"])
        slot = acc.get(key)
        if slot is None:
            acc[key] = rec
            return

        logger.warning(
            f"More than one Rucio dataset maps to {rec['campaign']}:"
            f"{rec['detector']}/{rec['process-name']} -- merging "
            f"{rec.get('rucio_datasets')} into {slot.get('rucio_datasets')}")

        for f in ("rucio_datasets", "replicas", "incomplete_rses"):
            merged = sorted(set(slot.get(f) or []) | set(rec.get(f) or []))
            slot[f] = merged or None
        # Derived, never summed: an RSE holding two of this process's DIDs
        # must count once.
        slot["replica_count"] = len(slot.get("replicas") or []) or None

    def _project(self, rec: dict[str, Any]) -> dict[str, Any]:
        """Keep identity fields plus only the whitelisted metadata keys.

        The single point deciding what Rucio may overwrite in the site
        database. Widening it is a one-line config change, reviewable in a PR,
        rather than a code change buried in the mapper.
        """
        out = {k: rec.get(k) for k in ("process-name", "campaign", "accelerator",
                                       "detector", "stage", "file-type")}
        for k in self.emit_fields:
            v = rec.get(k)
            if v is None:
                # Nulls dropped rather than sent: _filter_empty_metadata_values
                # would strip them anyway, and sending them clutters the dry-run.
                continue
            out[k] = v
        return out


# ----------------------------------------------------------------------
# One-shot entry point:  python -m app.services.rucio_sync [--dry-run]
# ----------------------------------------------------------------------

async def _main(dry_run: bool) -> None:
    config = get_config()
    database = Database()
    await database.setup(config)
    try:
        service = RucioSyncService(database)
        if not service.host:
            raise SystemExit("rucio_sync.host not configured")
        stats = await service.sync_once(dry_run=dry_run)
        print(json.dumps(stats, indent=2))
    finally:
        await database.aclose()


if __name__ == "__main__":
    import sys

    asyncio.run(_main(dry_run="--dry-run" in sys.argv))
