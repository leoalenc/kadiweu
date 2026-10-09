#!/usr/bin/env python3
"""Generate TSV coverage reports for the KadGramPed Tycho Brahe JSON files.

By default, reads van-data.json, hil-data.json, and ped-gramm.json from the
current directory and writes TSV reports to data/reports/annotation_coverage.
Pass input paths and/or --outdir to use differently named files or destination.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable

DEFAULT_FILES = ("van-data.json", "hil-data.json", "ped-gramm.json")
DEFAULT_OUTDIR = Path("data/reports/annotation_coverage")

SUMMARY_FIELDS = [
    "source", "sentences", "done_sentences", "review_sentences", "pt_translation",
    "all_tokens_segmented", "sentences_with_some_unsegmented_token", "no_tokens_segmented",
    "sentences_with_at_least_one_split_piece", "sentences_with_unglossed_split_piece",
    "all_split_pieces_glossed", "complete_segmentation_and_gloss", "tokens",
    "tokens_without_segmentation", "split_pieces", "split_pieces_without_gloss",
    "split_entries_without_morpheme_form",
]

SENTENCE_FIELDS = [
    "source", "sentence_number", "status", "sentence_uid", "token_count",
    "segmented_token_count", "unsegmented_token_count", "segmented_tokens_over_total",
    "all_tokens_segmented", "no_tokens_segmented", "pt_translation_present",
    "split_piece_count", "split_pieces_without_gloss", "split_entries_without_morpheme_form",
    "all_split_pieces_glossed", "complete_segmentation_and_gloss", "sentence_text",
]

TOKEN_FIELDS = [
    "source", "sentence_number", "status", "sentence_uid", "token_number",
    "token_form", "sentence_text",
]

UNGLOSSED_FIELDS = [
    "source", "sentence_number", "status", "sentence_uid", "token_number",
    "token_form", "split_number", "split_form", "split_tag", "sentence_text",
]

EMPTY_SPLIT_FIELDS = [
    "source", "sentence_number", "status", "sentence_uid", "token_number",
    "token_form", "split_number", "split_value", "sentence_text",
]


def load_sentences(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        document = json.load(stream)
    return [sentence for page in document.get("pages", [])
            for sentence in page.get("sentences", [])]


def split_entries(token: dict[str, Any]) -> list[Any]:
    value = token.get("splits")
    return value if isinstance(value, list) else []


def has_morpheme_form(piece: Any) -> bool:
    """True only when a split entry supplies a non-empty morpheme form."""
    if not isinstance(piece, dict):
        return False
    form = piece.get("v")
    return isinstance(form, str) and bool(form.strip())


def has_segmentation(token: dict[str, Any]) -> bool:
    """A token is segmented iff at least one split entry has an overt form."""
    return any(has_morpheme_form(piece) for piece in split_entries(token))


def has_complete_split_forms(token: dict[str, Any]) -> bool:
    """Require every split entry to be an object with an overt morpheme form."""
    entries = split_entries(token)
    return bool(entries) and all(has_morpheme_form(piece) for piece in entries)


def has_gloss(piece: dict[str, Any]) -> bool:
    gloss = (piece.get("attributes") or {}).get("gloss-br")
    return isinstance(gloss, str) and bool(gloss.strip())


def get_sentence_rows(source: str, sentences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for number, sentence in enumerate(sentences, start=1):
        tokens = (sentence.get("struct") or {}).get("tokens") or []
        segmented_flags = [has_segmentation(token) for token in tokens]
        segmented_count = sum(segmented_flags)
        pieces = [piece for token in tokens for piece in split_entries(token)
                  if has_morpheme_form(piece)]
        unglossed_count = sum(not has_gloss(piece) for piece in pieces)
        empty_entries = sum(
            not has_morpheme_form(piece)
            for token in tokens for piece in split_entries(token)
        )
        translations = sentence.get("translations") or {}
        pt = translations.get("pt-br")
        pt_present = isinstance(pt, str) and bool(pt.strip())
        all_segmented = bool(tokens) and all(segmented_flags)
        all_forms_present = bool(tokens) and all(has_complete_split_forms(token) for token in tokens)
        all_pieces_glossed = bool(pieces) and unglossed_count == 0 and empty_entries == 0
        complete = all_forms_present and all_pieces_glossed
        rows.append({
            "source": source,
            "sentence_number": number,
            "status": sentence.get("status", ""),
            "sentence_uid": sentence.get("uid", ""),
            "token_count": len(tokens),
            "segmented_token_count": segmented_count,
            "unsegmented_token_count": len(tokens) - segmented_count,
            "segmented_tokens_over_total": f"{segmented_count}/{len(tokens)}" if tokens else "0/0",
            "all_tokens_segmented": all_forms_present,
            "no_tokens_segmented": bool(tokens) and segmented_count == 0,
            "pt_translation_present": pt_present,
            "split_piece_count": len(pieces),
            "split_pieces_without_gloss": unglossed_count,
            "split_entries_without_morpheme_form": empty_entries,
            "all_split_pieces_glossed": all_pieces_glossed,
            "complete_segmentation_and_gloss": complete,
            "sentence_text": sentence.get("text", ""),
        })
    return rows


def summarize(source: str, sentences: list[dict[str, Any]], sentence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    tokens_total = tokens_unsegmented = pieces_total = pieces_unglossed = entries_without_form = 0
    for sentence in sentences:
        status = sentence.get("status", "")
        status_counts[status] = status_counts.get(status, 0) + 1
        tokens = (sentence.get("struct") or {}).get("tokens") or []
        tokens_total += len(tokens)
        tokens_unsegmented += sum(not has_segmentation(token) for token in tokens)
        for token in tokens:
            entries = split_entries(token)
            entries_without_form += sum(not has_morpheme_form(piece) for piece in entries)
            for piece in entries:
                if has_morpheme_form(piece):
                    pieces_total += 1
                    pieces_unglossed += not has_gloss(piece)

    return {
        "source": source,
        "sentences": len(sentences),
        "done_sentences": status_counts.get("DONE", 0),
        "review_sentences": status_counts.get("REVIEW", 0),
        "pt_translation": sum(row["pt_translation_present"] for row in sentence_rows),
        "all_tokens_segmented": sum(row["all_tokens_segmented"] for row in sentence_rows),
        "sentences_with_some_unsegmented_token": sum(row["unsegmented_token_count"] > 0 for row in sentence_rows),
        "no_tokens_segmented": sum(row["no_tokens_segmented"] for row in sentence_rows),
        "sentences_with_at_least_one_split_piece": sum(row["split_piece_count"] > 0 for row in sentence_rows),
        "sentences_with_unglossed_split_piece": sum(row["split_pieces_without_gloss"] > 0 for row in sentence_rows),
        "all_split_pieces_glossed": sum(row["all_split_pieces_glossed"] for row in sentence_rows),
        "complete_segmentation_and_gloss": sum(row["complete_segmentation_and_gloss"] for row in sentence_rows),
        "tokens": tokens_total,
        "tokens_without_segmentation": tokens_unsegmented,
        "split_pieces": pieces_total,
        "split_pieces_without_gloss": pieces_unglossed,
        "split_entries_without_morpheme_form": entries_without_form,
    }


def make_token_rows(source: str, sentences: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for sentence_number, sentence in enumerate(sentences, start=1):
        tokens = (sentence.get("struct") or {}).get("tokens") or []
        for token_number, token in enumerate(tokens, start=1):
            if not has_segmentation(token):
                yield {
                    "source": source, "sentence_number": sentence_number,
                    "status": sentence.get("status", ""), "sentence_uid": sentence.get("uid", ""),
                    "token_number": token_number, "token_form": token.get("v", ""),
                    "sentence_text": sentence.get("text", ""),
                }


def make_unglossed_rows(source: str, sentences: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for sentence_number, sentence in enumerate(sentences, start=1):
        tokens = (sentence.get("struct") or {}).get("tokens") or []
        for token_number, token in enumerate(tokens, start=1):
            for split_number, piece in enumerate(split_entries(token), start=1):
                if has_morpheme_form(piece) and not has_gloss(piece):
                    yield {
                        "source": source, "sentence_number": sentence_number,
                        "status": sentence.get("status", ""), "sentence_uid": sentence.get("uid", ""),
                        "token_number": token_number, "token_form": token.get("v", ""),
                        "split_number": split_number, "split_form": piece.get("v", ""),
                        "split_tag": piece.get("t", ""), "sentence_text": sentence.get("text", ""),
                    }


def make_empty_split_rows(source: str, sentences: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for sentence_number, sentence in enumerate(sentences, start=1):
        tokens = (sentence.get("struct") or {}).get("tokens") or []
        for token_number, token in enumerate(tokens, start=1):
            for split_number, piece in enumerate(split_entries(token), start=1):
                if not has_morpheme_form(piece):
                    yield {
                        "source": source, "sentence_number": sentence_number,
                        "status": sentence.get("status", ""), "sentence_uid": sentence.get("uid", ""),
                        "token_number": token_number, "token_form": token.get("v", ""),
                        "split_number": split_number, "split_value": json.dumps(piece, ensure_ascii=False),
                        "sentence_text": sentence.get("text", ""),
                    }


def write_tsv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_files", nargs="*", type=Path,
                        help="Input JSON files (default: van-data.json hil-data.json ped-gramm.json in the current directory)")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR,
                        help=f"Directory for TSV reports (default: {DEFAULT_OUTDIR})")
    args = parser.parse_args()
    paths = args.json_files or [Path(name) for name in DEFAULT_FILES]
    missing = [path for path in paths if not path.is_file()]
    if missing:
        for path in missing:
            print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    summary_rows = []
    sentence_rows_all = []
    unsegmented_rows = []
    unglossed_rows = []
    empty_split_rows = []
    for path in paths:
        sentences = load_sentences(path)
        sentence_rows = get_sentence_rows(path.name, sentences)
        summary_rows.append(summarize(path.name, sentences, sentence_rows))
        sentence_rows_all.extend(sentence_rows)
        unsegmented_rows.extend(make_token_rows(path.name, sentences))
        unglossed_rows.extend(make_unglossed_rows(path.name, sentences))
        empty_split_rows.extend(make_empty_split_rows(path.name, sentences))

    overall = summarize("TOTAL", [], sentence_rows_all)
    overall["sentences"] = sum(row["sentences"] for row in summary_rows)
    overall["done_sentences"] = sum(row["done_sentences"] for row in summary_rows)
    overall["review_sentences"] = sum(row["review_sentences"] for row in summary_rows)
    for key in ("tokens", "tokens_without_segmentation", "split_pieces", "split_pieces_without_gloss",
                "split_entries_without_morpheme_form"):
        overall[key] = sum(row[key] for row in summary_rows)
    summary_rows.append(overall)

    args.outdir.mkdir(parents=True, exist_ok=True)
    write_tsv(args.outdir / "summary.tsv", SUMMARY_FIELDS, summary_rows)
    write_tsv(args.outdir / "sentence_annotation_coverage.tsv", SENTENCE_FIELDS, sentence_rows_all)
    write_tsv(args.outdir / "non_segmented_tokens.tsv", TOKEN_FIELDS, unsegmented_rows)
    write_tsv(args.outdir / "split_pieces_without_gloss.tsv", UNGLOSSED_FIELDS, unglossed_rows)
    write_tsv(args.outdir / "split_entries_without_morpheme_form.tsv", EMPTY_SPLIT_FIELDS, empty_split_rows)

    print(f"Processed {len(sentence_rows_all)} sentence(s) from {len(paths)} JSON file(s).")
    print(f"Sentences with at least one non-segmented token: {overall['sentences_with_some_unsegmented_token']}")
    print(f"Fully segmented sentences: {overall['all_tokens_segmented']}")
    print(f"Sentences with no segmented tokens: {overall['no_tokens_segmented']}")
    print(f"Sentences with complete segmentation and glosses: {overall['complete_segmentation_and_gloss']}")
    print(f"Non-segmented token records: {len(unsegmented_rows)}")
    print(f"Split entries without a morpheme form: {len(empty_split_rows)}")
    print(f"TSV reports written to: {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
