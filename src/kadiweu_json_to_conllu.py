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

PRONTYPE_OVERRIDES = {
    ("ajo", "DET"): "Dem",
    ("ijo", "DET"): "Dem",
    ("ica", "DET"): "Dem",
    ("ane", "PRON"): "Rel",
    ("naGajo", "PRON"): "Prs",
}

TAG_TO_DEFAULT_PRONTYPE = {
    ("D", "DET"): "Dem",
    ("WPRO", "PRON"): "Rel",
    ("PRO", "PRON"): "Prs",
    ("PRO$", "PRON"): "Prs",
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

    feats = []

    splits = tok.get("splits", [])
    if not isinstance(splits, list):
        splits = []

    split_tags = normalize_split_tags(tok)

    # Tense/aspect auxiliaries
    if tag == "T":
        if "PFV" in split_tags:
            feats.append("Aspect=Perf")
        if "Imperf" in split_tags:
            feats.append("Aspect=Imp")

    # Negation: keep empty, following your gold sentence 7
    if tag == "NEG":
        return "_"

    # Applicative verbs
    if tag == "VBAPL":
        feats.append("Voice=Appl")

    # Possessor person on nouns such as N$
    # Cases to handle:
    #   t='Gen'  + gloss-br='1'/'2'/'3'  -> Person[psor]=1/2/3
    #   t='3POSS'                        -> Person[psor]=3
    # and similarly for 1POSS / 2POSS if they appear
    for s in splits:
        if not isinstance(s, dict):
            continue

        st = str(s.get("t", ""))
        gloss_br = safe_get(s, "attributes", "gloss-br", default=None)
        gloss_br = str(gloss_br).strip() if gloss_br is not None else None

        if st == "Gen" and gloss_br in {"1", "2", "3"}:
            feats.append(f"Person[psor]={gloss_br}")

        elif st in {"1POSS", "2POSS", "3POSS"}:
            person = st[0]
            feats.append(f"Person[psor]={person}")
            
    upos = infer_upos(tag)

    pron_type = PRONTYPE_OVERRIDES.get((form, upos))
    if pron_type is None:
        pron_type = TAG_TO_DEFAULT_PRONTYPE.get((tag, upos))

    if pron_type:
        feats.append(f"PronType={pron_type}")

    # Remove duplicates and keep stable order
    if feats:
        feats = sorted(set(feats))
        return "|".join(feats)

    return "_"


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

def parse_misc(misc: str) -> List[str]:
    """Split MISC into items, ignoring empty/_."""
    if not misc or misc == "_":
        return []
    return [x for x in misc.split("|") if x and x != "_"]


def join_misc(items: List[str]) -> str:
    """Join MISC items or return '_'."""
    items = [x for x in items if x]
    return "|".join(items) if items else "_"


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

    # -----------------------------------------------------------------
    # Pass 1: identify root and assign obvious relations
    # -----------------------------------------------------------------
    root_id: Optional[int] = None
    root_upos: Optional[str] = None

    for idx, dt in enumerate(draft_tokens):
        labels = chunk_map.get(dt.source_pos, [])

        if dt.upos == "VERB":
            dt.deprel = "root"
            root_id = dt.id
            root_upos = dt.upos
            continue

        if dt.upos == "AUX":
            dt.deprel = "aux"
            continue

        if dt.upos == "PART" and dt.xpos == "NEG":
            dt.deprel = "advmod"
            continue

        if dt.upos == "DET":
            dt.deprel = "det"
            continue

        if dt.upos == "ADV":
            dt.deprel = "advmod"
            continue

        prev_dt = draft_tokens[idx - 1] if idx > 0 else None
        if dt.upos == "PROPN" and prev_dt and prev_dt.upos == "NOUN":
            dt.deprel = "nmod:poss"
            continue

        dt.deprel = "dep"

    # Fallback root if no verbal predicate was found
    if root_id is None and draft_tokens:
        nominal_root = None
        for dt in draft_tokens:
            if dt.upos in {"NOUN", "ADJ", "PROPN", "PRON"}:
                nominal_root = dt
                break

        if nominal_root is not None:
            nominal_root.deprel = "root"
            root_id = nominal_root.id
            root_upos = nominal_root.upos
        else:
            draft_tokens[0].deprel = "root"
            root_id = draft_tokens[0].id
            root_upos = draft_tokens[0].upos

    # -----------------------------------------------------------------
    # Pass 2: controlled recovery of nsubj / obj
    # Rules:
    # - obj only if licensed by a VERB root
    # - at most one obj
    # - at most one nsubj
    # -----------------------------------------------------------------
    nominal_upos = {"NOUN", "PROPN", "PRON"}

    explicit_subj_candidates = []
    fallback_preverbal_candidates = []
    postverbal_candidates = []

    for dt in draft_tokens:
        if dt.deprel != "dep" or dt.upos not in nominal_upos or dt.id == root_id:
            continue

        labels = chunk_map.get(dt.source_pos, [])

        if "NP-SBJ" in labels:
            explicit_subj_candidates.append(dt)
        elif root_id is not None and dt.id < root_id:
            fallback_preverbal_candidates.append(dt)
        elif root_id is not None and dt.id > root_id:
            postverbal_candidates.append(dt)

    # Assign at most one subject
    if explicit_subj_candidates:
        explicit_subj_candidates[0].deprel = "nsubj"
    elif fallback_preverbal_candidates:
        fallback_preverbal_candidates[0].deprel = "nsubj"

    # Assign at most one object, and only with verbal predicates
    if root_upos == "VERB" and postverbal_candidates:
        postverbal_candidates[0].deprel = "obj"

    # Any remaining unresolved nominals stay as dep for manual correction

    # -----------------------------------------------------------------
    # Third pass: assign heads
    # -----------------------------------------------------------------
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

    # Add final punctuation
    punct_head = root_id or 0
    punct_id = len(draft_tokens) + 1
    p_start, p_end = final_punct_range_from_text(text_orig)

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
        "misc": f"SpaceAfter=No|{range_to_misc(p_start, p_end)}",
    })

    # Ensure SpaceAfter=No only on last real token (not inside MWT)
    last_real_idx = None
    for i in range(len(emitted_rows) - 2, -1, -1):
        if "-" not in emitted_rows[i]["id"]:
            last_real_idx = i
            break

    if last_real_idx is not None:
        prev_id = int(emitted_rows[last_real_idx]["id"])
        if prev_id not in mwt_component_ids:
            emitted_rows[last_real_idx]["misc"] = ensure_spaceafter_no(
                emitted_rows[last_real_idx]["misc"]
            )

    # Rebuild # text from rows
    rebuilt_text = build_text_from_rows(emitted_rows)

    for i, line in enumerate(out_lines):
        if line.startswith("# text = "):
            out_lines[i] = f"# text = {rebuilt_text}"
            break

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