#!/usr/bin/env python3

import csv
import sys

path = sys.argv[1]

CORRECT = {"EXACT_MATCH", "TRACE_EQUIVALENT"}

with open(path, encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream, delimiter="\t"))

done = [row for row in rows if row["struct_status"] == "DONE"]

both = [
    row for row in done
    if row["result_A"] in CORRECT
    and row["result_B"] in CORRECT
]

a_only = [
    row for row in done
    if row["result_A"] in CORRECT
    and row["result_B"] not in CORRECT
]

b_only = [
    row for row in done
    if row["result_A"] not in CORRECT
    and row["result_B"] in CORRECT
]

neither = [
    row for row in done
    if row["result_A"] not in CORRECT
    and row["result_B"] not in CORRECT
]

groups = [
    ("Correct under both", both),
    ("Correct only under A", a_only),
    ("Correct only under B", b_only),
    ("Incorrect under both", neither),
]

for label, group in groups:
    print(f"{label}: {len(group)}")
    for row in group:
        print(f"  {row['sentence_id']}")

print(f"Total DONE: {len(done)}")