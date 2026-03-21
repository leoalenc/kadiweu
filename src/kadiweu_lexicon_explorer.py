"""Utilities to explore the Kadiwéu lexicon stored in ``lexicon-kadiweu.json``.

The script is designed for interactive Python sessions as well as command-line use.
It provides functions to:

- load the JSON lexicon;
- look up entries by word or morpheme, with optional accent-insensitive matching;
- retrieve a compact dictionary with the most useful information of an entry;
- search by POS/tag, grammar label, status, or free text;
- inspect related entries and variants;
- compute simple descriptive statistics about the lexicon.

Example
-------
>>> lex = KadiweuLexicon("lexicon-kadiweu.json")
>>> lex.look_up("abaciǥegi")
>>> lex.search_by_tag("VB")[:5]
>>> lex.search_text("preguiç")[:10]
>>> lex.entry_summary("abaciǥegi")

Command-line examples
---------------------
python kadiweu_lexicon_explorer.py lexicon-kadiweu.json lookup abaciǥegi
python kadiweu_lexicon_explorer.py lexicon-kadiweu.json tag VB --limit 10
python kadiweu_lexicon_explorer.py lexicon-kadiweu.json text preguiç --limit 10
python kadiweu_lexicon_explorer.py lexicon-kadiweu.json stats
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

JsonDict = Dict[str, Any]


SPECIAL_CHAR_MAP = str.maketrans(
    {
        "ǥ": "g",
        "Ɠ": "G",
        "ɡ": "g",
        "º": "o",
    }
)


def normalize_text(text: Any) -> str:
    """Return a simplified string for accent-insensitive matching.

    The normalization is conservative: it lowercases the string, replaces a few
    Kadiwéu-specific or project-specific characters, strips combining marks, and
    collapses whitespace.
    """
    if text is None:
        return ""
    text = str(text).translate(SPECIAL_CHAR_MAP).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text


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

        for entry in self.entries:
            uid = entry.get("uid")
            if uid:
                self._uid_index[uid] = entry

            name = entry.get("name")
            if name:
                self._name_index[name].append(entry)
                self._normalized_name_index[normalize_text(name)].append(entry)

    def __len__(self) -> int:
        return len(self.entries)

    def all_names(self) -> List[str]:
        """Return all distinct entry names sorted alphabetically."""
        return sorted(self._name_index)

    def get_by_uid(self, uid: str) -> Optional[JsonDict]:
        """Return an entry by UID, or None if it is not found."""
        return self._uid_index.get(uid)

    def look_up(
        self,
        query: str,
        *,
        exact: bool = False,
        normalize: bool = True,
        limit: Optional[int] = None,
    ) -> List[JsonDict]:
        """Look up a word or morpheme.

        Parameters
        ----------
        query:
            Form to search for.
        exact:
            If True, require full-string match. Otherwise allow substring match.
        normalize:
            If True, use accent-insensitive normalization.
        limit:
            Maximum number of results.
        """
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
                results = [
                    entry for entry in self.entries if query in str(entry.get("name", ""))
                ]

        return results[:limit] if limit is not None else results

    def search_text(self, query: str, *, limit: Optional[int] = None) -> List[JsonDict]:
        """Search free text across selected descriptive fields."""
        q = normalize_text(query)
        searchable_fields = (
            "name",
            "definition",
            "grammar",
            "tag",
            "usageNotes",
            "plurals",
            "lexicon",
            "status",
        )
        results: List[JsonDict] = []
        for entry in self.entries:
            haystack_parts: List[str] = []
            for field in searchable_fields:
                haystack_parts.append(str(entry.get(field, "")))
            haystack_parts.extend(s.get("definition", "") for s in entry.get("senses", []))
            haystack_parts.extend(v if isinstance(v, str) else "" for v in entry.get("variants", []))
            haystack = normalize_text(" | ".join(haystack_parts))
            if q in haystack:
                results.append(entry)
        return results[:limit] if limit is not None else results

    def search_by_tag(self, tag: str, *, exact: bool = True, limit: Optional[int] = None) -> List[JsonDict]:
        """Search entries by the value of the `tag` field."""
        q = normalize_text(tag)
        results = []
        for entry in self.entries:
            tag_value = normalize_text(entry.get("tag", ""))
            if (tag_value == q) if exact else (q in tag_value):
                results.append(entry)
        return results[:limit] if limit is not None else results

    def search_by_grammar(
        self, grammar: str, *, exact: bool = False, limit: Optional[int] = None
    ) -> List[JsonDict]:
        """Search entries by the `grammar` field."""
        q = normalize_text(grammar)
        results = []
        for entry in self.entries:
            grammar_value = normalize_text(entry.get("grammar", ""))
            if (grammar_value == q) if exact else (q in grammar_value):
                results.append(entry)
        return results[:limit] if limit is not None else results

    def search_by_status(self, status: str, *, exact: bool = True, limit: Optional[int] = None) -> List[JsonDict]:
        """Search entries by editorial status such as DONE, REVIEW, TODO."""
        q = normalize_text(status)
        results = []
        for entry in self.entries:
            status_value = normalize_text(entry.get("status", ""))
            if (status_value == q) if exact else (q in status_value):
                results.append(entry)
        return results[:limit] if limit is not None else results

    def related_entries(self, entry: JsonDict) -> List[JsonDict]:
        """Resolve the `related` field into full entry dictionaries whenever possible."""
        resolved = []
        for rel in entry.get("related", []):
            uid = rel.get("entry") if isinstance(rel, dict) else None
            if uid and uid in self._uid_index:
                resolved.append(self._uid_index[uid])
        return resolved

    def variants_of(self, entry: JsonDict) -> List[JsonDict]:
        """Resolve string UIDs listed in `variants` into entry dictionaries."""
        resolved = []
        for uid in entry.get("variants", []):
            if isinstance(uid, str) and uid in self._uid_index:
                resolved.append(self._uid_index[uid])
        return resolved

    def entry_summary(self, item: str | JsonDict) -> JsonDict:
        """Return a compact, readable summary of one entry.

        If `item` is a string, the first exact normalized match is used.
        """
        entry = item if isinstance(item, dict) else self._first_match(item)
        if entry is None:
            raise KeyError(f"Entry not found: {item!r}")

        summary = {
            "name": entry.get("name"),
            "tag": entry.get("tag"),
            "grammar": entry.get("grammar"),
            "definition": entry.get("definition"),
            "senses": [s.get("definition") for s in entry.get("senses", []) if s.get("definition")],
            "plurals": entry.get("plurals"),
            "status": entry.get("status"),
            "uid": entry.get("uid"),
            "variants": [v.get("name") for v in self.variants_of(entry)],
            "related": [r.get("name") for r in self.related_entries(entry)],
            "has_conjugations": bool(entry.get("conjugations")),
            "has_nominal_paradigms": bool(entry.get("nominalParadigms")),
            "copyright": entry.get("copyright"),
        }
        return summary

    def stats(self) -> JsonDict:
        """Return descriptive statistics about the lexicon."""
        tag_counter = Counter(entry.get("tag", "<MISSING>") for entry in self.entries)
        grammar_counter = Counter(entry.get("grammar", "<MISSING>") for entry in self.entries)
        status_counter = Counter(entry.get("status", "<MISSING>") for entry in self.entries)

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
            "top_tags": tag_counter.most_common(20),
            "top_grammar_values": grammar_counter.most_common(20),
            "top_status_values": status_counter.most_common(20),
        }

    def _first_match(self, query: str) -> Optional[JsonDict]:
        results = self.look_up(query, exact=True, normalize=True, limit=1)
        if results:
            return results[0]
        results = self.look_up(query, exact=False, normalize=True, limit=1)
        return results[0] if results else None


def pretty_entry(entry: JsonDict) -> JsonDict:
    """Return a simplified entry dictionary for display or inspection."""
    cleaned = {
        "name": entry.get("name"),
        "uid": entry.get("uid"),
        "tag": entry.get("tag"),
        "grammar": entry.get("grammar"),
        "definition": entry.get("definition"),
        "senses": [s.get("definition") for s in entry.get("senses", []) if s.get("definition")],
        "plurals": entry.get("plurals"),
        "status": entry.get("status"),
        "variants": entry.get("variants"),
        "related": entry.get("related"),
        "conjugations": entry.get("conjugations"),
        "nominalParadigms": entry.get("nominalParadigms"),
        "attributes": entry.get("attributes"),
        "usageNotes": entry.get("usageNotes"),
    }
    return {k: v for k, v in cleaned.items() if v not in (None, "", [], {})}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explore lexicon-kadiweu.json")
    parser.add_argument("json_path", help="Path to lexicon-kadiweu.json")

    subparsers = parser.add_subparsers(dest="command", required=True)

    p_lookup = subparsers.add_parser("lookup", help="Look up an entry by name")
    p_lookup.add_argument("query")
    p_lookup.add_argument("--exact", action="store_true")
    p_lookup.add_argument("--limit", type=int, default=20)

    p_text = subparsers.add_parser("text", help="Search across text fields")
    p_text.add_argument("query")
    p_text.add_argument("--limit", type=int, default=20)

    p_tag = subparsers.add_parser("tag", help="Search by tag/POS")
    p_tag.add_argument("tag")
    p_tag.add_argument("--contains", action="store_true")
    p_tag.add_argument("--limit", type=int, default=20)

    p_grammar = subparsers.add_parser("grammar", help="Search by grammar label")
    p_grammar.add_argument("grammar")
    p_grammar.add_argument("--exact", action="store_true")
    p_grammar.add_argument("--limit", type=int, default=20)

    p_status = subparsers.add_parser("status", help="Search by editorial status")
    p_status.add_argument("status")
    p_status.add_argument("--contains", action="store_true")
    p_status.add_argument("--limit", type=int, default=20)

    p_summary = subparsers.add_parser("summary", help="Show a compact summary for one entry")
    p_summary.add_argument("query")

    subparsers.add_parser("stats", help="Show lexicon statistics")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    lex = KadiweuLexicon(args.json_path)

    if args.command == "lookup":
        results = lex.look_up(args.query, exact=args.exact, limit=args.limit)
        print(json.dumps([pretty_entry(e) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "text":
        results = lex.search_text(args.query, limit=args.limit)
        print(json.dumps([pretty_entry(e) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "tag":
        results = lex.search_by_tag(args.tag, exact=not args.contains, limit=args.limit)
        print(json.dumps([pretty_entry(e) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "grammar":
        results = lex.search_by_grammar(args.grammar, exact=args.exact, limit=args.limit)
        print(json.dumps([pretty_entry(e) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "status":
        results = lex.search_by_status(args.status, exact=not args.contains, limit=args.limit)
        print(json.dumps([pretty_entry(e) for e in results], ensure_ascii=False, indent=2))
    elif args.command == "summary":
        print(json.dumps(lex.entry_summary(args.query), ensure_ascii=False, indent=2))
    elif args.command == "stats":
        print(json.dumps(lex.stats(), ensure_ascii=False, indent=2))
    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
