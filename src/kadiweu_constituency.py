#!/usr/bin/env python3
"""Constituency-tree utilities for Tycho Brahe Platform JSON exports.

This module reconstructs tree objects from ``struct.chunks`` and
``struct.tokens``, provides text and Graphviz renderers, and keeps the original
chunk/token mappings available on every node for later processing.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
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

    def word_pos_sequence(
        self,
        *,
        include_empty_categories: bool = False,
    ) -> list[tuple[str, str]]:
        """Return the sentence yield as ``(word, POS)`` pairs.

        Tokens are returned in their annotated surface order. Empty-category
        terminals, such as traces, are excluded by default because they are
        not overt words. Set ``include_empty_categories`` to ``True`` when
        reproducing the complete terminal yield of an already parsed tree.

        Raises:
            TreeConstructionError: If a selected token has no POS tag.
        """
        sequence: list[tuple[str, str]] = []

        for token in self.tokens:
            if token.empty_category and not include_empty_categories:
                continue
            if token.tag is None:
                raise TreeConstructionError(
                    f"token {token.position} ({token.form!r}) has no POS tag"
                )
            sequence.append((token.form, token.tag))

        return sequence

    def to_corpussearch_pos(
        self,
        *,
        indent: int = 2,
        show_metadata: bool = True,
    ) -> str:
        """Return a flat POS-tagged IP-MAT record for parser-rule input."""
        if indent < 0:
            raise ValueError("indent must be non-negative")

        outer_margin = " " * indent
        terminal_margin = " " * (indent * 2)

        terminals = "\n".join(
            f"{terminal_margin}({tag} {form})"
            for form, tag in self.word_pos_sequence()
        )

        record = (
            "(\n"
            f"{outer_margin}(IP-MAT\n"
            f"{terminals}\n"
            f"{outer_margin})\n"
            f"{outer_margin}(ID {self.corpussearch_id()})\n"
            ")"
        )

        if show_metadata:
            return f"{self.corpussearch_metadata()}\n{record}"
        return record
    
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
        trace_format: str = "corpussearch",
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


@dataclass
class PsdRecord:
    """One CorpusSearch/Penn PSD record with metadata and a tree object."""

    tree: ConstituencyTree
    metadata: dict[str, str]
    corpussearch_id: str | None = None
    raw_comment: str | None = None


def _parse_psd_atom(text: str, index: int) -> tuple[str, int]:
    """Read one non-whitespace, non-parenthesis PSD atom."""
    n = len(text)
    while index < n and text[index].isspace():
        index += 1
    start = index
    while index < n and not text[index].isspace() and text[index] not in "()":
        index += 1
    if start == index:
        raise TreeConstructionError(f"expected PSD atom at offset {index}")
    return text[start:index], index


def _split_indexed_label(value: str) -> tuple[str, tuple[int, ...]]:
    """Split trailing numeric coindices, preserving labels such as NP-SBJ."""
    parts = value.split("-")
    indices: list[int] = []
    while parts and parts[-1].isdigit():
        indices.append(int(parts.pop()))
    indices.reverse()
    return "-".join(parts), tuple(indices)


def _parse_psd_sexpr(text: str, index: int = 0) -> tuple[Any, int]:
    """Parse the small S-expression subset used by the project PSD files."""
    n = len(text)
    while index < n and text[index].isspace():
        index += 1
    if index >= n:
        raise TreeConstructionError("unexpected end of PSD record")
    if text[index] != "(":
        return _parse_psd_atom(text, index)
    index += 1
    items: list[Any] = []
    while True:
        while index < n and text[index].isspace():
            index += 1
        if index >= n:
            raise TreeConstructionError("unclosed parenthesis in PSD record")
        if text[index] == ")":
            return items, index + 1
        item, index = _parse_psd_sexpr(text, index)
        items.append(item)


def _metadata_from_comment(comment: str | None) -> dict[str, str]:
    metadata: dict[str, str] = {}
    if not comment:
        return metadata
    body = comment[2:-2] if comment.startswith("/*") and comment.endswith("*/") else comment
    for line in body.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            metadata[key] = value.strip()
    return metadata


def _iter_psd_record_texts(text: str) -> Iterator[tuple[str | None, str]]:
    """Yield ``(preceding_comment, balanced_record_text)`` from a PSD document."""
    i = 0
    n = len(text)
    pending_comment: str | None = None
    while i < n:
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise TreeConstructionError("unclosed block comment in PSD file")
            pending_comment = text[i:end + 2]
            i = end + 2
            continue
        if text[i].isspace():
            i += 1
            continue
        if text[i] != "(":
            # Tolerate harmless non-record text between records.
            i += 1
            continue
        start = i
        depth = 0
        while i < n:
            if text.startswith("/*", i):
                end = text.find("*/", i + 2)
                if end < 0:
                    raise TreeConstructionError("unclosed block comment inside PSD record")
                i = end + 2
                continue
            ch = text[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    i += 1
                    yield pending_comment, text[start:i]
                    pending_comment = None
                    break
            i += 1
        else:
            raise TreeConstructionError("unclosed PSD record")


def tree_from_psd_record(record_text: str, *, metadata: Mapping[str, str] | None = None) -> tuple[ConstituencyTree, str | None]:
    """Build a :class:`ConstituencyTree` from one project PSD record."""
    sexpr, end = _parse_psd_sexpr(record_text)
    if record_text[end:].strip():
        raise TreeConstructionError("unexpected text after PSD record")
    if not isinstance(sexpr, list):
        raise TreeConstructionError("PSD record must be a list")

    # CorpusSearch records have an unlabeled outer wrapper containing one or
    # more roots and a final (ID ...).
    children = sexpr
    corpussearch_id: str | None = None
    root_exprs: list[Any] = []
    for child in children:
        if isinstance(child, list) and len(child) >= 2 and child[0] == "ID":
            corpussearch_id = str(child[1])
        else:
            root_exprs.append(child)
    if not root_exprs:
        raise TreeConstructionError("PSD record has no syntactic root")

    position = 0
    tokens: list[TokenNode] = []

    def convert(expr: Any, level: int) -> ConstituentNode:
        nonlocal position
        if not isinstance(expr, list) or not expr:
            raise TreeConstructionError(f"invalid constituent expression: {expr!r}")
        raw_label = str(expr[0])
        label, coindex = _split_indexed_label(raw_label)
        node = ConstituentNode(label=label, start=0, end=0, level=level, coindex=coindex)
        children_expr = expr[1:]

        # Tycho trace shorthand: (NP-TRACE *T*-1).  Keep the dominating NP
        # and represent the trace as an empty terminal.
        if len(children_expr) == 1 and isinstance(children_expr[0], str) and str(children_expr[0]).startswith("*"):
            position += 1
            form, token_coindex = _split_indexed_label(str(children_expr[0]))
            token = TokenNode(position=position, form=form, tag=None, level=level, empty_category=True, coindex=token_coindex)
            token.parent = node
            node.children.append(token)
            tokens.append(token)
            node.start = node.end = position
            return node

        # Preterminal: (N word), including punctuation tags.
        if len(children_expr) == 1 and isinstance(children_expr[0], str):
            position += 1
            form, token_coindex = _split_indexed_label(str(children_expr[0]))
            token = TokenNode(position=position, form=form, tag=label, level=level, coindex=token_coindex)
            token.parent = node
            node.children.append(token)
            tokens.append(token)
            node.start = node.end = position
            return node

        for child_expr in children_expr:
            if not isinstance(child_expr, list):
                raise TreeConstructionError(f"unexpected bare atom under {raw_label}: {child_expr!r}")
            # CorpusSearch trace form: (-NONE- *T*-1).  Attach only the empty
            # terminal, not an artificial -NONE- constituent.
            if len(child_expr) == 2 and child_expr[0] == "-NONE-" and isinstance(child_expr[1], str):
                position += 1
                form, token_coindex = _split_indexed_label(str(child_expr[1]))
                token = TokenNode(position=position, form=form, tag=None, level=level + 1, empty_category=True, coindex=token_coindex)
                token.parent = node
                node.children.append(token)
                tokens.append(token)
                continue
            # Ordinary PSD preterminal, e.g. (N wetiGa), becomes a TokenNode
            # directly. This matches JSON-derived trees, where POS tags are
            # terminal labels rather than an extra constituent layer.
            if len(child_expr) == 2 and isinstance(child_expr[0], str) and isinstance(child_expr[1], str):
                position += 1
                token_label, label_coindex = _split_indexed_label(str(child_expr[0]))
                form, token_coindex = _split_indexed_label(str(child_expr[1]))
                token = TokenNode(
                    position=position,
                    form=form,
                    tag=token_label,
                    level=level + 1,
                    coindex=token_coindex or label_coindex,
                )
                token.parent = node
                node.children.append(token)
                tokens.append(token)
                continue
            child = convert(child_expr, level + 1)
            child.parent = node
            node.children.append(child)

        spans = [child.span for child in node.children]
        if not spans:
            raise TreeConstructionError(f"empty constituent in PSD record: {raw_label}")
        node.start = min(start for start, _ in spans)
        node.end = max(end for _, end in spans)
        return node

    roots = [convert(expr, 0) for expr in root_exprs]
    md = dict(metadata or {})
    sent_number = None
    if md.get("sentence"):
        try:
            sent_number = int(md["sentence"])
        except ValueError:
            pass
    source_name = None
    if corpussearch_id and "," in corpussearch_id:
        source_name = corpussearch_id.split(",", 1)[0]
    tree = ConstituencyTree(
        roots=roots,
        tokens=tokens,
        sentence_uid=md.get("uid"),
        sentence_number=sent_number,
        source_name=source_name,
        text=md.get("text"),
        text_por=md.get("text_por"),
        status=md.get("status"),
    )
    return tree, corpussearch_id


def iter_psd_records(path: str | Path) -> Iterator[PsdRecord]:
    """Read project PSD records without altering their original file."""
    text = Path(path).read_text(encoding="utf-8")
    for comment, record_text in _iter_psd_record_texts(text):
        metadata = _metadata_from_comment(comment)
        tree, corpussearch_id = tree_from_psd_record(record_text, metadata=metadata)
        yield PsdRecord(tree=tree, metadata=metadata, corpussearch_id=corpussearch_id, raw_comment=comment)


def render_tree_text(
    tree: ConstituencyTree,
    *,
    style: str = "unicode",
    show_spans: bool = False,
    show_positions: bool = False,
) -> str:
    """Render a compact line-oriented tree for terminals or PSD comments.

    ``unicode`` uses box-drawing characters. ``ascii`` is deliberately plain
    so generated PSD files remain friendly to conservative command-line tools.
    """
    if style not in {"unicode", "ascii"}:
        raise ValueError("style must be 'unicode' or 'ascii'")
    lines: list[str] = []
    if style == "unicode":
        tee, elbow, pipe, blank = "├── ", "└── ", "│   ", "    "
    else:
        tee, elbow, pipe, blank = "+-- ", "`-- ", "|   ", "    "

    def label_for(node: TreeNode) -> str:
        if isinstance(node, ConstituentNode):
            return node.display_label(show_spans=show_spans)
        if node.empty_category:
            value = node.form + "".join(f"-{i}" for i in node.coindex)
            label = f"-NONE- {value}"
            return f"{node.position}: {label}" if show_positions else label
        label = f"{node.label} {node.form}"
        if node.coindex:
            label += "-" + ",".join(map(str, node.coindex))
        if show_positions:
            label = f"{node.position}: {label}"
        return label

    def visit(node: TreeNode, prefix: str, last: bool, top: bool) -> None:
        lines.append(prefix + ("" if top else (elbow if last else tee)) + label_for(node))
        if not isinstance(node, ConstituentNode):
            return
        next_prefix = prefix if top else prefix + (blank if last else pipe)
        for i, child in enumerate(node.children):
            visit(child, next_prefix, i == len(node.children) - 1, False)

    for i, root in enumerate(tree.roots):
        visit(root, "", i == len(tree.roots) - 1, True)
    return "\n".join(lines)


GRAPHVIZ_FORMATS = {"pdf", "png", "svg", "dot"}


def tree_to_graphviz_dot(
    tree: ConstituencyTree,
    *,
    comments: str | None = None,
) -> str:
    """Return a Graphviz DOT representation of one constituency tree.

    When supplied, ``comments`` is printed as a left-aligned metadata heading
    above the tree.  The caller decides whether comment delimiters are kept.
    """
    lines = [
        "digraph constituency_tree {",
        '  graph [rankdir=TB, ordering=out, bgcolor="white", margin="0.15"];',
        '  node [fontname="DejaVu Sans", fontsize=11, shape=box, '
        'style="rounded", margin="0.08,0.04"];',
        '  edge [color="#555555", penwidth=0.8, arrowsize=0];',
    ]
    if comments is not None:
        heading = comments.strip("\n")
        lines.extend([
            f"  label={json.dumps(heading, ensure_ascii=False)};",
            '  labelloc="t";',
            '  labeljust="l";',
            '  fontname="DejaVu Sans Mono";',
            "  fontsize=10;",
        ])
    next_id = 0

    def add_node(node: TreeNode) -> str:
        nonlocal next_id
        node_id = f"n{next_id}"
        next_id += 1
        if isinstance(node, ConstituentNode):
            label = node.label
            if node.coindex:
                label += "-" + ",".join(map(str, node.coindex))
            attributes = f"label={json.dumps(label, ensure_ascii=False)}"
        else:
            form = node.form + "".join(f"-{i}" for i in node.coindex)
            tag = "-NONE-" if node.empty_category else node.label
            label = f"{tag}\n{form}"
            attributes = (
                f"label={json.dumps(label, ensure_ascii=False)}, "
                'shape=plaintext, style=""'
            )
        lines.append(f"  {node_id} [{attributes}];")
        if isinstance(node, ConstituentNode):
            child_ids = [add_node(child) for child in node.children]
            for child_id in child_ids:
                lines.append(f"  {node_id} -> {child_id};")
            for left, right in zip(child_ids, child_ids[1:]):
                lines.append(
                    f"  {left} -> {right} "
                    '[style=invis, weight=10, constraint=false];'
                )
        return node_id

    root_ids = [add_node(root) for root in tree.roots]
    for left, right in zip(root_ids, root_ids[1:]):
        lines.append(
            f"  {left} -> {right} [style=invis, weight=10, constraint=false];"
        )
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_tree_graphviz(
    tree: ConstituencyTree,
    output_path: str | Path,
    *,
    output_format: str = "pdf",
    dot_command: str = "dot",
    comments: str | None = None,
) -> Path:
    """Render one tree with Graphviz to PDF, PNG, SVG, or DOT."""
    if output_format not in GRAPHVIZ_FORMATS:
        supported = ", ".join(sorted(GRAPHVIZ_FORMATS))
        raise ValueError(
            f"unsupported Graphviz format {output_format!r}; choose: {supported}"
        )
    path = Path(output_path)
    if not path.parent.exists():
        raise ValueError(f"output parent directory does not exist: {path.parent}")
    if path.exists() and path.is_dir():
        raise ValueError(f"output path is a directory: {path}")
    dot_source = tree_to_graphviz_dot(tree, comments=comments)
    if output_format == "dot":
        path.write_text(dot_source, encoding="utf-8", newline="\n")
        return path
    executable = shutil.which(dot_command)
    if executable is None:
        raise TreeConstructionError(
            f"Graphviz executable {dot_command!r} was not found; "
            "install Graphviz (on Ubuntu: sudo apt install graphviz)"
        )
    try:
        subprocess.run(
            [executable, f"-T{output_format}", "-o", str(path)],
            input=dot_source,
            text=True,
            encoding="utf-8",
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()
        raise TreeConstructionError(
            f"Graphviz failed to render {output_format}"
            + (f": {detail}" if detail else "")
        ) from error
    return path

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
    trace_format: str = "corpussearch",
) -> None:
    """Write one or more trees to a text stream."""
    for index, tree in enumerate(trees):
        if index:
            print(file=stream)
        if output_format == "corpussearch-pos":
            print(
                tree.to_corpussearch_pos(
                    show_metadata=show_metadata,
                ),
                file=stream,
            )
        elif output_format == "corpussearch":
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
    "corpussearch-pos": ".pos",
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
    trace_format: str = "corpussearch",
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
        choices=("pretty", "lisp", "corpussearch", "corpussearch-pos"),
        default="pretty",
        help="output format (default: pretty)",
    )
    parser.add_argument(
        "--trace-format",
        choices=("tycho", "corpussearch"),
        default="corpussearch",
        help=(
            "representation of empty-category terminals in CorpusSearch output: "
            "'tycho' produces (NP-TRACE *T*-1), while 'corpussearch' produces "
            "(NP-TRACE (-NONE- *T*-1)); default: corpussearch"
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

        if args.trace_format != "corpussearch" and args.format != "corpussearch":
            raise ValueError(
                "--trace-format tycho requires --format corpussearch"
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
