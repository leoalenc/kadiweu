#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Utilities to explore the Kadiwéu lexicon stored in ``lexicon-kadiweu.json``.

This module is meant for interactive Python use and command-line inspection.
It provides:

- lookup by word or morpheme;
- multi-field search (default) and single-field search;
- substring, whole-word, exact, and regex search modes;
- filters by raw POS/tag, inferred UD UPOS, grammar, editorial status, and
  semantic cues from definitions/senses;
- basic heuristics useful for UD treebank construction and future conversion
  from Penn-style tags to UD annotations.

Example
-------
>>> lex = KadiweuLexicon("lexicon-kadiweu.json")
>>> lex.look_up("abaciǥegi")
>>> lex.search("preguiç")[:5]
>>> lex.search_field("definition", "preguiç", mode="word")
>>> lex.search_by_pos_semantics(pos="VB", semantic_cues=["futuro", "tempo"])
>>> lex.ud_candidates("AUX")[:10]
>>> lex.conversion_hints("domaGa")

Command-line examples
---------------------
python kadiweu_lexicon_explorer.py lexicon-kadiweu.json lookup abaciǥegi
python kadiweu_lexicon_explorer.py lexicon-kadiweu.json search preguiç
python kadiweu_lexicon_explorer.py lexicon-kadiweu.json field definition preguiç --mode word
python kadiweu_lexicon_explorer.py lexicon-kadiweu.json semantic --pos VB --cue futuro --cue tempo
python kadiweu_lexicon_explorer.py lexicon-kadiweu.json ud AUX --limit 20
python kadiweu_lexicon_explorer.py lexicon-kadiweu.json hints domaGa
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence

JsonDict = Dict[str, Any]

SPECIAL_CHAR_MAP = str.maketrans(
    {
        "ǥ": "g",
        "Ɠ": "G",
        "ɡ": "g",
        "º": "o",
    }
)

TEXTUAL_FIELDS = (
    "name",
    "definition",
    "grammar",
    "tag",
    "usageNotes",
    "plurals",
    "lexicon",
    "status",
    "abbr",
)

SEMANTIC_FIELDS = ("definition", "senses.definition", "usageNotes", "attributes.gloss", "attributes.gloss-br")

WORD_CHARS = r"\w\-+'’"


_RAW_TO_UD_BASE = {
    "N": "NOUN",
    "N$": "NOUN",
    "NAPL": "NOUN",
    "N$APL": "NOUN",
    "NPR": "PROPN",
    "NUM": "NUM",
    "Num": "NUM",
    "D": "DET",
    "DEM": "DET",
    "Q": "DET",
    "QAPL": "DET",
    "PRO": "PRON",
    "PRO$": "PRON",
    "$PRO": "PRON",
    "NPRO": "PRON",
    "WPRO": "PRON",
    "WADV": "ADV",
    "ADV": "ADV",
    "ADVNEG": "ADV",
    "ADJ": "ADJ",
    "M": "PART",
    "MOD": "PART",
    "NEG": "PART",
    "CNEG": "SCONJ",
    "CONJ": "CCONJ",
    "C": "SCONJ",
    "P": "ADP",
    "VB": "VERB",
    "VBI": "VERB",
    "VBT": "VERB",
    "VBAPL": "VERB",
    "VBTAPL": "VERB",
    "AUX": "AUX",
    "T": "AUX",
    "EV": "PART",
    "REP": "PART",
    "INTJ": "INTJ",
    "FP": "PUNCT",
    ":": "PUNCT",
    "CT": "PART",
    "CT+EV": "PART",
    "Der": "X",
}


def normalize_text(text: Any) -> str:
    """Return a simplified string for accent-insensitive matching."""
    if text is None:
        return ""
    text = str(text).translate(SPECIAL_CHAR_MAP).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


