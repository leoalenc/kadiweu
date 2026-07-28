#!/usr/bin/env python3
"""Constituency-tree utilities for Tycho Brahe Platform JSON exports.

This first version reconstructs tree objects from ``struct.chunks`` and
``struct.tokens`` and pretty-prints individual sentences.  It deliberately
keeps the original chunk/token mappings available on every node so that later
versions can add head rules, dependency relations, and JSON enrichment without
having to parse the source again.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence, TextIO, Union

JsonObject = Mapping[str, Any]


class TreeConstructionError(ValueError):
    """Raised when chunk/token annotations cannot form a tree."""


@dataclass
class TokenNode:
    """A terminal node copied from a Tycho ``struct.tokens`` entry."""

    position: int
    form: str
    tag: str | None
    level: int
    token_id: str | None = None
    empty_category: bool = False
    coindex: tuple[int, ...] = ()
    source: JsonObject = field(default_factory=dict, repr=False, compare=False)
    parent: ConstituentNode | None = field(
        default=None, repr=False, compare=False
    )

    @property
    def label(self) -> str:
        return self.tag or "TOKEN"

    @property
    def span(self) -> tuple[int, int]:
        return self.position, self.position

    @property
    def is_terminal(self) -> bool:
        return True

    def display_label(self, *, show_positions: bool = False) -> str:
        label = f"{self.label} {json.dumps(self.form, ensure_ascii=False)}"
        if self.coindex:
            label += "-" + ",".join(map(str, self.coindex))
        if show_positions:
            label = f"{self.position}: {label}"
        return label


@dataclass
class ConstituentNode:
    """A nonterminal node copied from a Tycho ``struct.chunks`` entry."""

    label: str
    start: int
    end: int
    level: int
    coindex: tuple[int, ...] = ()
    source: JsonObject = field(default_factory=dict, repr=False, compare=False)
    children: list[TreeNode] = field(default_factory=list)
    parent: ConstituentNode | None = field(
        default=None, repr=False, compare=False
    )

    @property
    def span(self) -> tuple[int, int]:
        return self.start, self.end

    @property
    def is_terminal(self) -> bool:
        return False

    def display_label(self, *, show_spans: bool = False) -> str:
        label = self.label
        if self.coindex:
            label += "-" + ",".join(map(str, self.coindex))
        if show_spans:
            label += f" [{self.start}-{self.end}]"
        return label

    def walk(self) -> Iterator[TreeNode]:
        yield self
        for child in self.children:
            if isinstance(child, ConstituentNode):
                yield from child.walk()
            else:
                yield child


TreeNode = Union[ConstituentNode, TokenNode]


@dataclass
class ConstituencyTree:
    """A reconstructed tree and its sentence-level metadata."""

    roots: list[ConstituentNode]
    tokens: list[TokenNode]
    sentence_uid: str | None = None
    sentence_number: int | None = None
    source_name: str | None = None
    text: str | None = None
    text_por: str | None = None
    status: str | None = None
    source_sentence: JsonObject = field(
        default_factory=dict, repr=False, compare=False
    )

    @property
    def root(self) -> ConstituentNode:
        """Return the unique root, rejecting malformed multi-root structures."""
        if len(self.roots) != 1:
            raise TreeConstructionError(
                f"expected one root, found {len(self.roots)}"
            )
        return self.roots[0]

    def walk(self) -> Iterator[TreeNode]:
        for root in self.roots:
            yield from root.walk()

    def pretty(
        self, *, show_spans: bool = False, show_positions: bool = False
    ) -> str:
        """Return a Unicode, line-oriented representation of the tree."""
        lines: list[str] = []

        def visit(node: TreeNode, prefix: str, last: bool, top: bool) -> None:
            connector = "" if top else ("└── " if last else "├── ")
            if isinstance(node, ConstituentNode):
                label = node.display_label(show_spans=show_spans)
            else:
                label = node.display_label(show_positions=show_positions)
            lines.append(prefix + connector + label)
            if not isinstance(node, ConstituentNode):
                return
            next_prefix = prefix if top else prefix + ("    " if last else "│   ")
            for index, child in enumerate(node.children):
                visit(child, next_prefix, index == len(node.children) - 1, False)

        for index, root in enumerate(self.roots):
            visit(root, "", index == len(self.roots) - 1, True)
        return "\n".join(lines)

    def to_lisp(self, *, indent: int = 2) -> str:
        """Return an indented Lisp-style tree (useful for future JSON enrichment)."""
        if indent < 0:
            raise ValueError("indent must be non-negative")

        def render(node: TreeNode, depth: int) -> str:
            margin = " " * (indent * depth)
            if isinstance(node, TokenNode):
                return f"{margin}({node.label} {json.dumps(node.form, ensure_ascii=False)})"
            if not node.children:
                return f"{margin}({node.label})"
            children = "\n".join(render(child, depth + 1) for child in node.children)
            return f"{margin}({node.label}\n{children}\n{margin})"

        return "\n".join(render(root, 0) for root in self.roots)

    def corpussearch_id(self) -> str:
        """Return a stable CorpusSearch identifier for this sentence."""
        if not self.source_name:
            raise TreeConstructionError(
                "cannot generate a CorpusSearch ID without a source name"
            )
        if self.sentence_number is None:
            raise TreeConstructionError(
                "cannot generate a CorpusSearch ID without a sentence number"
            )

        source = re.sub(
            r"[^A-Za-z0-9_-]+", "_", self.source_name
        ).strip("_")
        if not source:
            raise TreeConstructionError(
                f"invalid CorpusSearch source name: {self.source_name!r}"
            )

        return f"{source},0.{self.sentence_number}"

    @staticmethod
    def _corpussearch_metadata_value(value: str) -> str:
        """Normalize a value for use inside a CorpusSearch block comment."""
        value = " ".join(value.split())
        return value.replace("*/", "* /")

    def corpussearch_metadata(self) -> str:
        """Return a CorpusSearch comment containing sentence metadata."""
        metadata: list[tuple[str, str]] = []

        if self.sentence_number is not None:
            metadata.append(("sentence", str(self.sentence_number)))
        if self.sentence_uid:
            metadata.append(("uid", self.sentence_uid))
        if self.status:
            metadata.append(("status", self.status))
        if self.text:
            metadata.append(("text", self.text))
        if self.text_por:
            metadata.append(("text_por", self.text_por))

        lines = [
            f"{key} = {self._corpussearch_metadata_value(value)}"
            for key, value in metadata
        ]
        return "/*\n" + "\n".join(lines) + "\n*/"

    def to_corpussearch(
        self,
        *,
        indent: int = 2,
        show_metadata: bool = True,
        trace_format: str = "tycho",
    ) -> str:
        """Return a Penn-style sentence record for CorpusSearch or Tycho.

        Coindices are appended to constituent labels and empty-category forms.

        In ``tycho`` trace format, an empty-category terminal is printed
        directly under its dominating constituent, for example::

            (NP-TRACE *T*-1)

        In ``corpussearch`` trace format, the terminal receives the ``-NONE-``
        preterminal required for lossless processing by CorpusSearch 2.003.00::

            (NP-TRACE (-NONE- *T*-1))

        The syntactic tree and its ID are enclosed in the unlabeled outer
        sentence wrapper required by CorpusSearch.
        """
        if indent < 0:
            raise ValueError("indent must be non-negative")
        if trace_format not in {"tycho", "corpussearch"}:
            raise ValueError(
                f"unsupported trace format: {trace_format!r}"
            )

        def indexed(value: str, coindex: tuple[int, ...]) -> str:
            if not coindex:
                return value
            return value + "".join(f"-{index}" for index in coindex)

        def render(node: TreeNode, depth: int) -> str:
            margin = " " * (indent * depth)

            if isinstance(node, TokenNode):
                form = indexed(node.form, node.coindex)
                if node.empty_category:
                    if trace_format == "corpussearch":
                        return f"{margin}(-NONE- {form})"
                    return f"{margin}{form}"

                label = indexed(node.label, node.coindex)
                return f"{margin}({label} {form})"

            label = indexed(node.label, node.coindex)
            if not node.children:
                return f"{margin}({label})"

            children = "\n".join(
                render(child, depth + 1) for child in node.children
            )
            return f"{margin}({label}\n{children}\n{margin})"

        roots = "\n".join(render(root, 1) for root in self.roots)
        id_margin = " " * indent
        record = (
            f"(\n"
            f"{roots}\n"
            f"{id_margin}(ID {self.corpussearch_id()})\n"
            f")"
        )

        if show_metadata:
            return f"{self.corpussearch_metadata()}\n{record}"
        return record

def _coindex(item: JsonObject) -> tuple[int, ...]:
    value = item.get("coidx", ())
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(int(index) for index in value)
    return (int(value),)


def _contains(parent: ConstituentNode, start: int, end: int) -> bool:
    return parent.start <= start and end <= parent.end


def tree_from_sentence(
    sentence: JsonObject,
    *,
    sentence_number: int | None = None,
    source_name: str | None = None,
) -> ConstituencyTree:
    """Build a :class:`ConstituencyTree` from one Tycho sentence mapping.

    Parent selection uses the annotated depth first and the narrowest
    containing span second.  This preserves unary projections whose chunks
    have identical spans.
    """
    struct = sentence.get("struct")
    if not isinstance(struct, Mapping):
        raise TreeConstructionError("sentence has no 'struct' mapping")
    raw_chunks = struct.get("chunks", [])
    raw_tokens = struct.get("tokens", [])
    if not isinstance(raw_chunks, list) or not isinstance(raw_tokens, list):
        raise TreeConstructionError("'chunks' and 'tokens' must be lists")
    if not raw_chunks:
        raise TreeConstructionError("sentence has no constituency chunks")

    chunks: list[ConstituentNode] = []
    for raw in raw_chunks:
        try:
            node = ConstituentNode(
                label=str(raw["t"]),
                start=int(raw["i"]),
                end=int(raw["f"]),
                level=int(raw["l"]),
                coindex=_coindex(raw),
                source=raw,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise TreeConstructionError(f"invalid chunk: {raw!r}") from error
        if node.start > node.end:
            raise TreeConstructionError(
                f"invalid span {node.start}-{node.end} for {node.label}"
            )
        chunks.append(node)

    # Attach every non-root chunk to a containing chunk at the nearest lower
    # annotated level. A well-formed Tycho tree normally means level - 1.
    for node in chunks:
        candidates = [
            parent
            for parent in chunks
            if parent is not node
            and parent.level < node.level
            and _contains(parent, node.start, node.end)
        ]
        if candidates:
            highest_level = max(parent.level for parent in candidates)
            nearest = [p for p in candidates if p.level == highest_level]
            parent = min(
                nearest,
                key=lambda p: (p.end - p.start, p.start, chunks.index(p)),
            )
            node.parent = parent
            parent.children.append(node)

    tokens: list[TokenNode] = []
    seen_positions: set[int] = set()
    for raw in raw_tokens:
        try:
            position = int(raw["p"])
            token = TokenNode(
                position=position,
                form=str(raw.get("v", "")),
                tag=str(raw["t"]) if raw.get("t") is not None else None,
                level=int(raw.get("l", 0)),
                token_id=str(raw["tid"]) if raw.get("tid") is not None else None,
                empty_category=bool(raw.get("ec", False)),
                coindex=_coindex(raw),
                source=raw,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise TreeConstructionError(f"invalid token: {raw!r}") from error
        if position in seen_positions:
            raise TreeConstructionError(f"duplicate token position: {position}")
        seen_positions.add(position)
        candidates = [
            chunk
            for chunk in chunks
            if chunk.level <= token.level
            and _contains(chunk, position, position)
        ]
        if not candidates:
            raise TreeConstructionError(
                f"token {position} ({token.form!r}) is outside all chunks"
            )
        highest_level = max(chunk.level for chunk in candidates)
        nearest = [c for c in candidates if c.level == highest_level]
        parent = min(
            nearest,
            key=lambda c: (c.end - c.start, c.start, chunks.index(c)),
        )
        token.parent = parent
        parent.children.append(token)
        tokens.append(token)

    def child_key(node: TreeNode) -> tuple[int, int, int, int]:
        # A constituent precedes a terminal at the same left edge, so its
        # complete yield stays together.
        return (
            node.span[0],
            1 if isinstance(node, TokenNode) else 0,
            node.span[1],
            node.level,
        )

    for chunk in chunks:
        chunk.children.sort(key=child_key)
    roots = sorted(
        (chunk for chunk in chunks if chunk.parent is None),
        key=lambda node: (node.start, node.end, node.level),
    )
    tokens.sort(key=lambda token: token.position)
    translations = sentence.get("translations")
    text_por: str | None = None
    if isinstance(translations, Mapping):
        translation = translations.get("pt-br")
        if translation is not None:
            text_por = str(translation).strip() or None
    return ConstituencyTree(
        roots=roots,
        tokens=tokens,
        sentence_uid=(
            str(sentence["uid"]) 
            if sentence.get("uid") is not None 
            else None
        ),
        sentence_number=sentence_number,
        source_name=source_name,
        text=str(sentence["text"]) if sentence.get("text") is not None else None,
        text_por=text_por,
        status=(
        str(sentence["status"]) if sentence.get("status") is not None else None
        ),
        source_sentence=sentence,
    )


def is_sentence_object(value: Any) -> bool:
    """Return whether a value has the shape of a Tycho sentence object."""
    if not isinstance(value, Mapping):
        return False
    struct = value.get("struct")
    return (
        isinstance(value.get("text"), str)
        and isinstance(struct, Mapping)
        and any(key in struct for key in ("tokens", "chunks", "conllu"))
    )


def iter_sentences(document: JsonObject) -> Iterator[tuple[int, JsonObject]]:
    """Recursively yield ``(one_based_number, sentence)`` in JSON order.

    This follows the discovery strategy used by ``inspect_kadiweu_json.py`` and
    therefore tolerates exports that wrap pages or sentences differently.
    """
    number = 0

    def visit(value: Any) -> Iterator[JsonObject]:
        if is_sentence_object(value):
            yield value
            return
        if isinstance(value, Mapping):
            for child in value.values():
                yield from visit(child)
        elif isinstance(value, list):
            for child in value:
                yield from visit(child)

    for sentence in visit(document):
        number += 1
        yield number, sentence


def find_sentence(
    document: JsonObject,
    *,
    number: int | None = None,
    uid: str | None = None,
) -> tuple[int, JsonObject]:
    """Find exactly one sentence by one-based document number or UID."""
    if (number is None) == (uid is None):
        raise ValueError("supply exactly one of number or uid")
    if number is not None and number < 1:
        raise ValueError("sentence number must be at least 1")
    for current_number, sentence in iter_sentences(document):
        if number == current_number or (
            uid is not None and str(sentence.get("uid", "")) == uid
        ):
            return current_number, sentence
    selector = f"number {number}" if number is not None else f"UID {uid!r}"
    raise LookupError(f"no sentence with {selector}")


def load_document(path: str | Path) -> JsonObject:
    """Load and minimally validate a Tycho JSON document."""
    with Path(path).open(encoding="utf-8") as stream:
        document = json.load(stream)
    if not isinstance(document, Mapping):
        raise TreeConstructionError("top-level JSON value must be an object")
    return document


def print_tree(
    tree: ConstituencyTree,
    *,
    stream: TextIO = sys.stdout,
    show_metadata: bool = True,
    show_spans: bool = False,
    show_positions: bool = False,
) -> None:
    """Pretty-print a reconstructed tree to a text stream."""
    if show_metadata:
        metadata = []
        if tree.sentence_number is not None:
            metadata.append(f"sentence = {tree.sentence_number}")
        if tree.sentence_uid:
            metadata.append(f"uid = {tree.sentence_uid}")
        if tree.status:
            metadata.append(f"status = {tree.status}")
        if tree.text:
            metadata.append(f"text = {tree.text}")
        for item in metadata:
            print(f"# {item}", file=stream)
    print(
        tree.pretty(show_spans=show_spans, show_positions=show_positions),
        file=stream,
    )


def selected_trees(
    document: JsonObject,
    *,
    numbers: Sequence[int] | None = None,
    source_name: str | None = None,
    uids: Sequence[str] | None = None,
    select_all: bool = False,
    statuses: Sequence[str] | None = None,
) -> list[ConstituencyTree]:
    """Return trees selected by number/UID and, optionally, sentence status."""
    if select_all:
        trees = [
            tree_from_sentence(
                sentence,
                sentence_number=number,
                source_name=source_name,
            )
            for number, sentence in iter_sentences(document)
        ]
    elif numbers is not None:
        trees = []
        for number in numbers:
            found_number, sentence = find_sentence(document, number=number)
            trees.append(
                tree_from_sentence(
                sentence,
                sentence_number=found_number,
                source_name=source_name,
                )
            )
    elif uids is not None:
        trees = []
        for uid in uids:
            found_number, sentence = find_sentence(document, uid=uid)
            trees.append(tree_from_sentence(
                sentence, 
                sentence_number=found_number, 
                source_name=source_name
                )
            )
    else:
        trees = []

    if statuses is not None:
        allowed = set(statuses)
        trees = [tree for tree in trees if tree.status in allowed]
    return trees


def write_trees(
    trees: Sequence[ConstituencyTree],
    *,
    stream: TextIO,
    output_format: str = "pretty",
    show_metadata: bool = True,
    show_spans: bool = False,
    show_positions: bool = False,
    trace_format: str = "tycho",
) -> None:
    """Write one or more trees to a text stream."""
    for index, tree in enumerate(trees):
        if index:
            print(file=stream)
        if output_format == "corpussearch":
            print(
                tree.to_corpussearch(
                    show_metadata=show_metadata,
                    trace_format=trace_format,
                ),
                file=stream,
            )
        elif output_format == "lisp":
            if show_metadata:
                if tree.sentence_number is not None:
                    print(f"# sentence = {tree.sentence_number}", file=stream)
                if tree.sentence_uid:
                    print(f"# uid = {tree.sentence_uid}", file=stream)
                if tree.text:
                    print(f"# text = {tree.text}", file=stream)
            print(tree.to_lisp(), file=stream)
        else:
            print_tree(
                tree,
                stream=stream,
                show_metadata=show_metadata,
                show_spans=show_spans,
                show_positions=show_positions,
            )


OUTPUT_EXTENSIONS = {
    "pretty": ".txt",
    "lisp": ".lisp",
    "corpussearch": ".psd",
}


def _filename_component(value: str, *, description: str) -> str:
    """Return a conservative, lowercase filename component."""
    component = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if not component:
        raise ValueError(
            f"{description} {value!r} cannot be represented in a filename"
        )
    return component


def status_suffix(statuses: Sequence[str] | None) -> str | None:
    """Return statuses as a lowercase, hyphen-separated filename suffix."""
    if not statuses:
        return None
    return "-".join(
        _filename_component(status, description="status") for status in statuses
    )


def _short_uid(uid: str, *, length: int = 8) -> str:
    """Return a readable prefix for use in an automatically generated name."""
    component = _filename_component(uid, description="UID")
    return component[:length]


def derived_output_name(
    json_file: Path,
    *,
    output_format: str,
    numbers: Sequence[int] | None,
    uids: Sequence[str] | None,
    select_all: bool,
    statuses: Sequence[str] | None,
    trace_format: str = "tycho",
) -> str:
    """Derive an unambiguous output filename from the input and selection."""
    try:
        extension = OUTPUT_EXTENSIONS[output_format]
    except KeyError as error:
        raise ValueError(f"unsupported output format: {output_format!r}") from error

    parts = [json_file.stem]
    if numbers is not None:
        parts.append("sent-" + "-".join(str(number) for number in numbers))
    elif uids is not None:
        parts.append("uid-" + "-".join(_short_uid(uid) for uid in uids))
    elif not select_all:
        raise ValueError("cannot derive a name without a sentence selection")

    statuses_part = status_suffix(statuses)
    if statuses_part:
        parts.append(statuses_part)
    elif select_all:
        # The unsuffixed name is reserved for the PSD downloaded from Tycho.
        parts.append("all-statuses")

    if output_format == "corpussearch" and trace_format == "corpussearch":
        parts.append("corpussearch")

    return ".".join(parts) + extension


def resolve_output_path(args: argparse.Namespace) -> Path | None:
    """Resolve the exact output path requested by the command line."""
    if args.output is not None:
        return args.output
    if args.output_dir is None:
        return None
    if not args.output_dir.exists():
        raise ValueError(f"output directory does not exist: {args.output_dir}")
    if not args.output_dir.is_dir():
        raise ValueError(f"output directory is not a directory: {args.output_dir}")
    return args.output_dir / derived_output_name(
        args.json_file,
        output_format=args.format,
        numbers=args.numbers,
        uids=args.uids,
        select_all=args.all,
        statuses=args.statuses,
        trace_format=args.trace_format,
    )


def _reject_duplicates(values: Sequence[Any] | None, description: str) -> None:
    """Reject repeated selectors or statuses that obscure user intent."""
    if values is None:
        return
    seen = set()
    duplicates = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    if duplicates:
        rendered = ", ".join(map(str, duplicates))
        raise ValueError(f"duplicate {description}: {rendered}")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reconstruct and print constituency trees from a Tycho JSON dump."
    )
    parser.add_argument("json_file", type=Path, help="Tycho JSON dump")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument(
        "-n",
        "--number",
        "--sentence-number",
        dest="numbers",
        type=int,
        nargs="+",
        metavar="NUMBER",
        help="one or more one-based sentence numbers in JSON order",
    )
    selector.add_argument(
        "-u",
        "--uid",
        dest="uids",
        nargs="+",
        metavar="UID",
        help="one or more sentence UIDs",
    )
    selector.add_argument("--all", action="store_true", help="print every tree")
    parser.add_argument(
        "--show-spans", action="store_true", help="show constituent token spans"
    )
    parser.add_argument(
        "--show-positions", action="store_true", help="show terminal positions"
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help=(
            "omit sentence metadata, including Portuguese translations; "
            "CorpusSearch IDs are retained"
        ),
    )
    parser.add_argument(
        "--status",
        dest="statuses",
        nargs="+",
        metavar="STATUS",
        help="include only sentences with one of these status values",
    )
    parser.add_argument(
        "--format",
        choices=("pretty", "lisp", "corpussearch"),
        default="pretty",
        help="output format (default: pretty)",
    )
    parser.add_argument(
        "--trace-format",
        choices=("tycho", "corpussearch"),
        default="tycho",
        help=(
            "representation of empty-category terminals in CorpusSearch output: "
            "'tycho' produces (NP-TRACE *T*-1), while 'corpussearch' produces "
            "(NP-TRACE (-NONE- *T*-1)); default: tycho"
        ),
    )
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="FILE",
        help="write to this exact filename instead of standard output",
    )
    destination.add_argument(
        "--output-dir",
        type=Path,
        metavar="DIR",
        help="write to DIR using an automatically derived filename",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        _reject_duplicates(args.numbers, "sentence number")
        _reject_duplicates(args.uids, "sentence UID")
        _reject_duplicates(args.statuses, "status")

        if args.trace_format != "tycho" and args.format != "corpussearch":
            raise ValueError(
                "--trace-format corpussearch requires --format corpussearch"
            )

        document = load_document(args.json_file)
        trees = selected_trees(
            document,
            source_name=args.json_file.stem,
            numbers=args.numbers,
            uids=args.uids,
            select_all=args.all,
            statuses=args.statuses,
        )
        if not trees:
            if args.statuses:
                requested = ", ".join(args.statuses)
                raise ValueError(
                    f"selection contains no trees with status: {requested}"
                )
            raise ValueError("selection contains no trees")

        output_path = resolve_output_path(args)
        if output_path is None:
                write_trees(
                trees,
                stream=sys.stdout,
                output_format=args.format,
                show_metadata=not args.no_metadata,
                show_spans=args.show_spans,
                show_positions=args.show_positions,
                trace_format=args.trace_format,
            )
        else:
            if output_path.exists() and output_path.is_dir():
                raise ValueError(f"output path is a directory: {output_path}")
            if not output_path.parent.exists():
                raise ValueError(
                    f"output parent directory does not exist: {output_path.parent}"
                )
            if not output_path.parent.is_dir():
                raise ValueError(
                    f"output parent is not a directory: {output_path.parent}"
                )
            with output_path.open("w", encoding="utf-8", newline="\n") as stream:
                write_trees(
                    trees,
                    stream=stream,
                    output_format=args.format,
                    show_metadata=not args.no_metadata,
                    show_spans=args.show_spans,
                    show_positions=args.show_positions,
                    trace_format=args.trace_format,
                )
            print(output_path)
    except (OSError, json.JSONDecodeError, TreeConstructionError, LookupError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
