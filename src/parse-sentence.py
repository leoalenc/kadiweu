#!/usr/bin/env python3
"""Parse tagged sentences using the existing TBP emulator.

Install beside run_kadiweu_parser_rules.py in ~/kadiweu/src.
Usage:
  python parse-sentence.py -s 'Mɨcura/N raɨíra/N$ oiumẽndári/VB cinimũ/N ./PUNCT' -r Kadiw-u-250926-1055.compat.json
  python parse-sentence.py -f sentences.txt -r Kadiw-u-250926-1055.compat.json
Files contain one whitespace-delimited FORM/TAG sentence per nonblank line.
Only the summary and generated LISP records go to stdout. Verbose diagnostics
and errors go to stderr. No gold tree, tagging or tag conversion is performed.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

RULE_NAME = 'Kadiw-u-250926-1055.compat.json'
RULE_HASH = '1d3291204215014851b0ae9f2e7888faa2361b0c6f022f73485ad2811b556a4a'
DEFINITION_HASH = '46b3e1fb5512747d4c20aa5bdcf600af6ac6a6d6b639d9debe2155470a050222'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_emulator(path):
    spec = importlib.util.spec_from_file_location('tbp_sentence_emulator', path)
    if spec is None or spec.loader is None:
        raise ValueError(f'cannot import emulator: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def tagged_record(sentence, number):
    pairs = []
    for token in sentence.split():
        form, separator, tag = token.rpartition('/')
        if not separator or not form or not tag:
            raise ValueError(f'sentence {number}: expected FORM/TAG, found {token!r}')
        if any(c in form + tag for c in '()') or '/*' in form + tag or '*/' in form + tag:
            raise ValueError(f'sentence {number}: parentheses/comment delimiters cannot be LISP atoms: {token!r}')
        pairs.append(f'({tag} {form})')
    if not pairs:
        raise ValueError(f'sentence {number}: empty sentence')
    return f'((IP-MAT {" ".join(pairs)}) (ID sentence,0.{number}))\n'


def build_parser():
    folder = Path.home() / 'Dropbox/projects/2025/post-doc/parser'
    root = Path(os.environ.get('KADIWEU_ROOT', str(Path.home() / 'kadiweu')))
    nearby = Path(__file__).resolve().parent / 'run_kadiweu_parser_rules.py'
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('-s', '--sentence', help='one tagged FORM/TAG sentence')
    source.add_argument('-f', '--file', type=Path, help='UTF-8 file, one tagged sentence per nonblank line')
    parser.add_argument('-r', '--rules', default=RULE_NAME, help='rules filename in the standard Dropbox parser folder, or an explicit path')
    parser.add_argument('-v', '--verbose', action='store_true', help='show emulator progress on stderr')
    parser.add_argument('--rules-dir', type=Path, default=folder, help='override standard Dropbox parser folder')
    parser.add_argument('--runner', type=Path, default=Path(os.environ.get('RUNNER', str(nearby if nearby.is_file() else root / 'src/run_kadiweu_parser_rules.py'))))
    parser.add_argument('--definitions', type=Path, default=Path(os.environ.get('DEFINITIONS_C', str(folder / 'kadiweu_parser_definitions_070726.txt'))))
    parser.add_argument('--corpussearch', default=os.environ.get('CORPUSSEARCH', 'corpussearch'))
    parser.add_argument('--expected-sha256', help='trusted SHA-256 for another rule version; required for unknown filenames')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        rules_path = Path(args.rules).expanduser()
        if rules_path.parent == Path('.'):
            rules_path = args.rules_dir.expanduser() / rules_path
        rules_path = rules_path.resolve()
        expected = args.expected_sha256 or (RULE_HASH if rules_path.name == RULE_NAME else None)
        if expected is None:
            raise ValueError('unknown rules version: supply its trusted --expected-sha256')
        if not re.fullmatch(r'[0-9a-fA-F]{64}', expected):
            raise ValueError('--expected-sha256 must contain 64 hexadecimal digits')
        actual = digest(rules_path)
        if actual != expected.lower():
            raise ValueError(f'rules SHA-256 MISMATCH: expected {expected.lower()}; found {actual}; aborting')
        definitions_path = args.definitions.expanduser().resolve()
        if digest(definitions_path) != DEFINITION_HASH:
            raise ValueError('definitions SHA-256 mismatch; expected the verified 070726 definitions; aborting')
        sentences = [args.sentence] if args.sentence is not None else [line.strip() for line in args.file.expanduser().read_text(encoding='utf-8-sig').splitlines() if line.strip()]
        if not sentences:
            raise ValueError('input file contains no sentences')
        input_text = ''.join(tagged_record(s, i) for i, s in enumerate(sentences, 1))
        emulator = load_emulator(args.runner.expanduser().resolve())
        definitions = emulator.parse_definitions(definitions_path)
        rules, _, skips = emulator.parse_rules(rules_path, definitions)
        active = [rule for rule in rules if rule.original_number not in skips]
        if not active:
            raise ValueError('no executable rules')
        if actual == RULE_HASH and len(active) != 175:
            raise ValueError(f'expected 175 executable rules; found {len(active)}')
        corpussearch = shutil.which(args.corpussearch)
        if not corpussearch:
            raise ValueError(f'CorpusSearch command not found: {args.corpussearch}')
        describe = lambda selected: ', '.join(f'{r.original_number} ({r.name})' for r in selected) or 'none'
        summary = (f'Rules SHA-256: {actual} OK\n'
                   f'Rules: {len(rules)} total; {len(active)} executed\n'
                   f'Skipped rules: {describe([r for r in rules if r.original_number in skips])}\n'
                   f'Recursive rules: {describe([r for r in active if r.recursive])}\n')
        with tempfile.TemporaryDirectory(prefix='parse-sentence-') as temporary:
            directory = Path(temporary)
            source = directory / 'sentences.pos'
            source.write_text(input_text, encoding='utf-8')
            # Spool quiet progress to disk, avoiding a growing in-memory buffer.
            with (directory / 'diagnostics.log').open('w+', encoding='utf-8') as log:
                destination = sys.stderr if args.verbose else log
                try:
                    with contextlib.redirect_stdout(destination), contextlib.redirect_stderr(destination):
                        final_path = emulator.run_rules(active, source, corpussearch, directory / 'work', False, None)
                    records = emulator.read_records(final_path)
                    if [r.sentence_id for r in records] != [f'sentence,0.{i}' for i in range(1, len(sentences)+1)]:
                        raise ValueError('parser output sentence IDs/count/order do not match input')
                    trees = '\n'.join(r.tree.strip() for r in records) + '\n'
                except Exception:
                    if not args.verbose:
                        log.seek(0)
                        diagnostics = log.read()
                        if diagnostics:
                            print(diagnostics, file=sys.stderr, end='')
                    raise
        sys.stdout.write(summary + trees)
        return 0
    except Exception as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
