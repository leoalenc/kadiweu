#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate gold-derived linguistic override resources for the Kadiwéu UD converter.

This script is designed for the project layout:

kadiweu/
├── data/
│   ├── gramatica-pedagogica.json
│   ├── treebank/
│   │   └── kbc_unicamp-ud-test.conllu
│   └── resources/
│       ├── gold_derived_overrides.json
│       └── gold_derived_overrides_report.md
└── src/
    ├── kadiweu_json_to_conllu.py
    └── update_overrides_from_gold.py

If run from kadiweu/src/update_overrides_from_gold.py with no arguments, it uses
those default paths. Command-line arguments can still override them.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

JsonDict = Dict[str, Any]

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_GOLD_PATH = PROJECT_ROOT / "data" / "treebank" / "kbc_unicamp-ud-test.conllu"
DEFAULT_JSON_PATH = PROJECT_ROOT / "data" / "gramatica-pedagogica.json"
DEFAULT_OUT_JSON = PROJECT_ROOT / "data" / "resources" / "gold_derived_overrides.json"
DEFAULT_OUT_REPORT = PROJECT_ROOT / "data" / "resources" / "gold_derived_overrides_report.md"


def safe_get(d: Any, *path: str, default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def normalize_feats(feats: str) -> str:
    if not feats or feats == "_":
        return "_"
    parts = [p for p in feats.split("|") if p and p != "_"]
    if not parts:
        return "_"
    return "|".join(sorted(parts))


def extract_prontype(feats: str) -> Optional[str]:
    if not feats or feats == "_":
        return None
    for part in feats.split("|"):
        if part.startswith("PronType="):
            return part.split("=", 1)[1]
    return None


def json_key(*parts: str) -> str:
    return "\t".join(parts)


def most_common_with_share(counter: Counter) -> Tuple[Optional[str], int, int, float]:
    if not counter:
        return None, 0, 0, 0.0
    value, best = counter.most_common(1)[0]
    total = sum(counter.values())
    share = best / total if total else 0.0
    return value, best, total, share


def parse_conllu(path: Path) -> List[JsonDict]:
    sentences: List[JsonDict] = []
    comments: Dict[str, str] = {}
    tokens: List[JsonDict] = []

    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")

            if not line.strip():
                if comments or tokens:
                    sentences.append({"comments": comments, "tokens": tokens})
                comments = {}
                tokens = []
                continue

            if line.startswith("#"):
                m = re.match(r"#\s*([^=]+?)\s*=\s*(.*)", line)
                if m:
                    comments[m.group(1).strip()] = m.group(2).strip()
                continue

            cols = line.split("\t")
            if len(cols) != 10:
                continue

            tok_id = cols[0]
            if "-" in tok_id or "." in tok_id:
                continue

            tokens.append(
                {
                    "id": tok_id,
                    "form": cols[1],
                    "lemma": cols[2],
                    "upos": cols[3],
                    "xpos": cols[4],
                    "feats": normalize_feats(cols[5]),
                }
            )

    if comments or tokens:
        sentences.append({"comments": comments, "tokens": tokens})

    return sentences


def is_sentence_object(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    text = obj.get("text")
    struct = obj.get("struct")
    if not isinstance(text, str):
        return False
    if not isinstance(struct, dict):
        return False
    return any(k in struct for k in ("tokens", "chunks", "conllu"))


def walk_collect_sentences(obj: Any, path: str = "$") -> List[JsonDict]:
    out: List[JsonDict] = []
    if isinstance(obj, dict):
        if is_sentence_object(obj):
            out.append({"path": path, "sentence": obj})
        for key, value in obj.items():
            out.extend(walk_collect_sentences(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            out.extend(walk_collect_sentences(item, f"{path}[{i}]"))
    return out


def parse_json_sentences(path: Path) -> List[JsonDict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    collected = walk_collect_sentences(data)
    out: List[JsonDict] = []

    for rec in collected:
        sent = rec["sentence"]
        struct = sent.get("struct", {})
        raw_tokens = struct.get("tokens", [])
        if not isinstance(raw_tokens, list):
            raw_tokens = []

        toks = []
        for tok in raw_tokens:
            if not isinstance(tok, dict):
                continue
            p = tok.get("p")
            form = tok.get("v")
            raw_tag = tok.get("t")
            if not isinstance(p, int):
                continue
            toks.append(
                {
                    "p": p,
                    "form": str(form) if form is not None else "",
                    "raw_tag": str(raw_tag) if raw_tag is not None else "",
                }
            )

        toks.sort(key=lambda x: x["p"])

        out.append(
            {
                "sent_uid": sent.get("uid"),
                "sent_id": sent.get("sent_id"),
                "text": sent.get("text", ""),
                "tokens": toks,
            }
        )

    return out


def index_json_sentences(sentences: List[JsonDict]) -> Tuple[Dict[str, JsonDict], Dict[str, JsonDict]]:
    by_uid: Dict[str, JsonDict] = {}
    by_text: Dict[str, JsonDict] = {}

    for s in sentences:
        uid = s.get("sent_uid")
        text = s.get("text")
        if isinstance(uid, str) and uid:
            by_uid[uid] = s
        if isinstance(text, str) and text:
            by_text[text] = s

    return by_uid, by_text


def filter_gold_learning_tokens(tokens: Iterable[JsonDict]) -> List[JsonDict]:
    return [t for t in tokens if t.get("upos") != "PUNCT"]


def align_gold_with_json(
    gold_sentences: List[JsonDict],
    json_by_uid: Dict[str, JsonDict],
    json_by_text: Dict[str, JsonDict],
) -> Tuple[List[Tuple[JsonDict, JsonDict]], List[JsonDict]]:
    aligned: List[Tuple[JsonDict, JsonDict]] = []
    issues: List[JsonDict] = []

    for gs in gold_sentences:
        comments = gs.get("comments", {})
        sent_uid = comments.get("sent_uid")
        text_orig = comments.get("text_orig")
        text = comments.get("text")

        js = None
        if sent_uid and sent_uid in json_by_uid:
            js = json_by_uid[sent_uid]
        elif text_orig and text_orig in json_by_text:
            js = json_by_text[text_orig]
        elif text and text.rstrip(".") in json_by_text:
            js = json_by_text[text.rstrip(".")]

        if js is None:
            issues.append(
                {
                    "type": "sentence_not_aligned",
                    "sent_id": comments.get("sent_id"),
                    "sent_uid": sent_uid,
                    "text": text,
                }
            )
            continue

        gold_tok = filter_gold_learning_tokens(gs["tokens"])
        json_tok = js["tokens"]

        if len(gold_tok) != len(json_tok):
            issues.append(
                {
                    "type": "token_count_mismatch",
                    "sent_id": comments.get("sent_id"),
                    "sent_uid": sent_uid,
                    "gold_count": len(gold_tok),
                    "json_count": len(json_tok),
                    "gold_forms": [t["form"] for t in gold_tok],
                    "json_forms": [t["form"] for t in json_tok],
                }
            )
            continue

        form_mismatches = []
        for gt, jt in zip(gold_tok, json_tok):
            if gt["form"] != jt["form"]:
                form_mismatches.append((gt["form"], jt["form"]))

        if form_mismatches:
            issues.append(
                {
                    "type": "token_form_mismatch",
                    "sent_id": comments.get("sent_id"),
                    "sent_uid": sent_uid,
                    "mismatches": form_mismatches,
                }
            )

        aligned.append((gs, js))

    return aligned, issues


def learn_overrides(
    gold_sentences: List[JsonDict],
    aligned_pairs: List[Tuple[JsonDict, JsonDict]],
    lemma_min_count: int,
    lemma_min_share: float,
    feats_min_count: int,
    feats_min_share: float,
    pron_min_count: int,
    pron_min_share: float,
    tag_pron_min_count: int,
    tag_pron_min_share: float,
) -> JsonDict:
    lemma_counts: Dict[Tuple[str, str], Counter] = defaultdict(Counter)
    feats_counts: Dict[Tuple[str, str], Counter] = defaultdict(Counter)
    pron_counts: Dict[Tuple[str, str], Counter] = defaultdict(Counter)
    tag_pron_counts: Dict[Tuple[str, str], Counter] = defaultdict(Counter)

    review: Dict[str, List[JsonDict]] = {
        "ambiguous_lemmas": [],
        "ambiguous_feats": [],
        "ambiguous_prontype": [],
        "ambiguous_tag_to_prontype": [],
        "low_evidence_lemmas": [],
        "low_evidence_feats": [],
        "low_evidence_prontype": [],
        "low_evidence_tag_to_prontype": [],
        "json_alignment_issues": [],
    }

    for sent in gold_sentences:
        for tok in filter_gold_learning_tokens(sent["tokens"]):
            form = tok["form"]
            upos = tok["upos"]
            lemma = tok["lemma"]
            feats = tok["feats"]
            pron = extract_prontype(feats)

            lemma_counts[(form, upos)][lemma] += 1
            feats_counts[(form, upos)][feats] += 1

            if pron is not None and upos in {"DET", "PRON", "ADV"}:
                pron_counts[(form, upos)][pron] += 1

    for gs, js in aligned_pairs:
        gold_tok = filter_gold_learning_tokens(gs["tokens"])
        json_tok = js["tokens"]

        for gt, jt in zip(gold_tok, json_tok):
            pron = extract_prontype(gt["feats"])
            if pron is None:
                continue
            upos = gt["upos"]
            raw_tag = jt["raw_tag"]
            if upos not in {"DET", "PRON", "ADV"}:
                continue
            if not raw_tag:
                continue
            tag_pron_counts[(raw_tag, upos)][pron] += 1

    lemma_overrides: Dict[str, str] = {}
    form_feat_overrides: Dict[str, str] = {}
    prontype_overrides: Dict[str, str] = {}
    tag_to_default_prontype: Dict[str, str] = {}

    for (form, upos), counter in sorted(lemma_counts.items()):
        value, best, total, share = most_common_with_share(counter)
        rec = {
            "form": form,
            "upos": upos,
            "counts": dict(counter),
            "best": value,
            "best_count": best,
            "total": total,
            "share": round(share, 4),
        }
        if total < lemma_min_count:
            review["low_evidence_lemmas"].append(rec)
        elif share < lemma_min_share:
            review["ambiguous_lemmas"].append(rec)
        else:
            lemma_overrides[form] = value

    for (form, upos), counter in sorted(feats_counts.items()):
        value, best, total, share = most_common_with_share(counter)
        rec = {
            "form": form,
            "upos": upos,
            "counts": dict(counter),
            "best": value,
            "best_count": best,
            "total": total,
            "share": round(share, 4),
        }
        if total < feats_min_count:
            review["low_evidence_feats"].append(rec)
        elif share < feats_min_share:
            review["ambiguous_feats"].append(rec)
        else:
            form_feat_overrides[form] = value

    for (form, upos), counter in sorted(pron_counts.items()):
        value, best, total, share = most_common_with_share(counter)
        rec = {
            "form": form,
            "upos": upos,
            "counts": dict(counter),
            "best": value,
            "best_count": best,
            "total": total,
            "share": round(share, 4),
        }
        if total < pron_min_count:
            review["low_evidence_prontype"].append(rec)
        elif share < pron_min_share:
            review["ambiguous_prontype"].append(rec)
        else:
            prontype_overrides[json_key(form, upos)] = value

    for (raw_tag, upos), counter in sorted(tag_pron_counts.items()):
        value, best, total, share = most_common_with_share(counter)
        rec = {
            "raw_tag": raw_tag,
            "upos": upos,
            "counts": dict(counter),
            "best": value,
            "best_count": best,
            "total": total,
            "share": round(share, 4),
        }
        if total < tag_pron_min_count:
            review["low_evidence_tag_to_prontype"].append(rec)
        elif share < tag_pron_min_share:
            review["ambiguous_tag_to_prontype"].append(rec)
        else:
            tag_to_default_prontype[json_key(raw_tag, upos)] = value

    return {
        "lemma_overrides": dict(sorted(lemma_overrides.items())),
        "form_feat_overrides": dict(sorted(form_feat_overrides.items())),
        "prontype_overrides": dict(sorted(prontype_overrides.items())),
        "tag_to_default_prontype": dict(sorted(tag_to_default_prontype.items())),
        "review": review,
    }


def short_preview(items: List[JsonDict], limit: int = 15) -> str:
    if not items:
        return "_None_"
    lines = []
    for item in items[:limit]:
        lines.append(f"- `{json.dumps(item, ensure_ascii=False, sort_keys=True)}`")
    if len(items) > limit:
        lines.append(f"- ... and {len(items) - limit} more")
    return "\n".join(lines)


def build_report(resource: JsonDict, gold_count: int, json_count: int, aligned_count: int) -> str:
    review = resource["review"]
    sections = [
        "# Gold-derived overrides report",
        "",
        "## Summary",
        "",
        f"- Gold sentences: **{gold_count}**",
        f"- JSON sentences: **{json_count}**",
        f"- Aligned sentence pairs: **{aligned_count}**",
        f"- `lemma_overrides`: **{len(resource['lemma_overrides'])}**",
        f"- `form_feat_overrides`: **{len(resource['form_feat_overrides'])}**",
        f"- `prontype_overrides`: **{len(resource['prontype_overrides'])}**",
        f"- `tag_to_default_prontype`: **{len(resource['tag_to_default_prontype'])}**",
        "",
        "## Review items",
        "",
        f"### json_alignment_issues ({len(review['json_alignment_issues'])})",
        short_preview(review["json_alignment_issues"]),
        "",
        f"### ambiguous_lemmas ({len(review['ambiguous_lemmas'])})",
        short_preview(review["ambiguous_lemmas"]),
        "",
        f"### ambiguous_feats ({len(review['ambiguous_feats'])})",
        short_preview(review["ambiguous_feats"]),
        "",
        f"### ambiguous_prontype ({len(review['ambiguous_prontype'])})",
        short_preview(review["ambiguous_prontype"]),
        "",
        f"### ambiguous_tag_to_prontype ({len(review['ambiguous_tag_to_prontype'])})",
        short_preview(review["ambiguous_tag_to_prontype"]),
        "",
        f"### low_evidence_lemmas ({len(review['low_evidence_lemmas'])})",
        short_preview(review["low_evidence_lemmas"]),
        "",
        f"### low_evidence_feats ({len(review['low_evidence_feats'])})",
        short_preview(review["low_evidence_feats"]),
        "",
        f"### low_evidence_prontype ({len(review['low_evidence_prontype'])})",
        short_preview(review["low_evidence_prontype"]),
        "",
        f"### low_evidence_tag_to_prontype ({len(review['low_evidence_tag_to_prontype'])})",
        short_preview(review["low_evidence_tag_to_prontype"]),
        "",
        "## Notes",
        "",
        "- `FORM_FEAT_OVERRIDES` are currently learned directly from stable gold bundles.",
        "- In a later step, this can be made residual relative to converter heuristics.",
        "- Sentence alignment prefers `sent_uid`, then falls back to `text_orig` / `text`.",
        "- Token alignment ignores punctuation and MWT lines.",
        "",
    ]
    return "\n".join(sections)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate gold-derived Kadiwéu converter overrides."
    )
    parser.add_argument(
        "--gold",
        type=Path,
        default=DEFAULT_GOLD_PATH,
        help=f"Gold CoNLL-U file (default: {DEFAULT_GOLD_PATH})",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON_PATH,
        help=f"Pedagogical JSON file (default: {DEFAULT_JSON_PATH})",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=DEFAULT_OUT_JSON,
        help=f"Output JSON resource file (default: {DEFAULT_OUT_JSON})",
    )
    parser.add_argument(
        "--out-report",
        type=Path,
        default=DEFAULT_OUT_REPORT,
        help=f"Output Markdown report file (default: {DEFAULT_OUT_REPORT})",
    )
    parser.add_argument("--lemma-min-count", type=int, default=2)
    parser.add_argument("--lemma-min-share", type=float, default=0.80)
    parser.add_argument("--feats-min-count", type=int, default=2)
    parser.add_argument("--feats-min-share", type=float, default=0.90)
    parser.add_argument("--pron-min-count", type=int, default=2)
    parser.add_argument("--pron-min-share", type=float, default=0.90)
    parser.add_argument("--tag-pron-min-count", type=int, default=5)
    parser.add_argument("--tag-pron-min-share", type=float, default=0.90)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    gold_sentences = parse_conllu(args.gold)
    json_sentences = parse_json_sentences(args.json)
    json_by_uid, json_by_text = index_json_sentences(json_sentences)

    aligned_pairs, alignment_issues = align_gold_with_json(
        gold_sentences,
        json_by_uid,
        json_by_text,
    )

    resource = learn_overrides(
        gold_sentences=gold_sentences,
        aligned_pairs=aligned_pairs,
        lemma_min_count=args.lemma_min_count,
        lemma_min_share=args.lemma_min_share,
        feats_min_count=args.feats_min_count,
        feats_min_share=args.feats_min_share,
        pron_min_count=args.pron_min_count,
        pron_min_share=args.pron_min_share,
        tag_pron_min_count=args.tag_pron_min_count,
        tag_pron_min_share=args.tag_pron_min_share,
    )

    resource["metadata"] = {
        "gold_file": str(args.gold),
        "json_file": str(args.json),
        "gold_sentence_count": len(gold_sentences),
        "json_sentence_count": len(json_sentences),
        "aligned_sentence_count": len(aligned_pairs),
        "thresholds": {
            "lemma_min_count": args.lemma_min_count,
            "lemma_min_share": args.lemma_min_share,
            "feats_min_count": args.feats_min_count,
            "feats_min_share": args.feats_min_share,
            "pron_min_count": args.pron_min_count,
            "pron_min_share": args.pron_min_share,
            "tag_pron_min_count": args.tag_pron_min_count,
            "tag_pron_min_share": args.tag_pron_min_share,
        },
    }

    resource["review"]["json_alignment_issues"] = alignment_issues

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.parent.mkdir(parents=True, exist_ok=True)

    with args.out_json.open("w", encoding="utf-8") as f:
        json.dump(resource, f, ensure_ascii=False, indent=2, sort_keys=True)

    report = build_report(
        resource=resource,
        gold_count=len(gold_sentences),
        json_count=len(json_sentences),
        aligned_count=len(aligned_pairs),
    )
    with args.out_report.open("w", encoding="utf-8") as f:
        f.write(report)

    print(f"Wrote JSON resource to: {args.out_json}", file=sys.stderr)
    print(f"Wrote report to:        {args.out_report}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
