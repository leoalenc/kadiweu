#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Basic semi-automatic converter from Kadiwéu Tycho Brahe JSON source documents
to draft UD CoNLL-U.

Goals
-----
- Produce draft CoNLL-U files for manual correction.
- Derive sent_id prefixes from the input filename (e.g. ped-gramm,
  hil-data, van-data) so that sentence identifiers remain stable,
  globally unique, and consistent with the project's gold treebank.
- Handle missing keys robustly.
- Reconstruct split source tokens such as:
      aG@ + @ipegetege -> MWT aGipegetege
- Emit proper CoNLL-U MWT lines.
- Preserve space-aware TokenRange alignment.
- Add metadata in the current project style:
      sent_id, sent_uid, text, text_orig, text_por, text_por_orig,
      text_eng, text_eng_orig
- Use lightweight heuristics learned from manually annotated sentences.

Canonical source files
----------------------
    data/ped-gramm.json
    data/hil-data.json
    data/van-data.json

Canonical draft outputs
-----------------------
    data/treebank/draft-ped-gramm.conllu
    data/treebank/draft-hil-data.conllu
    data/treebank/draft-van-data.conllu

Usage
-----
Convert one source document:

    python3 kadiweu_json_to_conllu.py \
      ../data/ped-gramm.json \
      > ../data/treebank/draft-ped-gramm.conllu

    python3 kadiweu_json_to_conllu.py \
      ../data/hil-data.json \
      > ../data/treebank/draft-hil-data.conllu

    python3 kadiweu_json_to_conllu.py \
      ../data/van-data.json \
      > ../data/treebank/draft-van-data.conllu

Create the combined draft:

    cat \
      ../data/treebank/draft-ped-gramm.conllu \
      ../data/treebank/draft-hil-data.conllu \
      ../data/treebank/draft-van-data.conllu \
      > ../data/treebank/draft-all.conllu
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from kadiweu_empty_categories import resolve_empty_categories
from kadiweu_normalization import get_surface_and_lookup_form

from kadiweu_linguistic_mappings_with_split_tags import (
    LEMMA_OVERRIDES,
    FORM_TO_UPOS,
    FORM_TO_XPOS,
    configure_override_resources,
    infer_lemma,
    infer_feats,
    infer_upos,
    infer_upos_for_form,
    apply_upos_override,
    get_form_correction,
)

from kadiweu_token_ranges import assign_token_ranges_to_emitted_rows


# ---------------------------------------------------------------------
# Project layout defaults
# ---------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_BASE_OVERRIDES_PATH = PROJECT_ROOT / "data" / "resources" / "kadiweu_default_overrides.json"
DEFAULT_GOLD_OVERRIDES_PATH = PROJECT_ROOT / "data" / "resources" / "gold_derived_overrides.json"
DEFAULT_MANUAL_OVERRIDES_PATH = PROJECT_ROOT / "data" / "resources" / "kadiweu_manual_overrides.json"

# ---------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------

STRICT_MWT_CHECK = False

def warn_on_composite_tag_without_mwt(tok):
    form = str(tok.get("v", "")).strip()
    tag = str(tok.get("t", "")).strip()

    if "+" in tag and "@" not in form:
        msg = f"Composite tag without @-style MWT marker: {form} / {tag}"
        if STRICT_MWT_CHECK:
            raise ValueError(msg)
        else:
            print(f"WARNING: {msg}", file=sys.stderr)

def apply_spaceafter_from_text(
    emitted_rows: List[Dict[str, str]],
    text: str,
    mwt_component_ids: Set[int],
) -> None:
    """
    Set SpaceAfter=No from the sentence text, treating `text` as the source of truth.

    Rules:
    - MWT rows may carry SpaceAfter=No.
    - Component rows of an MWT must never carry SpaceAfter=No.
    - Ordinary token rows may carry SpaceAfter=No.
    - Punctuation rows are not handled here.
    """
    cursor = 0
    n = len(text)

    i = 0
    while i < len(emitted_rows):
        row = emitted_rows[i]
        row_id = row["id"]

        # Never keep SpaceAfter=No on MWT component rows
        if "-" not in row_id:
            try:
                num_id = int(row_id)
            except ValueError:
                num_id = None
            if num_id is not None and num_id in mwt_component_ids:
                row["misc"] = remove_spaceafter_no(row["misc"])
                i += 1
                continue

        # Skip spaces in text before matching current surface token
        while cursor < n and text[cursor].isspace():
            cursor += 1

        form = row["form"]
        if text[cursor:cursor + len(form)] != form:
            raise ValueError(
                f"Text/token alignment failed at row {row_id}: "
                f"expected {form!r} at text position {cursor} in {text!r}"
            )

        cursor += len(form)

        # Skip spaces after the token to inspect the next visible character
        next_cursor = cursor
        while next_cursor < n and text[next_cursor].isspace():
            next_cursor += 1

        if next_cursor < n:
            # If the next visible character is not a space-separated continuation,
            # the current surface token must have SpaceAfter=No.
            if next_cursor == cursor:
                row["misc"] = ensure_spaceafter_no(row["misc"])
            else:
                row["misc"] = remove_spaceafter_no(row["misc"])
        else:
            row["misc"] = remove_spaceafter_no(row["misc"])

        i += 1

