#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Check gramatica-pedagogica.json for omissions and inconsistencies.

The script traverses the pedagogical grammar JSON, collects sentence objects,
and reports issues such as:
- missing token tags/forms
- missing split tags/forms/glosses
- inconsistent token tags or glosses for the same surface form
- inconsistent split-tag / split-form sequences for the same token form
- inconsistent morpheme tags or glosses for the same morpheme form
- overlap between the roles of tag and gloss for the same morpheme form
- tokens lacking splits although the same token is segmented elsewhere
- token/proto-CoNLL-U count and form mismatches
- chunk spans outside the token range

Usage:
    python3 check_kadiweu_json_consistency.py gramatica-pedagogica.json
    python3 check_kadiweu_json_consistency.py gramatica-pedagogica.json \
        --json-out kadiweu_consistency_report.json
    python3 check_kadiweu_json_consistency.py gramatica-pedagogica.json \
        --json-out kadiweu_consistency_report.json \
        --tsv-dir kadiweu_consistency_tsvs
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def safe_get(d: Any, *path: str, default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def norm_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def token_gloss(token: Dict[str, Any]) -> Optional[str]:
    return norm_text(safe_get(token, "attributes", "gloss-br"))


def split_gloss(split: Dict[str, Any]) -> Optional[str]:
    return norm_text(safe_get(split, "attributes", "gloss-br"))


def is_sentence_object(obj: Any) -> bool:
    return (
        isinstance(obj, dict)
        and isinstance(obj.get("text"), str)
        and isinstance(obj.get("struct"), dict)
        and any(k in obj["struct"] for k in ("tokens", "chunks", "conllu"))
    )


def walk_collect_sentences(obj: Any, path: str = "$") -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if isinstance(obj, dict):
        if is_sentence_object(obj):
            out.append({"path": path, "sentence": obj})
        for key, value in obj.items():
            out.extend(walk_collect_sentences(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            out.extend(walk_collect_sentences(item, f"{path}[{i}]"))
    return out


def split_signature(token: Dict[str, Any], field: str) -> Tuple[str, ...]:
    splits = token.get("splits", [])
    if not isinstance(splits, list) or not splits:
        return tuple()
    values: List[str] = []
    for sp in splits:
        if not isinstance(sp, dict):
            values.append("")
        else:
            values.append(norm_text(sp.get(field)) or "")
    return tuple(values)


def report_issue(bucket: Dict[str, List[Dict[str, Any]]], issue_type: str, **payload: Any) -> None:
    bucket[issue_type].append({"issue_type": issue_type, **payload})


def flatten_for_tsv(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def write_issue_tsvs(issues: Dict[str, List[Dict[str, Any]]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for issue_type, rows in sorted(issues.items()):
        if not rows:
            continue
        fieldnames = sorted({key for row in rows for key in row.keys()})
        tsv_path = out_dir / f"{issue_type}.tsv"
        with tsv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({key: flatten_for_tsv(row.get(key)) for key in fieldnames})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("json_file", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--tsv-dir", type=Path, help="Directory where per-issue TSV reports will be written")
    args = ap.parse_args()

    data = json.loads(args.json_file.read_text(encoding="utf-8"))
    sentence_records = walk_collect_sentences(data)

    issues: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    token_records_by_form: Dict[str, List[Tuple[Dict[str, Any], Dict[str, Any]]]] = defaultdict(list)
    morph_records_by_form: Dict[str, List[Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]]] = defaultdict(list)

    # pass 1: local checks + index token/morpheme occurrences
    for rec in sentence_records:
        sent = rec["sentence"]
        uid = sent.get("uid")
        text = sent.get("text")
        struct = sent.get("struct") if isinstance(sent.get("struct"), dict) else {}
        tokens = struct.get("tokens") if isinstance(struct.get("tokens"), list) else []
        conllu = struct.get("conllu") if isinstance(struct.get("conllu"), list) else []
        chunks = struct.get("chunks") if isinstance(struct.get("chunks"), list) else []

        if len(tokens) != len(conllu):
            report_issue(
                issues,
                "token_conllu_count_mismatch",
                uid=uid,
                text=text,
                path=rec["path"],
                token_count=len(tokens),
                conllu_count=len(conllu),
            )

        for i, (tok, col) in enumerate(zip(tokens, conllu), start=1):
            tok_form = norm_text(tok.get("v")) if isinstance(tok, dict) else None
            col_form = norm_text(col.get("form")) if isinstance(col, dict) else None
            if tok_form != col_form:
                report_issue(
                    issues,
                    "token_conllu_form_mismatch",
                    uid=uid,
                    text=text,
                    path=rec["path"],
                    position=i,
                    token_form=tok_form,
                    conllu_form=col_form,
                )

        positions = sorted(tok.get("p") for tok in tokens if isinstance(tok, dict) and isinstance(tok.get("p"), int))
        min_p = positions[0] if positions else None
        max_p = positions[-1] if positions else None
        for ch in chunks:
            if not isinstance(ch, dict):
                continue
            start = ch.get("i")
            end = ch.get("f")
            if min_p is None or max_p is None:
                continue
            if not isinstance(start, int) or not isinstance(end, int) or start < min_p or end > max_p or start > end:
                report_issue(
                    issues,
                    "chunk_span_out_of_range",
                    uid=uid,
                    text=text,
                    path=rec["path"],
                    chunk=ch,
                    token_range=[min_p, max_p],
                )

        for tok in tokens:
            if not isinstance(tok, dict):
                continue
            tok_form = norm_text(tok.get("v"))
            tok_tag = norm_text(tok.get("t"))
            splits = tok.get("splits") if isinstance(tok.get("splits"), list) else []

            if tok_form is None:
                report_issue(issues, "missing_token_form", uid=uid, text=text, path=rec["path"], token=tok)
                continue

            token_records_by_form[tok_form].append((tok, rec))

            if tok_tag is None:
                report_issue(
                    issues,
                    "missing_token_tag",
                    uid=uid,
                    text=text,
                    path=rec["path"],
                    host_token=tok_form,
                )

            if tok_form == "*T*" and tok_tag is None:
                report_issue(
                    issues,
                    "empty_category_without_tag",
                    uid=uid,
                    text=text,
                    path=rec["path"],
                    host_token=tok_form,
                )

            for j, sp in enumerate(splits, start=1):
                if not isinstance(sp, dict):
                    report_issue(
                        issues,
                        "empty_split_object",
                        uid=uid,
                        text=text,
                        path=rec["path"],
                        host_token=tok_form,
                        split_index=j,
                    )
                    continue
                sp_form = norm_text(sp.get("v"))
                sp_tag = norm_text(sp.get("t"))
                sp_gl = split_gloss(sp)
                if sp_form is None and sp_tag is None and sp_gl is None:
                    report_issue(
                        issues,
                        "empty_split_object",
                        uid=uid,
                        text=text,
                        path=rec["path"],
                        host_token=tok_form,
                        split_index=j,
                    )
                    continue
                if sp_form is None:
                    report_issue(
                        issues,
                        "missing_split_form",
                        uid=uid,
                        text=text,
                        path=rec["path"],
                        host_token=tok_form,
                        split_index=j,
                    )
                    continue
                morph_records_by_form[sp_form].append((sp, tok, rec))
                if sp_tag is None:
                    report_issue(
                        issues,
                        "missing_split_tag",
                        uid=uid,
                        text=text,
                        path=rec["path"],
                        host_token=tok_form,
                        split_index=j,
                        morpheme_form=sp_form,
                    )

    for tok_form, recs in sorted(token_records_by_form.items()):
        tags = sorted({norm_text(tok.get("t")) for tok, _ in recs if norm_text(tok.get("t"))})
        glosses = sorted({token_gloss(tok) for tok, _ in recs if token_gloss(tok)})
        tag_seqs = sorted({split_signature(tok, "t") for tok, _ in recs if split_signature(tok, "t")})
        form_seqs = sorted({split_signature(tok, "v") for tok, _ in recs if split_signature(tok, "v")})

        if len(tags) > 1:
            report_issue(
                issues,
                "conflicting_token_tags",
                token_form=tok_form,
                tags=tags,
                occurrences=[{"uid": r[1]["sentence"].get("uid"), "text": r[1]["sentence"].get("text"), "tag": norm_text(r[0].get("t"))} for r in recs],
            )
        if len(glosses) > 1:
            report_issue(
                issues,
                "conflicting_token_glosses",
                token_form=tok_form,
                glosses=glosses,
                occurrences=[{"uid": r[1]["sentence"].get("uid"), "text": r[1]["sentence"].get("text"), "gloss": token_gloss(r[0])} for r in recs if token_gloss(r[0])],
            )
        if len(tag_seqs) > 1:
            report_issue(
                issues,
                "conflicting_split_tag_sequences",
                token_form=tok_form,
                split_tag_sequences=[list(x) for x in tag_seqs],
            )
        if len(form_seqs) > 1:
            report_issue(
                issues,
                "conflicting_split_form_sequences",
                token_form=tok_form,
                split_form_sequences=[list(x) for x in form_seqs],
            )
        if any(split_signature(tok, "v") for tok, _ in recs) and any(not split_signature(tok, "v") for tok, _ in recs):
            report_issue(
                issues,
                "token_lacks_splits_but_analyzed_elsewhere",
                token_form=tok_form,
                missing_in=[{"uid": r[1]["sentence"].get("uid"), "text": r[1]["sentence"].get("text")} for r in recs if not split_signature(r[0], "v")],
                known_split_forms=[list(x) for x in form_seqs if x],
            )

    for morph_form, recs in sorted(morph_records_by_form.items()):
        tags = sorted({norm_text(sp.get("t")) for sp, _, _ in recs if norm_text(sp.get("t"))})
        glosses = sorted({split_gloss(sp) for sp, _, _ in recs if split_gloss(sp)})

        if len(tags) > 1:
            report_issue(
                issues,
                "conflicting_morpheme_tags",
                morpheme_form=morph_form,
                tags=tags,
                occurrences=[{
                    "uid": rec[2]["sentence"].get("uid"),
                    "text": rec[2]["sentence"].get("text"),
                    "host_token": norm_text(rec[1].get("v")),
                    "tag": norm_text(rec[0].get("t")),
                } for rec in recs],
            )
        if len(glosses) > 1:
            report_issue(
                issues,
                "conflicting_morpheme_glosses",
                morpheme_form=morph_form,
                glosses=glosses,
                occurrences=[{
                    "uid": rec[2]["sentence"].get("uid"),
                    "text": rec[2]["sentence"].get("text"),
                    "host_token": norm_text(rec[1].get("v")),
                    "gloss": split_gloss(rec[0]),
                } for rec in recs if split_gloss(rec[0])],
            )
        overlap = sorted(set(tags) & set(glosses))
        if overlap:
            report_issue(
                issues,
                "morpheme_tag_gloss_role_overlap",
                morpheme_form=morph_form,
                overlapping_values=overlap,
                tag_occurrences=[{
                    "uid": rec[2]["sentence"].get("uid"),
                    "text": rec[2]["sentence"].get("text"),
                    "host_token": norm_text(rec[1].get("v")),
                    "tag": norm_text(rec[0].get("t")),
                } for rec in recs if norm_text(rec[0].get("t")) in overlap],
                gloss_occurrences=[{
                    "uid": rec[2]["sentence"].get("uid"),
                    "text": rec[2]["sentence"].get("text"),
                    "host_token": norm_text(rec[1].get("v")),
                    "gloss": split_gloss(rec[0]),
                } for rec in recs if split_gloss(rec[0]) in overlap],
            )
        if glosses:
            for sp, tok, rec in recs:
                if split_gloss(sp) is None:
                    report_issue(
                        issues,
                        "missing_split_gloss_but_known_for_same_morpheme",
                        morpheme_form=morph_form,
                        uid=rec["sentence"].get("uid"),
                        text=rec["sentence"].get("text"),
                        host_token=norm_text(tok.get("v")),
                        known_glosses_elsewhere=glosses,
                    )

    counts = {k: len(v) for k, v in sorted(issues.items())}
    report = {
        "source_file": str(args.json_file),
        "sentence_count": len(sentence_records),
        "issue_counts": counts,
        "issues": dict(sorted(issues.items())),
    }

    print(f"Sentences checked: {len(sentence_records)}")
    for key, value in counts.items():
        print(f"{key}: {value}")

    if args.json_out:
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nWrote JSON report to {args.json_out}")

    if args.tsv_dir:
        write_issue_tsvs(issues, args.tsv_dir)
        print(f"Wrote TSV reports to {args.tsv_dir}")


if __name__ == "__main__":
    main()
