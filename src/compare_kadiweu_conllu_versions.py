#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compare two draft CoNLL-U files against a gold CoNLL-U file.

Purpose
-------
This script is designed for small-treebank conversion work, where aggregate
scores are helpful but not sufficient. It evaluates an old and a new draft
against the same gold file and reports:

- sentence coverage and alignment by sent_id
- tokenization and MWT agreement
- column-wise accuracy for FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL
- UAS and LAS
- changes between old and new relative to gold
- per-token error details for manual inspection
- optional targeted reports for selected sentence ids
- optional filtered CoNLL-U subsets restricted to the sentence ids present in gold

The script aligns sentences by sent_id, not by order. Gold is treated as the
reference inventory of sentences to compare. If old and new contain more
sentences than gold, only the sentences present in gold are scored. Extra
sentences in old/new are reported separately and can optionally be exported as
filtered subsets.

Definitions
-----------
- FEATS exact match: feature bundles are normalized and compared as sets.
- UAS: HEAD correct.
- LAS: HEAD and DEPREL correct.
- Tokenization exact: sequence of syntactic words (integer ids only) matches.
- MWT exact: set of multiword-token intervals/forms matches.

Notes
-----
- Empty nodes are ignored.
- Multiword token lines are evaluated separately from syntactic words.
- Metrics are computed only on aligned sentences whose token counts match.
  Tokenization mismatches are reported separately and excluded from token-level
  scoring, because token-by-token comparison would be unreliable there.

Usage
-----
Basic:
    python3 compare_kadiweu_conllu_versions.py gold.conllu old.conllu new.conllu

Write detailed outputs:
    python3 compare_kadiweu_conllu_versions.py gold.conllu old.conllu new.conllu \
        --outdir compare_report

Also export filtered subsets containing only gold sentence ids:
    python3 compare_kadiweu_conllu_versions.py gold.conllu old.conllu new.conllu \
        --outdir compare_report --write-filtered-subsets

Inspect only selected sentence ids:
    python3 compare_kadiweu_conllu_versions.py gold.conllu old.conllu new.conllu \
        --focus-sent-id ped-gramm-11 --focus-sent-id ped-gramm-15

Ignore FORM in scoring (normally do not do this):
    python3 compare_kadiweu_conllu_versions.py gold.conllu old.conllu new.conllu \
        --ignore-form
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


SENT_ID_RE = re.compile(r"^#\s*sent_id\s*=\s*(.+?)\s*$")
TEXT_RE = re.compile(r"^#\s*text\s*=\s*(.+?)\s*$")


@dataclass
class Token:
    raw_id: str
    id_type: str  # int, mwt, empty
    id_int: Optional[int]
    form: str
    lemma: str
    upos: str
    xpos: str
    feats: str
    head: str
    deprel: str
    deps: str
    misc: str


@dataclass
class Sentence:
    sent_id: str
    comments: List[str] = field(default_factory=list)
    text: Optional[str] = None
    tokens: List[Token] = field(default_factory=list)

    @property
    def word_tokens(self) -> List[Token]:
        return [t for t in self.tokens if t.id_type == "int"]

    @property
    def mwt_tokens(self) -> List[Token]:
        return [t for t in self.tokens if t.id_type == "mwt"]


@dataclass
class MetricCounts:
    correct: int = 0
    total: int = 0

    def add(self, ok: bool) -> None:
        self.total += 1
        if ok:
            self.correct += 1

    @property
    def acc(self) -> float:
        return (self.correct / self.total) if self.total else float("nan")


def parse_id(raw_id: str) -> Tuple[str, Optional[int]]:
    if "-" in raw_id:
        return "mwt", None
    if "." in raw_id:
        return "empty", None
    return "int", int(raw_id)


def normalize_feats(feats: str) -> str:
    feats = feats.strip()
    if not feats or feats == "_":
        return "_"
    parts = [p.strip() for p in feats.split("|") if p.strip()]
    kv = []
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            vals = ",".join(sorted(x for x in v.split(",") if x))
            kv.append((k, vals))
        else:
            kv.append((part, ""))
    kv.sort(key=lambda x: (x[0], x[1]))
    return "|".join(f"{k}={v}" if v else k for k, v in kv) or "_"


