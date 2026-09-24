#!/usr/bin/env python3
"""Inventory TBP annotation per sentence and document.

Examples:
  python3 src/inventory_tbp_annotations.py ~/kadiweu/data/nheengatu/tycho \
      --tree-module ~/kadiweu/src/kadiweu_constituency.py \
      --output-dir ~/kadiweu/data/nheengatu/reports/annotation-inventory
  python3 src/inventory_tbp_annotations.py ~/Downloads/stories.zip \
      --tree-module ~/kadiweu/src/kadiweu_constituency.py

ZIP input selects the latest archive timestamp for each document UID. A directory
with duplicate exports selects the newest file mtime per UID. Source JSON is
never modified. Empty or absent fields are reported separately.
"""
from __future__ import annotations

import argparse
import collections
import csv
import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path


def load_tree_module(path):
    if path is None:
        return None
    spec = importlib.util.spec_from_file_location('tbp_constituency', path)
    if spec is None or spec.loader is None:
        raise ValueError(f'cannot import tree module: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_documents(source):
    candidates = collections.defaultdict(list)
    if source.is_dir():
        items = [(p.name, p.stat().st_mtime_ns, p.read_bytes())
                 for p in source.glob('*.json') if p.is_file()]
    elif zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            items = [(i.filename, i.date_time, archive.read(i))
                     for i in archive.infolist() if not i.is_dir() and i.filename.lower().endswith('.json')]
    elif source.suffix.lower() == '.json':
        items = [(source.name, source.stat().st_mtime_ns, source.read_bytes())]
    else:
        raise ValueError('input must be a JSON file, directory of JSON files, or ZIP')
    for name, timestamp, raw in items:
        data = json.loads(raw)
        doc = data.get('document')
        if not isinstance(doc, dict) or not doc.get('uid'):
            raise ValueError(f'{name}: missing document.uid')
        candidates[str(doc['uid'])].append((timestamp, name, data))
    if not candidates:
        raise ValueError('no JSON documents found')
    return [(max(group, key=lambda x: (x[0], x[1])), len(group))
            for group in candidates.values()]


def iter_sentences(data):
    # Follow the same page/sentence order as the supplied tree module.
    def visit(obj):
        if isinstance(obj, dict):
            struct = obj.get('struct')
            if isinstance(obj.get('text'), str) and isinstance(struct, dict) and any(
                    key in struct for key in ('tokens', 'chunks', 'conllu')):
                yield obj
                return
            for value in obj.values():
                yield from visit(value)
        elif isinstance(obj, list):
            for value in obj:
                yield from visit(value)
    yield from visit(data)


def available(value):
    return value is not None and value != '' and value != [] and value != {}


def number(value):
    return str(value) if value is not None else ''


def inspect_sentence(sentence, n, doc, source_name, module):
    struct = sentence.get('struct') or {}
    tokens = struct.get('tokens') or []
    chunks = struct.get('chunks') or []
    conllu = struct.get('conllu') or []
    if not all(isinstance(x, list) for x in (tokens, chunks, conllu)):
        raise ValueError(f'{source_name} sentence {n}: tokens/chunks/conllu must be lists')
    pos_count = sum(isinstance(t, dict) and available(t.get('t')) for t in tokens)
    chunk_levels = sum(isinstance(c, dict) and c.get('l') is not None for c in chunks)
    tok_levels = sum(isinstance(t, dict) and t.get('l') is not None for t in tokens)
    glosses = sum(isinstance(t, dict) and isinstance(t.get('attributes'), dict)
                  and available(t['attributes'].get('gloss-br')) for t in tokens)
    splits = sum(isinstance(t, dict) and (available(t.get('split')) or available(t.get('splits')))
                 for t in tokens)
    parsed = struct.get('parsed')
    translations = sentence.get('translations') or {}
    pt = (translations.get('pt-BR') or translations.get('pt-br') or '') if isinstance(translations, dict) else ''
    result = 'not_checked' if module is None else 'no_chunks'
    error = ''
    if module is not None and chunks:
        try:
            tree = module.tree_from_sentence(sentence, sentence_number=n,
                                             source_name=Path(str(doc.get('reference') or source_name)).stem)
            tree.root  # Require a unique root.
            result = 'yes'
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            result = 'no'
            error = f'{type(exc).__name__}: {exc}'
    return {
        'document_uid': str(doc['uid']), 'reference': str(doc.get('reference') or ''),
        'document_title': str(doc.get('name') or ''), 'source_json': source_name,
        'sentence_number': n, 'sentence_uid': str(sentence.get('uid') or ''),
        'text': sentence.get('text') or '', 'text_por': pt,
        'sentence_status': number(sentence.get('status')),
        'struct_status': number(struct.get('status')),
        'parsed_marker': number(parsed), 'token_count': len(tokens),
        'pos_tagged_tokens': pos_count,
        'pos_coverage': ('complete' if tokens and pos_count == len(tokens)
                         else 'partial' if pos_count else 'none'),
        'token_levels': tok_levels, 'chunk_count': len(chunks),
        'chunk_labels': '|'.join(str(c.get('t', '')) for c in chunks if isinstance(c, dict)),
        'chunk_levels': chunk_levels,
        'chunk_coverage': ('none' if not chunks else 'root_only' if len(chunks) == 1 else 'multiple'),
        'tree_reconstructable': result, 'tree_error': error,
        'proto_conllu_rows': len(conllu),
        'proto_conllu_with_head': sum(isinstance(c, dict) and available(c.get('head')) for c in conllu),
        'proto_conllu_with_deprel': sum(isinstance(c, dict) and available(c.get('deprel')) for c in conllu),
        'translations_present': int(bool(translations)), 'token_glosses': glosses,
        'tokens_with_splits': splits,
        'sentence_comments': len(sentence.get('comments') or []),
        'break_markers': len(sentence.get('breaks') or []),
    }


def write_tsv(path, rows, columns):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input', type=Path)
    parser.add_argument('--tree-module', type=Path, help='Path to kadiweu_constituency.py for a real reconstruction check')
    parser.add_argument('--output-dir', type=Path, default=Path('annotation-inventory'))
    args = parser.parse_args()
    module = load_tree_module(args.tree_module.expanduser()) if args.tree_module else None
    selected = load_documents(args.input.expanduser())
    rows = []
    docs = []
    for (timestamp, name, data), export_count in sorted(
            selected, key=lambda pair: (str(pair[0][2]['document'].get('reference') or ''), pair[0][1])):
        doc = data['document']
        group = [inspect_sentence(s, n, doc, name, module)
                 for n, s in enumerate(iter_sentences(data), 1)]
        rows.extend(group)
        docs.append({
            'document_uid': doc['uid'], 'reference': doc.get('reference') or '',
            'document_title': doc.get('name') or '', 'source_json': name,
            'exports_found': export_count, 'sentences': len(group),
            'pos_complete': sum(r['pos_coverage'] == 'complete' for r in group),
            'pos_partial': sum(r['pos_coverage'] == 'partial' for r in group),
            'pos_none': sum(r['pos_coverage'] == 'none' for r in group),
            'with_chunks': sum(r['chunk_count'] > 0 for r in group),
            'with_multiple_chunks': sum(r['chunk_count'] > 1 for r in group),
            'tree_reconstructable': sum(r['tree_reconstructable'] == 'yes' for r in group),
            'tree_failed': sum(r['tree_reconstructable'] == 'no' for r in group),
            'with_proto_conllu': sum(r['proto_conllu_rows'] > 0 for r in group),
            'with_parsed_marker': sum(bool(r['parsed_marker']) for r in group),
            'with_translation': sum(bool(r['translations_present']) for r in group),
        })
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sentence_path = args.output_dir / 'sentences.tsv'
    document_path = args.output_dir / 'documents.tsv'
    write_tsv(sentence_path, rows, list(rows[0]) if rows else list(inspect_sentence(
        {'struct': {}}, 1, {'uid': ''}, '', None)))
    write_tsv(document_path, docs, list(docs[0]))
    print(f'{len(docs)} documents; {len(rows)} sentences; '
          f'{sum(d["pos_complete"] for d in docs)} fully POS tagged; '
          f'{sum(d["pos_partial"] for d in docs)} partially POS tagged; '
          f'{sum(d["with_multiple_chunks"] for d in docs)} with multiple chunks')
    if module:
        print(f'{sum(d["tree_reconstructable"] for d in docs)} reconstructable with {args.tree_module}')
    print(f'Wrote {sentence_path} and {document_path}')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as exc:
        sys.exit(f'ERROR: {exc}')