class KadiweuLexicon:
    """Explorer for the Kadiwéu lexicon JSON file."""

    def __init__(self, json_path: str | Path):
        self.path = Path(json_path)
        with self.path.open("r", encoding="utf-8") as f:
            self.entries: List[JsonDict] = json.load(f)

        if not isinstance(self.entries, list):
            raise ValueError("The JSON root must be a list of entries.")

        self._uid_index: Dict[str, JsonDict] = {}
        self._name_index: Dict[str, List[JsonDict]] = defaultdict(list)
        self._normalized_name_index: Dict[str, List[JsonDict]] = defaultdict(list)
        self._field_cache: Dict[str, Dict[int, str]] = defaultdict(dict)

        for i, entry in enumerate(self.entries):
            entry["__index__"] = i
            uid = entry.get("uid")
            if uid:
                self._uid_index[uid] = entry

            name = entry.get("name")
            if name:
                self._name_index[str(name)].append(entry)
                self._normalized_name_index[normalize_text(name)].append(entry)

    def __len__(self) -> int:
        return len(self.entries)

    def all_names(self) -> List[str]:
        return sorted(self._name_index)

    def list_fields(self) -> List[str]:
        """Return searchable fields, including dotted pseudo-fields."""
        fields = set(TEXTUAL_FIELDS)
        fields.update(
            {
                "senses.definition",
                "related.name",
                "variants.name",
                "attributes.gloss",
                "attributes.gloss-br",
                "conjugations.values",
                "morphemes",
            }
        )
        return sorted(fields)

    def get_by_uid(self, uid: str) -> Optional[JsonDict]:
        return self._uid_index.get(uid)

    def look_up(
        self,
        query: str,
        *,
        exact: bool = False,
        normalize: bool = True,
        limit: Optional[int] = None,
    ) -> List[JsonDict]:
        if not query:
            return []

        if normalize:
            q = normalize_text(query)
            if exact and q in self._normalized_name_index:
                results = list(self._normalized_name_index[q])
            else:
                results = [
                    entry
                    for entry in self.entries
                    if q in normalize_text(entry.get("name", ""))
                ]
        else:
            if exact and query in self._name_index:
                results = list(self._name_index[query])
            else:
                results = [entry for entry in self.entries if query in str(entry.get("name", ""))]

        return self._trim(results, limit)

    def search(
        self,
        query: str,
        *,
        fields: Optional[Sequence[str]] = None,
        mode: str = "substring",
        normalize: bool = True,
        limit: Optional[int] = None,
    ) -> List[JsonDict]:
        """Search text in one or more fields.

        Parameters
        ----------
        query:
            Text or regex pattern.
        fields:
            Fields to search. If omitted, use a broad multi-field search.
        mode:
            One of: ``substring`` (default), ``word``, ``exact``, ``regex``.
            ``word`` approximates ``grep -Ew``.
        normalize:
            Whether to normalize both query and haystack.
        """
        if not query:
            return []
        chosen_fields = tuple(fields) if fields else (
            "name",
            "definition",
            "senses.definition",
            "grammar",
            "tag",
            "usageNotes",
            "plurals",
            "lexicon",
            "status",
            "attributes.gloss",
            "attributes.gloss-br",
            "conjugations.values",
            "related.name",
            "variants.name",
        )
        results = [
            entry
            for entry in self.entries
            if self._matches_entry(entry, query, fields=chosen_fields, mode=mode, normalize=normalize)
        ]
        return self._trim(results, limit)

    def search_field(
        self,
        field: str,
        query: str,
        *,
        mode: str = "substring",
        normalize: bool = True,
        limit: Optional[int] = None,
    ) -> List[JsonDict]:
        """Search a single field only."""
        return self.search(query, fields=[field], mode=mode, normalize=normalize, limit=limit)

    def search_by_text(
        self,
        query: str,
        *,
        fields: Optional[Sequence[str]] = None,
        mode: str = "substring",
        normalize: bool = True,
        limit: Optional[int] = None,
    ) -> List[JsonDict]:
        """Backward-compatible alias for :meth:`search`."""
        return self.search(query, fields=fields, mode=mode, normalize=normalize, limit=limit)

    def search_by_tag(self, tag: str, *, exact: bool = True, limit: Optional[int] = None) -> List[JsonDict]:
        q = normalize_text(tag)
        results = []
        for entry in self.entries:
            tag_value = normalize_text(entry.get("tag", ""))
            if (tag_value == q) if exact else (q in tag_value):
                results.append(entry)
        return self._trim(results, limit)

    def search_by_grammar(self, grammar: str, *, exact: bool = False, limit: Optional[int] = None) -> List[JsonDict]:
        q = normalize_text(grammar)
        results = []
        for entry in self.entries:
            grammar_value = normalize_text(entry.get("grammar", ""))
            if (grammar_value == q) if exact else (q in grammar_value):
                results.append(entry)
        return self._trim(results, limit)

    def search_by_status(self, status: str, *, exact: bool = True, limit: Optional[int] = None) -> List[JsonDict]:
        q = normalize_text(status)
        results = []
        for entry in self.entries:
            status_value = normalize_text(entry.get("status", ""))
            if (status_value == q) if exact else (q in status_value):
                results.append(entry)
        return self._trim(results, limit)

    def search_by_pos_semantics(
        self,
        *,
        pos: Optional[str] = None,
        ud_upos: Optional[str] = None,
        semantic_cues: Optional[Sequence[str]] = None,
        raw_tag_contains: bool = False,
        grammar: Optional[str] = None,
        status: Optional[str] = None,
        mode: str = "substring",
        limit: Optional[int] = None,
    ) -> List[JsonDict]:
        """Filter entries by raw POS/tag or inferred UD UPOS plus semantic cues.

        This is useful when building inventories for UD annotation, e.g. likely
        auxiliaries, determiners, interrogatives, negation markers, evidentials,
        temporal markers, or discourse particles.
        """
        cues = list(semantic_cues or [])
        results: List[JsonDict] = []

        for entry in self.entries:
            if pos:
                raw = normalize_text(entry.get("tag", ""))
                wanted = normalize_text(pos)
                if raw_tag_contains:
                    if wanted not in raw:
                        continue
                elif raw != wanted:
                    continue

            if ud_upos:
                inferred = self.infer_ud_upos(entry)
                if inferred != ud_upos.upper():
                    continue

            if grammar:
                grammar_value = normalize_text(entry.get("grammar", ""))
                wanted_grammar = normalize_text(grammar)
                if wanted_grammar not in grammar_value:
                    continue

            if status:
                status_value = normalize_text(entry.get("status", ""))
                if status_value != normalize_text(status):
                    continue

            if cues and not all(
                self._matches_entry(entry, cue, fields=SEMANTIC_FIELDS, mode=mode, normalize=True)
                for cue in cues
            ):
                continue

            results.append(entry)

        return self._trim(results, limit)

    def filter_entries(
        self,
        *,
        pos: Optional[str] = None,
        ud_upos: Optional[str] = None,
        grammar: Optional[str] = None,
        status: Optional[str] = None,
        semantic_cues: Optional[Sequence[str]] = None,
        mode: str = "substring",
        has_conjugations: Optional[bool] = None,
        has_nominal_paradigms: Optional[bool] = None,
        has_variants: Optional[bool] = None,
        mark_to_delete: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[JsonDict]:
        """General-purpose combined filter."""
        results = self.search_by_pos_semantics(
            pos=pos,
            ud_upos=ud_upos,
            grammar=grammar,
            status=status,
            semantic_cues=semantic_cues,
            mode=mode,
            limit=None,
        )

        filtered: List[JsonDict] = []
        for entry in results:
            if has_conjugations is not None and bool(entry.get("conjugations")) != has_conjugations:
                continue
            if has_nominal_paradigms is not None and bool(entry.get("nominalParadigms")) != has_nominal_paradigms:
                continue
            if has_variants is not None and bool(entry.get("variants")) != has_variants:
                continue
            if mark_to_delete is not None and bool(entry.get("markToDelete")) != mark_to_delete:
                continue
            filtered.append(entry)
        return self._trim(filtered, limit)

    def infer_ud_upos(self, item: str | JsonDict) -> str:
        """Infer a likely UD UPOS from the lexicon entry.

        This is heuristic and should be treated as a suggestion for conversion,
        not as a final annotation.
        """
        entry = item if isinstance(item, dict) else self._first_match(item)
        if entry is None:
            raise KeyError(f"Entry not found: {item!r}")

        raw_tag = (entry.get("tag") or "").strip()
        grammar = normalize_text(entry.get("grammar", ""))
        definition = normalize_text(entry.get("definition", ""))
        senses = normalize_text(self._field_text(entry, "senses.definition", normalize=True))
        text = " | ".join(x for x in (grammar, definition, senses) if x)

        if raw_tag in _RAW_TO_UD_BASE:
            base = _RAW_TO_UD_BASE[raw_tag]
        else:
            parts = [p for p in re.split(r"[+\s]+", raw_tag) if p]
            mapped_parts = [_RAW_TO_UD_BASE.get(p) for p in parts if _RAW_TO_UD_BASE.get(p)]
            base = mapped_parts[-1] if mapped_parts else "X"

        # Heuristic adjustments from grammar/definition.
        if "interrog" in text and base in {"DET", "PRON", "ADV", "X"}:
            if "onde" in text or "quando" in text or "como" in text:
                return "ADV"
            return "PRON"
        if any(cue in text for cue in ["futuro", "tempo", "passado", "prospectivo", "aspect", "perfectivo", "imperfectivo"]):
            if raw_tag.startswith("T") or raw_tag == "AUX":
                return "AUX"
        if any(cue in text for cue in ["nega", "negativo", "negacao", "negação"]):
            return "PART"
        if any(cue in text for cue in ["conj", "liga", "coordena", "subordina"]):
            return "SCONJ" if raw_tag.startswith("C") else "CCONJ"
        if "adv" in grammar and base == "X":
            return "ADV"
        if "adj" in grammar and base == "X":
            return "ADJ"
        if any(cue in grammar for cue in ["subst", "nome"]) and base == "X":
            return "NOUN"
        if any(cue in grammar for cue in ["vt", "vi", "unergative", "unaccusative", "bivalent"]):
            return "VERB" if base not in {"AUX", "PART"} else base
        return base

    def ud_candidates(self, ud_upos: str, *, limit: Optional[int] = None) -> List[JsonDict]:
        results = [entry for entry in self.entries if self.infer_ud_upos(entry) == ud_upos.upper()]
        return self._trim(results, limit)

    def conversion_hints(self, item: str | JsonDict) -> JsonDict:
        """Return heuristic hints useful for Penn-style -> UD conversion."""
        entry = item if isinstance(item, dict) else self._first_match(item)
        if entry is None:
            raise KeyError(f"Entry not found: {item!r}")

        raw_tag = entry.get("tag")
        grammar = entry.get("grammar")
        name = entry.get("name")
        definition = entry.get("definition")
        parts = [p for p in re.split(r"[+\s]+", raw_tag or "") if p]
        inferred = self.infer_ud_upos(entry)
        semantic_flags = self.semantic_flags(entry)

        hints = {
            "name": name,
            "uid": entry.get("uid"),
            "raw_tag": raw_tag,
            "tag_parts": parts,
            "grammar": grammar,
            "inferred_ud_upos": inferred,
            "definition": definition,
            "has_conjugations": bool(entry.get("conjugations")),
            "has_nominal_paradigms": bool(entry.get("nominalParadigms")),
            "has_variants": bool(entry.get("variants")),
            "has_related": bool(entry.get("related")),
            "is_marked_for_deletion": bool(entry.get("markToDelete")),
            "is_draft": bool(entry.get("draft")),
            "start_hyphen": bool(entry.get("startHyphen")),
            "semantic_flags": semantic_flags,
            "tokenization_warning": self.tokenization_warning(entry),
            "ud_notes": self.ud_notes(entry),
        }
        return hints

    def semantic_flags(self, item: str | JsonDict) -> List[str]:
        entry = item if isinstance(item, dict) else self._first_match(item)
        if entry is None:
            raise KeyError(f"Entry not found: {item!r}")
        text = normalize_text(self._field_text(entry, "definition", normalize=False) + " | " + self._field_text(entry, "senses.definition", normalize=False) + " | " + self._field_text(entry, "usageNotes", normalize=False))
        flags = []
        flag_map = {
            "NEGATION": ["nao", "não", "negacao", "negação", "negativo", "nega"],
            "TENSE_ASPECT": ["futuro", "tempo", "passado", "perfectivo", "imperfectivo", "aspecto", "prospectivo"],
            "EVIDENTIALITY": ["evidencial", "reportativo", "reportative", "evidencia"],
            "INTERROGATIVE": ["interrog", "pergunta", "quem", "onde", "quando", "como"],
            "DEMONSTRATIVE": ["este", "essa", "aquele", "demonstr"],
            "QUANTIFICATION": ["todo", "todos", "algum", "nenhum", "quant"],
            "LOCATION": ["lugar", "locativo", "aqui", "ali", "la", "lá"],
            "MOTION": ["ir", "vir", "levar", "trazer", "aproximar", "chegar"],
            "DISCOURSE": ["intro", "particula", "partícula", "ênfase", "enfase", "foco"],
        }
        for label, cues in flag_map.items():
            if any(cue in text for cue in cues):
                flags.append(label)
        return flags

    def tokenization_warning(self, item: str | JsonDict) -> Optional[str]:
        entry = item if isinstance(item, dict) else self._first_match(item)
        if entry is None:
            raise KeyError(f"Entry not found: {item!r}")
        raw_tag = entry.get("tag") or ""
        name = str(entry.get("name") or "")
        if "+" in raw_tag:
            return "Composite raw tag; check whether the source token bundles more than one lexical or grammatical element before converting to UD."
        if entry.get("startHyphen"):
            return "Entry may behave like a bound or clitic-like form; review tokenization in the Penn-style source."
        if name != name.strip():
            return "Entry name contains leading/trailing whitespace; normalize string matching before conversion."
        return None

    def ud_notes(self, item: str | JsonDict) -> List[str]:
        entry = item if isinstance(item, dict) else self._first_match(item)
        if entry is None:
            raise KeyError(f"Entry not found: {item!r}")
        notes = []
        raw_tag = entry.get("tag") or ""
        inferred = self.infer_ud_upos(entry)
        flags = self.semantic_flags(entry)

        if "+" in raw_tag:
            notes.append("Composite Penn-style tag detected; conversion may require delexicalizing fused elements into AUX/PART/SCONJ/DET plus host.")
        if inferred == "AUX":
            notes.append("Candidate auxiliary or TAM marker; verify whether it should attach with aux rather than head the clause.")
        if inferred == "PART":
            notes.append("Candidate particle; inspect whether UD relation should be advmod, discourse, mark, or fixed depending on syntax.")
        if inferred in {"DET", "PRON"}:
            notes.append("Potential determiner/pronominal form; check whether the source treebank distinguishes DET vs PRON consistently.")
        if "NEGATION" in flags:
            notes.append("Negation-related item; verify scope and whether the element is independent, cliticized, or fused in the source tokenization.")
        if "EVIDENTIALITY" in flags:
            notes.append("Evidential-related item; inspect whether UD treatment should be AUX, PART, or a separate construction-specific analysis.")
        return notes

    def related_entries(self, entry: JsonDict) -> List[JsonDict]:
        resolved = []
        for rel in entry.get("related", []):
            uid = rel.get("entry") if isinstance(rel, dict) else None
            if uid and uid in self._uid_index:
                resolved.append(self._uid_index[uid])
        return resolved

    def variants_of(self, entry: JsonDict) -> List[JsonDict]:
        resolved = []
        for value in entry.get("variants", []):
            if isinstance(value, str) and value in self._uid_index:
                resolved.append(self._uid_index[value])
            elif isinstance(value, dict):
                uid = value.get("entry") or value.get("uid")
                if uid and uid in self._uid_index:
                    resolved.append(self._uid_index[uid])
        return resolved

    def entry_summary(self, item: str | JsonDict) -> JsonDict:
        entry = item if isinstance(item, dict) else self._first_match(item)
        if entry is None:
            raise KeyError(f"Entry not found: {item!r}")

        summary = {
            "name": entry.get("name"),
            "tag": entry.get("tag"),
            "ud_upos_guess": self.infer_ud_upos(entry),
            "grammar": entry.get("grammar"),
            "definition": entry.get("definition"),
            "senses": [s.get("definition") for s in entry.get("senses", []) if isinstance(s, dict) and s.get("definition")],
            "semantic_flags": self.semantic_flags(entry),
            "plurals": entry.get("plurals"),
            "status": entry.get("status"),
            "uid": entry.get("uid"),
            "variants": [v.get("name") for v in self.variants_of(entry)],
            "related": [r.get("name") for r in self.related_entries(entry)],
            "has_conjugations": bool(entry.get("conjugations")),
            "has_nominal_paradigms": bool(entry.get("nominalParadigms")),
            "tokenization_warning": self.tokenization_warning(entry),
        }
        return summary

    def stats(self) -> JsonDict:
        tag_counter = Counter(entry.get("tag", "<MISSING>") for entry in self.entries)
        grammar_counter = Counter(entry.get("grammar", "<MISSING>") for entry in self.entries)
        status_counter = Counter(entry.get("status", "<MISSING>") for entry in self.entries)
        ud_counter = Counter(self.infer_ud_upos(entry) for entry in self.entries)

        return {
            "entries": len(self.entries),
            "distinct_names": len(self._name_index),
            "distinct_uids": len(self._uid_index),
            "with_tag": sum(1 for e in self.entries if e.get("tag")),
            "with_grammar": sum(1 for e in self.entries if e.get("grammar")),
            "with_senses": sum(1 for e in self.entries if e.get("senses")),
            "with_related": sum(1 for e in self.entries if e.get("related")),
            "with_variants": sum(1 for e in self.entries if e.get("variants")),
            "with_conjugations": sum(1 for e in self.entries if e.get("conjugations")),
            "with_nominal_paradigms": sum(1 for e in self.entries if e.get("nominalParadigms")),
            "marked_to_delete": sum(1 for e in self.entries if e.get("markToDelete")),
            "draft_entries": sum(1 for e in self.entries if e.get("draft")),
            "top_tags": tag_counter.most_common(25),
            "top_grammar_values": grammar_counter.most_common(25),
            "top_status_values": status_counter.most_common(10),
            "ud_upos_guess_counts": ud_counter.most_common(),
        }

    def _trim(self, results: List[JsonDict], limit: Optional[int]) -> List[JsonDict]:
        return results[:limit] if limit is not None else results

    def _first_match(self, query: str) -> Optional[JsonDict]:
        results = self.look_up(query, exact=True, normalize=True, limit=1)
        if results:
            return results[0]
        results = self.look_up(query, exact=False, normalize=True, limit=1)
        return results[0] if results else None

    def _field_text(self, entry: JsonDict, field: str, *, normalize: bool = False) -> str:
        cache = self._field_cache[field]
        idx = entry["__index__"]
        if idx not in cache:
            values = list(self._extract_field_values(entry, field))
            cache[idx] = " | ".join(v for v in values if v)
        text = cache[idx]
        return normalize_text(text) if normalize else text

    def _extract_field_values(self, entry: JsonDict, field: str) -> Iterator[str]:
        if field == "related.name":
            for rel_entry in self.related_entries(entry):
                name = rel_entry.get("name")
                if name:
                    yield str(name)
            return
        if field == "variants.name":
            for var_entry in self.variants_of(entry):
                name = var_entry.get("name")
                if name:
                    yield str(name)
            return

        values = [entry]
        for part in field.split("."):
            next_values: List[Any] = []
            for value in values:
                if isinstance(value, dict):
                    extracted = value.get(part)
                    if isinstance(extracted, list):
                        next_values.extend(extracted)
                    elif extracted is not None:
                        next_values.append(extracted)
                elif isinstance(value, list):
                    next_values.extend(value)
            values = next_values

        for value in values:
            if isinstance(value, str):
                yield value
            elif isinstance(value, (int, float, bool)):
                yield str(value)
            elif isinstance(value, dict):
                for subvalue in value.values():
                    if isinstance(subvalue, str):
                        yield subvalue
                    elif isinstance(subvalue, list):
                        for item in subvalue:
                            if isinstance(item, str):
                                yield item
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        yield item

    def _matches_entry(
        self,
        entry: JsonDict,
        query: str,
        *,
        fields: Sequence[str],
        mode: str,
        normalize: bool,
    ) -> bool:
        haystack = " | ".join(self._field_text(entry, field, normalize=False) for field in fields)
        return self._text_matches(haystack, query, mode=mode, normalize=normalize)

    def _text_matches(self, haystack: str, query: str, *, mode: str, normalize: bool) -> bool:
        mode = mode.lower()
        if normalize:
            haystack_cmp = normalize_text(haystack)
            query_cmp = normalize_text(query)
        else:
            haystack_cmp = haystack
            query_cmp = query

        if mode == "substring":
            return query_cmp in haystack_cmp
        if mode == "exact":
            return haystack_cmp == query_cmp
        if mode == "word":
            pattern = rf"(?<![{WORD_CHARS}]){re.escape(query_cmp)}(?![{WORD_CHARS}])"
            return re.search(pattern, haystack_cmp, flags=re.UNICODE) is not None
        if mode == "regex":
            return re.search(query_cmp, haystack_cmp, flags=re.UNICODE) is not None
        raise ValueError("mode must be one of: substring, word, exact, regex")


def pretty_entry(entry: JsonDict, *, include_hints: bool = False, lexicon: Optional[KadiweuLexicon] = None) -> JsonDict:
    cleaned = {
        "name": entry.get("name"),
        "uid": entry.get("uid"),
        "tag": entry.get("tag"),
        "ud_upos_guess": lexicon.infer_ud_upos(entry) if lexicon else None,
        "grammar": entry.get("grammar"),
        "definition": entry.get("definition"),
        "senses": [s.get("definition") for s in entry.get("senses", []) if isinstance(s, dict) and s.get("definition")],
        "plurals": entry.get("plurals"),
        "status": entry.get("status"),
        "variants": [v.get("name") for v in lexicon.variants_of(entry)] if lexicon else entry.get("variants"),
        "related": [r.get("name") for r in lexicon.related_entries(entry)] if lexicon else entry.get("related"),
        "conjugations": entry.get("conjugations"),
        "nominalParadigms": entry.get("nominalParadigms"),
        "attributes": entry.get("attributes"),
        "usageNotes": entry.get("usageNotes"),
        "semantic_flags": lexicon.semantic_flags(entry) if lexicon else None,
    }
    if include_hints and lexicon:
        cleaned["conversion_hints"] = lexicon.conversion_hints(entry)
    return {k: v for k, v in cleaned.items() if v not in (None, "", [], {})}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explore lexicon-kadiweu.json")
    parser.add_argument("json_path", help="Path to lexicon-kadiweu.json")

    subparsers = parser.add_subparsers(dest="command", required=True)

    p_lookup = subparsers.add_parser("lookup", help="Look up an entry by name")
    p_lookup.add_argument("query")
    p_lookup.add_argument("--exact", action="store_true")
    p_lookup.add_argument("--limit", type=int, default=20)

    p_search = subparsers.add_parser("search", help="Multi-field search (default: substring)")
    p_search.add_argument("query")
    p_search.add_argument("--field", action="append", help="Restrict search to one or more fields")
    p_search.add_argument("--mode", choices=["substring", "word", "exact", "regex"], default="substring")
    p_search.add_argument("--no-normalize", action="store_true")
    p_search.add_argument("--limit", type=int, default=20)

    p_field = subparsers.add_parser("field", help="Search one field only")
    p_field.add_argument("field")
    p_field.add_argument("query")
    p_field.add_argument("--mode", choices=["substring", "word", "exact", "regex"], default="substring")
    p_field.add_argument("--no-normalize", action="store_true")
    p_field.add_argument("--limit", type=int, default=20)

    p_text = subparsers.add_parser("text", help="Backward-compatible alias of search")
    p_text.add_argument("query")
    p_text.add_argument("--field", action="append")
    p_text.add_argument("--mode", choices=["substring", "word", "exact", "regex"], default="substring")
    p_text.add_argument("--no-normalize", action="store_true")
    p_text.add_argument("--limit", type=int, default=20)

    p_tag = subparsers.add_parser("tag", help="Search by raw tag/POS")
    p_tag.add_argument("tag")
    p_tag.add_argument("--contains", action="store_true")
    p_tag.add_argument("--limit", type=int, default=20)

    p_ud = subparsers.add_parser("ud", help="Return candidates for an inferred UD UPOS")
    p_ud.add_argument("upos")
    p_ud.add_argument("--limit", type=int, default=20)

    p_grammar = subparsers.add_parser("grammar", help="Search by grammar label")
    p_grammar.add_argument("grammar")
    p_grammar.add_argument("--exact", action="store_true")
    p_grammar.add_argument("--limit", type=int, default=20)

    p_status = subparsers.add_parser("status", help="Search by editorial status")
    p_status.add_argument("status")
    p_status.add_argument("--contains", action="store_true")
    p_status.add_argument("--limit", type=int, default=20)

    p_sem = subparsers.add_parser("semantic", help="Filter by POS/UD UPOS plus semantic cues")
    p_sem.add_argument("--pos")
    p_sem.add_argument("--ud-upos")
    p_sem.add_argument("--grammar")
    p_sem.add_argument("--status")
    p_sem.add_argument("--cue", action="append", default=[])
    p_sem.add_argument("--mode", choices=["substring", "word", "exact", "regex"], default="substring")
    p_sem.add_argument("--tag-contains", action="store_true")
    p_sem.add_argument("--limit", type=int, default=20)

    p_hints = subparsers.add_parser("hints", help="Show conversion hints for one entry")
    p_hints.add_argument("query")

    p_summary = subparsers.add_parser("summary", help="Show a compact summary for one entry")
    p_summary.add_argument("query")

    subparsers.add_parser("fields", help="List searchable fields")
    subparsers.add_parser("stats", help="Show lexicon statistics")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    lex = KadiweuLexicon(args.json_path)

    if args.command == "lookup":
        results = lex.look_up(args.query, exact=args.exact, limit=args.limit)
        print(json.dumps([pretty_entry(e, lexicon=lex) for e in results], ensure_ascii=False, indent=2))
    elif args.command in {"search", "text"}:
        results = lex.search(
            args.query,
            fields=args.field,
            mode=args.mode,
            normalize=not args.no_normalize,
            limit=args.limit,
        )
        print(json.dumps([pretty_entry(e, lexicon=lex) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "field":
        results = lex.search_field(
            args.field,
            args.query,
            mode=args.mode,
            normalize=not args.no_normalize,
            limit=args.limit,
        )
        print(json.dumps([pretty_entry(e, lexicon=lex) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "tag":
        results = lex.search_by_tag(args.tag, exact=not args.contains, limit=args.limit)
        print(json.dumps([pretty_entry(e, lexicon=lex) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "ud":
        results = lex.ud_candidates(args.upos, limit=args.limit)
        print(json.dumps([pretty_entry(e, lexicon=lex) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "grammar":
        results = lex.search_by_grammar(args.grammar, exact=args.exact, limit=args.limit)
        print(json.dumps([pretty_entry(e, lexicon=lex) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "status":
        results = lex.search_by_status(args.status, exact=not args.contains, limit=args.limit)
        print(json.dumps([pretty_entry(e, lexicon=lex) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "semantic":
        results = lex.search_by_pos_semantics(
            pos=args.pos,
            ud_upos=args.ud_upos,
            grammar=args.grammar,
            status=args.status,
            semantic_cues=args.cue,
            raw_tag_contains=args.tag_contains,
            mode=args.mode,
            limit=args.limit,
        )
        print(json.dumps([pretty_entry(e, include_hints=True, lexicon=lex) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "hints":
        print(json.dumps(lex.conversion_hints(args.query), ensure_ascii=False, indent=2))
    elif args.command == "summary":
        print(json.dumps(lex.entry_summary(args.query), ensure_ascii=False, indent=2))
    elif args.command == "fields":
        print(json.dumps(lex.list_fields(), ensure_ascii=False, indent=2))
    elif args.command == "stats":
        print(json.dumps(lex.stats(), ensure_ascii=False, indent=2))
    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