def normalize_deprel(rel: str) -> str:
    return rel.strip()


def read_conllu(path: Path) -> Dict[str, Sentence]:
    sentences: Dict[str, Sentence] = {}
    comments: List[str] = []
    rows: List[str] = []

    def flush() -> None:
        nonlocal comments, rows
        if not comments and not rows:
            return
        sent_id = None
        text = None
        for line in comments:
            m = SENT_ID_RE.match(line)
            if m:
                sent_id = m.group(1)
            m = TEXT_RE.match(line)
            if m:
                text = m.group(1)
        if sent_id is None:
            raise ValueError(f"Sentence without sent_id in {path}")
        if sent_id in sentences:
            raise ValueError(f"Duplicate sent_id {sent_id!r} in {path}")
        sent = Sentence(sent_id=sent_id, comments=list(comments), text=text)
        for row in rows:
            cols = row.split("\t")
            if len(cols) != 10:
                raise ValueError(f"Expected 10 columns in {path}, got {len(cols)}: {row}")
            raw_id = cols[0]
            id_type, id_int = parse_id(raw_id)
            sent.tokens.append(
                Token(
                    raw_id=raw_id,
                    id_type=id_type,
                    id_int=id_int,
                    form=cols[1],
                    lemma=cols[2],
                    upos=cols[3],
                    xpos=cols[4],
                    feats=cols[5],
                    head=cols[6],
                    deprel=cols[7],
                    deps=cols[8],
                    misc=cols[9],
                )
            )
        sentences[sent_id] = sent
        comments = []
        rows = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                flush()
                continue
            if line.startswith("#"):
                comments.append(line)
            else:
                rows.append(line)
        flush()
    return sentences


def serialize_sentence(sent: Sentence) -> str:
    lines = list(sent.comments)
    for tok in sent.tokens:
        lines.append(
            "\t".join(
                [
                    tok.raw_id,
                    tok.form,
                    tok.lemma,
                    tok.upos,
                    tok.xpos,
                    tok.feats,
                    tok.head,
                    tok.deprel,
                    tok.deps,
                    tok.misc,
                ]
            )
        )
    return "\n".join(lines) + "\n\n"


