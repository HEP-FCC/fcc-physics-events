#!/usr/bin/env python3
"""Stage 4: convert enriched Rucio NDJSON into fcc-physics-events import JSON.

Usage:
    python3 convert_rucio.py --scope winter2023 --prefix rucio_winter2023
    python3 convert_rucio.py --scope winter2023 --granularity process --strict

IMPORT CONTRACT (verified against HEP-FCC/fcc-physics-events @ master)
----------------------------------------------------------------------
  * json_data_model.py       - collection detection requires a top-level
                               "processes" list; FccDataset reads the entity
                               name from alias "process-name" ONLY; the
                               navigation keys are accelerator / stage /
                               campaign / detector / file-type; events use
                               alias "n-events".
  * database.sql             - the entities table is NOT columnar. Five
                               navigation foreign keys plus one `metadata`
                               JSONB blob. Extra keys therefore never create
                               columns, but they DO land in JSONB and are
                               trigram-indexed through
                               idx_datasets_metadata_search_gin, which indexes
                               the concatenation of every metadata VALUE. A
                               constant field such as account="root" makes a
                               free-text search for "root" match the entire
                               catalogue. Hence the strict whitelist.
  * data_import_module.py    - _filter_empty_metadata_values() drops "" , None
                               and []. It does NOT drop 0 or false. Emitting a
                               fabricated 0 for an unknown value defeats a
                               mechanism that would otherwise handle it
                               correctly. Never coerce null to 0.
  * uuid_utils.py            - upsert UUID = uuid5(name + navigation FK ids).
                               Navigation values are part of the dedup key, so
                               changing one between runs creates a DUPLICATE
                               entity, not an update. Same for the granularity
                               mode below.
  * String validators normalise whitespace but do NOT case-fold, so 'IDEA' and
    'idea' import as two distinct navigation entities.

CHANGES vs the previous version
-------------------------------
1. accelerator is no longer the literal "fcc-ee". It is resolved from
   vocabulary.accelerator_by_campaign, and left null + counted when the
   campaign is unknown.
2. Layouts are declarative config, not hardcoded segment-index branches.
3. Strict output whitelist replaces "copy every remaining flattened key".
4. Nulls stay null. n-events / size / replica_count are never coerced to 0.
5. Bookkeeping-only datasets (a lone .tar.gz weights bundle) no longer inherit
   file-type from the path token that produced the wrong edm4hep-root label.
6. --granularity process collapses job and batch DIDs into one entity per
   physics process. Default remains 'did'; see granularity notes in the config.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from rucio_common import DEFAULT_CONFIG, die, load_config


# --------------------------------------------------------------------------
# Vocabulary resolution
# --------------------------------------------------------------------------

class Vocab:
    """Compiled view of the config's vocabulary and layout sections.

    Compiled once at startup rather than per record: the regexes and the
    longest-suffix-first extension ordering are fixed for the whole run, and
    re-deriving them inside a 1e6-iteration loop is pure waste.
    """

    def __init__(self, cfg: dict):
        v = cfg["vocabulary"]
        self.stage_tokens = {k: tuple(val) for k, val in v["stage_tokens"].items()}

        # Sort longest-first so '.lhe.gz' is tested before '.lhe' regardless of
        # how the config happens to be ordered. Relying on author discipline
        # for correctness is a latent bug.
        self.ext_map = sorted(((e.lower(), tuple(p)) for e, p in v["extension_map"]),
                              key=lambda x: -len(x[0]))
        self.bookkeeping = tuple(e.lower() for e in v.get("bookkeeping_extensions", []))
        self.accel_by_campaign = v.get("accelerator_by_campaign", {})
        self.no_detector_value = v.get("no_detector_value", "not-defined")
        self.detector_aliases = v.get("detector_aliases", {})
        self.energy_re = re.compile(v["energy_from_process_regex"], re.IGNORECASE)
        self.energy_suffix = v.get("energy_suffix", "gev")
        self.gen_re = re.compile(v["generator_convention_regex"])
        self.layouts = cfg["layouts"]["rules"]

    def resolve_placeholder(self, value):
        """'@no_detector_value' in a layout rule -> the vocabulary constant."""
        if isinstance(value, str) and value.startswith("@"):
            return getattr(self, value[1:], None)
        return value


def classify_extension(child_name: str, vocab: Vocab):
    """(stage, file_type, is_bookkeeping) implied by the child file extension."""
    if not child_name:
        return None, None, False
    low = child_name.lower()
    if any(low.endswith(b) for b in vocab.bookkeeping):
        return None, None, True
    for ext, (stage, ftype) in vocab.ext_map:
        if low.endswith(ext):
            return stage, ftype, False
    return None, None, False


def parse_path(child_name: str, vocab: Vocab) -> dict:
    """Derive navigation fields from a Rucio-relative child DID name.

    Driven entirely by layouts.rules. Every field is read from a path segment,
    the process name, or the file extension; nothing is invented. Unresolvable
    fields stay None and are counted by the caller.
    """
    out = {"energy": None, "process": None, "stage": None, "file_type": None,
           "detector": None, "layout": None, "bookkeeping": False}
    if not child_name:
        return out

    segs = [s for s in child_name.split("/") if s]
    ext_stage, ext_ftype, is_bk = classify_extension(child_name, vocab)
    out["bookkeeping"] = is_bk

    for rule in vocab.layouts:
        if len(segs) < rule.get("min_segments", 0):
            continue

        idx = rule.get("stage_token_at")
        if idx is not None:
            if idx >= len(segs) or segs[idx] not in vocab.stage_tokens:
                continue
            out["stage"], out["file_type"] = vocab.stage_tokens[segs[idx]]

        out["layout"] = rule.get("name")
        for field, seg_i in rule.get("fields", {}).items():
            if seg_i < len(segs):
                out[field] = segs[seg_i]

        if "detector" in rule:
            out["detector"] = vocab.resolve_placeholder(rule["detector"])

        if rule.get("energy_from_process") and out["process"]:
            m = vocab.energy_re.search(out["process"])
            if m:
                # 'ecm87p9' -> '87.9gev', matching the '91.19gev' form used by
                # the job-structured layouts.
                token = m.group(1).replace("p", ".").replace("P", ".")
                out["energy"] = f"{token}{vocab.energy_suffix}"

        if rule.get("stage_from_extension"):
            out["stage"], out["file_type"] = ext_stage, ext_ftype

        # A dataset whose representative child is a bookkeeping artefact must
        # NOT inherit file-type from the path token. This is the defect that
        # labelled a 15 kB .tar.gz weights bundle as edm4hep-root.
        if is_bk:
            out["file_type"] = None

        return out

    return out


# --------------------------------------------------------------------------
# Entity construction
# --------------------------------------------------------------------------

def first_not_none(*values):
    for v in values:
        if v is not None:
            return v
    return None


def build_entity(raw: dict, cfg: dict, vocab: Vocab, args,
                 counters: Counter, seen: dict) -> dict:
    name = raw.get("name")
    if not name:
        # Without a name the backend invents a random fallback via
        # _generate_entity_name(), so the upsert UUID differs on every run and
        # each import creates fresh duplicates. Refuse rather than emit that.
        raise ValueError("record has no 'name'")

    nav = parse_path(raw.get("sample_child_name") or "", vocab)
    agg = raw.get("child_aggregates") or {}

    # raw["scope"] is written per-record by join_enrich, so a multi-scope run
    # gets the right campaign per record without threading a scope argument
    # through. args.campaign is an explicit operator override only.
    campaign = first_not_none(args.campaign, raw.get("scope"))

    # The one field no DID path encodes. Looked up, never assumed.
    accelerator = first_not_none(args.accelerator,
                                 vocab.accel_by_campaign.get(campaign))

    detector = first_not_none(nav["detector"], args.detector)
    if detector:
        detector = vocab.detector_aliases.get(detector, detector)

    stage = first_not_none(nav["stage"], args.stage)
    file_type = first_not_none(nav["file_type"], args.file_type)

    # Dataset's own Rucio value wins; child sum is the fallback. Both may be
    # None, and None is the correct output when neither is known.
    n_events = first_not_none(raw.get("events"), agg.get("total_events"))
    size = first_not_none(raw.get("bytes"), agg.get("total_bytes"))

    proc = nav["process"]
    gen_type = proc.split("_")[0] if proc and vocab.gen_re.search(proc) else None

    for field, val in (("accelerator", accelerator), ("stage", stage),
                       ("campaign", campaign), ("detector", detector),
                       ("file_type", file_type), ("energy", nav["energy"])):
        if val is None:
            counters[f"no_{field}"] += 1
    if detector:
        seen["detector"][detector] += 1
    if nav["layout"]:
        seen["layout"][nav["layout"]] += 1
    else:
        counters["no_layout"] += 1
    if nav["bookkeeping"]:
        counters["bookkeeping_only"] += 1

    entity = {
        "process-name": name.rstrip("/"),
        # The Rucio DID storage path goes to the backend's dedicated `path`
        # column, NOT into the name. The website name is the physics process
        # string; the path is separate provenance.
        "path": name.rstrip("/"),
        "n-events": n_events,
        "size": size,
        "accelerator": accelerator,
        "stage": stage,
        "campaign": campaign,
        "detector": detector,
        "file-type": file_type,
        "gen-type": gen_type,
        "energy": nav["energy"],
        "process": proc,
        "file_count": agg.get("file_count"),
        "replicas": raw.get("replicas"),
        "replica_count": raw.get("replica_count"),
        "rse_names": raw.get("rse_names"),
        "unavailable_rse_names": raw.get("unavailable_rse_names"),
        "sample_child_name": raw.get("sample_child_name"),
        "pfn_file_count": raw.get("pfn_file_count"),
        "pfn_prefixes": raw.get("pfn_prefixes"),
        "parent_containers": raw.get("parent_containers"),
        "replication_rules": raw.get("replication_rules"),
        "parent_rules": raw.get("parent_rules"),
        "replica_query_status": raw.get("replica_query_status"),
        "did-layout": nav["layout"],
        "source": "rucio",
        "produced-with": "rucio-harvester",
        # Prefixed so they cannot collide with the platform's own created_at /
        # updated_at columns, which mean "when the website learned about this".
        "rucio_created_at": raw.get("created_at"),
        "rucio_updated_at": raw.get("updated_at"),
    }
    return apply_whitelist(entity, cfg)


def apply_whitelist(entity: dict, cfg: dict) -> dict:
    """Drop anything not explicitly allowed, preserving whitelist order."""
    allowed = cfg["output"]["metadata_whitelist"]
    return {k: entity[k] for k in allowed if k in entity}


# --------------------------------------------------------------------------
# Optional collapse to one entity per physics process
# --------------------------------------------------------------------------

def sum_optional(values):
    """Sum, treating None as absent. Returns None if every value is absent."""
    present = [v for v in values if v is not None]
    return sum(present) if present else None


def collapse(entities: list[dict], cfg: dict) -> list[dict]:
    """Merge job/batch DIDs of the same physics process into one entity.

    Rucio DATASETs in this scope are job (00016139) and batch (.../000) storage
    directories, so a single ee_Zbb production appears as many DIDs. Grouping
    on the navigation tuple plus energy/process yields one row per physics
    process, which is what a "Physics Events" listing means.

    Complexity: O(N) with a dict grouping pass; O(G) additional space for G
    groups. Alternative considered and rejected: sorting by key and grouping
    with itertools.groupby, which is O(N log N) for no benefit here since the
    key is hashable and the input already fits in memory.
    """
    g = cfg["granularity"]
    key_fields = g["process_key"]
    template = g.get("name_template", "{energy}/{process}/{detector}/{stage}")

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for e in entities:
        groups[tuple(e.get(k) for k in key_fields)].append(e)

    out = []
    for key, members in groups.items():
        base = dict(members[0])
        base["n-events"] = sum_optional(m.get("n-events") for m in members)
        base["size"] = sum_optional(m.get("size") for m in members)
        base["file_count"] = sum_optional(m.get("file_count") for m in members)

        rses = sorted({r for m in members for r in (m.get("rse_names") or [])})
        base["rse_names"] = rses or None
        unavail = sorted({r for m in members
                          for r in (m.get("unavailable_rse_names") or [])}
                         - set(rses))   # an RSE available in ANY member DID
                                        # is not "unavailable" for the process
        base["unavailable_rse_names"] = unavail or None

        # replicas is RSE -> {"state", "bytes", "length", "available_bytes",
        # "available_length"} (fetch_rucio.py, summarise_dataset_replicas).
        # Merging job/batch DIDs of one process means summing the numeric
        # fields per RSE across members and keeping every distinct state seen,
        # since one batch dir's replica can be AVAILABLE while another's is
        # still COPYING.
        merged: dict[str, dict] = {}
        for m in members:
            for rse, info in (m.get("replicas") or {}).items():
                if not isinstance(info, dict):
                    # Defensive: guard against a stale/mismatched upstream
                    # format rather than crashing the whole conversion on one
                    # bad record.
                    continue
                slot = merged.setdefault(rse, {
                    "states": set(), "bytes": None, "length": None,
                    "available_bytes": None, "available_length": None,
                })
                if info.get("state") is not None:
                    slot["states"].add(info["state"])
                for field in ("bytes", "length", "available_bytes",
                             "available_length"):
                    slot[field] = sum_optional([slot[field], info.get(field)])

        base["replicas"] = {
            rse: {**{k: v for k, v in info.items() if k != "states"},
                 "state": (",".join(sorted(info["states"]))
                          if info["states"] else None)}
            for rse, info in merged.items()
        } or None
        # replica_count counts only AVAILABLE RSEs -- reuse `rses` (built from
        # each member's already-filtered rse_names, see summarise_dataset_
        # replicas in fetch_rucio.py), NOT len(merged), which spans every
        # state including UNAVAILABLE/BAD/COPYING and would silently
        # reintroduce the exact "replica_count counts unusable replicas" bug
        # this whole field exists to avoid.
        base["replica_count"] = len(rses) or None

        parts = [str(base.get(f)) for f in re.findall(r"\{([\w-]+)\}", template)
                 if base.get(f) is not None]
        # The website name is the physics process string. Fall back to the
        # shortest member DID only if the process field is absent, rather than
        # emitting an empty name (which the backend would replace with a random
        # one, breaking the upsert UUID on every run).
        base["process-name"] = "/".join(parts) or min(
            m["process-name"] for m in members)
        # Provenance path: keep a representative DID path in the dedicated
        # column so the storage location is not lost when the name is collapsed
        # to the process string.
        base["path"] = min((m.get("path") for m in members if m.get("path")),
                           default=base["process-name"])
        base["did-layout"] = ",".join(sorted(
            {m["did-layout"] for m in members if m.get("did-layout")})) or None
        base["sample_child_name"] = min(
            (m["sample_child_name"] for m in members
             if m.get("sample_child_name")), default=None)
        out.append(apply_whitelist(base, cfg))

    return out


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def write_chunk(entities: list, out_dir: Path, prefix: str, idx: int,
                indent) -> Path:
    final = out_dir / f"{prefix}_{idx:04d}.json"
    tmp = out_dir / f"{prefix}_{idx:04d}.json.tmp"
    # Same-directory temp file plus rename is atomic on POSIX, and the watcher
    # only matches ".json", so it can never observe a half-written file.
    with tmp.open("w", encoding="utf-8") as f:
        json.dump({"processes": entities}, f, ensure_ascii=False, indent=indent)
    os.rename(tmp, final)
    return final


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--scope", action="append", default=[], required=True,
                    help="Rucio scope, repeatable. Run once per scope, or "
                         "pass several to merge them into one output set.")
    ap.add_argument("--workdir", type=Path, default=Path.cwd())
    ap.add_argument("--input", type=Path, default=None,
                    help="enriched NDJSON (default: <workdir>/<scope>_datasets_enriched.ndjson)")
    ap.add_argument("--exclude-layouts", nargs="*", default=None,
                    metavar="NAME",
                    help="skip entities whose did-layout matches, e.g. "
                         "--exclude-layouts A B. Excluded entities are "
                         "counted and listed, never silently dropped. "
                         "Default: config output.exclude_layouts, else none.")
    ap.add_argument("--indent", type=int, default=None,
                    help="JSON indent (default: 2). Use --indent -1 for "
                         "compact single-line output.")
    ap.add_argument("--out", type=Path, default=Path("."),
                    help="directory for the converted JSON (default: cwd, "
                         "matching --workdir so every pipeline artefact for a "
                         "scope sits in one place)")
    ap.add_argument("--prefix", default=None,
                    help="stable filename prefix (default: rucio_<scope>). "
                         "Stable across reruns so the watcher re-imports and "
                         "the backend upserts instead of accumulating files.")
    ap.add_argument("--granularity", choices=["did", "process"], default=None,
                    help="override granularity.mode from config")
    ap.add_argument("--strict", action="store_true",
                    help="exit 2 if ANY navigation field is unresolved")
    ap.add_argument("--max-fail-ratio", type=float, default=0.01)
    ap.add_argument("--drop-bookkeeping", action="store_true", default=None,
                    help="skip datasets whose only children are job "
                         "bookkeeping artefacts (weights tarballs, logs); "
                         "overrides output.drop_bookkeeping_only")

    # Fallbacks only. None of these has a hardcoded physics default; each is
    # null unless the data or the config resolves it.
    ap.add_argument("--accelerator", default=None)
    ap.add_argument("--stage", default=None)
    ap.add_argument("--file-type", dest="file_type", default=None)
    ap.add_argument("--campaign", default=None)
    ap.add_argument("--detector", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    vocab = Vocab(cfg)

    mode = args.granularity or cfg["granularity"]["mode"]
    scopes = list(dict.fromkeys(args.scope))
    prefix = args.prefix or f"rucio_{'_'.join(scopes)}"

    if args.input:
        infiles = [args.input]
    else:
        infiles = [args.workdir / f"{s}_datasets_enriched.ndjson"
                   for s in scopes]
    missing = [f for f in infiles if not f.exists()]
    if missing:
        die(f"Missing input(s): {[str(m) for m in missing]} "
            f"(run join_enrich.py first)")
    args.out.mkdir(parents=True, exist_ok=True)

    drop_bk = (args.drop_bookkeeping if args.drop_bookkeeping is not None
               else cfg["output"].get("drop_bookkeeping_only", False))

    # Layout exclusion. Off by default: Layout A/B DIDs are real physics data
    # (e.g. 91.19gev/ee_Zbb/.../000 holds 991 Delphes .root files, ~811 GB)
    # whose NAMES cannot be joined to the website's canonical process form --
    # a catalogue-content decision, not a parsing default. This
    # filter exists so that decision, once made, is one reversible flag
    # instead of a code edit. Excluded entities are counted per layout and
    # listed on stderr; nothing is ever dropped silently.
    exclude_layouts = set(args.exclude_layouts or
                          cfg["output"].get("exclude_layouts") or [])

    counters: Counter = Counter()
    seen = {"detector": Counter(), "layout": Counter()}
    entities: list[dict] = []
    excluded_by_layout: Counter = Counter()
    excluded_names: list[str] = []
    failed = dropped_bk = 0

    for infile in infiles:
        with infile.open(encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    raw = json.loads(line)
                    ent = build_entity(raw, cfg, vocab, args, counters, seen)
                    if ent.get("did-layout") in exclude_layouts:
                        excluded_by_layout[ent["did-layout"]] += 1
                        excluded_names.append(ent.get("process-name")
                                              or raw.get("name"))
                        continue
                    if drop_bk and parse_path(
                            raw.get("sample_child_name") or "",
                            vocab)["bookkeeping"]:
                        dropped_bk += 1
                        continue
                    entities.append(ent)
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    failed += 1
                    if failed <= 20:
                        print(f"{infile.name} line {lineno}: skipped ({e})",
                              file=sys.stderr)

    n_raw = len(entities)
    if mode == "process":
        entities = collapse(entities, cfg)

    # The website's canonical entity name is the physics process string:
    # <generator>_<final-state>_ecm<energy>, e.g. wzp6_ee_ww_4q_Vcs_Vcs_ecm163.
    # Layout A DIDs do not carry the generator or the ecm-energy token, so their
    # names cannot be reconstructed to this form from Rucio alone. Flag every
    # name that lacks the 'ecm' marker so the gap is visible, not silent.
    nonconforming = [e["process-name"] for e in entities
                     if "ecm" not in (e.get("process-name") or "")]
    chunk_size = cfg["output"].get("chunk_size", 10000)
    # Pretty-print by default, in CODE, not config. A config with
    # "indent": null used to force the entire {"processes": [...]} object onto
    # one physical line, which is valid JSON but unreadable and un-greppable.
    # Config/CLI can still override; absent or null now means 2, not compact.
    indent = args.indent if args.indent is not None else cfg["output"].get("indent")
    if indent is None:
        indent = 2
    if indent < 0:
        indent = None      # --indent -1 for deliberately compact output
    written = [write_chunk(entities[i:i + chunk_size], args.out, prefix,
                           i // chunk_size, indent)
               for i in range(0, len(entities), chunk_size)] or \
              [write_chunk([], args.out, prefix, 0, indent)]

    # ---------------- report ----------------
    print(f"\nGranularity   : {mode}", file=sys.stderr)
    print(f"DID entities  : {n_raw}", file=sys.stderr)
    if mode == "process":
        print(f"After collapse: {len(entities)} "
              f"({n_raw - len(entities)} DIDs merged)", file=sys.stderr)
    print(f"Failed lines  : {failed}", file=sys.stderr)
    if drop_bk:
        print(f"Bookkeeping   : {dropped_bk} dropped", file=sys.stderr)
    print(f"Layouts       : {dict(seen['layout'])}", file=sys.stderr)
    if excluded_by_layout:
        print(f"EXCLUDED      : {dict(excluded_by_layout)} entities skipped "
              f"by layout filter {sorted(exclude_layouts)}:", file=sys.stderr)
        for n in excluded_names:
            print(f"  - {n}", file=sys.stderr)
        print("  These DIDs exist in Rucio and hold real data; they are "
              "absent from the output by explicit choice, not by parsing "
              "failure.", file=sys.stderr)
    print(f"Detectors     : {dict(seen['detector'])}", file=sys.stderr)
    for k in sorted(counters):
        print(f"  {k:<20}: {counters[k]}", file=sys.stderr)
    for p in written:
        print(f"Wrote: {p}", file=sys.stderr)

    if nonconforming:
        sample = nonconforming[:5]
        print(f"\nWARNING: {len(nonconforming)}/{len(entities)} entity names "
              f"do NOT match the website convention (no 'ecm' energy token), "
              f"e.g. {sample}. These are Layout A DIDs whose generator and "
              f"ecm-energy are absent from the Rucio path. They will list "
              f"under a different name shape than the existing EventProducer "
              f"entities for the same physics. Resolve the canonical name "
              f"source before importing.", file=sys.stderr)

    # Two entities sharing a display name confuse the listing even when their
    # upsert UUIDs differ (they will, because the navigation values feed the
    # UUID). Happens in 'process' mode when two groups differ only in a key
    # field absent from granularity.name_template.
    name_counts = Counter(e["process-name"] for e in entities)
    dupes = {n: c for n, c in name_counts.items() if c > 1}
    if dupes:
        print(f"\nWARNING: {len(dupes)} process-name(s) emitted more than once "
              f"{dict(list(dupes.items())[:5])}. Add the distinguishing field "
              f"to granularity.name_template, or narrow process_key.",
              file=sys.stderr)

    # Two spellings of one detector become two navigation entities AND two
    # upsert-UUID families for identical physics. Detect before import, not
    # after.
    collisions = {}
    for d in seen["detector"]:
        variants = sorted(x for x in seen["detector"] if x.lower() == d.lower())
        if len(variants) > 1:
            collisions[d.lower()] = variants
    if collisions:
        print(f"\nWARNING: detector case collision {collisions}. Add the "
              f"canonical spelling to vocabulary.detector_aliases in the "
              f"config before importing.", file=sys.stderr)

    gaps = {k: v for k, v in counters.items() if v and k.startswith("no_")}
    if gaps:
        print(f"\nWARNING: unresolved navigation fields {gaps}. A field left "
              f"null now and filled in later produces a DUPLICATE entity, not "
              f"an update, because the navigation values are part of the "
              f"upsert UUID.", file=sys.stderr)

    if args.strict and gaps:
        print("FAIL: --strict set and navigation gaps remain.", file=sys.stderr)
        return 2
    total = n_raw + failed
    if total and failed / total > args.max_fail_ratio:
        print(f"FAIL: {failed}/{total} lines failed "
              f"(> {args.max_fail_ratio:.0%})", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
