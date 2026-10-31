#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from compare_conllu_drafts_to_gold import parse_conllu

parser = argparse.ArgumentParser()
parser.add_argument("gold", type=Path)
parser.add_argument("drafts", type=Path, nargs="+")
parser.add_argument(
    "--status",
    help="Filter by sentence status in the source TBP JSON (e.g. DONE or REVIEW).",
)
parser.add_argument(
    "--json",
    dest="json_paths",
    type=Path,
    nargs="+",
    metavar="PATH",
    help="Source TBP JSON file(s), required when --status is specified.",
)
args = parser.parse_args()

if args.status and not args.json_paths:
    parser.error("--status requires --json with the source TBP JSON files")

selected_uids = None
if args.status:
    selected_uids = set()
    for json_path in args.json_paths:
        with json_path.open(encoding="utf-8") as source:
            document = json.load(source)
        for page in document.get("pages", []):
            for sentence in page.get("sentences", []):
                if sentence.get("status") == args.status:
                    uid = sentence.get("uid")
                    if uid:
                        selected_uids.add(uid)


gold = {
    s.sent_uid: s
    for s in parse_conllu(args.gold)
    if s.sent_uid
}

results = []
seen_uids = set()

for draft_path in args.drafts:
    for draft in parse_conllu(draft_path):
        if selected_uids is not None and draft.sent_uid not in selected_uids:
            continue
        if draft.sent_uid in seen_uids:
            continue
        reference = gold.get(draft.sent_uid)
        if reference is None:
            continue

        gt = reference.tokens
        dt = draft.tokens

        if len(gt) != len(dt):
            continue
        if [t.id for t in gt] != [t.id for t in dt]:
            continue

        errors = []
        for g, d in zip(gt, dt):
            if g.head != d.head or g.deprel != d.deprel:
                errors.append(
                    f"{g.id}:{g.form} "
                    f"gold=({g.head},{g.deprel}) "
                    f"draft=({d.head},{d.deprel})"
                )

        seen_uids.add(draft.sent_uid)
        results.append((
            reference.sent_id or draft.sent_id or "(no sent_id)",
            draft.sent_uid,
            len(gt),
            len(errors),
            reference.meta.get("text", ""),
            errors,
        ))

print("SUCCESS CANDIDATES")
for short_id, uid, n, e, sentence, _ in sorted(
    (r for r in results if r[3] == 0 and r[2] >= 6),
    key=lambda r: -r[2]
)[:20]:
    print(short_id, uid, n, sentence)

print("\nERROR CANDIDATES")
for short_id, uid, n, e, sentence, errors in sorted(
    (r for r in results if r[3] == 1),
    key=lambda r: -r[2]
)[:30]:
    print(short_id, uid, n, sentence)
    for error in errors:
        print("  ", error)
