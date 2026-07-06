#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Check one or more Kadiwéu Tycho Brahe JSON dumps for omissions and inconsistencies.

This script is designed for treebank cleanup before UD conversion. It reuses the
same sentence-collection approach found in the project's inspection utilities,
then adds consistency checks over tokens and split morphemes.

Main checks
-----------
1. Missing token fields
   - missing token form
   - missing token tag
   - missing token gloss
2. Missing split fields
   - empty split object
   - missing split form
   - missing split tag
   - missing split gloss when the same morpheme elsewhere has one
3. Repeated token form with conflicting analyses
   - conflicting token tags for the same surface form
   - conflicting split-tag sequences for the same surface form
   - conflicting token-level glosses for the same surface form
4. Repeated morpheme form with conflicting analyses
   - conflicting split tags for the same morpheme form
   - conflicting split glosses for the same morpheme form
5. Alignment / structure warnings
   - token count vs proto-CoNLL-U count mismatch
   - token/conllu surface mismatch by position
   - chunk spans outside attested token positions
6. Helpful cleanup heuristics
   - tokens with no splits although the same token elsewhere has splits
   - tokens with incomplete split descriptions although the same token elsewhere
     has a fuller analysis

Output
------
By default the script prints a concise human-readable summary.

Optional machine-readable outputs:
- --json-out REPORT.json   full report as JSON
- --tsv-dir DIR            grouped TSV files, one per issue type

Usage
-----
Basic:
    python3 check_kadiweu_json_consistency.py data/ped-gramm.json --source-id ped-gramm

Write JSON report and TSVs:
    python3 check_kadiweu_json_consistency.py data/ped-gramm.json \
        --source-id ped-gramm \
        --json-out consistency-report.json --tsv-dir consistency-tsv

Inspect only one sentence:
    python3 check_kadiweu_json_consistency.py data/ped-gramm.json \
        --source-id ped-gramm \
        --uid e553e02e-0d33-4fed-8f6a-b7cf5c9cf9c9

Inspect only sentences whose text contains a string:
    python3 check_kadiweu_json_consistency.py data/ped-gramm.json \
        --source-id ped-gramm \
        --text-contains ipegitegi

Consolidated report for the three canonical project sources:
    python3 check_kadiweu_json_consistency.py \
        data/ped-gramm.json data/hil-data.json data/van-data.json \
        --source-id ped-gramm --source-id hil-data --source-id van-data \
        --json-out data/consistency/kadiweu-all.consistency.json \
        --tsv-dir data/consistency/kadiweu-all-tsv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


JsonDict = Dict[str, Any]


def safe_get(d: Any, *path: str, default=None):
    """Safely descend nested dicts."""
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def is_sentence_object(obj: Any) -> bool:
    """
    Heuristic for recognizing a sentence object.
    We expect:
      - text
      - struct with at least one of tokens/chunks/conllu
    """
    if not isinstance(obj, dict):
        return False
    text = obj.get("text")
    struct = obj.get("struct")
    if not isinstance(text, str):
        return False
    if not isinstance(struct, dict):
        return False
    return any(k in struct for k in ("tokens", "chunks", "conllu"))


