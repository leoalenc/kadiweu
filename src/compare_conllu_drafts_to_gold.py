#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compare one or more draft CoNLL-U files against a gold CoNLL-U treebank.

This version explicitly checks token-count comparability before scoring.

Comparison policy
-----------------
1. Sentences are matched by `sent_uid`.
2. Only syntactic token rows are counted: integer CoNLL-U IDs such as `1`, `2`, `3`.
   Multiword-token rows such as `1-2` and empty nodes such as `3.1` are ignored.
3. Every matched sentence is reported in the coverage counts.
4. Sentences whose gold and draft token counts differ are reported separately and
   are excluded from token-level accuracy.
5. Sentences with the same token count but different integer token IDs are also
   reported separately and excluded from token-level accuracy, because ID-based
   alignment would be unsafe.
6. Token-level accuracy is computed only for comparable matched sentences.

Reported fields
---------------
FORM, LEMMA, UPOS, XPOS, FEATS, UAS/HEAD, DEPREL, and LAS.

LAS is correct when both HEAD and DEPREL match the corresponding gold token.

Example
-------
    python3 compare_conllu_to_gold_v2.py \
        data/treebank/kbc_unicamp-ud-test.conllu \
        data/treebank/draft-van.edt.conllu \
        data/treebank/draft-hil.pdt.conllu \
        data/treebank/draft.edt.conllu \
        --markdown-out conllu_accuracy_report.md \
        --csv-out conllu_accuracy_report.csv \
        --mismatch-csv-out conllu_token_mismatches.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

