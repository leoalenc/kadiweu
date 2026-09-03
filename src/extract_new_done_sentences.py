#!/usr/bin/env python3
"""Copy new DONE draft sentences to a manual-review file, never to gold.

UID, not text or sentence number, identifies membership in the reference.
Review status comes from the source JSON's sentence.status (the current
converter does not reliably export this field). Copied annotations remain
draft annotations: DONE describes the source tree, not UD review completion.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ("ped-gramm", "hil-data", "van-data")


def read_blocks(path):
    """Keep comments and token lines verbatim, including MWT/empty-node rows."""
    with Path(path).open(encoding="utf-8", newline="") as stream:
        text = stream.read()
    blocks = []
    lines = []
    for line in text.splitlines(keepends=True):
        if not line.strip():
            if lines:
                blocks.append("".join(lines))
                lines = []
        else:
            lines.append(line)
    if lines:
        blocks.append("".join(lines))
    return blocks


def metadata(block, key):
    values = re.findall(r"^#\s*" + re.escape(key) + r"\s*=\s*([^\r\n]*)", block, re.M)
    if len(values) > 1:
        raise ValueError("duplicate metadata field: " + key)
    return values[0].strip() if values else ""


def index_conllu(paths):
    records = []
    seen = set()
    for path in paths:
        for number, block in enumerate(read_blocks(path), 1):
            uid = metadata(block, "sent_uid")
            sid = metadata(block, "sent_id")
            if not uid or not sid:
                raise ValueError("{} block {}: missing sent_uid or sent_id".format(path, number))
            if uid in seen:
                raise ValueError("duplicate sent_uid {} in {}".format(uid, path))
            seen.add(uid)
            records.append((uid, sid, block))
    return records


def source_statuses(paths):
    statuses = {}
    for path in paths:
        with Path(path).open(encoding="utf-8") as stream:
            document = json.load(stream)
        if not isinstance(document.get("pages"), list):
            raise ValueError("{}: expected JSON pages list".format(path))
        for page in document["pages"]:
            for sentence in page.get("sentences", []):
                uid = sentence.get("uid")
                if not isinstance(uid, str) or not uid.strip():
                    raise ValueError("{}: source sentence missing uid".format(path))
                uid = uid.strip()
                if uid in statuses:
                    raise ValueError("duplicate source uid: " + uid)
                # Keep TBP status unchanged; do not promote adjudicated REVIEW.
                statuses[uid] = sentence.get("status")
    return statuses


def select_sentences(drafts, reference, json_sources):
    gold = index_conllu([reference])
    gold_uids = {uid for uid, _, _ in gold}
    gold_ids = {sid for _, sid, _ in gold}
    statuses = source_statuses(json_sources)
    selected = []
    selected_ids = set()
    counts = Counter()
    for uid, sid, block in index_conllu(drafts):
        counts["draft_sentences"] += 1
        if uid in gold_uids:
            counts["already_in_reference"] += 1
        elif uid not in statuses:
            counts["missing_source_uid"] += 1
        elif statuses[uid] != "DONE":
            counts["not_done"] += 1
        else:
            if sid in gold_ids or sid in selected_ids:
                raise ValueError("sent_id collision for new UID: " + sid)
            selected.append(block)
            selected_ids.add(sid)
            counts["selected"] += 1
    return selected, counts


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts", nargs="+", type=Path,
                        default=[ROOT / "data/treebank" / ("draft-" + s + ".conllu") for s in SOURCES])
    parser.add_argument("--reference", type=Path, default=ROOT / "data/treebank/kbc_unicamp-ud-test.conllu")
    parser.add_argument("--json", nargs="+", type=Path,
                        default=[ROOT / "data" / (s + ".json") for s in SOURCES])
    parser.add_argument("-o", "--output", type=Path,
                        default=ROOT / "data/treebank/review/new-done-sentences.conllu")
    parser.add_argument("--dry-run", action="store_true", help="Report selection counts without writing a file")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        inputs = args.drafts + [args.reference] + args.json
        if args.output.resolve() in {p.resolve() for p in inputs}:
            raise ValueError("output must not be an input file")
        selected, counts = select_sentences(args.drafts, args.reference, args.json)
        if not args.dry_run:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation protects a transitional file already edited.
            with args.output.open("x", encoding="utf-8", newline="") as stream:
                for block in selected:
                    stream.write(block)
                    if not block.endswith(("\n", "\r")):
                        stream.write("\n")
                    stream.write("\n")
        print("Selection: " + " ".join("{}={}".format(k, counts[k]) for k in
              ("draft_sentences", "already_in_reference", "not_done", "missing_source_uid", "selected")), file=sys.stderr)
        if counts["missing_source_uid"]:
            print("WARNING: drafts with no matching source UID were excluded; check that the JSON exports correspond to the drafts.", file=sys.stderr)
        if not args.dry_run:
            print("Manual-review file: " + str(args.output), file=sys.stderr)
        return 0
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