def walk_collect_sentences(
    obj: Any,
    path: str = "$",
    inherited_meta: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Recursively traverse the JSON and collect sentence-like objects.

    This follows the same basic pattern used in the existing project scripts.
    """
    if inherited_meta is None:
        inherited_meta = {}

    out: List[Dict[str, Any]] = []

    if isinstance(obj, dict):
        local_meta = dict(inherited_meta)

        for key in ("uid", "id", "title", "name", "label", "content", "contents"):
            if key in obj and key not in local_meta:
                local_meta[key] = obj[key]

        if is_sentence_object(obj):
            out.append(
                {
                    "path": path,
                    "container_meta": local_meta,
                    "sentence": obj,
                }
            )

        for key, value in obj.items():
            out.extend(walk_collect_sentences(value, f"{path}.{key}", local_meta))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            out.extend(walk_collect_sentences(item, f"{path}[{i}]", inherited_meta))

    return out


def filter_sentences(
    sentences: List[Dict[str, Any]],
    uid: Optional[str] = None,
    text_contains: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter sentence records by UID or substring in text."""
    out = sentences

    if uid is not None:
        out = [r for r in out if safe_get(r, "sentence", "uid") == uid]

    if text_contains is not None:
        needle = text_contains.lower()
        out = [
            r
            for r in out
            if isinstance(safe_get(r, "sentence", "text"), str)
            and needle in safe_get(r, "sentence", "text").lower()
        ]

    return out


def token_gloss(token: JsonDict) -> Optional[str]:
    return safe_get(token, "attributes", "gloss-br")


def split_gloss(split: JsonDict) -> Optional[str]:
    return safe_get(split, "attributes", "gloss-br")


def norm_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def split_signature(token: JsonDict) -> Tuple[str, ...]:
    splits = token.get("splits", [])
    if not isinstance(splits, list):
        return tuple()
    return tuple(norm_text(s.get("t")) if isinstance(s, dict) else "" for s in splits)


def split_forms_signature(token: JsonDict) -> Tuple[str, ...]:
    splits = token.get("splits", [])
    if not isinstance(splits, list):
        return tuple()
    return tuple(norm_text(s.get("v")) if isinstance(s, dict) else "" for s in splits)


def has_any_split_content(token: JsonDict) -> bool:
    splits = token.get("splits")
    if not isinstance(splits, list) or not splits:
        return False
    for s in splits:
        if not isinstance(s, dict):
            continue
        if any(k in s and s.get(k) not in (None, "", [], {}) for k in ("v", "t", "attributes", "fn", "idx")):
            return True
    return False


def best_known_split_profile(token_records: Sequence[Tuple[JsonDict, Dict[str, Any]]]) -> Dict[str, Any]:
    """Pick the fullest known split analysis for a token form."""
    best = None
    best_score = -1
    for tok, meta in token_records:
        splits = tok.get("splits", []) if isinstance(tok.get("splits"), list) else []
        score = 0
        for s in splits:
            if not isinstance(s, dict):
                continue
            if norm_text(s.get("v")):
                score += 1
            if norm_text(s.get("t")):
                score += 2
            if split_gloss(s):
                score += 1
        if score > best_score:
            best = {"token": tok, "meta": meta, "score": score}
            best_score = score
    return best or {}


def issue_base(issue_type: str, meta: Dict[str, Any], sentence: JsonDict) -> Dict[str, Any]:
    return {
        "issue_type": issue_type,
        "source_id": meta.get("source_id"),
        "source_file": meta.get("source_file"),
        "source_ordinal": meta.get("source_ordinal"),
        "path": meta["path"],
        "uid": sentence.get("uid"),
        "text": sentence.get("text"),
    }


def collect_sentence_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    sentence = record["sentence"]
    return {
        "source_id": record.get("source_id"),
        "source_file": record.get("source_file"),
        "source_ordinal": record.get("source_ordinal"),
        "path": record["path"],
        "uid": sentence.get("uid"),
        "text": sentence.get("text"),
    }


def analyze(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    issues: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    token_records_by_form: Dict[str, List[Tuple[JsonDict, Dict[str, Any]]]] = defaultdict(list)
    morpheme_records_by_form: Dict[str, List[Tuple[JsonDict, JsonDict, Dict[str, Any], int]]] = defaultdict(list)

    n_sent = len(records)
    n_tok = 0
    n_split = 0

    for record in records:
        sentence = record["sentence"]
        meta = collect_sentence_metadata(record)
        struct = sentence.get("struct", {}) if isinstance(sentence.get("struct"), dict) else {}

        tokens = struct.get("tokens", [])
        chunks = struct.get("chunks", [])
        conllu = struct.get("conllu", [])

        if not isinstance(tokens, list):
            tokens = []
        if not isinstance(chunks, list):
            chunks = []
        if not isinstance(conllu, list):
            conllu = []

        n_tok += len(tokens)

        positions = []
        for tok in tokens:
            if not isinstance(tok, dict):
                continue
            p = tok.get("p")
            if isinstance(p, int):
                positions.append(p)

        if len(tokens) != len(conllu):
            item = issue_base("token_conllu_count_mismatch", meta, sentence)
            item.update({"token_count": len(tokens), "conllu_count": len(conllu)})
            issues[item["issue_type"]].append(item)

        for i, (tok, crow) in enumerate(zip(tokens, conllu), start=1):
            if not isinstance(tok, dict) or not isinstance(crow, dict):
                continue
            tv = norm_text(tok.get("v"))
            cv = norm_text(crow.get("form"))
            if tv and cv and tv != cv:
                item = issue_base("token_conllu_form_mismatch", meta, sentence)
                item.update({"position": i, "token_form": tv, "conllu_form": cv})
                issues[item["issue_type"]].append(item)

        pos_set = set(positions)
        for ch in chunks:
            if not isinstance(ch, dict):
                continue
            start = ch.get("i")
            end = ch.get("f")
            label = ch.get("t")
            if not isinstance(start, int) or not isinstance(end, int):
                continue
            if positions and (start < min(positions) or end > max(positions) or start > end):
                item = issue_base("chunk_span_out_of_range", meta, sentence)
                item.update({"chunk_label": label, "start": start, "end": end, "token_positions": positions})
                issues[item["issue_type"]].append(item)

        for tok in tokens:
            if not isinstance(tok, dict):
                continue
            form = norm_text(tok.get("v"))
            tag = norm_text(tok.get("t"))
            gloss = token_gloss(tok)
            position = tok.get("p")
            token_item_base = issue_base("", meta, sentence)
            token_item_base.update({"position": position, "token_form": form, "token_tag": tag, "token_gloss": gloss})

            if not form:
                item = dict(token_item_base)
                item["issue_type"] = "missing_token_form"
                issues[item["issue_type"]].append(item)
            if not tag and not tok.get("ec"):
                item = dict(token_item_base)
                item["issue_type"] = "missing_token_tag"
                issues[item["issue_type"]].append(item)
            if tok.get("ec") and not tag:
                item = dict(token_item_base)
                item["issue_type"] = "empty_category_without_tag"
                issues[item["issue_type"]].append(item)
            if form:
                token_records_by_form[form].append((tok, meta))

            splits = tok.get("splits", [])
            if splits is None:
                splits = []
            if not isinstance(splits, list):
                splits = []

            if not splits:
                # full omission only if this form is segmented somewhere else will be handled later
                pass

            for idx, sp in enumerate(splits, start=1):
                n_split += 1
                if not isinstance(sp, dict):
                    item = dict(token_item_base)
                    item["issue_type"] = "non_dict_split"
                    item["split_index"] = idx
                    item["split_raw"] = repr(sp)
                    issues[item["issue_type"]].append(item)
                    continue

                sv = norm_text(sp.get("v"))
                st = norm_text(sp.get("t"))
                sg = split_gloss(sp)

                if not sp:
                    item = dict(token_item_base)
                    item["issue_type"] = "empty_split_object"
                    item["split_index"] = idx
                    issues[item["issue_type"]].append(item)
                else:
                    if not sv:
                        item = dict(token_item_base)
                        item["issue_type"] = "missing_split_form"
                        item["split_index"] = idx
                        item["split_tag"] = st
                        issues[item["issue_type"]].append(item)
                    if not st:
                        item = dict(token_item_base)
                        item["issue_type"] = "missing_split_tag"
                        item["split_index"] = idx
                        item["split_form"] = sv
                        issues[item["issue_type"]].append(item)

                if sv:
                    morpheme_records_by_form[sv].append((sp, tok, meta, idx))

    # token-form level consistency
    for form, token_records in token_records_by_form.items():
        tags = sorted({norm_text(tok.get("t")) for tok, _ in token_records if norm_text(tok.get("t"))})
        token_glosses = sorted({norm_text(token_gloss(tok)) for tok, _ in token_records if norm_text(token_gloss(tok))})
        splitseqs = sorted({"|".join(split_signature(tok)) for tok, _ in token_records})
        splitformseqs = sorted({"|".join(split_forms_signature(tok)) for tok, _ in token_records})
        has_splits = [has_any_split_content(tok) for tok, _ in token_records]

        examples = [
            {
                "source_id": meta.get("source_id"),
                "source_file": meta.get("source_file"),
                "uid": meta["uid"],
                "text": meta["text"],
                "token_tag": tok.get("t"),
                "token_gloss": token_gloss(tok),
                "split_tags": list(split_signature(tok)),
                "split_forms": list(split_forms_signature(tok)),
            }
            for tok, meta in token_records
        ]

        if len(tags) > 1:
            issues["conflicting_token_tags_for_form"].append(
                {"issue_type": "conflicting_token_tags_for_form", "token_form": form, "token_tags": tags, "examples": examples}
            )

        if len(token_glosses) > 1:
            issues["conflicting_token_glosses_for_form"].append(
                {"issue_type": "conflicting_token_glosses_for_form", "token_form": form, "token_glosses": token_glosses, "examples": examples}
            )

        nonempty_splitseqs = [s for s in splitseqs if s]
        if len(set(nonempty_splitseqs)) > 1:
            issues["conflicting_split_tag_sequences_for_form"].append(
                {"issue_type": "conflicting_split_tag_sequences_for_form", "token_form": form, "split_tag_sequences": sorted(set(nonempty_splitseqs)), "examples": examples}
            )

        nonempty_splitformseqs = [s for s in splitformseqs if s]
        if len(set(nonempty_splitformseqs)) > 1:
            issues["conflicting_split_form_sequences_for_form"].append(
                {"issue_type": "conflicting_split_form_sequences_for_form", "token_form": form, "split_form_sequences": sorted(set(nonempty_splitformseqs)), "examples": examples}
            )

        if any(has_splits) and not all(has_splits):
            best = best_known_split_profile(token_records)
            for tok, meta in token_records:
                if not has_any_split_content(tok):
                    issues["token_without_splits_but_analyzed_elsewhere"].append(
                        {
                            "issue_type": "token_without_splits_but_analyzed_elsewhere",
                            "token_form": form,
                            "source_id": meta.get("source_id"),
                            "source_file": meta.get("source_file"),
                            "uid": meta["uid"],
                            "text": meta["text"],
                            "token_tag": tok.get("t"),
                            "expected_from_uid": safe_get(best, "meta", "uid"),
                            "expected_from_text": safe_get(best, "meta", "text"),
                            "expected_split_tags": list(split_signature(best.get("token", {}))),
                            "expected_split_forms": list(split_forms_signature(best.get("token", {}))),
                        }
                    )

        # same form, some splits missing tags although fuller analysis exists elsewhere
        has_fuller = any(
            all(norm_text(s.get("v")) and norm_text(s.get("t")) for s in (tok.get("splits", []) or []) if isinstance(s, dict))
            and bool(tok.get("splits"))
            for tok, _ in token_records
        )
        if has_fuller:
            best = best_known_split_profile(token_records)
            for tok, meta in token_records:
                splits = tok.get("splits", []) if isinstance(tok.get("splits"), list) else []
                if not splits:
                    continue
                incomplete = False
                for s in splits:
                    if isinstance(s, dict) and (not norm_text(s.get("v")) or not norm_text(s.get("t"))):
                        incomplete = True
                        break
                if incomplete:
                    issues["token_with_incomplete_splits_but_fuller_analysis_elsewhere"].append(
                        {
                            "issue_type": "token_with_incomplete_splits_but_fuller_analysis_elsewhere",
                            "token_form": form,
                            "source_id": meta.get("source_id"),
                            "source_file": meta.get("source_file"),
                            "uid": meta["uid"],
                            "text": meta["text"],
                            "split_tags_here": list(split_signature(tok)),
                            "split_forms_here": list(split_forms_signature(tok)),
                            "expected_from_uid": safe_get(best, "meta", "uid"),
                            "expected_from_text": safe_get(best, "meta", "text"),
                            "expected_split_tags": list(split_signature(best.get("token", {}))),
                            "expected_split_forms": list(split_forms_signature(best.get("token", {}))),
                        }
                    )

    # morpheme-form consistency
    for morph, morph_records in morpheme_records_by_form.items():
        tags = sorted({norm_text(sp.get("t")) for sp, _, _, _ in morph_records if norm_text(sp.get("t"))})
        glosses = sorted({norm_text(split_gloss(sp)) for sp, _, _, _ in morph_records if norm_text(split_gloss(sp))})
        examples = [
            {
                "source_id": meta.get("source_id"),
                "source_file": meta.get("source_file"),
                "uid": meta["uid"],
                "text": meta["text"],
                "host_token": tok.get("v"),
                "split_index": idx,
                "split_tag": sp.get("t"),
                "split_gloss": split_gloss(sp),
            }
            for sp, tok, meta, idx in morph_records
        ]

        if len(tags) > 1:
            issues["conflicting_morpheme_tags"].append(
                {"issue_type": "conflicting_morpheme_tags", "morpheme_form": morph, "split_tags": tags, "examples": examples}
            )
        if len(glosses) > 1:
            issues["conflicting_morpheme_glosses"].append(
                {"issue_type": "conflicting_morpheme_glosses", "morpheme_form": morph, "split_glosses": glosses, "examples": examples}
            )

        overlap = sorted(set(tags) & set(glosses))
        if overlap:
            issues["morpheme_tag_gloss_role_overlap"].append(
                {
                    "issue_type": "morpheme_tag_gloss_role_overlap",
                    "morpheme_form": morph,
                    "overlap_values": overlap,
                    "split_tags": tags,
                    "split_glosses": glosses,
                    "examples": examples,
                }
            )

        # missing morpheme tag or gloss where known elsewhere
        if tags:
            for sp, tok, meta, idx in morph_records:
                if not norm_text(sp.get("t")):
                    issues["missing_split_tag_but_known_for_same_morpheme"].append(
                        {
                            "issue_type": "missing_split_tag_but_known_for_same_morpheme",
                            "morpheme_form": morph,
                            "source_id": meta.get("source_id"),
                            "source_file": meta.get("source_file"),
                            "uid": meta["uid"],
                            "text": meta["text"],
                            "host_token": tok.get("v"),
                            "split_index": idx,
                            "known_tags_elsewhere": tags,
                        }
                    )
        if glosses:
            for sp, tok, meta, idx in morph_records:
                if not norm_text(split_gloss(sp)):
                    issues["missing_split_gloss_but_known_for_same_morpheme"].append(
                        {
                            "issue_type": "missing_split_gloss_but_known_for_same_morpheme",
                            "morpheme_form": morph,
                            "source_id": meta.get("source_id"),
                            "source_file": meta.get("source_file"),
                            "uid": meta["uid"],
                            "text": meta["text"],
                            "host_token": tok.get("v"),
                            "split_index": idx,
                            "known_glosses_elsewhere": glosses,
                        }
                    )

    source_counts = Counter(norm_text(record.get("source_id")) or "UNKNOWN" for record in records)

    summary = {
        "sources": dict(sorted(source_counts.items())),
        "sentences": n_sent,
        "tokens": n_tok,
        "splits": n_split,
        "issue_counts": {k: len(v) for k, v in sorted(issues.items())},
        "issue_total": sum(len(v) for v in issues.values()),
    }

    return {
        "summary": summary,
        "issues": dict(issues),
    }


def print_summary(report: Dict[str, Any], max_examples: int = 3) -> None:
    summary = report["summary"]
    issues = report["issues"]

    print("Kadiwéu JSON consistency report")
    print("=" * 80)
    print(f"Sentences: {summary['sentences']}")
    print(f"Tokens:    {summary['tokens']}")
    print(f"Splits:    {summary['splits']}")
    print(f"Issues:    {summary['issue_total']}")
    if summary.get("sources"):
        print("Sources:")
        for source_id, count in summary["sources"].items():
            print(f"  {source_id}: {count} sentence(s)")
    print()

    if not summary["issue_counts"]:
        print("No issues found.")
        return

    print("Issue counts")
    print("-" * 80)
    for kind, count in sorted(summary["issue_counts"].items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{count:>4}  {kind}")

    print()
    print("Sample issues")
    print("-" * 80)
    for kind, count in sorted(summary["issue_counts"].items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"\n[{kind}] total={count}")
        for item in issues[kind][:max_examples]:
            print(json.dumps(item, ensure_ascii=False, sort_keys=False))


def write_tsvs(report: Dict[str, Any], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for kind, rows in report["issues"].items():
        path = outdir / f"{kind}.tsv"

        all_fields = set()
        flat_rows: List[Dict[str, Any]] = []
        for row in rows:
            flat = {}
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    flat[k] = json.dumps(v, ensure_ascii=False, sort_keys=False)
                else:
                    flat[k] = v
            flat_rows.append(flat)
            all_fields.update(flat.keys())

        fieldnames = sorted(all_fields)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(flat_rows)


def validate_source_ids(json_paths: Sequence[str], source_ids: Optional[Sequence[str]]) -> List[str]:
    """Return one source identifier per input JSON file."""
    if not source_ids:
        return [Path(path).stem for path in json_paths]
    if len(source_ids) != len(json_paths):
        raise ValueError(
            f"received {len(source_ids)} --source-id value(s) for {len(json_paths)} JSON file(s); "
            "provide exactly one --source-id per input file, or omit --source-id to use file stems"
        )
    return list(source_ids)


def load_sentence_records(json_paths: Sequence[str], source_ids: Sequence[str]) -> List[Dict[str, Any]]:
    """Load all input JSON files and attach source provenance to every sentence record."""
    all_records: List[Dict[str, Any]] = []
    for ordinal, (json_path, source_id) in enumerate(zip(json_paths, source_ids), start=1):
        path = Path(json_path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        records = walk_collect_sentences(data)
        for record in records:
            record["source_id"] = source_id
            record["source_file"] = str(path)
            record["source_ordinal"] = ordinal
        all_records.extend(records)
    return all_records


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check omissions and inconsistencies in one or more Kadiwéu Tycho Brahe JSON dumps.")
    parser.add_argument("json_paths", nargs="+", help="Path(s) to Kadiwéu Tycho Brahe JSON dump(s)")
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help=(
            "Stable source identifier for the corresponding JSON file. "
            "Repeat once per input file, e.g. --source-id ped-gramm --source-id hil-data. "
            "If omitted, file stems are used."
        ),
    )
    parser.add_argument("--uid", help="Restrict analysis to one sentence UID")
    parser.add_argument("--text-contains", help="Restrict analysis to sentences whose text contains this string")
    parser.add_argument("--json-out", help="Write full report as JSON")
    parser.add_argument("--tsv-dir", help="Write one TSV file per issue type into this directory")
    parser.add_argument("--max-examples", type=int, default=3, help="Examples per issue type in stdout summary")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    try:
        source_ids = validate_source_ids(args.json_paths, args.source_ids)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    sentence_records = load_sentence_records(args.json_paths, source_ids)
    sentence_records = filter_sentences(sentence_records, uid=args.uid, text_contains=args.text_contains)

    if not sentence_records:
        print("No sentences matched the requested filters.", file=sys.stderr)
        return 1

    report = analyze(sentence_records)
    report["inputs"] = [
        {"source_id": source_id, "source_file": str(Path(json_path))}
        for json_path, source_id in zip(args.json_paths, source_ids)
    ]
    print_summary(report, max_examples=args.max_examples)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    if args.tsv_dir:
        write_tsvs(report, Path(args.tsv_dir))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
