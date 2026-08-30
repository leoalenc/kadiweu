#!/usr/bin/env python3
"""Compare certain constituency-derived dependencies with gold CoNLL-U.

Sentences are aligned by ``sent_uid``.  Within an aligned sentence, overt PSD
terminals are paired by ordinal with integer-ID CoNLL-U word rows.  PSD empty
categories, CoNLL-U MWT range rows, and CoNLL-U empty nodes are excluded.  One
converter-added final punctuation token in CoNLL-U is tolerated.

The output begins with the columns of ``possessive-dependencies.tsv`` and adds
the corresponding gold fields, comparison status, and alignment diagnostics.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Set, TextIO, Tuple

from kadiweu_constituency import PsdRecord, TokenNode, iter_psd_records
from kadiweu_constituency_dependencies import DependencyAssignment, infer_dependencies


DEFAULT_RELATIONS = frozenset(
    {"nmod:poss", "det", "mark", "acl:relcl", "nsubj"}
)
RELATIVE_ARGUMENT_RELATIONS = frozenset({"nsubj", "obj", "obl"})


@dataclass(frozen=True)
class ConlluToken:
    id: int
    form: str
    upos: str
    xpos: str
    feats: str
    head: int
    deprel: str


@dataclass
class ConlluSentence:
    metadata: Dict[str, str] = field(default_factory=dict)
    tokens: List[ConlluToken] = field(default_factory=list)

    @property
    def sent_id(self) -> str:
        return self.metadata.get("sent_id", "")

    @property
    def sent_uid(self) -> str:
        return self.metadata.get("sent_uid", "")


@dataclass
class TokenAlignment:
    psd_to_gold: Dict[int, int]
    gold_to_psd: Dict[int, int]
    gold_tokens: List[ConlluToken]
    status: str
    error: str = ""


def iter_conllu_sentences(path: Path) -> Iterator[ConlluSentence]:
    """Read CoNLL-U without requiring a third-party library."""

    sentence = ConlluSentence()
    with path.open(encoding="utf-8") as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            line = raw_line.rstrip("\n\r")
            if not line:
                if sentence.metadata or sentence.tokens:
                    yield sentence
                    sentence = ConlluSentence()
                continue
            if line.startswith("#"):
                if " = " in line:
                    key, value = line[1:].split(" = ", 1)
                    sentence.metadata[key.strip()] = value.strip()
                continue
            columns = line.split("\t")
            if len(columns) != 10:
                raise ValueError(
                    f"{path}:{line_number}: expected 10 columns, found {len(columns)}"
                )
            token_id = columns[0]
            if "-" in token_id or "." in token_id:
                continue
            try:
                integer_id = int(token_id)
                head = int(columns[6])
            except ValueError as error:
                raise ValueError(
                    f"{path}:{line_number}: invalid integer ID or HEAD"
                ) from error
            sentence.tokens.append(
                ConlluToken(
                    integer_id,
                    columns[1],
                    columns[3],
                    columns[4],
                    columns[5],
                    head,
                    columns[7],
                )
            )
    if sentence.metadata or sentence.tokens:
        yield sentence


def _normalized_form(form: str) -> str:
    return form.replace("@", "").casefold()


def align_tokens(record: PsdRecord, gold: ConlluSentence) -> TokenAlignment:
    """Align overt PSD terminals and CoNLL-U words by ordinal."""

    psd_tokens = [token for token in record.tree.tokens if not token.empty_category]
    gold_tokens = list(gold.tokens)
    status_parts: List[str] = []

    if (
        len(gold_tokens) == len(psd_tokens) + 1
        and gold_tokens[-1].deprel == "punct"
        and gold_tokens[-1].form in {".", "!", "?"}
    ):
        gold_tokens = gold_tokens[:-1]
        status_parts.append("FINAL_PUNCT_IGNORED")

    if len(psd_tokens) != len(gold_tokens):
        return TokenAlignment(
            {},
            {},
            gold_tokens,
            "ERROR",
            f"TOKEN_COUNT_MISMATCH:psd={len(psd_tokens)},gold={len(gold_tokens)}",
        )

    psd_to_gold: Dict[int, int] = {}
    gold_to_psd: Dict[int, int] = {}
    form_mismatches = 0
    for psd_token, gold_token in zip(psd_tokens, gold_tokens):
        psd_to_gold[psd_token.position] = gold_token.id
        gold_to_psd[gold_token.id] = psd_token.position
        if _normalized_form(psd_token.form) != _normalized_form(gold_token.form):
            form_mismatches += 1
    if form_mismatches:
        status_parts.append(f"FORM_MISMATCHES={form_mismatches}")
    if not status_parts:
        status_parts.append("OK")
    return TokenAlignment(
        psd_to_gold,
        gold_to_psd,
        gold_tokens,
        ";".join(status_parts),
    )


def _tree_assignment_by_gold_dependent(
    assignments: Iterable[DependencyAssignment],
    alignment: TokenAlignment,
    relations: Set[str],
) -> Dict[int, DependencyAssignment]:
    result: Dict[int, DependencyAssignment] = {}
    for assignment in assignments:
        if assignment.deprel not in relations:
            continue
        gold_id = alignment.psd_to_gold.get(assignment.dependent_position)
        if gold_id is None:
            continue
        if gold_id in result:
            raise ValueError(f"multiple tree assignments for aligned token {gold_id}")
        result[gold_id] = assignment
    return result


def _is_target_gold_token(token: ConlluToken, relations: Set[str]) -> bool:
    """Return whether a gold dependency belongs to the audited rule scope.

    Core-argument relations are widespread in the treebank but the current
    predictor emits them only for overt relative pronouns.  Restricting
    gold-only argument rows to WPRO/PronType=Rel prevents every ordinary
    subject from being reported as a missing relative-clause prediction.
    """

    if token.deprel not in relations:
        return False
    if token.deprel not in RELATIVE_ARGUMENT_RELATIONS:
        return True
    return token.xpos == "WPRO" or "PronType=Rel" in token.feats.split("|")


OUTPUT_COLUMNS = [
    "sent_id",
    "dependent_position",
    "dependent",
    "head_position",
    "head",
    "deprel",
    "rule",
    "gold_sent_id",
    "sent_uid",
    "gold_dependent_id",
    "gold_dependent",
    "gold_head_id",
    "gold_head",
    "gold_deprel",
    "comparison",
    "token_alignment",
]


def _empty_row() -> Dict[str, object]:
    return {column: "" for column in OUTPUT_COLUMNS}


def _fill_tree_fields(
    row: Dict[str, object],
    record: PsdRecord,
    assignment: DependencyAssignment,
) -> None:
    tokens = {token.position: token for token in record.tree.tokens}
    row.update(
        {
            "sent_id": record.corpussearch_id or "",
            "dependent_position": assignment.dependent_position,
            "dependent": tokens[assignment.dependent_position].form,
            "head_position": assignment.head_position,
            "head": tokens[assignment.head_position].form,
            "deprel": assignment.deprel,
            "rule": assignment.rule,
        }
    )


def _fill_gold_fields(
    row: Dict[str, object],
    gold: ConlluSentence,
    token: ConlluToken,
    tokens_by_id: Mapping[int, ConlluToken],
) -> None:
    row.update(
        {
            "gold_sent_id": gold.sent_id,
            "sent_uid": gold.sent_uid,
            "gold_dependent_id": token.id,
            "gold_dependent": token.form,
            "gold_head_id": token.head,
            "gold_head": tokens_by_id[token.head].form if token.head in tokens_by_id else "ROOT",
            "gold_deprel": token.deprel,
        }
    )


def comparison_rows(
    psd_records: Iterable[PsdRecord],
    gold_sentences: Iterable[ConlluSentence],
    relations: Set[str],
) -> Iterator[Dict[str, object]]:
    """Yield the union of targeted tree-derived and gold dependencies."""

    records_by_uid: Dict[str, PsdRecord] = {}
    for record in psd_records:
        uid = record.tree.sentence_uid or ""
        if not uid:
            raise ValueError("PSD: record without sentence_uid")
        if uid in records_by_uid:
            raise ValueError(f"PSD: duplicate sentence_uid {uid!r}")
        records_by_uid[uid] = record

    gold_by_uid: Dict[str, ConlluSentence] = {}
    for gold in gold_sentences:
        if not gold.sent_uid:
            raise ValueError(f"CoNLL-U sentence {gold.sent_id!r} has no sent_uid")
        if gold.sent_uid in gold_by_uid:
            raise ValueError(f"CoNLL-U: duplicate sent_uid {gold.sent_uid!r}")
        gold_by_uid[gold.sent_uid] = gold

    all_uids = list(records_by_uid)
    all_uids.extend(uid for uid in gold_by_uid if uid not in records_by_uid)
    for uid in all_uids:
        record = records_by_uid.get(uid)
        gold = gold_by_uid.get(uid)
        if record is None:
            assert gold is not None
            tokens_by_id = {token.id: token for token in gold.tokens}
            for token in gold.tokens:
                if not _is_target_gold_token(token, relations):
                    continue
                row = _empty_row()
                _fill_gold_fields(row, gold, token, tokens_by_id)
                row["comparison"] = "NO_DONE_TREE"
                row["token_alignment"] = "NOT_ALIGNED"
                yield row
            continue

        tree_assignments = [
            assignment
            for assignment in infer_dependencies(record.tree)
            if assignment.deprel in relations
        ]
        if gold is None:
            for assignment in tree_assignments:
                row = _empty_row()
                _fill_tree_fields(row, record, assignment)
                row["sent_uid"] = uid
                row["comparison"] = "NO_GOLD_SENTENCE"
                row["token_alignment"] = "NOT_ALIGNED"
                yield row
            continue

        alignment = align_tokens(record, gold)
        if alignment.error:
            for assignment in tree_assignments:
                row = _empty_row()
                _fill_tree_fields(row, record, assignment)
                row.update(
                    {
                        "gold_sent_id": gold.sent_id,
                        "sent_uid": uid,
                        "comparison": "TOKEN_ALIGNMENT_ERROR",
                        "token_alignment": alignment.error,
                    }
                )
                yield row
            tokens_by_id = {token.id: token for token in gold.tokens}
            for token in gold.tokens:
                if not _is_target_gold_token(token, relations):
                    continue
                row = _empty_row()
                _fill_gold_fields(row, gold, token, tokens_by_id)
                row.update(
                    {
                        "sent_id": record.corpussearch_id or "",
                        "comparison": "TOKEN_ALIGNMENT_ERROR",
                        "token_alignment": alignment.error,
                    }
                )
                yield row
            continue

        tree_by_gold_id = _tree_assignment_by_gold_dependent(
            tree_assignments, alignment, relations
        )
        gold_target_ids = {
            token.id
            for token in alignment.gold_tokens
            if _is_target_gold_token(token, relations)
        }
        dependent_ids = sorted(set(tree_by_gold_id) | gold_target_ids)
        gold_tokens_by_id = {token.id: token for token in gold.tokens}
        for dependent_id in dependent_ids:
            assignment = tree_by_gold_id.get(dependent_id)
            gold_token = gold_tokens_by_id[dependent_id]
            row = _empty_row()
            row.update(
                {
                    "sent_id": record.corpussearch_id or "",
                    "gold_sent_id": gold.sent_id,
                    "sent_uid": uid,
                    "token_alignment": alignment.status,
                }
            )
            if assignment is not None:
                _fill_tree_fields(row, record, assignment)
            if assignment is not None or _is_target_gold_token(
                gold_token, relations
            ):
                _fill_gold_fields(row, gold, gold_token, gold_tokens_by_id)

            if assignment is None:
                comparison = "GOLD_ONLY"
            elif gold_token.deprel not in relations:
                comparison = "TREE_ONLY_GOLD_OTHER"
                _fill_gold_fields(row, gold, gold_token, gold_tokens_by_id)
            else:
                tree_head_id = alignment.psd_to_gold.get(assignment.head_position)
                if assignment.deprel != gold_token.deprel:
                    comparison = "DEPREL_MISMATCH"
                elif tree_head_id != gold_token.head:
                    comparison = "HEAD_MISMATCH"
                else:
                    comparison = "MATCH"
            row["comparison"] = comparison
            yield row


def write_comparison(
    rows: Iterable[Mapping[str, object]], stream: TextIO
) -> Counter:
    writer = csv.DictWriter(
        stream, fieldnames=OUTPUT_COLUMNS, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    counts: Counter = Counter()
    for row in rows:
        writer.writerow(row)
        counts[str(row["comparison"])] += 1
    return counts


def parse_relations(value: str) -> Set[str]:
    relations = {item.strip() for item in value.split(",") if item.strip()}
    if not relations:
        raise argparse.ArgumentTypeError("at least one relation is required")
    return relations


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare constituency-derived dependencies with gold CoNLL-U."
    )
    parser.add_argument("psd", type=Path, help="DONE CorpusSearch/Penn PSD file")
    parser.add_argument("conllu", type=Path, help="gold CoNLL-U file")
    parser.add_argument("-o", "--output", type=Path, help="TSV output; default: stdout")
    parser.add_argument(
        "--relations",
        type=parse_relations,
        default=set(DEFAULT_RELATIONS),
        help=(
            "comma-separated relations; default: "
            "nmod:poss,det,mark,acl:relcl,nsubj"
        ),
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_argument_parser().parse_args(argv)
    psd_records = list(iter_psd_records(args.psd))
    gold_sentences = list(iter_conllu_sentences(args.conllu))
    rows = comparison_rows(psd_records, gold_sentences, args.relations)
    if args.output is None:
        counts = write_comparison(rows, sys.stdout)
    else:
        with args.output.open("w", encoding="utf-8", newline="") as stream:
            counts = write_comparison(rows, stream)
    summary = " ".join(f"{key}={counts[key]}" for key in sorted(counts))
    print(f"Comparison summary: {summary}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
