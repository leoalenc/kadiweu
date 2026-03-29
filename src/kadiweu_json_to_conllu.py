#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Basic semi-automatic converter from Tycho Brahe Kadiwéu JSON to draft UD CoNLL-U.

Goals
-----
- Produce a draft CoNLL-U for manual correction.
- Handle missing keys robustly.
- Reconstruct split source tokens such as:
      aG@ + @ipegetege -> MWT aGipegetege
- Emit proper CoNLL-U MWT lines.
- Preserve space-aware TokenRange alignment.
- Add metadata in the user's current style:
      sent_id, sent_uid, text, text_orig, text_por, text_por_orig, text_eng, text_eng_orig
- Use lightweight heuristics learned from the user's manually annotated sentences.

Usage
-----
    python3 kadiweu_json_to_conllu.py gramatica-pedagogica.json > draft.conllu
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------
# Basic mappings
# ---------------------------------------------------------------------

UPOS_MAP = {
    "VB": "VERB",
    "VBAPL": "VERB",
    "VBT": "VERB",
    "VBTAPL": "VERB",
    "VBI": "VERB",
    "N": "NOUN",
    "N$": "NOUN",
    "NAPL": "NOUN",
    "NPR": "PROPN",
    "D": "DET",
    "Q": "DET",
    "PRO": "PRON",
    "PRO$": "PRON",
    "WPRO": "PRON",
    "WADV": "ADV",
    "ADV": "ADV",
    "ADJ": "ADJ",
    "NEG": "PART",
    "C": "SCONJ",
    "CT": "SCONJ",
    "CONJ": "CCONJ",
    "T": "AUX",
    "PUNCT": "PUNCT",
}

# Small lemma overrides from the user's gold sentences.
# Extend as needed.
LEMMA_OVERRIDES = {
    "ajo": "ijo",
    "ica": "ica",
    "ja": "jaG",
    "aG": "ag",
    "etadi": "etidi",
    "iwaGadi": "wagadi",
    "niwatece": "watece",
    "liwatece": "watece",
    "liGeladi": "geladi",
    "loigi": "oigi",
    "ipegitege": "pegi",
    "ipegetege": "pege",
    "ipegitegi": "pegi",
    "GanigotGa": "nigotaGa",
    "Maria": "maria",
}

# Form-specific feature overrides from the user's 10 gold sentences.
# These spare manual correction for common early examples.
FORM_FEAT_OVERRIDES = {
    "ajo": "Deixis=Remt|Gender=Fem|Number=Sing|PronType=Dem",
    "ica": "Gender=Masc|Number=Sing|PronType=Dem",
    "ja": "Aspect=Perf",
    "aG": "_",
    "weiigi": "Gender=Masc|Number=Sing",
    "digoida": "AdvType=Loc|Deixis=Remt|PronType=Dem",
    "Maria": "_",
    "liwatece": "Gender=Fem|Number=Sing|Person[psor]=3",
    "niwatece": "Gender=Fem|Number=Sing",
    "liGeladi": "Gender=Masc|Number=Sing|Person[psor]=3",
    "loigi": "Gender=Masc|Number=Sing|Person[psor]=3",
    "GanigotGa": "Gender=Fem|Number=Sing|Person[psor]=2",
    "etadi": "Gender=Fem|Person=3",
    "iwaGadi": "Mood=Ind|Person=3|VerbForm=Fin",
    "ipegitege": "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl",
    "ipegetege": "Gender[obj]=Fem|Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl",
    "ipegitegi": "Mood=Ind|Person[erg]=3|Person[obj]=3|VerbForm=Fin|Voice=Appl",
}


# ---------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------