FIELDS = ("FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "LAS")


@dataclass
class Token:
    """One syntactic CoNLL-U token row."""

    id: str
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
    """One CoNLL-U sentence block."""

    meta: Dict[str, str] = field(default_factory=dict)
    tokens: List[Token] = field(default_factory=list)

    @property
    def sent_uid(self) -> Optional[str]:
        return self.meta.get("sent_uid")

    @property
    def sent_id(self) -> str:
        return self.meta.get("sent_id", "")

    @property
    def text(self) -> str:
        return self.meta.get("text", "")

    def token_by_id(self) -> Dict[str, Token]:
        return {tok.id: tok for tok in self.tokens}

    def token_forms(self) -> str:
        return " ".join(tok.form for tok in self.tokens)

    def token_ids(self) -> List[str]:
        return [tok.id for tok in self.tokens]


@dataclass
class TokenMismatch:
    """A matched sentence that cannot safely be scored token by token."""

    draft_file: str
    sent_uid: str
    gold_sent_id: str
    draft_sent_id: str
    reason: str
    gold_token_count: int
    draft_token_count: int
    gold_token_ids: str
    draft_token_ids: str
    gold_forms: str
    draft_forms: str


@dataclass
class FileStats:
    """Accumulated comparison counts for one draft file."""

    draft_path: Path
    draft_sentences_total: int = 0
    gold_sentences_total: int = 0
    matched_sentences: int = 0
    comparable_sentences: int = 0
    token_count_mismatch_sentences: int = 0
    token_id_mismatch_sentences: int = 0
    scored_tokens: int = 0
    gold_tokens_in_matched_sentences: int = 0
    draft_tokens_in_matched_sentences: int = 0
    gold_tokens_in_scored_sentences: int = 0
    draft_tokens_in_scored_sentences: int = 0
    duplicate_draft_uids_ignored: int = 0
    correct: Dict[str, int] = field(default_factory=lambda: {name: 0 for name in FIELDS})
    mismatches: List[TokenMismatch] = field(default_factory=list)

    def accuracy(self, field_name: str) -> Optional[float]:
        if self.scored_tokens == 0:
            return None
        return self.correct[field_name] / self.scored_tokens

    def percent(self, field_name: str) -> str:
        value = self.accuracy(field_name)
        return "NA" if value is None else f"{value * 100:.2f}"


def is_integer_token_id(token_id: str) -> bool:
    """Return True for syntactic token IDs, False for MWT ranges and empty nodes."""
    return token_id.isdigit()


def normalize_feats(feats: str) -> str:
    """Normalize FEATS order for comparison."""
    if feats in ("", "_"):
        return "_"
    parts = [part for part in feats.split("|") if part]
    return "|".join(sorted(parts)) if parts else "_"


def parse_conllu(path: Path) -> List[Sentence]:
    """Parse a CoNLL-U file into Sentence objects."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Could not read {path}: {exc}") from exc

    sentences: List[Sentence] = []
    current = Sentence()

    def flush() -> None:
        nonlocal current
        if current.meta or current.tokens:
            sentences.append(current)
            current = Sentence()

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip("\n")
        if not line.strip():
            flush()
            continue

        if line.startswith("#"):
            body = line[1:].strip()
            if " = " in body:
                key, value = body.split(" = ", 1)
                current.meta[key.strip()] = value.strip()
            continue

        cols = line.split("\t")
        if len(cols) != 10:
            raise ValueError(
                f"{path}:{lineno}: expected 10 tab-separated CoNLL-U columns, got {len(cols)}"
            )

        if not is_integer_token_id(cols[0]):
            continue

        current.tokens.append(
            Token(
                id=cols[0],
                form=cols[1],
                lemma=cols[2],
                upos=cols[3],
                xpos=cols[4],
                feats=normalize_feats(cols[5]),
                head=cols[6],
                deprel=cols[7],
                deps=cols[8],
                misc=cols[9],
            )
        )

    flush()
    return sentences


def index_gold_by_uid(gold_sentences: Sequence[Sentence]) -> Dict[str, Sentence]:
    """Build a gold `sent_uid` index and fail on duplicate UIDs."""
    index: Dict[str, Sentence] = {}
    duplicates: List[str] = []

    for sent in gold_sentences:
        uid = sent.sent_uid
        if not uid:
            continue
        if uid in index:
            duplicates.append(uid)
        else:
            index[uid] = sent

    if duplicates:
        sample = ", ".join(duplicates[:10])
        suffix = "" if len(duplicates) <= 10 else f" ... (+{len(duplicates) - 10} more)"
        raise ValueError(f"Duplicate sent_uid values in gold treebank: {sample}{suffix}")

    return index


def compare_token(gold: Token, draft: Token) -> Dict[str, bool]:
    """Return correctness booleans for one aligned token pair."""
    uas = draft.head == gold.head
    deprel = draft.deprel == gold.deprel
    return {
        "FORM": draft.form == gold.form,
        "LEMMA": draft.lemma == gold.lemma,
        "UPOS": draft.upos == gold.upos,
        "XPOS": draft.xpos == gold.xpos,
        "FEATS": draft.feats == gold.feats,
        "HEAD": uas,
        "DEPREL": deprel,
        "LAS": uas and deprel,
    }


def make_mismatch(draft_path: Path, uid: str, gold: Sentence, draft: Sentence, reason: str) -> TokenMismatch:
    """Create a compact mismatch record for reporting."""
    return TokenMismatch(
        draft_file=draft_path.name,
        sent_uid=uid,
        gold_sent_id=gold.sent_id,
        draft_sent_id=draft.sent_id,
        reason=reason,
        gold_token_count=len(gold.tokens),
        draft_token_count=len(draft.tokens),
        gold_token_ids=" ".join(gold.token_ids()),
        draft_token_ids=" ".join(draft.token_ids()),
        gold_forms=gold.token_forms(),
        draft_forms=draft.token_forms(),
    )


def compare_draft(gold_index: Dict[str, Sentence], gold_total: int, draft_path: Path) -> FileStats:
    """Compare one draft file with the gold `sent_uid` index."""
    draft_sentences = parse_conllu(draft_path)
    stats = FileStats(
        draft_path=draft_path,
        draft_sentences_total=len(draft_sentences),
        gold_sentences_total=gold_total,
    )

    seen_draft_uids: set[str] = set()

    for draft_sent in draft_sentences:
        uid = draft_sent.sent_uid
        if not uid or uid not in gold_index:
            continue

        if uid in seen_draft_uids:
            stats.duplicate_draft_uids_ignored += 1
            continue
        seen_draft_uids.add(uid)

        gold_sent = gold_index[uid]
        stats.matched_sentences += 1
        stats.gold_tokens_in_matched_sentences += len(gold_sent.tokens)
        stats.draft_tokens_in_matched_sentences += len(draft_sent.tokens)

        if len(gold_sent.tokens) != len(draft_sent.tokens):
            stats.token_count_mismatch_sentences += 1
            stats.mismatches.append(
                make_mismatch(draft_path, uid, gold_sent, draft_sent, "token_count_mismatch")
            )
            continue

        gold_ids = set(gold_sent.token_by_id())
        draft_ids = set(draft_sent.token_by_id())
        if gold_ids != draft_ids:
            stats.token_id_mismatch_sentences += 1
            stats.mismatches.append(
                make_mismatch(draft_path, uid, gold_sent, draft_sent, "token_id_mismatch")
            )
            continue

        stats.comparable_sentences += 1
        stats.gold_tokens_in_scored_sentences += len(gold_sent.tokens)
        stats.draft_tokens_in_scored_sentences += len(draft_sent.tokens)

        gold_tokens = gold_sent.token_by_id()
        draft_tokens = draft_sent.token_by_id()
        for token_id in sorted(gold_ids, key=int):
            stats.scored_tokens += 1
            result = compare_token(gold_tokens[token_id], draft_tokens[token_id])
            for field_name, ok in result.items():
                if ok:
                    stats.correct[field_name] += 1

    return stats


def make_markdown_report(stats_list: Sequence[FileStats]) -> str:
    """Render a Markdown report."""
    lines: List[str] = []
    lines.append("# CoNLL-U draft accuracy against gold")
    lines.append("")
    lines.append(
        "Only sentences with matching `sent_uid` are considered. "
        "Token-level accuracy is computed only for matched sentences with the same number "
        "of syntactic tokens and the same integer token IDs."
    )
    lines.append("")

    headers = [
        "draft_file",
        "matched_sents",
        "comparable_sents",
        "token_count_mismatch_sents",
        "token_id_mismatch_sents",
        "scored_tokens",
        "FORM",
        "LEMMA",
        "UPOS",
        "XPOS",
        "FEATS",
        "UAS",
        "DEPREL",
        "LAS",
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for stats in stats_list:
        row = [
            stats.draft_path.name,
            str(stats.matched_sentences),
            str(stats.comparable_sentences),
            str(stats.token_count_mismatch_sentences),
            str(stats.token_id_mismatch_sentences),
            str(stats.scored_tokens),
            stats.percent("FORM"),
            stats.percent("LEMMA"),
            stats.percent("UPOS"),
            stats.percent("XPOS"),
            stats.percent("FEATS"),
            stats.percent("HEAD"),
            stats.percent("DEPREL"),
            stats.percent("LAS"),
        ]
        lines.append("| " + " | ".join(row) + " |")

    all_mismatches = [m for stats in stats_list for m in stats.mismatches]
    lines.append("")
    lines.append("## Token-count / token-ID mismatches")
    lines.append("")
    if not all_mismatches:
        lines.append("No token-count or token-ID mismatches were found in matched sentences.")
    else:
        mismatch_headers = [
            "draft_file",
            "sent_uid",
            "gold_sent_id",
            "draft_sent_id",
            "reason",
            "gold_n",
            "draft_n",
            "gold_forms",
            "draft_forms",
        ]
        lines.append("| " + " | ".join(mismatch_headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(mismatch_headers)) + " |")
        for m in all_mismatches:
            row = [
                m.draft_file,
                f"`{m.sent_uid}`",
                f"`{m.gold_sent_id}`",
                f"`{m.draft_sent_id}`",
                m.reason,
                str(m.gold_token_count),
                str(m.draft_token_count),
                f"`{m.gold_forms}`",
                f"`{m.draft_forms}`",
            ]
            lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- `UAS` is `HEAD` accuracy.")
    lines.append("- `LAS` requires both `HEAD` and `DEPREL` to match.")
    lines.append("- `FEATS` are compared after alphabetic normalization of feature order.")
    lines.append("- MWT range rows and empty nodes are ignored in token counts and scoring.")
    lines.append("- Non-comparable matched sentences are excluded from the accuracy denominators.")
    lines.append("")
    return "\n".join(lines)


def write_summary_csv(stats_list: Sequence[FileStats], csv_path: Path) -> None:
    """Write one-row-per-draft CSV summary."""
    fieldnames = [
        "draft_file",
        "draft_path",
        "gold_sentences_total",
        "draft_sentences_total",
        "matched_sentences",
        "comparable_sentences",
        "token_count_mismatch_sentences",
        "token_id_mismatch_sentences",
        "duplicate_draft_uids_ignored",
        "scored_tokens",
        "gold_tokens_in_matched_sentences",
        "draft_tokens_in_matched_sentences",
        "gold_tokens_in_scored_sentences",
        "draft_tokens_in_scored_sentences",
        "FORM_accuracy",
        "LEMMA_accuracy",
        "UPOS_accuracy",
        "XPOS_accuracy",
        "FEATS_accuracy",
        "UAS_accuracy",
        "DEPREL_accuracy",
        "LAS_accuracy",
        "FORM_correct",
        "LEMMA_correct",
        "UPOS_correct",
        "XPOS_correct",
        "FEATS_correct",
        "HEAD_correct",
        "DEPREL_correct",
        "LAS_correct",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for stats in stats_list:
            row = {
                "draft_file": stats.draft_path.name,
                "draft_path": str(stats.draft_path),
                "gold_sentences_total": stats.gold_sentences_total,
                "draft_sentences_total": stats.draft_sentences_total,
                "matched_sentences": stats.matched_sentences,
                "comparable_sentences": stats.comparable_sentences,
                "token_count_mismatch_sentences": stats.token_count_mismatch_sentences,
                "token_id_mismatch_sentences": stats.token_id_mismatch_sentences,
                "duplicate_draft_uids_ignored": stats.duplicate_draft_uids_ignored,
                "scored_tokens": stats.scored_tokens,
                "gold_tokens_in_matched_sentences": stats.gold_tokens_in_matched_sentences,
                "draft_tokens_in_matched_sentences": stats.draft_tokens_in_matched_sentences,
                "gold_tokens_in_scored_sentences": stats.gold_tokens_in_scored_sentences,
                "draft_tokens_in_scored_sentences": stats.draft_tokens_in_scored_sentences,
            }
            for field_name in FIELDS:
                label = "UAS" if field_name == "HEAD" else field_name
                acc = stats.accuracy(field_name)
                row[f"{label}_accuracy"] = "" if acc is None else f"{acc:.6f}"
                row[f"{field_name}_correct"] = stats.correct[field_name]
            writer.writerow(row)


def write_mismatch_csv(stats_list: Sequence[FileStats], csv_path: Path) -> None:
    """Write detailed token-count/token-ID mismatches to CSV."""
    fieldnames = [
        "draft_file",
        "sent_uid",
        "gold_sent_id",
        "draft_sent_id",
        "reason",
        "gold_token_count",
        "draft_token_count",
        "gold_token_ids",
        "draft_token_ids",
        "gold_forms",
        "draft_forms",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for stats in stats_list:
            for m in stats.mismatches:
                writer.writerow({name: getattr(m, name) for name in fieldnames})


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare draft CoNLL-U files against a gold treebank by sent_uid."
    )
    parser.add_argument("gold", type=Path, help="Gold CoNLL-U file.")
    parser.add_argument("drafts", type=Path, nargs="+", help="One or more draft CoNLL-U files.")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report path.")
    parser.add_argument("--csv-out", type=Path, help="Optional CSV summary path.")
    parser.add_argument(
        "--mismatch-csv-out",
        type=Path,
        help="Optional CSV path for token-count/token-ID mismatch details.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    try:
        gold_sentences = parse_conllu(args.gold)
        gold_index = index_gold_by_uid(gold_sentences)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not gold_index:
        print("ERROR: no sentences with sent_uid found in gold treebank.", file=sys.stderr)
        return 2

    stats_list: List[FileStats] = []
    had_error = False
    for draft_path in args.drafts:
        try:
            stats_list.append(compare_draft(gold_index, len(gold_sentences), draft_path))
        except (OSError, ValueError) as exc:
            had_error = True
            print(f"ERROR: {exc}", file=sys.stderr)

    if not stats_list:
        return 1

    report = make_markdown_report(stats_list)
    print(report)

    if args.markdown_out:
        args.markdown_out.write_text(report, encoding="utf-8")
        print(f"Wrote Markdown report: {args.markdown_out}", file=sys.stderr)

    if args.csv_out:
        write_summary_csv(stats_list, args.csv_out)
        print(f"Wrote CSV summary: {args.csv_out}", file=sys.stderr)

    if args.mismatch_csv_out:
        write_mismatch_csv(stats_list, args.mismatch_csv_out)
        print(f"Wrote mismatch CSV: {args.mismatch_csv_out}", file=sys.stderr)

    return 2 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
