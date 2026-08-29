#!/usr/bin/env python3
"""Archive TBP parser exports and create emulator-compatible rules."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


EXPECTED_RULES = {
    "cp-d-daǥa",
    "cp-daGa",
}
ORIGINAL_CONDITION = "(C iDoms daǥa)"
COMPAT_CONDITION = "(C iDoms daǥa|daGa)"
FILENAME_RE = re.compile(
    r"^(?P<stem>.+)-(?P<date>\d{6})-(?P<time>\d{4})\.json$"
)
HISTORY_TIMESTAMP_RE = re.compile(r"^(?P<stamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\t")
DEFAULT_BASENAME = "Kadiw-u"


class GeneratorError(RuntimeError):
    """Raised when an input cannot safely produce the requested files."""


@dataclass(frozen=True)
class Publication:
    date_code: str
    time_code: str
    instant: datetime

    @property
    def identifier(self) -> str:
        return f"{self.date_code}-{self.time_code}"

    @property
    def display(self) -> str:
        return self.instant.strftime("%Y-%m-%d %H:%M")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def publication_from_filename(path: Path) -> Publication:
    match = FILENAME_RE.fullmatch(path.name)
    if not match:
        raise GeneratorError(
            "rules filename must end in DDMMYY-HHMM.json, for example "
            "Kadiw-u-210826-1220.json"
        )
    date_code = match.group("date")
    time_code = match.group("time")
    try:
        instant = datetime.strptime(date_code + time_code, "%d%m%y%H%M")
    except ValueError as exc:
        raise GeneratorError(
            f"invalid Brazilian date/time in filename {path.name}: {exc}"
        ) from exc
    return Publication(date_code, time_code, instant)


def publication_from_history(path: Path) -> Publication:
    """Return the newest TBP publication recorded in a tab-separated history."""
    if not path.is_file():
        raise GeneratorError(f"TBP history file not found: {path}")
    publications: list[datetime] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        if not line.strip() or line.startswith("Histórico") or line.startswith("Data\t"):
            continue
        fields = line.split("\t")
        match = HISTORY_TIMESTAMP_RE.match(line)
        if len(fields) < 3 or not match:
            raise GeneratorError(
                f"malformed TBP history row in {path}:{line_number}: {line!r}"
            )
        if fields[2].strip() != "Publicação":
            continue
        try:
            publications.append(datetime.strptime(match.group("stamp"), "%Y-%m-%d %H:%M:%S"))
        except ValueError as exc:
            raise GeneratorError(
                f"invalid publication timestamp in {path}:{line_number}: {exc}"
            ) from exc
    if not publications:
        raise GeneratorError(f"no publication rows found in TBP history: {path}")
    instant = max(publications)
    return Publication(instant.strftime("%d%m%y"), instant.strftime("%H%M"), instant)


def load_json_array(text: str, path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GeneratorError(
            f"malformed JSON in {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(data, list) or not data:
        raise GeneratorError(f"{path} must contain a non-empty JSON array")
    if not all(isinstance(item, dict) for item in data):
        raise GeneratorError(f"every rule in {path} must be a JSON object")
    return data


def make_compat_text(source_text: str, source_path: Path) -> tuple[str, list[int]]:
    original = load_json_array(source_text, source_path)
    labels: dict[str, list[int]] = {}
    for number, rule in enumerate(original, start=1):
        label = rule.get("label")
        if isinstance(label, str):
            labels.setdefault(label, []).append(number)

    missing = sorted(EXPECTED_RULES - labels.keys())
    duplicated = sorted(label for label in EXPECTED_RULES if len(labels.get(label, [])) != 1)
    if missing:
        raise GeneratorError("missing required daGa rule(s): " + ", ".join(missing))
    if duplicated:
        raise GeneratorError("required rule label is not unique: " + ", ".join(duplicated))

    target_numbers = sorted(labels[label][0] for label in EXPECTED_RULES)
    expected = deepcopy(original)
    for number in target_numbers:
        value = expected[number - 1].get("value")
        if not isinstance(value, str):
            raise GeneratorError(f"rule {number} has no string value")
        count = value.count(ORIGINAL_CONDITION)
        if count != 1:
            raise GeneratorError(
                f"rule {number} ({expected[number - 1].get('label')}) must contain "
                f"exactly one {ORIGINAL_CONDITION!r}; found {count}"
            )
        expected[number - 1]["value"] = value.replace(
            ORIGINAL_CONDITION, COMPAT_CONDITION, 1
        )

    raw_count = source_text.count(ORIGINAL_CONDITION)
    if raw_count != len(target_numbers):
        raise GeneratorError(
            f"the JSON text contains {raw_count} occurrences of "
            f"{ORIGINAL_CONDITION!r}; expected exactly {len(target_numbers)} in "
            "the two daGa rules"
        )

    compat_text = source_text.replace(ORIGINAL_CONDITION, COMPAT_CONDITION)
    actual = load_json_array(compat_text, source_path)
    if actual != expected:
        raise GeneratorError("compatibility edit would change data outside the two daGa rules")
    return compat_text, target_numbers


def atomic_write(path: Path, content: str, mode: int, force: bool) -> None:
    if path.exists() and not force:
        raise GeneratorError(f"output already exists: {path}; use --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_bytes(path: Path, content: bytes, mode: int, force: bool) -> None:
    if path.exists() and not force:
        raise GeneratorError(f"output already exists: {path}; use --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def render_runner(
    template_text: str,
    template_path: Path,
    compat_path: Path,
    compat_hash: str,
    publication: Publication,
    executed_rules: int,
    ignored_rules: list[tuple[int, str]],
) -> str:
    hash_pattern = re.compile(
        r'(?m)^readonly EXPECTED_RULES_SHA256="[0-9a-f]{64}"$'
    )
    rules_pattern = re.compile(r'(?m)^RULES_C="\$\{RULES_C:-[^\r\n]+\}"$')
    executed_pattern = re.compile(
        r"(?m)^readonly EXPECTED_EXECUTED_RULES=\d+$"
    )
    if len(hash_pattern.findall(template_text)) != 1:
        raise GeneratorError(
            f"{template_path} must contain exactly one EXPECTED_RULES_SHA256 declaration"
        )
    if len(rules_pattern.findall(template_text)) != 1:
        raise GeneratorError(
            f"{template_path} must contain exactly one RULES_C default declaration"
        )
    if len(executed_pattern.findall(template_text)) != 1:
        raise GeneratorError(
            f"{template_path} must contain exactly one "
            "EXPECTED_EXECUTED_RULES declaration"
        )

    rendered = hash_pattern.sub(
        f'readonly EXPECTED_RULES_SHA256="{compat_hash}"', template_text
    )
    rendered = rules_pattern.sub(
        f'RULES_C="${{RULES_C:-{compat_path}}}"', rendered
    )
    rendered = executed_pattern.sub(
        f"readonly EXPECTED_EXECUTED_RULES={executed_rules}", rendered
    )
    marker = "set -euo pipefail"
    provenance = (
        f"# Generated for TBP publication {publication.display} "
        f"(America/Fortaleza), identifier {publication.identifier}."
    )
    if marker not in rendered:
        raise GeneratorError(f"{template_path} does not contain {marker!r}")
    rendered = rendered.replace(marker, marker + "\n\n" + provenance, 1)

    skipped_description = ", ".join(
        f"{number} ({label})" for number, label in ignored_rules
    )
    executed_printf = re.compile(
        r"(?m)^printf '  Executed rules: %s \(JSON ignore markers skipped "
        r"TBP Rules .*\)\\n' \"\$rule_rows\"$"
    )
    replacement = (
        "printf '  Executed rules: %s (JSON ignore markers skipped TBP "
        f"rules {skipped_description})\\n' \"$rule_rows\""
    )
    if len(executed_printf.findall(rendered)) == 1:
        rendered = executed_printf.sub(lambda _: replacement, rendered)
    return rendered


def default_template() -> Path:
    return Path.home() / "kadiweu/src/run_kadiweu_parser_full_test_C.sh"


def default_archive_dir() -> Path:
    return Path.home() / "Dropbox/projects/2025/post-doc/parser"


def default_downloads_dir() -> Path:
    return Path.home() / "Downloads"


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "With a JSON argument, preserve the original compatibility-generator "
            "workflow. With no JSON argument, archive Kadiw-u.txt and Kadiw-u.json "
            "from ~/Downloads under a publication-dated name first."
        )
    )
    parser.add_argument(
        "rules_json",
        nargs="?",
        type=Path,
        help=("already archived TBP JSON named like Kadiw-u-DDMMYY-HHMM.json; "
              "omit to archive the latest downloads"),
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=default_template(),
        help="full-test C shell-script template (default: %(default)s)",
    )
    parser.add_argument(
        "--runner-output",
        type=Path,
        help=(
            "generated runner path (default: beside the template as "
            "run_kadiweu_parser_full_test_C_DDMMYY_HHMM.sh)"
        ),
    )
    parser.add_argument(
        "--downloads-dir",
        type=Path,
        default=default_downloads_dir(),
        help="directory containing undated Kadiw-u.txt/json exports (default: %(default)s)",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=default_archive_dir(),
        help="destination for dated parser versions (default: %(default)s)",
    )
    parser.add_argument(
        "--history",
        type=Path,
        help="TBP histórico.txt (archive mode default: DOWNLOADS_DIR/histórico.txt)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace existing generated files",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_arguments(argv)
    template = args.template.expanduser().resolve()
    if not template.is_file():
        raise GeneratorError(f"runner template not found: {template}")

    archived_txt: Path | None = None
    downloaded_txt: Path | None = None
    if args.rules_json is not None:
        source = args.rules_json.expanduser().resolve()
        if not source.is_file():
            raise GeneratorError(f"rules file not found: {source}")
        if source.name.endswith(".compat.json"):
            raise GeneratorError("input must be the original JSON, not a .compat.json file")
        publication = publication_from_filename(source)
        source_text = source.read_text(encoding="utf-8")
    else:
        downloads = args.downloads_dir.expanduser().resolve()
        archive_dir = args.archive_dir.expanduser().resolve()
        history = (
            args.history.expanduser().resolve()
            if args.history
            else downloads / "histórico.txt"
        )
        publication = publication_from_history(history)
        downloaded_json = downloads / f"{DEFAULT_BASENAME}.json"
        downloaded_txt = downloads / f"{DEFAULT_BASENAME}.txt"
        missing = [str(path) for path in (downloaded_txt, downloaded_json) if not path.is_file()]
        if missing:
            raise GeneratorError("downloaded parser export(s) not found: " + ", ".join(missing))
        dated_stem = f"{DEFAULT_BASENAME}-{publication.identifier}"
        source = archive_dir / f"{dated_stem}.json"
        archived_txt = archive_dir / f"{dated_stem}.txt"
        source_text = downloaded_json.read_text(encoding="utf-8")

    compat = source.with_name(source.stem + ".compat.json")
    runner = (
        args.runner_output.expanduser().resolve()
        if args.runner_output
        else template.with_name(
            f"run_kadiweu_parser_full_test_C_"
            f"{publication.date_code}_{publication.time_code}.sh"
        )
    )
    if compat == runner:
        raise GeneratorError("compatibility JSON and runner output paths must differ")

    compat_text, changed_rules = make_compat_text(source_text, source)

    # Write to a temporary sibling first so the runner can be pinned to the
    # exact bytes that will become the compatibility file.
    compat_hash = hashlib.sha256(compat_text.encode("utf-8")).hexdigest()
    compat_data = load_json_array(compat_text, compat)
    ignored_rules = [
        (number, str(rule.get("label", "unnamed")))
        for number, rule in enumerate(compat_data, start=1)
        if rule.get("ignore") is True
    ]
    executed_rules = len(compat_data) - len(ignored_rules)
    template_text = template.read_text(encoding="utf-8")
    runner_text = render_runner(
        template_text,
        template,
        compat,
        compat_hash,
        publication,
        executed_rules,
        ignored_rules,
    )

    # Validate every output and collision before modifying any destination.
    load_json_array(compat_text, compat)
    if not runner_text.startswith("#!/usr/bin/env bash\n"):
        raise GeneratorError("generated runner has an unexpected shebang")
    outputs = [compat, runner]
    if archived_txt is not None:
        outputs = [archived_txt, source, *outputs]
    if not args.force:
        collisions = [str(path) for path in outputs if path.exists()]
        if collisions:
            raise GeneratorError(
                "output already exists: " + ", ".join(collisions) + "; use --force to replace it"
            )

    if archived_txt is not None and downloaded_txt is not None:
        atomic_write_bytes(archived_txt, downloaded_txt.read_bytes(), 0o664, args.force)
        atomic_write_bytes(source, source_text.encode("utf-8"), 0o664, args.force)

    atomic_write(compat, compat_text, 0o600, args.force)
    try:
        atomic_write(runner, runner_text, 0o755, args.force)
    except Exception:
        # Do not delete a pre-existing file replaced under --force. Without
        # --force, compat did not exist before this invocation and is safe to remove.
        if not args.force and compat.exists():
            compat.unlink()
        raise

    print(f"TBP publication: {publication.display} America/Fortaleza")
    if archived_txt is not None:
        print(f"Archived TXT: {archived_txt}")
        print(f"Archived JSON: {source}")
    print("Changed rules: " + ", ".join(map(str, changed_rules)))
    print(f"Compatibility JSON: {compat}")
    print(f"Compatibility SHA-256: {sha256(compat)}")
    print(f"JSON rules: {len(compat_data)} total, {len(ignored_rules)} ignored, "
          f"{executed_rules} executed")
    if ignored_rules:
        print("Ignored rules: " + ", ".join(
            f"{number} ({label})" for number, label in ignored_rules
        ))
    print(f"Test runner: {runner}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GeneratorError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