def write_filtered_conllu(path: Path, sentences: Dict[str, Sentence], sent_ids: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for sent_id in sent_ids:
            sent = sentences.get(sent_id)
            if sent is None:
                continue
            f.write(serialize_sentence(sent))


def mwt_signature(sent: Sentence) -> List[Tuple[str, str]]:
    return [(t.raw_id, t.form) for t in sent.mwt_tokens]


def word_signature(sent: Sentence) -> List[str]:
    return [t.form for t in sent.word_tokens]


def token_count_match(a: Sentence, b: Sentence) -> bool:
    return len(a.word_tokens) == len(b.word_tokens)


def safe_pct(x: float) -> str:
    if math.isnan(x):
        return "NA"
    return f"{100*x:.2f}"


def compare_token_columns(gold: Token, pred: Token, ignore_form: bool = False) -> Dict[str, bool]:
    result = {
        "FORM": True if ignore_form else (gold.form == pred.form),
        "LEMMA": gold.lemma == pred.lemma,
        "UPOS": gold.upos == pred.upos,
        "XPOS": gold.xpos == pred.xpos,
        "FEATS": normalize_feats(gold.feats) == normalize_feats(pred.feats),
        "HEAD": gold.head == pred.head,
        "DEPREL": normalize_deprel(gold.deprel) == normalize_deprel(pred.deprel),
    }
    result["UAS"] = result["HEAD"]
    result["LAS"] = result["HEAD"] and result["DEPREL"]
    return result


def init_metric_dict(ignore_form: bool = False) -> Dict[str, MetricCounts]:
    metrics = ["LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "UAS", "LAS"]
    if not ignore_form:
        metrics = ["FORM"] + metrics
    return {m: MetricCounts() for m in metrics}


def update_metrics(metric_dict: Dict[str, MetricCounts], column_results: Dict[str, bool], ignore_form: bool = False) -> None:
    for metric, counts in metric_dict.items():
        if metric == "FORM" and ignore_form:
            continue
        counts.add(column_results[metric])


def metric_table(old_metrics: Dict[str, MetricCounts], new_metrics: Dict[str, MetricCounts]) -> List[Dict[str, object]]:
    rows = []
    for key in old_metrics.keys():
        old_acc = old_metrics[key].acc
        new_acc = new_metrics[key].acc
        delta = (new_acc - old_acc) if (not math.isnan(old_acc) and not math.isnan(new_acc)) else float("nan")
        rows.append(
            {
                "metric": key,
                "old_correct": old_metrics[key].correct,
                "old_total": old_metrics[key].total,
                "old_acc": old_acc,
                "new_correct": new_metrics[key].correct,
                "new_total": new_metrics[key].total,
                "new_acc": new_acc,
                "delta": delta,
            }
        )
    return rows


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold", type=Path)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--outdir", type=Path, default=None, help="Directory for CSV/JSON reports")
    parser.add_argument("--focus-sent-id", action="append", default=[], help="Repeatable sent_id for focused reporting")
    parser.add_argument("--ignore-form", action="store_true", help="Do not score FORM")
    parser.add_argument(
        "--write-filtered-subsets",
        action="store_true",
        help="Write gold/old/new CoNLL-U subsets restricted to the sentence ids present in gold",
    )
    args = parser.parse_args(argv)

    gold = read_conllu(args.gold)
    old = read_conllu(args.old)
    new = read_conllu(args.new)

    gold_ids = set(gold)
    old_ids = set(old)
    new_ids = set(new)

    gold_ordered_ids = list(gold.keys())
    gold_present_in_old = [sid for sid in gold_ordered_ids if sid in old]
    gold_present_in_new = [sid for sid in gold_ordered_ids if sid in new]
    common_ids = [sid for sid in gold_ordered_ids if sid in old and sid in new]
    missing_old = [sid for sid in gold_ordered_ids if sid not in old]
    missing_new = [sid for sid in gold_ordered_ids if sid not in new]
    extra_old = sorted(old_ids - gold_ids)
    extra_new = sorted(new_ids - gold_ids)

    old_metrics = init_metric_dict(ignore_form=args.ignore_form)
    new_metrics = init_metric_dict(ignore_form=args.ignore_form)

    summary_rows: List[Dict[str, object]] = []
    token_diff_rows: List[Dict[str, object]] = []
    sentence_issue_rows: List[Dict[str, object]] = []
    improvement_counter = Counter()

    for sent_id in common_ids:
        g = gold[sent_id]
        o = old[sent_id]
        n = new[sent_id]

        old_tok_match = word_signature(g) == word_signature(o)
        new_tok_match = word_signature(g) == word_signature(n)
        old_mwt_match = mwt_signature(g) == mwt_signature(o)
        new_mwt_match = mwt_signature(g) == mwt_signature(n)
        old_count_match = token_count_match(g, o)
        new_count_match = token_count_match(g, n)

        summary_rows.append(
            {
                "sent_id": sent_id,
                "text": g.text or "",
                "gold_word_count": len(g.word_tokens),
                "old_word_count": len(o.word_tokens),
                "new_word_count": len(n.word_tokens),
                "old_tokenization_exact": old_tok_match,
                "new_tokenization_exact": new_tok_match,
                "old_mwt_exact": old_mwt_match,
                "new_mwt_exact": new_mwt_match,
                "old_text": o.text or "",
                "new_text": n.text or "",
            }
        )

        if not old_count_match or not new_count_match:
            sentence_issue_rows.append(
                {
                    "sent_id": sent_id,
                    "issue": "token-count-mismatch",
                    "gold_word_count": len(g.word_tokens),
                    "old_word_count": len(o.word_tokens),
                    "new_word_count": len(n.word_tokens),
                    "gold_mwt": json.dumps(mwt_signature(g), ensure_ascii=False),
                    "old_mwt": json.dumps(mwt_signature(o), ensure_ascii=False),
                    "new_mwt": json.dumps(mwt_signature(n), ensure_ascii=False),
                    "text": g.text or "",
                }
            )
            continue

        for idx, (gt, ot, nt) in enumerate(zip(g.word_tokens, o.word_tokens, n.word_tokens), start=1):
            old_cols = compare_token_columns(gt, ot, ignore_form=args.ignore_form)
            new_cols = compare_token_columns(gt, nt, ignore_form=args.ignore_form)
            update_metrics(old_metrics, old_cols, ignore_form=args.ignore_form)
            update_metrics(new_metrics, new_cols, ignore_form=args.ignore_form)

            for metric in old_metrics.keys():
                old_ok = old_cols[metric]
                new_ok = new_cols[metric]
                if old_ok == new_ok:
                    continue
                change = "improved" if ((not old_ok) and new_ok) else "regressed"
                improvement_counter[f"{metric}:{change}"] += 1
                token_diff_rows.append(
                    {
                        "sent_id": sent_id,
                        "token_index": idx,
                        "token_id": gt.raw_id,
                        "gold_form": gt.form,
                        "metric": metric,
                        "change": change,
                        "gold_value": {
                            "FORM": gt.form,
                            "LEMMA": gt.lemma,
                            "UPOS": gt.upos,
                            "XPOS": gt.xpos,
                            "FEATS": normalize_feats(gt.feats),
                            "HEAD": gt.head,
                            "DEPREL": gt.deprel,
                            "UAS": gt.head,
                            "LAS": f"{gt.head}|{gt.deprel}",
                        }[metric],
                        "old_value": {
                            "FORM": ot.form,
                            "LEMMA": ot.lemma,
                            "UPOS": ot.upos,
                            "XPOS": ot.xpos,
                            "FEATS": normalize_feats(ot.feats),
                            "HEAD": ot.head,
                            "DEPREL": ot.deprel,
                            "UAS": ot.head,
                            "LAS": f"{ot.head}|{ot.deprel}",
                        }[metric],
                        "new_value": {
                            "FORM": nt.form,
                            "LEMMA": nt.lemma,
                            "UPOS": nt.upos,
                            "XPOS": nt.xpos,
                            "FEATS": normalize_feats(nt.feats),
                            "HEAD": nt.head,
                            "DEPREL": nt.deprel,
                            "UAS": nt.head,
                            "LAS": f"{nt.head}|{nt.deprel}",
                        }[metric],
                    }
                )

    metric_rows = metric_table(old_metrics, new_metrics)

    corpus_summary = {
        "gold_sentences": len(gold_ids),
        "old_sentences": len(old_ids),
        "new_sentences": len(new_ids),
        "gold_present_in_old": len(gold_present_in_old),
        "gold_present_in_new": len(gold_present_in_new),
        "common_sentences": len(common_ids),
        "missing_old_count": len(missing_old),
        "missing_new_count": len(missing_new),
        "extra_old_count": len(extra_old),
        "extra_new_count": len(extra_new),
        "missing_old": missing_old,
        "missing_new": missing_new,
        "extra_old": extra_old,
        "extra_new": extra_new,
        "sentence_issues": len(sentence_issue_rows),
        "token_diffs": len(token_diff_rows),
        "improvement_counter": dict(improvement_counter),
    }

    print("CoNLL-U version comparison")
    print("=" * 80)
    print(f"Gold sentences:                 {len(gold_ids)}")
    print(f"Old sentences:                  {len(old_ids)}")
    print(f"New sentences:                  {len(new_ids)}")
    print(f"Gold ids present in old:        {len(gold_present_in_old)}")
    print(f"Gold ids present in new:        {len(gold_present_in_new)}")
    print(f"Compared in all three files:    {len(common_ids)}")
    print()
    if missing_old:
        print(f"Missing in old ({len(missing_old)}): {', '.join(missing_old[:10])}{' ...' if len(missing_old) > 10 else ''}")
    if missing_new:
        print(f"Missing in new ({len(missing_new)}): {', '.join(missing_new[:10])}{' ...' if len(missing_new) > 10 else ''}")
    if extra_old:
        print(f"Extra in old ({len(extra_old)}): {', '.join(extra_old[:10])}{' ...' if len(extra_old) > 10 else ''}")
    if extra_new:
        print(f"Extra in new ({len(extra_new)}): {', '.join(extra_new[:10])}{' ...' if len(extra_new) > 10 else ''}")
    if sentence_issue_rows:
        print(f"Sentence-level alignment/tokenization issues: {len(sentence_issue_rows)}")
    print()

    print("Aggregate metrics")
    print("-" * 80)
    print(f"{'Metric':<8} {'Old':>10} {'New':>10} {'Delta(pp)':>12} {'Old corr/total':>18} {'New corr/total':>18}")
    for row in metric_rows:
        delta_pp = "NA" if math.isnan(row["delta"]) else f"{100*row['delta']:+.2f}"
        print(
            f"{row['metric']:<8} {safe_pct(row['old_acc']):>10} {safe_pct(row['new_acc']):>10} {delta_pp:>12} "
            f"{row['old_correct']}/{row['old_total']:>10} {row['new_correct']}/{row['new_total']:>10}"
        )
    print()

    if improvement_counter:
        print("Changed token decisions relative to gold")
        print("-" * 80)
        for key in sorted(improvement_counter):
            print(f"{key}: {improvement_counter[key]}")
        print()

    if args.focus_sent_id:
        print("Focused sentence summaries")
        print("-" * 80)
        focus_ids = [sid for sid in args.focus_sent_id if sid in gold]
        for sid in focus_ids:
            g = gold.get(sid)
            o = old.get(sid)
            n = new.get(sid)
            print(f"{sid}")
            print(f"  Gold text: {g.text if g else ''}")
            if o:
                print(f"  Old words: {len(o.word_tokens)}  MWT: {mwt_signature(o)}")
            else:
                print("  Old: missing")
            if n:
                print(f"  New words: {len(n.word_tokens)}  MWT: {mwt_signature(n)}")
            else:
                print("  New: missing")
            if g and o and n and len(g.word_tokens) == len(o.word_tokens) == len(n.word_tokens):
                for gt, ot, nt in zip(g.word_tokens, o.word_tokens, n.word_tokens):
                    changed = []
                    for metric in old_metrics.keys():
                        old_ok = compare_token_columns(gt, ot, ignore_form=args.ignore_form)[metric]
                        new_ok = compare_token_columns(gt, nt, ignore_form=args.ignore_form)[metric]
                        if old_ok != new_ok:
                            changed.append(metric)
                    if changed:
                        print(
                            f"    id={gt.raw_id} form={gt.form} changed={','.join(changed)} "
                            f"gold=({gt.lemma},{gt.upos},{gt.xpos},{normalize_feats(gt.feats)},{gt.head},{gt.deprel})"
                        )
            print()

    if args.outdir:
        args.outdir.mkdir(parents=True, exist_ok=True)
        write_csv(args.outdir / "metric_summary.csv", metric_rows)
        write_csv(args.outdir / "sentence_summary.csv", summary_rows)
        write_csv(args.outdir / "sentence_issues.csv", sentence_issue_rows)
        write_csv(args.outdir / "token_diffs.csv", token_diff_rows)
        (args.outdir / "corpus_summary.json").write_text(
            json.dumps(corpus_summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if args.write_filtered_subsets:
            write_filtered_conllu(args.outdir / "gold.filtered.conllu", gold, gold_ordered_ids)
            write_filtered_conllu(args.outdir / "old.filtered_to_gold.conllu", old, gold_present_in_old)
            write_filtered_conllu(args.outdir / "new.filtered_to_gold.conllu", new, gold_present_in_new)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
