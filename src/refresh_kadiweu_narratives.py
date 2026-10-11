#!/usr/bin/env python3
"""Refresh five Kadiwéu narratives from the latest valid TBP JSON downloads.

Install as ~/kadiweu/src/refresh_kadiweu_narratives.py and run:
    python3 src/refresh_kadiweu_narratives.py ~/Downloads

The JSON is authoritative. A uniquely adjacent TBP PSD export is archived
verbatim; ambiguous PSDs must be passed explicitly with --archive-psd.
"""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


# Document UID is stable across exported filenames and title revisions.
NARRATIVES = {
    "D300": ("creation", "1 - iliidaGatajegi (criação)"),
    "D309": ("warrior", "2 - GodapoaGeneGegi (Nosso guerreiro)"),
    "D388": ("jaguar", "3 - nigedioli (onça)"),
    "D302": ("young-man", "4 - LiwoneGa ane libonaGadi Exabigo (o jovem chamado Exabigo)"),
    "D305": ("frog", "5 - LigedemaGa (sapo)"),
}


def sentences(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get("text"), str) and isinstance(obj.get("struct"), dict) and isinstance(obj["struct"].get("tokens"), list):
            yield obj
        else:
            for value in obj.values():
                yield from sentences(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from sentences(value)


def source_info(path):
    try:
        raw = path.read_bytes()
        data = json.loads(raw)
        doc = data.get("document", {})
        uid = doc.get("uid")
        if uid not in NARRATIVES or not isinstance(doc.get("name"), str):
            return None
        entries = list(sentences(data))
        if not entries:
            return None
        return raw, doc, entries
    except (OSError, UnicodeError, ValueError, AttributeError):
        return None


def archive(source, directory):
    directory.mkdir(parents=True, exist_ok=True)
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()[:12]
    dest = directory / f"{source.stem}.{digest}{source.suffix.lower()}"
    if dest.exists():
        if dest.read_bytes() != raw:
            raise RuntimeError(f"Archive collision: {dest}")
    else:
        shutil.copy2(source, dest)
    return dest


def export_id(path):
    """Extract a 24-digit export ID, allowing browser '(2)' suffixes."""
    match = re.fullmatch(r"([0-9a-fA-F]{24})(?: ?\(\d+\))?", path.stem)
    return match.group(1).lower() if match else None


def paired_psd(json_path, psd_paths):
    """Use the observed consecutive export IDs only when pairing is unique."""
    json_id = export_id(json_path)
    if json_id is None:
        return None
    candidates = []
    for path in psd_paths:
        psd_id = export_id(path)
        if (psd_id and psd_id[8:18] == json_id[8:18]
                and int(psd_id[18:], 16) == int(json_id[18:], 16) + 1
                and 0 <= int(psd_id[:8], 16) - int(json_id[:8], 16) <= 300):
            candidates.append(path)
    # Browser copies of the same export ID are possible: choose the most
    # recently downloaded identical-ID copy, but reject distinct IDs.
    if len({export_id(path) for path in candidates}) == 1:
        return max(candidates, key=lambda path: (path.stat().st_mtime_ns, path.name))
    return None


def export_trees(converter, canonical, output, numbers=None, status=None):
    selector = ["--all"] if numbers is None else ["-n", *(str(n) for n in numbers)]
    command = [sys.executable, str(converter), str(canonical), *selector]
    if status:
        command += ["--status", status]
    command += ["--format", "corpussearch", "--output", str(output)]
    return subprocess.run(command, capture_output=True, text=True)


def run(args):
    repo = args.repo.resolve()
    downloads = args.downloads.expanduser().resolve()
    if not downloads.is_dir():
        raise RuntimeError(f"Download directory not found: {downloads}")
    converter = repo / "src" / "kadiweu_constituency.py"
    inspector = repo / "src" / "inspect_kadiweu_json.py"
    for script in (converter, inspector):
        if not script.is_file():
            raise RuntimeError(f"Required repository script not found: {script}")

    candidates = {uid: [] for uid in NARRATIVES}
    for path in downloads.glob("*.json"):
        info = source_info(path)
        if info:
            candidates[info[1]["uid"]].append((path, info))
    root = repo / "data" / "narratives"
    root.mkdir(parents=True, exist_ok=True)
    psd_paths = [p for p in downloads.iterdir() if p.is_file() and p.suffix.lower() == ".psd"]
    used_psds = set()
    for uid, (base, expected_title) in NARRATIVES.items():
        found = candidates[uid]
        if not found:
            print(f"SKIP {base}: no valid JSON export for {uid} in {downloads}")
            continue
        # Deterministic tie breaker; an incomplete newer download is ignored.
        source, (raw, doc, entries) = max(found, key=lambda item: (item[0].stat().st_mtime_ns, item[0].name))
        target = root / base
        target.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f".{base}-", dir=root) as temp:
            stage = Path(temp)
            canonical = stage / f"{base}.json"
            canonical.write_text(raw.decode("utf-8").replace("ǥ", "G"), encoding="utf-8")
            derived = stage / "generated" / "constituency"
            derived.mkdir(parents=True)
            counts = Counter(s.get("status", "<missing>") for s in entries)
            # Every narrative sentence can have chunks even without a DONE or
            # REVIEW status. Produce the complete JSON-derived collection too.
            all_output = derived / f"{base}.psd"
            initial = export_trees(converter, canonical, all_output)
            skipped = []
            if initial.returncode:
                # A single malformed JSON chunk must not prevent trees for
                # other sentences. Selecting by original JSON number retains
                # each sentence's stable CorpusSearch ID.
                parts = []
                for number, sentence in enumerate(entries, 1):
                    part = stage / f"tree-{number}.psd"
                    result = export_trees(converter, canonical, part, [number])
                    if result.returncode or not part.is_file():
                        skipped.append({"number": number, "uid": sentence.get("uid"),
                                        "status": sentence.get("status"),
                                        "error": result.stderr.strip()})
                    else:
                        parts.append((number, part))
                if not parts:
                    raise RuntimeError(f"No trees could be reconstructed for {base}: {initial.stderr.strip()}")
                all_output.write_text("\n".join(p.read_text(encoding="utf-8").rstrip()
                                                 for _, p in parts) + "\n", encoding="utf-8")
                good_numbers = {n for n, _ in parts}
            else:
                good_numbers = set(range(1, len(entries) + 1))
            if not all_output.is_file():
                raise RuntimeError(f"Missing generated file: {all_output}")
            for status in ("DONE", "REVIEW"):
                selected = [n for n, s in enumerate(entries, 1)
                            if s.get("status") == status and n in good_numbers]
                if selected:
                    output = derived / f"{base}.{status.lower()}.psd"
                    result = export_trees(converter, canonical, output, selected, status)
                    if result.returncode or not output.is_file():
                        raise RuntimeError(f"Status export failed for {base} {status}: {result.stderr.strip()}")
            # Inspect all sentences, including those with no status. This is
            # the same inspector used for the existing three documents.
            jsonl = stage / f"{base}.jsonl"
            result = subprocess.run([sys.executable, str(inspector), str(canonical),
                                     "--source-id", base, "--jsonl-out", str(jsonl)],
                                    check=True, capture_output=True, text=True)
            (stage / f"{base}.txt").write_text(result.stdout, encoding="utf-8")
            manifest = {
                "document_uid": uid, "document_title": doc["name"],
                "expected_title": expected_title, "source_json": source.name,
                "source_json_sha256": hashlib.sha256(raw).hexdigest(),
                "sentences": len(entries), "statuses": dict(counts),
                "reconstructed_trees": len(good_numbers),
                "skipped_trees": skipped,
            }
            matched_psd = paired_psd(source, psd_paths)
            if matched_psd and matched_psd in used_psds:
                raise RuntimeError(f"PSD selected for two narratives: {matched_psd}")
            if matched_psd:
                archived_psd = archive(matched_psd, root / "tycho" / "psd")
                used_psds.add(matched_psd)
                manifest["source_psd"] = matched_psd.name
                manifest["archived_psd"] = str(archived_psd.relative_to(root))
            (stage / "source.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            archived = archive(source, root / "tycho" / "json")
            for item in (canonical, jsonl, stage / f"{base}.txt", stage / "source.json"):
                os.replace(item, target / item.name)
            dest = target / "generated" / "constituency"
            dest.mkdir(parents=True, exist_ok=True)
            for item in derived.iterdir():
                os.replace(item, dest / item.name)
            # An earlier status can disappear after editing; remove only stale
            # status-specific outputs generated by this script.
            for status in ("DONE", "REVIEW"):
                if not any(s.get("status") == status and n in good_numbers
                           for n, s in enumerate(entries, 1)):
                    (dest / f"{base}.{status.lower()}.psd").unlink(missing_ok=True)
        print(f"{base}: {len(entries)} sentences, source {source.name}, archive {archived.name}")
        if skipped:
            print(f"  WARNING: {len(skipped)} tree(s) skipped; details in {target / 'source.json'}")
        if matched_psd:
            print(f"  TBP PSD archived: {matched_psd.name}")
        else:
            print("  No unique adjacent TBP PSD export found; supply --archive-psd if needed")

    # Archive PSD files only by explicit selection; never infer a pairing from
    # opaque names or feed a TBP PSD into the generated constituency pipeline.
    for psd in args.archive_psd:
        path = psd.expanduser().resolve()
        if not path.is_file() or path.suffix.lower() != ".psd":
            raise RuntimeError(f"PSD file not found: {path}")
        print(f"Archived TBP PSD: {archive(path, root / 'tycho' / 'psd')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("downloads", nargs="?", type=Path, default=Path.home() / "Downloads")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--archive-psd", type=Path, action="append", default=[], metavar="FILE",
                        help="archive an original TBP PSD verbatim; may be repeated")
    args = parser.parse_args()
    try:
        run(args)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