def safe_get(d: Any, *path: str, default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def normalize_text_ground_truth(text: Optional[str], punct: str = ".") -> Optional[str]:
    if text is None:
        return None
    text = text.strip()
    if not text:
        return text

    # remove whitespace before final punctuation
    text = re.sub(r"\s+([.?!]+)$", r"\1", text)

    # add final punctuation only if missing
    if text.endswith(("...", ".", "!", "?")):
        return text

    return text + punct


def get_proto_rows(sentence: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = safe_get(sentence, "struct", "conllu", default=[])
    return rows if isinstance(rows, list) else []


def get_tokens(sentence: Dict[str, Any]) -> List[Dict[str, Any]]:
    toks = safe_get(sentence, "struct", "tokens", default=[])
    return toks if isinstance(toks, list) else []


def get_chunks(sentence: Dict[str, Any]) -> List[Dict[str, Any]]:
    ch = safe_get(sentence, "struct", "chunks", default=[])
    return ch if isinstance(ch, list) else []


def extract_range(misc: Any) -> Optional[Tuple[int, int]]:
    """
    Accept either:
      "TokenRange=13:24"
    or dict-like misc with TokenRange.
    """
    if isinstance(misc, dict):
        tr = misc.get("TokenRange")
        if isinstance(tr, str):
            m = re.match(r"(\d+):(\d+)$", tr)
            if m:
                return int(m.group(1)), int(m.group(2))
        return None

    if isinstance(misc, str):
        m = re.search(r"TokenRange=(\d+):(\d+)", misc)
        if m:
            return int(m.group(1)), int(m.group(2))
    return None


def build_space_aware_token_ranges(text_orig: str, proto_rows: List[Dict[str, Any]]) -> List[Tuple[int, int]]:
    """
    Build ranges against the real spaced sentence string, not the compact source TokenRange.

    Example:
      text_orig = "liGeladi Maria aGipegetege"
      proto forms = ["liGeladi", "Maria", "aGipegetege"]

    returns:
      [(0, 8), (9, 14), (15, 26)]
    """
    ranges: List[Tuple[int, int]] = []
    cursor = 0

    for row in proto_rows:
        form = str(row.get("form", ""))

        # skip spaces
        while cursor < len(text_orig) and text_orig[cursor].isspace():
            cursor += 1

        if text_orig[cursor:cursor + len(form)] == form:
            start = cursor
            end = cursor + len(form)
            ranges.append((start, end))
            cursor = end
            continue

        # fallback: find next occurrence
        idx = text_orig.find(form, cursor)
        if idx >= 0:
            start = idx
            end = idx + len(form)
            ranges.append((start, end))
            cursor = end
            continue

        # last resort: keep a dummy range
        ranges.append((cursor, cursor + len(form)))
        cursor += len(form)

    return ranges


def range_to_misc(start: int, end: int) -> str:
    return f"TokenRange={start}:{end}"


def final_punct_range(text_orig: str) -> Tuple[int, int]:
    start = len(text_orig)
    end = start + 1
    return start, end


def chunk_membership_for_tokens(tokens: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> Dict[int, List[str]]:
    """
    Map source token position p -> chunk labels containing it.
    """
    memberships: Dict[int, List[str]] = {}

    positions = []
    for tok in tokens:
        p = tok.get("p")
        if isinstance(p, int):
            positions.append(p)
            memberships.setdefault(p, [])

    for ch in chunks:
        if not isinstance(ch, dict):
            continue
        start = ch.get("i")
        end = ch.get("f")
        label = ch.get("t")
        if not isinstance(start, int) or not isinstance(end, int) or label is None:
            continue
        for p in positions:
            if start <= p <= end:
                memberships[p].append(str(label))

    return memberships




def chunk_head_candidates(indices: List[int], draft_tokens: List["DraftToken"]) -> List[int]:
    """Return token indices inside a chunk that are plausible lexical heads."""
    preferred_upos = ("VERB", "NOUN", "PROPN", "PRON", "ADJ", "ADV")
    out: List[int] = []
    for upos in preferred_upos:
        matches = [i for i in indices if draft_tokens[i].upos == upos]
        if matches:
            out.extend(matches)
            break
    if out:
        return out
    return list(indices)


def choose_chunk_head(
    indices: List[int],
    draft_tokens: List["DraftToken"],
    label: Optional[str] = None,
) -> Optional[int]:
    """Choose a lexical head index for one chunk span.

    Heuristic:
    - verbal/predicative chunks: prefer leftmost verbal/predicative head
    - NP-like chunks: prefer leftmost nominal head
    This avoids selecting a noun inside a right-peripheral relative clause
    as the head of the containing NP.
    """
    if not indices:
        return None

    candidates = chunk_head_candidates(indices, draft_tokens)
    if not candidates:
        return None

    np_like = {
        "NP", "NP-SBJ", "NP-ACC", "NP-APL", "NP-LOC", "NP-ADV", "NP-GEN", "NP-PRN"
    }

    if label in np_like:
        nominal_candidates = [
            i for i in candidates
            if draft_tokens[i].upos in {"NOUN", "PROPN", "PRON", "ADJ"}
        ]
        if nominal_candidates:
            return nominal_candidates[0]

    return candidates[0]


def build_chunk_infos(tokens: List[Dict[str, Any]], chunks: List[Dict[str, Any]], draft_tokens: List["DraftToken"]) -> List[Dict[str, Any]]:
    """Build chunk records with token coverage and selected lexical heads."""
    by_source_pos = {dt.source_pos: i for i, dt in enumerate(draft_tokens)}
    infos: List[Dict[str, Any]] = []
    for ch in chunks:
        if not isinstance(ch, dict):
            continue
        start = ch.get("i")
        end = ch.get("f")
        label = ch.get("t")
        level = ch.get("l")
        if not isinstance(start, int) or not isinstance(end, int) or label is None:
            continue
        covered = []
        for p in range(start, end + 1):
            idx = by_source_pos.get(p)
            if idx is not None:
                covered.append(idx)
        if not covered:
            continue
        infos.append({
            "start": start,
            "end": end,
            "label": str(label),
            "level": level if isinstance(level, int) else 999,
            "indices": covered,
            "head_idx": choose_chunk_head(covered, draft_tokens, str(label)),
        })
    infos.sort(key=lambda x: (x["level"], x["start"], x["end"]))
    return infos


def pick_root_index(draft_tokens: List["DraftToken"], chunk_infos: List[Dict[str, Any]]) -> Optional[int]:
    """Choose the clause root using chunk labels before POS fallbacks."""
    # 1. verbal predicates inside VP-like chunks
    for label in ("VP", "IP-MAT", "IP-SUB", "IP-REL"):
        for info in chunk_infos:
            if info["label"] != label:
                continue
            verb_indices = [i for i in info["indices"] if draft_tokens[i].upos == "VERB"]
            if verb_indices:
                return verb_indices[0]

    # 2. any verbal token anywhere in the clause
    for i, dt in enumerate(draft_tokens):
        if dt.upos == "VERB":
            return i

    # 3. explicit predicative chunks
    for label in ("NP-PRD", "ADJP-PRD", "ADVP-PRD"):
        for info in chunk_infos:
            if info["label"] == label and info["head_idx"] is not None:
                return info["head_idx"]

    # 4. older overloaded accusative chunk used predicatively in nonverbal clauses
    for info in chunk_infos:
        if info["label"] == "NP-ACC" and info["head_idx"] is not None:
            return info["head_idx"]

    # 5. bare NP/ADJP/ADVP chunks as weak fallback
    for label in ("NP", "ADJP", "ADVP"):
        for info in chunk_infos:
            if info["label"] == label and info["head_idx"] is not None:
                return info["head_idx"]

    # 6. POS fallback
    for i, dt in enumerate(draft_tokens):
        if dt.upos in {"NOUN", "ADJ", "PROPN", "PRON"}:
            return i
    return 0 if draft_tokens else None


def choose_nominal_attachment_target(
    idx: int,
    draft_tokens: List["DraftToken"],
    root_idx: Optional[int],
    used_indices: Set[int],
) -> Optional[int]:
    """Choose a conservative subject/object-like candidate among bare nominals."""
    if root_idx is None:
        return None
    dt = draft_tokens[idx]
    if dt.upos not in {"NOUN", "PROPN", "PRON"} or idx in used_indices or idx == root_idx:
        return None
    if idx < root_idx:
        return idx
    if idx > root_idx and draft_tokens[root_idx].upos == "VERB":
        return idx
    return None

def is_mwt_start(tok: Dict[str, Any]) -> bool:
    """
    Detect start of a split-token sequence such as:
      tok["v"] = "aG@"
      tok["split"] = {"v": "aGipegetege", "t": "NEG+VBAPL", "idx": 0}
    """
    form = str(tok.get("v", ""))
    split = tok.get("split")
    if not isinstance(split, dict):
        return False
    if split.get("idx") not in (0, "0", None) and "v" not in split:
        return False
    return ("@" in form) and ("v" in split)


def clean_component_form(form: str) -> str:
    """
    Remove boundary placeholders from source token forms:
      aG@ -> aG
      @ipegetege -> ipegetege
    """
    return form.replace("@", "")


def collect_mwt_group(tokens: List[Dict[str, Any]], start_idx: int) -> Tuple[List[Dict[str, Any]], int]:
    """
    Collect one MWT group starting at start_idx.

    Stop when:
    - the next token is not part of an @-style split token, or
    - the next token starts a new MWT (split.idx == 0).
    """
    group = [tokens[start_idx]]
    j = start_idx + 1

    while j < len(tokens):
        tok = tokens[j]
        form = str(tok.get("v", ""))
        split = tok.get("split")

        # Not MWT-like at all -> stop
        if "@" not in form and not (isinstance(split, dict) and "idx" in split):
            break

        # A new split token starts here -> stop before consuming it
        if isinstance(split, dict):
            idx = split.get("idx")
            if idx in (0, "0"):
                break

        group.append(tok)
        j += 1

    return group, j


def mwt_surface_form(group: List[Dict[str, Any]], proto_form: Optional[str]) -> str:
    """
    Prefer explicit combined form from split metadata, else proto form, else concatenate cleaned parts.
    """
    first_split = group[0].get("split")
    if isinstance(first_split, dict):
        v = first_split.get("v")
        if isinstance(v, str) and v:
            return v
    if proto_form:
        return proto_form
    return "".join(clean_component_form(str(tok.get("v", ""))) for tok in group)


def add_spaceafter_no(misc: str) -> str:
    """
    Ensure SpaceAfter=No is present in MISC.
    """
    if not misc or misc == "_":
        return "SpaceAfter=No"

    parts = misc.split("|")
    if "SpaceAfter=No" not in parts:
        parts.insert(0, "SpaceAfter=No")
    return "|".join(parts)

def parse_misc(misc: str) -> List[str]:
    """Split MISC into items, ignoring empty/_."""
    if not misc or misc == "_":
        return []
    return [x for x in misc.split("|") if x and x != "_"]


def join_misc(items: List[str]) -> str:
    """Join MISC items or return '_'."""
    items = [x for x in items if x]
    return "|".join(items) if items else "_"

def add_misc_item(misc: str, item: str) -> str:
    items = parse_misc(misc)
    if item not in items:
        items.append(item)
    return join_misc(items)

def remove_spaceafter_no(misc: str) -> str:
    """Remove SpaceAfter=No from MISC."""
    items = [x for x in parse_misc(misc) if x != "SpaceAfter=No"]
    return join_misc(items)


def ensure_spaceafter_no(misc: str) -> str:
    """Ensure SpaceAfter=No is present in MISC."""
    items = parse_misc(misc)
    if "SpaceAfter=No" not in items:
        items.insert(0, "SpaceAfter=No")
    return join_misc(items)


def build_text_from_rows(rows: List[Dict[str, str]]) -> str:
    """
    Rebuild # text from the emitted surface tokenization.

    Rules:
    - If an MWT line (e.g. 3-4) is present, use its FORM in # text.
    - Skip the component rows covered by that MWT.
    - Otherwise use the ordinary token FORM.
    - Insert a space unless MISC contains SpaceAfter=No.
    """
    parts = []
    i = 0

    while i < len(rows):
        row = rows[i]
        tok_id = row["id"]

        # MWT line: use fused surface form and skip covered component tokens
        if "-" in tok_id:
            start, end = tok_id.split("-", 1)
            start_i = int(start)
            end_i = int(end)

            parts.append(row["form"])
            if "SpaceAfter=No" not in parse_misc(row["misc"]):
                parts.append(" ")

            # Skip component tokens covered by the MWT
            i += 1
            while i < len(rows):
                next_id = rows[i]["id"]
                if "-" in next_id or "." in next_id:
                    break
                try:
                    num_id = int(next_id)
                except ValueError:
                    break
                if start_i <= num_id <= end_i:
                    i += 1
                else:
                    break
            continue

        # Ordinary token
        if "." not in tok_id:
            parts.append(row["form"])
            if "SpaceAfter=No" not in parse_misc(row["misc"]):
                parts.append(" ")

        i += 1

    return "".join(parts).rstrip()


def final_punct_range_from_text(text_orig: str) -> Tuple[int, int]:
    """
    Range of appended final punctuation when original text has none.
    """
    start = len(text_orig)
    end = start + 1
    return start, end

def is_embedded_chunk(info: Dict[str, Any], chunk_infos: List[Dict[str, Any]]) -> bool:
    """Return True if this chunk is dominated by a subordinate/relative clause chunk."""
    embedded_labels = {"IP-SUB", "IP-REL", "CP-REL", "CP-me", "CP-THT"}
    for parent in chunk_infos:
        if parent is info:
            continue
        if parent["label"] not in embedded_labels:
            continue
        if (
            parent["level"] < info["level"]
            and parent["start"] <= info["start"]
            and info["end"] <= parent["end"]
        ):
            return True
    return False


# ---------------------------------------------------------------------
# Conversion heuristics
# ---------------------------------------------------------------------

class DraftToken:
    def __init__(
        self,
        source_pos: int,
        form: str,
        lemma: str,
        upos: str,
        xpos: str,
        feats: str,
        misc: str = "_",
        deprel: str = "dep",
        head: int = 0,
        is_mwt_component: bool = False,
    ):
        self.source_pos = source_pos
        self.form = form
        self.lemma = lemma
        self.upos = upos
        self.xpos = xpos
        self.feats = feats
        self.misc = misc
        self.deprel = deprel
        self.head = head
        self.id: Optional[int] = None
        self.is_mwt_component = is_mwt_component
        self.forced_head_source_pos: Optional[int] = None
        self.locked_deprel: bool = False


def convert_sentence(sentence: Dict[str, Any], sent_index: int, sent_id_prefix: str) -> str:
    text_orig = str(sentence.get("text", "")).strip()
    text = normalize_text_ground_truth(text_orig) or text_orig
    sent_uid = sentence.get("uid", "")

    translations = sentence.get("translations", {}) if isinstance(sentence.get("translations"), dict) else {}
    pt_orig = translations.get("pt-br")
    en_orig = translations.get("en")

    pt_punct = normalize_text_ground_truth(pt_orig)
    en_punct = normalize_text_ground_truth(en_orig)

    proto_rows = get_proto_rows(sentence)
    proto_ranges = build_space_aware_token_ranges(text_orig, proto_rows)
    proto_index = 0

    original_tokens = get_tokens(sentence)
    original_chunks = get_chunks(sentence)

    empty_resolution = resolve_empty_categories(original_tokens, original_chunks)
    tokens = empty_resolution.tokens
    chunks = empty_resolution.chunks
    dependency_hints = empty_resolution.dependency_hints

    chunk_map = chunk_membership_for_tokens(tokens, chunks)

    out_lines: List[str] = []

    # Metadata
    out_lines.append(f"# sent_id = {sent_id_prefix}{sent_index}")
    out_lines.append(f"# sent_uid = {sent_uid}")
    out_lines.append(f"# text = {text}")
    out_lines.append(f"# text_orig = {text_orig}")

    if pt_orig:
        out_lines.append(f"# text_por_orig = {pt_orig}")
    if pt_punct:
        out_lines.append(f"# text_por = {pt_punct}")
    if en_orig:
        out_lines.append(f"# text_eng_orig = {en_orig}")
    if en_punct:
        out_lines.append(f"# text_eng = {en_punct}")

    draft_tokens: List[DraftToken] = []
    mwt_lines: List[Tuple[int, int, str, str]] = []  # start_id, end_id, form, misc

    i = 0
    while i < len(tokens):
        tok = tokens[i] if isinstance(tokens[i], dict) else {}
        surface_form = str(tok.get("v", "")).strip()
        surface_form, lookup_form = get_surface_and_lookup_form(surface_form)
        tag = tok.get("t")

        correction = get_form_correction(lookup_form)

        standard_form = None
        if correction is not None:
            standard_form = correction.get("standard_form")
            if standard_form:
                lookup_form = standard_form

        warn_on_composite_tag_without_mwt(tok)

        # Skip empty garbage safely
        if not surface_form:
            i += 1
            continue

                # MWT handling
        if is_mwt_start(tok):
            group, next_i = collect_mwt_group(tokens, i)

            proto_form = None
            proto_misc = None
            if proto_index < len(proto_rows):
                proto_form = str(proto_rows[proto_index].get("form", ""))
                proto_misc = proto_rows[proto_index].get("misc", "")
            mwt_form = mwt_surface_form(group, proto_form)

            # MWT line will use proto TokenRange if available, but converted to space-aware range
            if proto_index < len(proto_ranges):
                start, end = proto_ranges[proto_index]
                mwt_misc = range_to_misc(start, end)
            else:
                mwt_misc = "_"

            # Record the exact component interval for this MWT
            mwt_start_id = len(draft_tokens) + 1

            # Build component tokens
            for gtok in group:
                gform_raw = str(gtok.get("v", ""))
                gform = clean_component_form(gform_raw)
                surface_form, lookup_form = get_surface_and_lookup_form(gform)
                gtag = str(gtok.get("t", "X"))
                upos = infer_upos(gtag)
                upos = apply_upos_override(lookup_form, gtag, upos)
                lemma = infer_lemma(lookup_form, gtok)
                feats = infer_feats(
                    lookup_form,
                    gtag,
                    gtok,
                    upos=upos,
                    surface_form=surface_form,
                    lemma_override=lemma,
                    feature_source_token=group[0],
                    restrict_split_feats_to_component=True,
                )

                draft = DraftToken(
                    source_pos=int(gtok.get("p", 0) or 0),
                    form=surface_form,
                    lemma=lemma,
                    upos=upos,
                    xpos=gtag,
                    feats=feats,
                    misc="_",
                    deprel="dep",
                    head=0,
                    is_mwt_component=True,
                )
                draft_tokens.append(draft)

            mwt_end_id = len(draft_tokens)

            # Store exact boundaries now, instead of trying to infer them later
            mwt_lines.append((mwt_start_id, mwt_end_id, mwt_form, mwt_misc))

            i = next_i
            proto_index += 1
            continue

        # Regular token
        gtag = str(tag) if tag is not None else "X"
        # --- FIX: normalize punctuation tokens ---
        if surface_form in {".", ",", ":", ";", "!", "?"}:
            upos = "PUNCT"
            gtag = "PUNCT"
            lemma = surface_form
            feats = "_"
        else:
            if correction is not None:
                upos = correction.get("upos")
                if upos is None:
                    upos = FORM_TO_UPOS.get(lookup_form)
                if upos is None:
                    upos = infer_upos_for_form(lookup_form, gtag)

                gtag = correction.get("xpos")
                if gtag is None:
                    gtag = FORM_TO_XPOS.get(lookup_form)
                if gtag is None:
                    gtag = str(tag) if tag is not None else "X"

                lemma = LEMMA_OVERRIDES.get(lookup_form)
                if lemma is None:
                    lemma = LEMMA_OVERRIDES.get(surface_form)
                if lemma is None:
                    lemma = correction.get("standard_lemma")
                if lemma is None:
                    lemma = infer_lemma(lookup_form, tok)
            else:
                upos = FORM_TO_UPOS.get(lookup_form)
                if upos is None:
                    upos = infer_upos(gtag)
                    upos = apply_upos_override(lookup_form, gtag, upos)

                if gtag == "X":
                    gtag = FORM_TO_XPOS.get(lookup_form, gtag)

                lemma = infer_lemma(lookup_form, tok)

            feats = infer_feats(
                lookup_form,
                gtag,
                tok,
                upos=upos,
                surface_form=surface_form,
                lemma_override=lemma,
            )

            if correction is not None and correction.get("feats"):
                correction_feats = correction["feats"].split("|")
                current_feats = [] if feats == "_" else feats.split("|")

                for feat in correction_feats:
                    if feat not in current_feats:
                        current_feats.append(feat)

                feats = "|".join(sorted(set(current_feats))) if current_feats else "_"

        # Range from proto scaffold, converted to space-aware positions
        misc = "_"
        if proto_index < len(proto_ranges):
            start, end = proto_ranges[proto_index]
            misc = range_to_misc(start, end)
        if standard_form is not None and standard_form != surface_form:
            misc = add_misc_item(misc, f"StandardForm={standard_form}")
        draft = DraftToken(
            source_pos=int(tok.get("p", 0) or 0),
            form=surface_form,
            lemma=lemma,
            upos=upos,
            xpos=gtag,
            feats=feats,
            misc=misc,
            deprel="dep",
            head=0,
            is_mwt_component=False,
        )
        draft_tokens.append(draft)

        i += 1
        proto_index += 1

    # Assign sequential IDs to real tokens
    for idx, dt in enumerate(draft_tokens, start=1):
        dt.id = idx

    source_pos_to_dt = {dt.source_pos: dt for dt in draft_tokens}

    for hint in dependency_hints:
        dt = source_pos_to_dt.get(hint.source_pos)
        if dt is None:
            continue
        dt.deprel = hint.deprel
        dt.locked_deprel = True
        dt.forced_head_source_pos = hint.head_source_pos

    resolved_mwt_lines = list(mwt_lines)

    # -----------------------------------------------------------------
    # Chunk-first dependency induction
    # -----------------------------------------------------------------
    chunk_infos = build_chunk_infos(tokens, chunks, draft_tokens)
    root_idx = pick_root_index(draft_tokens, chunk_infos)
    root_id: Optional[int] = None
    root_upos: Optional[str] = None

    if root_idx is not None and draft_tokens:
        root_token = draft_tokens[root_idx]
        root_token.deprel = "root"
        root_token.head = 0
        root_id = root_token.id
        root_upos = root_token.upos

    for idx, dt in enumerate(draft_tokens):
        if idx == root_idx:
            continue
        if dt.locked_deprel:
            continue
        if dt.upos == "AUX":
            dt.deprel = "aux"
        elif dt.upos == "PART" and dt.xpos == "NEG":
            dt.deprel = "advmod"
        elif dt.upos == "DET":
            dt.deprel = "det"
        elif dt.upos == "ADV":
            dt.deprel = "advmod"
        elif dt.upos == "PUNCT":
            dt.deprel = "punct"
        else:
            dt.deprel = "dep"

    used_indices: Set[int] = set()
    if root_idx is not None:
        used_indices.add(root_idx)

    # Strong chunk-driven relations first
    for info in chunk_infos:
        head_idx = info.get("head_idx")
        if head_idx is None or head_idx in used_indices or head_idx == root_idx:
            continue
        if draft_tokens[head_idx].locked_deprel:
            used_indices.add(head_idx)
            continue

        label = info["label"]
        if label == "NP-SBJ":
            draft_tokens[head_idx].deprel = "nsubj"
            used_indices.add(head_idx)
        elif label == "NP-GEN":
            draft_tokens[head_idx].deprel = "nmod:poss"
            used_indices.add(head_idx)
        elif label == "NP-LOC":
            draft_tokens[head_idx].deprel = "obl"
            used_indices.add(head_idx)
        elif label == "NP-ADV":
            draft_tokens[head_idx].deprel = "obl"
            used_indices.add(head_idx)
        elif label == "NP-APL":
            # In the locative applicative constructions currently attested in the
            # pedagogical grammar, the applied locative is a core object.
            #draft_tokens[head_idx].deprel = "obl:arg"
            if root_upos == "VERB":
                draft_tokens[head_idx].deprel = "obj"
            else:
                draft_tokens[head_idx].deprel = "dep"
            used_indices.add(head_idx)
        elif label == "NP-PRN":
            draft_tokens[head_idx].deprel = "appos"
            used_indices.add(head_idx)

    # Ambiguous chunk labels resolved by clause type
    for info in chunk_infos:
        head_idx = info.get("head_idx")
        if head_idx is None or head_idx in used_indices or head_idx == root_idx:
            continue
        if draft_tokens[head_idx].locked_deprel:
            used_indices.add(head_idx)
            continue
        label = info["label"]
        if label == "NP-PRD":
            if root_idx is not None and draft_tokens[root_idx].upos == "VERB":
                draft_tokens[head_idx].deprel = "xcomp"
                used_indices.add(head_idx)
            continue
        if label == "NP-ACC":
            if root_upos == "VERB":
                draft_tokens[head_idx].deprel = "obj"
            else:
                draft_tokens[head_idx].deprel = "nsubj"
            used_indices.add(head_idx)

    # Possessive N$ sequence heuristic:
    # consecutive possessed nominals in the same clause layer often form
    # [head noun + possessor], not two core arguments.
    for idx in range(1, len(draft_tokens)):
        dt = draft_tokens[idx]
        prev_dt = draft_tokens[idx - 1]

        if idx == root_idx or (idx - 1) == root_idx:
            continue
        if idx in used_indices or (idx - 1) in used_indices:
            continue
        if dt.locked_deprel or prev_dt.locked_deprel:
            continue

        if dt.upos == "NOUN" and prev_dt.upos == "NOUN":
            if dt.xpos == "N$" and prev_dt.xpos == "N$":
                # conservative: only apply if both are on the same side of the root
                # and are contiguous in source positions
                if dt.source_pos == prev_dt.source_pos + 1:
                    same_side = (
                        root_idx is None or
                        ((idx < root_idx and (idx - 1) < root_idx) or
                         (idx > root_idx and (idx - 1) > root_idx))
                    )
                    if same_side:
                        dt.deprel = "nmod:poss"
                        used_indices.add(idx)

    # Bare chunk fallbacks
    for info in chunk_infos:
        head_idx = info.get("head_idx")
        if head_idx is None or head_idx in used_indices or head_idx == root_idx:
            continue
        if draft_tokens[head_idx].locked_deprel:
            used_indices.add(head_idx)
            continue
        label = info["label"]
        if label in {"NP", "ADJP", "ADVP"}:
            # Do not promote chunks inside subordinate/relative clauses
            # to matrix subjects/objects.
            if is_embedded_chunk(info, chunk_infos):
                continue
            chosen = choose_nominal_attachment_target(head_idx, draft_tokens, root_idx, used_indices)
            if chosen is None:
                continue
            if chosen < (root_idx if root_idx is not None else -1):
                draft_tokens[chosen].deprel = "nsubj"
            elif root_upos == "VERB":
                draft_tokens[chosen].deprel = "obj"
            else:
                draft_tokens[chosen].deprel = "dep"
            used_indices.add(chosen)

    # Possessive proper-name heuristic retained as weak fallback
    for idx, dt in enumerate(draft_tokens):
        if dt.locked_deprel or dt.deprel != "dep" or dt.upos != "PROPN":
            continue
        prev_dt = draft_tokens[idx - 1] if idx > 0 else None
        if prev_dt and prev_dt.upos == "NOUN":
            dt.deprel = "nmod:poss"

    def demote_extra_core_dependents() -> None:
        if root_idx is None:
            return

        subj_indices = [i for i, dt in enumerate(draft_tokens) if dt.deprel == "nsubj"]
        obj_indices = [i for i, dt in enumerate(draft_tokens) if dt.deprel == "obj"]

        # Keep the leftmost subject, demote later ones.
        for extra in subj_indices[1:]:
            dt = draft_tokens[extra]
            if dt.xpos == "N$":
                dt.deprel = "nmod:poss"
            else:
                dt.deprel = "dep"

        # Keep the leftmost object, demote later ones.
        for extra in obj_indices[1:]:
            draft_tokens[extra].deprel = "dep"

    demote_extra_core_dependents()


    # -----------------------------------------------------------------
    # Head assignment
    # -----------------------------------------------------------------
    for idx, dt in enumerate(draft_tokens):
        if dt.deprel == "root":
            dt.head = 0
            continue
        
        if dt.upos == "PUNCT":
            dt.head = root_id or 0
            continue

        if dt.forced_head_source_pos is not None:
            forced = source_pos_to_dt.get(dt.forced_head_source_pos)
            dt.head = forced.id if forced is not None else (root_id or 0)
            continue

        if dt.deprel == "det":
            target = None
            for later in draft_tokens[idx + 1:]:
                if later.upos in {"NOUN", "PROPN", "PRON", "ADJ"}:
                    target = later.id
                    break
            dt.head = target or root_id or 0
            continue

        if dt.deprel == "aux":
            dt.head = root_id or 0
            continue

        if dt.deprel == "advmod" and dt.xpos == "NEG":
            target = None
            for later in draft_tokens[idx + 1:]:
                if later.upos == "VERB":
                    target = later.id
                    break
            dt.head = target or root_id or 0
            continue

        if dt.deprel == "advmod":
            dt.head = root_id or 0
            continue

        if dt.deprel in {"nsubj", "obj", "obl", "obl:arg", "xcomp"}:
            dt.head = root_id or 0
            continue

        if dt.deprel in {"nmod:poss", "appos"}:
            target = None
            for j in range(idx - 1, -1, -1):
                if draft_tokens[j].upos in {"NOUN", "PROPN", "PRON"}:
                    target = draft_tokens[j].id
                    break
            dt.head = target or root_id or 0
            continue

        dt.head = root_id or 0

    # -----------------------------------------------------------------
    # Clean metadata/writer block (REPLACEMENT)
    # -----------------------------------------------------------------

    # MWT lookup
    mwt_by_start = {start: (end, form, misc) for start, end, form, misc in resolved_mwt_lines}

    # Collect MWT component ids
    mwt_component_ids = set()
    for start, end, _form, _misc in resolved_mwt_lines:
        for tok_id in range(start, end + 1):
            mwt_component_ids.add(tok_id)

    emitted_rows: List[Dict[str, str]] = []

    current_idx = 0
    while current_idx < len(draft_tokens):
        dt = draft_tokens[current_idx]

        # Emit MWT line
        if dt.id in mwt_by_start:
            end, form, misc = mwt_by_start[dt.id]
            emitted_rows.append({
                "id": f"{dt.id}-{end}",
                "form": form,
                "lemma": "_",
                "upos": "_",
                "xpos": "_",
                "feats": "_",
                "head": "_",
                "deprel": "_",
                "deps": "_",
                "misc": misc if misc else "_",
            })

        # Remove SpaceAfter=No from MWT components
        token_misc = dt.misc
        if dt.id in mwt_component_ids:
            token_misc = remove_spaceafter_no(token_misc)

        emitted_rows.append({
            "id": str(dt.id),
            "form": dt.form,
            "lemma": dt.lemma,
            "upos": dt.upos,
            "xpos": dt.xpos,
            "feats": dt.feats,
            "head": str(dt.head),
            "deprel": dt.deprel,
            "deps": "_",
            "misc": token_misc,
        })

        current_idx += 1

    apply_spaceafter_from_text(emitted_rows, text, mwt_component_ids)
    
    # Add final punctuation
    needs_final_punct = bool(text_orig and not str(text_orig).strip().endswith(("...", ".", "!", "?")))
    if needs_final_punct:
        punct_head = root_id or 0
        punct_id = len(draft_tokens) + 1

        emitted_rows.append({
            "id": str(punct_id),
        "form": ".",
        "lemma": ".",
        "upos": "PUNCT",
        "xpos": "PUNCT",
        "feats": "_",
        "head": str(punct_head),
        "deprel": "punct",
        "deps": "_",
        "misc": "SpaceAfter=No",
    })
        
    assign_token_ranges_to_emitted_rows(emitted_rows, text)

    # Serialize
    for row in emitted_rows:
        out_lines.append(
            "\t".join([
                row["id"],
                row["form"],
                row["lemma"],
                row["upos"],
                row["xpos"],
                row["feats"],
                row["head"],
                row["deprel"],
                row["deps"],
                row["misc"],
            ])
        )

    out_lines.append("")

    return "\n".join(out_lines)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
    description="Convert a Kadiwéu Tycho Brahe JSON source document to draft UD CoNLL-U.",
    epilog="""Examples:
        python3 kadiweu_json_to_conllu.py ../data/ped-gramm.json > ../data/treebank/draft-ped-gramm.conllu
        python3 kadiweu_json_to_conllu.py ../data/hil-data.json > ../data/treebank/draft-hil-data.conllu
        python3 kadiweu_json_to_conllu.py ../data/van-data.json > ../data/treebank/draft-van-data.conllu
    """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "json_path",
        nargs="?",
        default=str(PROJECT_ROOT / "data" / "ped-gramm.json"),
        help=(
            "Path to a Kadiwéu Tycho Brahe JSON source document. "
            "Canonical inputs are data/ped-gramm.json, data/hil-data.json, "
            "and data/van-data.json. "
            "Defaults to <project_root>/data/ped-gramm.json."
        ),
    )
    parser.add_argument(
    "--overrides",
    dest="overrides_path",
    type=Path,
    default=None,
    help=(
        "Optional JSON file with additional override resources. "
        "Overrides are applied in layers, with later layers taking precedence:\n"
        "  1. data/resources/kadiweu_default_overrides.json\n"
        "  2. data/resources/gold_derived_overrides.json\n"
        "  3. data/resources/kadiweu_manual_overrides.json\n"
        "  4. this file (if provided via --overrides)\n"
        "The file must contain the keys: lemma_overrides, form_feat_overrides, "
        "prontype_overrides, tag_to_default_prontype."
    ),
)
    return parser.parse_args(argv)


def main(json_path: str, overrides_path: Optional[Path] = None) -> int:
    """
    Convert one Tycho Brahe JSON document into a draft UD CoNLL-U treebank.

    The stem of the input filename is used as the sent_id prefix.
    For example, converting

        ped-gramm.json
        hil-data.json
        van-data.json

    produces sentence identifiers beginning with

        ped-gramm-
        hil-data-
        van-data-

    respectively. This convention guarantees globally unique sentence
    identifiers when multiple source documents are merged into a single
    draft treebank and preserves compatibility with the project's gold
    treebank.
    """
    print(SCRIPT_DIR, file=sys.stderr)
    print(PROJECT_ROOT, file=sys.stderr)
    configure_override_resources(overrides_path)

    data = load_json(Path(json_path))
    sent_id_prefix = Path(json_path).stem + "-"

    pages = data.get("pages", [])
    if not isinstance(pages, list):
        print("ERROR: JSON has no valid 'pages' list.", file=sys.stderr)
        return 1

    sent_index = 1
    for page in pages:
        if not isinstance(page, dict):
            continue
        sentences = page.get("sentences", [])
        if not isinstance(sentences, list):
            continue
        for sentence in sentences:
            if not isinstance(sentence, dict):
                continue
            print(convert_sentence(sentence, sent_index, sent_id_prefix))
            sent_index += 1

    return 0


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(main(args.json_path, args.overrides_path))