def safe_get(d: Any, *path: str, default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def punctuate_if_missing(text: Optional[str], punct: str = ".") -> Optional[str]:
    if text is None:
        return None
    text = text.strip()
    if not text:
        return text
    if text[-1] in ".!?":
        return text
    return text + punct


def normalize_split_tags(token: Dict[str, Any]) -> List[str]:
    splits = token.get("splits", [])
    if not isinstance(splits, list):
        return []
    tags = []
    for s in splits:
        if isinstance(s, dict):
            t = s.get("t")
            if t:
                tags.append(str(t))
    return tags


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
    Collect consecutive placeholder tokens belonging to one MWT.

    Example:
      aG@, @ipegetege
    """
    group = [tokens[start_idx]]
    j = start_idx + 1
    while j < len(tokens):
        form = str(tokens[j].get("v", ""))
        split = tokens[j].get("split")
        if "@" in form or (isinstance(split, dict) and "idx" in split):
            group.append(tokens[j])
            j += 1
        else:
            break
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


def infer_lemma(form: str, tok: Dict[str, Any]) -> str:
    if form in LEMMA_OVERRIDES:
        return LEMMA_OVERRIDES[form]

    splits = tok.get("splits", [])
    if isinstance(splits, list):
        # Prefer lexical-looking split tags
        for s in splits:
            if not isinstance(s, dict):
                continue
            tag = str(s.get("t", ""))
            val = str(s.get("v", ""))
            if tag in {"v", "n"} and val:
                return val
        # Fallback: final split with actual letters
        for s in reversed(splits):
            if not isinstance(s, dict):
                continue
            val = str(s.get("v", ""))
            if val:
                return val

    return form.lower()


def infer_feats(form: str, tag: str, tok: Dict[str, Any]) -> str:
    if form in FORM_FEAT_OVERRIDES:
        return FORM_FEAT_OVERRIDES[form]

    split_tags = normalize_split_tags(tok)
    feats = []

    if tag == "T":
        if "PFV" in split_tags:
            feats.append("Aspect=Perf")
        if "Imperf" in split_tags:
            feats.append("Aspect=Imp")

    if tag == "NEG":
        # Your gold leaves NEG feats empty in sentence 7.
        return "_"

    if tag == "N$":
        if "Gen" in split_tags or "3POSS" in split_tags:
            feats.append("Poss=Yes")

    if tag == "VBAPL":
        feats.append("Voice=Appl")

    return "|".join(feats) if feats else "_"


def infer_upos(tag: str) -> str:
    return UPOS_MAP.get(tag, "X")


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


def convert_sentence(sentence: Dict[str, Any], sent_index: int) -> str:
    text_orig = str(sentence.get("text", "")).strip()
    text = punctuate_if_missing(text_orig) or text_orig
    sent_uid = sentence.get("uid", "")

    translations = sentence.get("translations", {}) if isinstance(sentence.get("translations"), dict) else {}
    pt_orig = translations.get("pt-br")
    en_orig = translations.get("en")

    pt_punct = punctuate_if_missing(pt_orig)
    en_punct = punctuate_if_missing(en_orig)

    proto_rows = get_proto_rows(sentence)
    proto_ranges = build_space_aware_token_ranges(text_orig, proto_rows)
    proto_index = 0

    tokens = get_tokens(sentence)
    chunks = get_chunks(sentence)
    chunk_map = chunk_membership_for_tokens(tokens, chunks)

    out_lines: List[str] = []

    # Metadata
    out_lines.append(f"# sent_id = ped-gramm-{sent_index}")
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
        form = str(tok.get("v", "")).strip()
        tag = tok.get("t")

        # Skip empty garbage safely
        if not form:
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
                mwt_misc = f"SpaceAfter=No|{range_to_misc(start, end)}"
            else:
                mwt_misc = "SpaceAfter=No"

            # Build component tokens
            # Sentence 7 pattern:
            #   aG@ -> aG PART NEG
            #   @ipegetege -> ipegetege VERB VBAPL
            for gtok in group:
                gform_raw = str(gtok.get("v", ""))
                gform = clean_component_form(gform_raw)
                gtag = str(gtok.get("t", "X"))
                upos = infer_upos(gtag)
                lemma = infer_lemma(gform, gtok)
                feats = infer_feats(gform, gtag, gtok)

                draft = DraftToken(
                    source_pos=int(gtok.get("p", 0) or 0),
                    form=gform,
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

            # record placeholder; ids filled later
            mwt_lines.append((-1, -1, mwt_form, mwt_misc))

            i = next_i
            proto_index += 1
            continue

        # Regular token
        gtag = str(tag) if tag is not None else "X"
        upos = infer_upos(gtag)
        lemma = infer_lemma(form, tok)
        feats = infer_feats(form, gtag, tok)

        # Range from proto scaffold, converted to space-aware positions
        misc = "_"
        if proto_index < len(proto_ranges):
            start, end = proto_ranges[proto_index]
            misc = range_to_misc(start, end)
        draft = DraftToken(
            source_pos=int(tok.get("p", 0) or 0),
            form=form,
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

    # Resolve MWT line ids after token ids exist.
    # We assume each MWT occupies a consecutive token interval at creation time.
    mwt_line_index = 0
    cursor = 0
    resolved_mwt_lines: List[Tuple[int, int, str, str]] = []
    while cursor < len(draft_tokens):
        if draft_tokens[cursor].is_mwt_component:
            start = draft_tokens[cursor].id
            end_cursor = cursor
            while end_cursor + 1 < len(draft_tokens) and draft_tokens[end_cursor + 1].is_mwt_component:
                end_cursor += 1
            end = draft_tokens[end_cursor].id
            form, misc = mwt_lines[mwt_line_index][2], mwt_lines[mwt_line_index][3]
            resolved_mwt_lines.append((start, end, form, misc))
            mwt_line_index += 1
            cursor = end_cursor + 1
        else:
            cursor += 1

    # Identify root candidate
    root_id: Optional[int] = None

    # First pass: deprel heuristics
    for idx, dt in enumerate(draft_tokens):
        # chunk labels from original source token position
        labels = chunk_map.get(dt.source_pos, [])

        if dt.upos == "VERB":
            dt.deprel = "root"
            root_id = dt.id
            continue

        if dt.upos == "AUX":
            dt.deprel = "aux"
            continue

        if dt.upos == "PART" and dt.xpos == "NEG":
            # attach later to nearest following verb
            dt.deprel = "advmod"
            continue

        if "NP-SBJ" in labels and dt.upos in {"NOUN", "PROPN", "PRON"}:
            dt.deprel = "nsubj"
            continue

        if dt.upos == "DET":
            dt.deprel = "det"
            continue

        if dt.upos == "ADV":
            dt.deprel = "advmod"
            continue

        # Gold-inspired possessive heuristic:
        # PROPN immediately after a NOUN/N$ often modifies it as possessor.
        prev_dt = draft_tokens[idx - 1] if idx > 0 else None
        if dt.upos == "PROPN" and prev_dt and prev_dt.upos == "NOUN":
            dt.deprel = "nmod:poss"
            continue

        if dt.upos in {"NOUN", "PROPN", "PRON"}:
            dt.deprel = "obj"
            continue

        dt.deprel = "dep"

    # Safety fallback if no verb was found
    if root_id is None and draft_tokens:
        root_id = 1
        draft_tokens[0].deprel = "root"

    # Second pass: heads
    for idx, dt in enumerate(draft_tokens):
        if dt.deprel == "root":
            dt.head = 0
            continue

        if dt.deprel == "det":
            # attach to nearest following nominal if available
            target = None
            for later in draft_tokens[idx + 1:]:
                if later.upos in {"NOUN", "PROPN", "PRON"}:
                    target = later.id
                    break
            dt.head = target or root_id or 0
            continue

        if dt.deprel == "aux":
            dt.head = root_id or 0
            continue

        if dt.deprel == "advmod" and dt.xpos == "NEG":
            # nearest following verb preferred
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

        if dt.deprel == "nsubj":
            dt.head = root_id or 0
            continue

        if dt.deprel == "nmod:poss":
            prev_dt = draft_tokens[idx - 1] if idx > 0 else None
            dt.head = prev_dt.id if prev_dt else (root_id or 0)
            continue

        if dt.deprel == "obj":
            dt.head = root_id or 0
            continue

        dt.head = root_id or 0

        # Because # text includes final punctuation with no intervening space,
    # the last real token must carry SpaceAfter=No.
    if draft_tokens:
        if draft_tokens[-1].misc == "_" or not draft_tokens[-1].misc:
            draft_tokens[-1].misc = "SpaceAfter=No"
        elif "SpaceAfter=No" not in draft_tokens[-1].misc.split("|"):
            draft_tokens[-1].misc = "SpaceAfter=No|" + draft_tokens[-1].misc

    # Build token output with inserted MWT lines
    mwt_by_start = {start: (end, form, misc) for start, end, form, misc in resolved_mwt_lines}

    current_idx = 0
    while current_idx < len(draft_tokens):
        dt = draft_tokens[current_idx]
        if dt.id in mwt_by_start:
            end, form, misc = mwt_by_start[dt.id]
            out_lines.append(f"{dt.id}-{end}\t{form}\t_\t_\t_\t_\t_\t_\t_\t{misc}")

        out_lines.append(
            "\t".join([
                str(dt.id),
                dt.form,
                dt.lemma,
                dt.upos,
                dt.xpos,
                dt.feats,
                str(dt.head),
                dt.deprel,
                "_",
                dt.misc,
            ])
        )
        current_idx += 1

    # Final punctuation token
    p_start, p_end = final_punct_range(text_orig)
    punct_head = root_id or 0
    punct_id = len(draft_tokens) + 1
    out_lines.append(
        f"{punct_id}\t.\t.\tPUNCT\tPUNCT\t_\t{punct_head}\tpunct\t_\tSpaceAfter=No|{range_to_misc(p_start, p_end)}"
    )
    out_lines.append("")  # blank line between sentences

    return "\n".join(out_lines)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main(json_path: str) -> int:
    data = load_json(Path(json_path))

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
            print(convert_sentence(sentence, sent_index))
            sent_index += 1

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 kadiweu_json_to_conllu.py gramatica-pedagogica.json", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))