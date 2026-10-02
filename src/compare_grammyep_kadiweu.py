#!/usr/bin/env python3
"""
compare_grammyep_kadiweu.py

Reproducible comparison between the Portuguese stimuli/equivalents in
GrammYEP (Alencar 2021) and Portuguese text_por backtranslations/annotations in the
Kadiwéu Tycho Brahe JSON exports.

The script deliberately distinguishes:
  EXACT_RAW          same Portuguese string after trimming whitespace only
  EXACT_NORMALIZED   same after conservative mechanical normalization
  VARIANT_CANDIDATE  no exact match, but a high string-similarity candidate
  NO_MATCH           no candidate above the chosen threshold
  NO_PORTUGUESE      Kadiwéu record has no pt-br translation/prompt

IMPORTANT:
VARIANT_CANDIDATE is NOT automatically asserted to be semantically equivalent.
It is an auditable proposal for manual adjudication.

Outputs:
  summary.tsv
  kadiweu_matches.tsv
  stimulus_coverage.tsv
  variant_candidates.tsv
  ambiguous_portuguese.tsv
  input_sha256.tsv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tarfile
import zipfile
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path


SENT_RE = re.compile(r"^SENT-(\d+)::\s*(.*)$")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def raw_key(text: str) -> str:
    """Only trim leading/trailing whitespace."""
    return unicodedata.normalize("NFC", text).strip()


def normalize_pt(text: str) -> str:
    """
    Conservative normalization used for EXACT_NORMALIZED.

    Changes ONLY:
      * Unicode -> NFC
      * casefold
      * collapse whitespace
      * remove whitespace immediately before punctuation
      * remove final . ! ? punctuation

    It does NOT normalize lexical or grammatical differences such as:
      é/está, este/esta, meu/a minha, de/do, tu/você, fotografia/retrato.
    """
    s = unicodedata.normalize("NFC", text).casefold().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,;:.!?])", r"\1", s)
    s = re.sub(r"[.!?]+$", "", s).strip()
    return s


def token_set(text: str) -> set[str]:
    return set(re.findall(r"\w+", normalize_pt(text), flags=re.UNICODE))


def strip_parenthetical(text: str) -> str:
    """Diagnostic form without parenthetical text; never an EXACT normalization."""
    previous = None
    current = text
    while previous != current:
        previous = current
        current = re.sub(r"\([^()]*\)", " ", current)
    return normalize_pt(current)


def slash_variants(text: str) -> list[str]:
    """Diagnostic alternatives for slash notation; source text is preserved."""
    if "/" not in text:
        return []
    full = normalize_pt(text)
    parts = [normalize_pt(x) for x in text.split("/") if normalize_pt(x)]
    out = list(parts)
    if len(parts) == 2:
        left, right = parts
        lt, rt = left.split(), right.split()
        if len(lt) >= 2 and 0 < len(rt) < len(lt):
            k = 0
            while k < min(len(lt), len(rt)) and lt[-1-k] == rt[-1-k]:
                k += 1
            if k > 0:
                right_nonshared = rt[:-k]
                prefix_len = max(0, len(lt) - k - max(1, len(right_nonshared)))
                candidate = normalize_pt(" ".join(lt[:prefix_len] + rt))
                if candidate:
                    out.append(candidate)
    return list(dict.fromkeys(x for x in out if x and x != full))


def diagnostic_forms(text: str) -> list[tuple[str, str]]:
    """Extra retrieval forms; never used to assign EXACT_* status."""
    forms = []
    stripped = strip_parenthetical(text)
    if stripped and stripped != normalize_pt(text):
        forms.append(("PARENTHETICAL_STRIPPED", stripped))
    for v in slash_variants(text):
        forms.append(("SLASH_ALTERNATIVE", v))
        sv = strip_parenthetical(v)
        if sv and sv != v:
            forms.append(("SLASH_ALTERNATIVE+PARENTHETICAL_STRIPPED", sv))
    return list(dict.fromkeys(forms))


def similarity(a: str, b: str) -> tuple[float, float, float]:
    """
    Return:
      combined score,
      character SequenceMatcher score,
      token Jaccard score.

    The combined score favors character similarity because the intended
    candidates are usually small Portuguese wording variants.
    """
    na, nb = normalize_pt(a), normalize_pt(b)
    char = SequenceMatcher(None, na, nb).ratio()
    ta, tb = token_set(a), token_set(b)
    jac = len(ta & tb) / len(ta | tb) if (ta | tb) else 1.0
    combined = 0.75 * char + 0.25 * jac
    return combined, char, jac


def parse_grammyep_portuguese_text(text: str) -> list[dict]:
    """
    Parse blocks of the form:

      SENT-1:: Nheengatu sentence
      Portuguese equivalent 1
      Portuguese equivalent 2

      SENT-2:: ...

    Repeated Portuguese equivalents are preserved in the source list but
    deduplicated for matching within each SENT item.
    """
    records = []
    current = None

    for line in text.splitlines():
        m = SENT_RE.match(line)
        if m:
            if current is not None:
                records.append(current)
            current = {
                "sent_id": int(m.group(1)),
                "nheengatu": m.group(2).strip(),
                "portuguese": [],
            }
        elif current is not None and line.strip():
            current["portuguese"].append(line.strip())

    if current is not None:
        records.append(current)

    for rec in records:
        # stable deduplication
        rec["portuguese_unique"] = list(dict.fromkeys(rec["portuguese"]))

    return records


def parse_gf_release(archive: Path) -> tuple[list[dict], dict[int, list[str]]]:
    """Read parallel 1.0.0 treebank files; align by validated SENT block order."""
    def member(name: str) -> str:
        suffix = "/treebank/" + name
        if tarfile.is_tarfile(archive):
            with tarfile.open(archive, "r:*") as tf:
                names = [n for n in tf.getnames() if n.endswith(suffix)]
                if len(names) != 1:
                    raise ValueError(f"Expected one {name} in {archive}; got {names}")
                return tf.extractfile(names[0]).read().decode("utf-8-sig")
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as zf:
                names = [n for n in zf.namelist() if n.endswith(suffix)]
                if len(names) != 1:
                    raise ValueError(f"Expected one {name} in {archive}; got {names}")
                return zf.read(names[0]).decode("utf-8-sig")
        raise ValueError(f"Unsupported archive: {archive}")

    def blocks(text: str) -> list[str]:
        return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]

    sources = blocks(member("GraYrl-GraPor.txt"))
    parsed = blocks(member("GraYrl-Pos.parsed"))
    if len(sources) != len(parsed):
        raise ValueError(f"GF alignment differs: {len(sources)} vs {len(parsed)} blocks")
    result = {}
    for source, gf in zip(sources, parsed):
        m = SENT_RE.match(source.splitlines()[0])
        if not m or int(m.group(1)) in result:
            raise ValueError(f"Missing/duplicate SENT-ID in GF source: {source[:90]}")
        trees = [line.strip() for line in gf.splitlines() if line.strip()]
        if not trees or not all(t.startswith("Pred ") for t in trees):
            raise ValueError(f"Unexpected GF trees for SENT-{m.group(1)}")
        result[int(m.group(1))] = trees
    gram = parse_grammyep_portuguese_text(member("GraYrl-GraPor.txt"))
    if {g["sent_id"] for g in gram} != result.keys():
        raise ValueError("GrammYEP Portuguese and GF identifiers differ")
    return gram, result


def gf_fields(ids: set[int], index: dict[int, list[str]]) -> dict[str, str]:
    """Keep every tree for every matched SENT-ID, with unambiguous provenance."""
    resolved = [(sid, t) for sid in sorted(ids) for t in index.get(sid, [])]
    missing = sorted(ids - index.keys())
    return {
        "gf_tree_count": str(len(resolved)),
        "gf_abstract_trees": " || ".join(t for _, t in resolved),
        "gf_trees_by_sent_id": " || ".join(f"SENT-{sid}::{t}" for sid, t in resolved),
        "gf_alignment_status": (
            "NO_MATCH" if not ids else
            "MISSING_GF_SENT_IDS:" + ",".join(map(str, missing)) if missing else
            "MATCHED_MULTIPLE_SENT_IDS" if len(ids) > 1 else "MATCHED"
        ),
    }


def looks_like_sentence_record(obj: dict) -> bool:
    # Tycho sentence objects in these exports contain these fields.
    return (
        isinstance(obj, dict)
        and "text" in obj
        and "status" in obj
        and "struct" in obj
    )


def extract_tycho_records(path: Path, source: str) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = []

    def walk(obj):
        if isinstance(obj, dict):
            if looks_like_sentence_record(obj):
                translations = obj.get("translations") or {}
                records.append({
                    "source": source,
                    "uid": obj.get("uid", ""),
                    "status": obj.get("status", ""),
                    "kadiweu": obj.get("text", ""),
                    "portuguese": translations.get("pt-br", "") or "",
                })
                # Do not recurse into a sentence record.
                return
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(data)

    # Give every source record a stable ordinal reflecting JSON order.
    for i, rec in enumerate(records, start=1):
        rec["source_index"] = i

    return records


def write_tsv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t",
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gf-release", type=Path, required=True,
                    help="GrammYEP release archive containing aligned GF treebank")
    ap.add_argument("--van", type=Path, required=True)
    ap.add_argument("--hil", type=Path, required=True)
    ap.add_argument("--ped", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, default=Path("grammyep-kadiweu-comparison"))
    ap.add_argument("--variant-threshold", type=float, default=0.80,
                    help="Minimum combined score for VARIANT_CANDIDATE (default: 0.80)")
    ap.add_argument("--editorial-threshold", type=float, default=0.80,
                    help="Minimum transformed-form score for slash/parenthetical provenance normalization (default: 0.80)")
    ap.add_argument("--top-k", type=int, default=5,
                    help="Number of variant candidates retained per unmatched Kadiwéu record")
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    inputs = [
        ("grammyep_gf_release", args.gf_release),
        ("van", args.van),
        ("hil", args.hil),
        ("ped", args.ped),
    ]

    # Reproducibility hashes
    hash_rows = [
        {"role": role, "path": str(path), "sha256": sha256(path)}
        for role, path in inputs
    ]
    write_tsv(args.outdir / "input_sha256.tsv", hash_rows,
              ["role", "path", "sha256"])

    gram, gf_index = parse_gf_release(args.gf_release)

    raw_index = defaultdict(set)
    norm_index = defaultdict(set)
    gram_pt_rows = []

    for g in gram:
        for pt in g["portuguese_unique"]:
            raw_index[raw_key(pt)].add(g["sent_id"])
            norm_index[normalize_pt(pt)].add(g["sent_id"])
            gram_pt_rows.append({
                "sent_id": g["sent_id"],
                "nheengatu": g["nheengatu"],
                "portuguese": pt,
                "normalized_portuguese": normalize_pt(pt),
            })

    gram_by_id = {g["sent_id"]: g for g in gram}

    tycho = []
    for source, path in [("van", args.van), ("hil", args.hil), ("ped", args.ped)]:
        tycho.extend(extract_tycho_records(path, source))

    match_rows = []
    variant_rows = []
    coverage_by_source = defaultdict(set)
    coverage_all = set()

    # All unique GrammYEP Portuguese strings used for fuzzy candidate search.
    unique_gram_pt = {}
    for row in gram_pt_rows:
        unique_gram_pt.setdefault(
            (row["sent_id"], row["portuguese"]),
            row
        )

    for rec in tycho:
        pt = rec["portuguese"]
        raw_ids = raw_index.get(raw_key(pt), set()) if pt else set()
        norm_ids = norm_index.get(normalize_pt(pt), set()) if pt else set()

        if not pt:
            match_type = "NO_PORTUGUESE"
            ids = set()
        elif raw_ids:
            match_type = "EXACT_RAW"
            ids = raw_ids
        elif norm_ids:
            match_type = "EXACT_NORMALIZED"
            ids = norm_ids
        else:
            match_type = "NO_MATCH"
            ids = set()

        for sid in ids:
            coverage_by_source[rec["source"]].add(sid)
            coverage_all.add(sid)

        # Second provenance-normalization layer. GrammYEP itself contains no
        # slash notation or parenthetical additions of this kind. We preserve
        # text_por unchanged, but compare controlled forms that remove these
        # later devices. A sufficiently strong transformed-form relationship
        # is classified separately from ordinary fuzzy matching and does not
        # require open-ended adjudication.
        diagnostic_best = None
        if pt:
            for strategy, form in diagnostic_forms(pt):
                for grow in gram_pt_rows:
                    combined_d, char_d, jac_d = similarity(form, grow["portuguese"])
                    item = (combined_d, char_d, jac_d, strategy, form, grow)
                    if diagnostic_best is None or item[:3] > diagnostic_best[:3]:
                        diagnostic_best = item

        editorial_match = False
        editorial_match_type = ""
        editorial_ids = set()
        if match_type == "NO_MATCH" and diagnostic_best is not None:
            dscore, _, _, dstrategy, dform, drow = diagnostic_best
            exact_transformed_ids = norm_index.get(normalize_pt(dform), set())
            if exact_transformed_ids:
                editorial_match = True
                editorial_match_type = "EDITORIAL_NORMALIZED_EXACT"
                editorial_ids = set(exact_transformed_ids)
            elif dscore >= args.editorial_threshold:
                editorial_match = True
                editorial_match_type = "EDITORIAL_NORMALIZED_SIMILAR"
                editorial_ids = {drow["sent_id"]}

        if editorial_match:
            match_type = editorial_match_type
            ids = editorial_ids
            for sid in ids:
                coverage_by_source[rec["source"]].add(sid)
                coverage_all.add(sid)

        match_rows.append({
            **rec,
            "match_type": match_type,
            "has_slash": "yes" if "/" in pt else "no",
            "has_parenthetical": "yes" if re.search(r"\([^()]*\)", pt) else "no",
            "diagnostic_best_strategy": "" if diagnostic_best is None else diagnostic_best[3],
            "diagnostic_best_form": "" if diagnostic_best is None else diagnostic_best[4],
            "diagnostic_best_sent_id": "" if diagnostic_best is None else diagnostic_best[5]["sent_id"],
            "diagnostic_best_portuguese": "" if diagnostic_best is None else diagnostic_best[5]["portuguese"],
            "diagnostic_best_combined_score": "" if diagnostic_best is None else f"{diagnostic_best[0]:.6f}",
            "diagnostic_best_char_score": "" if diagnostic_best is None else f"{diagnostic_best[1]:.6f}",
            "diagnostic_best_token_jaccard": "" if diagnostic_best is None else f"{diagnostic_best[2]:.6f}",
            "grammyep_sent_ids": ",".join(map(str, sorted(ids))),
            "normalized_portuguese": normalize_pt(pt) if pt else "",
            "portuguese_field_role": "TBP_TRANSLATION_NOT_VERIFIED_STIMULUS",
            **gf_fields(ids, gf_index),
        })

        # Ordinary fuzzy proposals only after both normalization layers fail.
        if pt and not ids:
            candidates = []
            for (_, _), grow in unique_gram_pt.items():
                combined, char, jac = similarity(pt, grow["portuguese"])
                if combined >= args.variant_threshold:
                    candidates.append((
                        combined, char, jac,
                        grow["sent_id"], grow["nheengatu"], grow["portuguese"]
                    ))

            candidates.sort(key=lambda x: (-x[0], -x[1], x[3], x[5]))
            for rank, (combined, char, jac, sid, yrl, gpt) in enumerate(
                candidates[:args.top_k], start=1
            ):
                variant_rows.append({
                    "source": rec["source"],
                    "source_index": rec["source_index"],
                    "uid": rec["uid"],
                    "status": rec["status"],
                    "kadiweu": rec["kadiweu"],
                    "kadiweu_portuguese": pt,
                    "rank": rank,
                    "grammyep_sent_id": sid,
                    "nheengatu": yrl,
                    "grammyep_portuguese": gpt,
                    "combined_score": f"{combined:.6f}",
                    "char_score": f"{char:.6f}",
                    "token_jaccard": f"{jac:.6f}",
                    "manual_decision": "",
                    "manual_comment": "",
                    **gf_fields({sid}, gf_index),
                })

    # Exact/normalized stimulus coverage table.
    coverage_rows = []
    for g in gram:
        sources = sorted(
            s for s in ("van", "hil", "ped")
            if g["sent_id"] in coverage_by_source[s]
        )
        coverage_rows.append({
            "sent_id": g["sent_id"],
            "nheengatu": g["nheengatu"],
            "portuguese_equivalents": " || ".join(g["portuguese_unique"]),
            "covered_by_normalization_layers": "yes" if sources else "no",
            "sources": ",".join(sources),
            **gf_fields({g["sent_id"]}, gf_index),
        })

    # Portuguese equivalents that map to >1 GrammYEP SENT-ID.
    ambiguous_rows = []
    for normalized, ids in sorted(norm_index.items()):
        if len(ids) > 1:
            forms = sorted({
                row["portuguese"]
                for row in gram_pt_rows
                if row["sent_id"] in ids
                and row["normalized_portuguese"] == normalized
            })
            ambiguous_rows.append({
                "normalized_portuguese": normalized,
                "grammyep_sent_ids": ",".join(map(str, sorted(ids))),
                "surface_forms": " || ".join(forms),
            })

    gf_cols = ["gf_tree_count", "gf_abstract_trees", "gf_trees_by_sent_id", "gf_alignment_status"]
    write_tsv(
        args.outdir / "kadiweu_matches.tsv",
        match_rows,
        ["source", "source_index", "uid", "status", "kadiweu", "portuguese",
         "match_type", "has_slash", "has_parenthetical",
         "diagnostic_best_strategy", "diagnostic_best_form",
         "diagnostic_best_sent_id", "diagnostic_best_portuguese",
         "diagnostic_best_combined_score", "diagnostic_best_char_score",
         "diagnostic_best_token_jaccard", "grammyep_sent_ids",
         "normalized_portuguese", "portuguese_field_role", *gf_cols]
    )
    editorial_rows = [r for r in match_rows if r["has_slash"] == "yes" or r["has_parenthetical"] == "yes"]
    write_tsv(
        args.outdir / "editorial_normalization_cases.tsv",
        editorial_rows,
        ["source", "source_index", "uid", "status", "kadiweu", "portuguese",
         "match_type", "has_slash", "has_parenthetical",
         "diagnostic_best_strategy", "diagnostic_best_form",
         "diagnostic_best_sent_id", "diagnostic_best_portuguese",
         "diagnostic_best_combined_score", "diagnostic_best_char_score",
         "diagnostic_best_token_jaccard", "grammyep_sent_ids",
         "portuguese_field_role", *gf_cols]
    )

    write_tsv(
        args.outdir / "stimulus_coverage.tsv",
        coverage_rows,
        ["sent_id", "nheengatu", "portuguese_equivalents",
         "covered_by_normalization_layers", "sources", *gf_cols]
    )
    write_tsv(
        args.outdir / "variant_candidates.tsv",
        variant_rows,
        ["source", "source_index", "uid", "status", "kadiweu",
         "kadiweu_portuguese", "rank", "grammyep_sent_id", "nheengatu",
         "grammyep_portuguese", "combined_score", "char_score",
         "token_jaccard", "manual_decision", "manual_comment", *gf_cols]
    )
    write_tsv(
        args.outdir / "ambiguous_portuguese.tsv",
        ambiguous_rows,
        ["normalized_portuguese", "grammyep_sent_ids", "surface_forms"]
    )

    # Summary
    counts = Counter(r["match_type"] for r in match_rows)
    by_source = {
        s: [r for r in match_rows if r["source"] == s]
        for s in ("van", "hil", "ped")
    }

    summary = []
    summary.append({"measure": "grammyep_base_sentences", "value": len(gram)})
    summary.append({"measure": "grammyep_portuguese_equivalents_total",
                    "value": sum(len(g["portuguese"]) for g in gram)})
    summary.append({"measure": "grammyep_portuguese_equivalents_unique_normalized",
                    "value": len(norm_index)})
    summary.append({"measure": "grammyep_ambiguous_normalized_equivalents",
                    "value": len(ambiguous_rows)})
    summary.append({"measure": "kadiweu_records_total", "value": len(tycho)})

    for s in ("van", "hil", "ped"):
        rs = by_source[s]
        exactish = sum(r["match_type"] in ("EXACT_RAW", "EXACT_NORMALIZED") for r in rs)
        editorial = sum(r["match_type"].startswith("EDITORIAL_NORMALIZED_") for r in rs)
        summary.extend([
            {"measure": f"{s}_records", "value": len(rs)},
            {"measure": f"{s}_exact_or_normalized_records", "value": exactish},
            {"measure": f"{s}_editorial_normalized_records", "value": editorial},
            {"measure": f"{s}_covered_grammyep_sentences",
             "value": len(coverage_by_source[s])},
        ])

    exactish_total = sum(
        r["match_type"] in ("EXACT_RAW", "EXACT_NORMALIZED")
        for r in match_rows
    )
    editorial_exact_total = sum(r["match_type"] == "EDITORIAL_NORMALIZED_EXACT" for r in match_rows)
    editorial_similar_total = sum(r["match_type"] == "EDITORIAL_NORMALIZED_SIMILAR" for r in match_rows)
    editorial_total = editorial_exact_total + editorial_similar_total
    # Count Kadiweu RECORDS with at least one variant candidate, rather
    # than rows in variant_candidates.tsv (which may contain up to top-k
    # candidates for the same Kadiweu record).
    variant_records = {
        (r["source"], r["source_index"])
        for r in variant_rows
    }
    variant_record_total = len(variant_records)
    related_total = exactish_total + editorial_total + variant_record_total
    related_percentage = (
        100.0 * related_total / len(tycho) if tycho else 0.0
    )

    slash_n = sum(r["has_slash"] == "yes" for r in match_rows)
    paren_n = sum(r["has_parenthetical"] == "yes" for r in match_rows)
    diagnostic_n = sum(bool(r["diagnostic_best_strategy"]) for r in match_rows)

    summary.extend([
        {"measure": "kadiweu_exact_or_normalized_records", "value": exactish_total},
        {"measure": "kadiweu_editorial_normalized_exact_records", "value": editorial_exact_total},
        {"measure": "kadiweu_editorial_normalized_similar_records", "value": editorial_similar_total},
        {"measure": "kadiweu_editorial_normalized_records", "value": editorial_total},
        {"measure": "kadiweu_records_with_slash", "value": slash_n},
        {"measure": "kadiweu_records_with_parenthetical", "value": paren_n},
        {"measure": "kadiweu_records_with_diagnostic_form", "value": diagnostic_n},
        {"measure": "kadiweu_records_with_variant_candidate",
         "value": variant_record_total},
        {"measure": "kadiweu_related_records_total", "value": related_total},
        {"measure": "kadiweu_related_records_percentage",
         "value": f"{related_percentage:.2f}"},
        {"measure": "covered_grammyep_sentences_union", "value": len(coverage_all)},
        {"measure": "van_hil_covered_intersection",
         "value": len(coverage_by_source["van"] & coverage_by_source["hil"])},
        {"measure": "variant_candidate_rows", "value": len(variant_rows)},
        {"measure": "no_portuguese_records", "value": counts["NO_PORTUGUESE"]},
    ])

    write_tsv(args.outdir / "summary.tsv", summary, ["measure", "value"])

    print(f"GF treebank: {len(gf_index)} SENT-IDs; {sum(map(len, gf_index.values()))} trees")
    print(f"GrammYEP base sentences: {len(gram)}")
    print(f"Kadiweu records: {len(tycho)}")
    print(f"Exact/raw or conservatively normalized Kadiweu records: {exactish_total}")
    print(f"Covered GrammYEP base sentences: {len(coverage_all)}")
    print()
    for s in ("van", "hil", "ped"):
        rs = by_source[s]
        exactish = sum(r["match_type"] in ("EXACT_RAW", "EXACT_NORMALIZED") for r in rs)
        editorial = sum(r["match_type"].startswith("EDITORIAL_NORMALIZED_") for r in rs)
        editorial = sum(r["match_type"].startswith("EDITORIAL_NORMALIZED_") for r in rs)
        print(f"{s}: {len(rs)} records; {exactish} strict exact/normalized; "
              f"{editorial} editorial-normalized; "
              f"{len(coverage_by_source[s])} GrammYEP SENT-IDs covered")
    print(f"van ∩ hil stimulus coverage: "
          f"{len(coverage_by_source['van'] & coverage_by_source['hil'])}")
    print(f"Editorial-normalized records: {editorial_total} "
          f"({editorial_exact_total} exact after transformation; "
          f"{editorial_similar_total} similar after transformation)")
    print(f"Variant candidate rows written after normalization layers: {len(variant_rows)}")
    print(f"Kadiweu records with >=1 variant candidate: {variant_record_total}")
    print(f"Automatically related Kadiweu records (strict + editorial + fuzzy): "
          f"{related_total}/{len(tycho)} ({related_percentage:.2f}%)")
    print(f"Kadiweu records containing '/': {slash_n}")
    print(f"Kadiweu records containing parenthetical material: {paren_n}")
    print(f"Output directory: {args.outdir}")


if __name__ == "__main__":
    main()
