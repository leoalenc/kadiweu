#!/usr/bin/env python3

import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGET = "teste-20261117"
DESTINATION = PROJECT_ROOT / "data" / f"{TARGET}.json"
HISTORY = PROJECT_ROOT / "data" / "import-json-history-test.tsv"
REQUIRED_COLUMNS = ["timestamp", "target", "document_uid", "sha256"]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} NEW_TBP_EXPORT.json")

    source = Path(sys.argv[1]).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Input file not found: {source}")

    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read valid JSON from {source}: {exc}")

    pages = data.get("pages")
    if not isinstance(pages, list):
        raise SystemExit("JSON has no valid 'pages' list.")

    page_uids = [
        str(page["uid"]).strip()
        for page in pages
        if isinstance(page, dict) and page.get("uid")
    ]
    if len(page_uids) != 1:
        raise SystemExit(
            f"Expected exactly one page UID; found {len(page_uids)}. "
            "The converter's provenance check needs a page UID."
        )

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.parent.mkdir(parents=True, exist_ok=True)

    # Copy through a temporary file so an interrupted copy won't leave a
    # partially written export at the destination.
    if source != DESTINATION.resolve():
        fd, temporary_name = tempfile.mkstemp(
            dir=DESTINATION.parent, prefix=f".{TARGET}.", suffix=".tmp"
        )
        os.close(fd)
        try:
            shutil.copy2(source, temporary_name)
            os.replace(temporary_name, DESTINATION)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    sha256 = hashlib.sha256(DESTINATION.read_bytes()).hexdigest()
    new_row = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": TARGET,
        "document_uid": page_uids[0],
        "sha256": sha256,
    }

    rows = []
    columns = REQUIRED_COLUMNS
    if HISTORY.exists():
        with HISTORY.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file, delimiter="\t")
            if reader.fieldnames:
                columns = list(reader.fieldnames)
                missing = set(REQUIRED_COLUMNS) - set(columns)
                if missing:
                    raise SystemExit(
                        "Test history TSV is missing columns: "
                        + ", ".join(sorted(missing))
                    )
                rows = [
                    row for row in reader if row.get("target") != TARGET
                ]

    rows.append({column: new_row.get(column, "") for column in columns})

    fd, temporary_name = tempfile.mkstemp(
        dir=HISTORY.parent, prefix=f".{HISTORY.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file, fieldnames=columns, delimiter="\t",
                lineterminator="\n", extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_name, HISTORY)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)

    print(f"Copied export: {DESTINATION}")
    print(f"Updated history: {HISTORY}")
    print(f"Page UID: {page_uids[0]}")
    print(f"SHA-256: {sha256}")


if __name__ == "__main__":
    main()