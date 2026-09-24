#!/usr/bin/env python3
"""Import a TBP Nheengatu ZIP into data/nheengatu (standard library only).

Usage: python3 src/import_nheengatu_tbp.py ~/Downloads/stories.zip
       python3 src/import_nheengatu_tbp.py stories.zip --repo ~/kadiweu
The latest ZIP timestamp is selected for each document UID. Originals are kept.
"""

import argparse
import collections
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path


def sentences(data):
    return [s for page in data['pages'] for s in page.get('sentences', [])]


def atom(value):
    """Escape TBP surface forms for Penn-style leaf positions."""
    if not isinstance(value, str) or not value or re.search(r'[\s()]', value):
        raise ValueError(f'unsafe Penn tree atom: {value!r}')
    return value


def tree_for(sentence):
    struct = sentence.get('struct') or {}
    tokens = struct.get('tokens') or []
    chunks = struct.get('chunks') or []
    if not tokens or not chunks or any(not t.get('t') for t in tokens):
        return None
    positions = [t.get('p') for t in tokens]
    if positions != list(range(1, len(tokens) + 1)):
        raise ValueError('tagged sentence has nonconsecutive token positions')
    spans = []
    for c in chunks:
        a, b = c.get('i'), c.get('f')
        if not isinstance(a, int) or not isinstance(b, int) or not 1 <= a <= b <= len(tokens):
            raise ValueError(f'invalid chunk: {c!r}')
        spans.append((a, b, atom(c.get('t'))))
    if len({(a, b, tag) for a, b, tag in spans}) != len(spans):
        raise ValueError('duplicate chunk')
    # Equal spans are nested in source order, allowing unary projections.
    ordered = sorted(enumerate(spans), key=lambda v: (v[1][0], -v[1][1], v[0]))
    for _, (a, b, _) in ordered:
        for _, (c, d, _) in ordered:
            if a < c <= b < d:
                raise ValueError('crossing constituency chunks')
    if not any(a == 1 and b == len(tokens) for a, b, _ in spans):
        raise ValueError('tagged sentence has no full-span root chunk')

    def render(a, b, candidates):
        if candidates and candidates[0][1][:2] == (a, b):
            idx, (_, _, tag) = candidates[0]
            return f'({tag} {render(a, b, candidates[1:])})'
        pieces = []
        p = a
        while p <= b:
            starts = [c for c in candidates if c[1][0] == p]
            if starts:
                end = max(c[1][1] for c in starts)
                if end > b:
                    raise ValueError('chunk extends outside parent')
                inner = [c for c in candidates if p <= c[1][0] and c[1][1] <= end]
                pieces.append(render(p, end, inner))
                p = end + 1
            else:
                token = tokens[p - 1]
                pieces.append(f"({atom(token['t'])} {atom(token.get('v'))})")
                p += 1
        return ' '.join(pieces)

    return render(1, len(tokens), ordered)


def clean_comment(value):
    return str(value or '').replace('\r', ' ').replace('\n', ' ').replace('*/', '* /')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive', type=Path)
    ap.add_argument('--repo', type=Path, default=Path('~/kadiweu').expanduser())
    args = ap.parse_args()
    target = args.repo.expanduser() / 'data' / 'nheengatu'
    choices = collections.defaultdict(list)
    with zipfile.ZipFile(args.archive) as archive:
        for info in archive.infolist():
            if info.is_dir() or not info.filename.lower().endswith('.json'):
                continue
            if Path(info.filename).name != info.filename:
                raise ValueError(f'JSON must be at archive root: {info.filename}')
            raw = archive.read(info)
            data = json.loads(raw)
            doc = data['document']
            uid = doc['uid']
            if not isinstance(uid, str) or not re.fullmatch(r'[0-9a-f-]{36}', uid):
                raise ValueError(f'invalid document UID in {info.filename}')
            choices[uid].append((info, raw, data))
        if not choices:
            raise ValueError('No TBP document JSON files in archive')
        picked = [max(group, key=lambda item: (item[0].date_time, item[0].filename))
                  for group in choices.values()]
        refs = [item[2]['document'].get('reference') for item in picked]
        if any(not isinstance(r, str) or not re.fullmatch(r'[A-Za-z0-9_-]+\.txt', r) for r in refs):
            raise ValueError('Missing or unsafe TBP document reference')
        if len(set(refs)) != len(refs):
            raise ValueError('Different document UIDs share a reference; cannot name outputs safely')
        # Build and validate all derived files before changing destination files.
        staged = []
        rows = []
        for info, raw, data in sorted(picked, key=lambda item: item[2]['document']['reference']):
            doc = data['document']
            base = Path(doc['reference']).stem
            lines = [f"document_uid: {doc['uid']}", f"title: {doc.get('name', '')}",
                     f"reference: {doc['reference']}", f"source_json: {info.filename}", '']
            trees = []
            ss = sentences(data)
            for n, sent in enumerate(ss, 1):
                translation = sent.get('translations') or {}
                pt = translation.get('pt-BR', translation.get('pt-br', ''))
                lines += [f'sentence: {n}', f"uid: {sent.get('uid', '')}",
                          f"text: {sent.get('text', '')}", f'text_por: {pt}',
                          'tokens: ' + json.dumps(sent.get('struct', {}).get('tokens', []), ensure_ascii=False),
                          'chunks: ' + json.dumps(sent.get('struct', {}).get('chunks', []), ensure_ascii=False), '']
                try:
                    tree = tree_for(sent)
                except ValueError as exc:
                    raise ValueError(f'{base} sentence {n}: {exc}') from exc
                if tree:
                    comment = '\n'.join(['/*', f'sentence = {n}',
                        f"uid = {clean_comment(sent.get('uid'))}",
                        f"text = {clean_comment(sent.get('text'))}",
                        f'text_por = {clean_comment(pt)}', '*/'])
                    trees.append(f'{comment}\n{tree[:-1]} (ID {base},0.{n}))')
            staged.extend([(target / 'tycho' / info.filename, raw),
                           (target / 'txt' / (base + '.txt'), ('\n'.join(lines) + '\n').encode())])
            if trees:
                staged.append((target / 'psd' / (base + '.psd'),
                               ('\n\n'.join(trees) + '\n').encode()))
            rows.append([base, doc['uid'], doc.get('name', ''), doc['reference'], info.filename,
                         str(len(choices[doc['uid']])), str(len(ss)), str(len(trees)),
                         hashlib.sha256(raw).hexdigest()])
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter='\t', lineterminator='\n')
        writer.writerow(['base', 'document_uid', 'title', 'reference', 'selected_json',
                         'exports_in_archive', 'sentences', 'psd_trees', 'sha256'])
        writer.writerows(rows)
        staged.append((target / 'manifest.tsv', buffer.getvalue().encode()))
        readme = ('# Nheengatu TBP imports\n\n'
                  'Run `python3 src/import_nheengatu_tbp.py ARCHIVE --repo ~/kadiweu`.\n'
                  'The newest ZIP member timestamp per document UID is selected; ties use filename order.\n'
                  '`tycho/` stores byte-identical selected JSON exports; `txt/` lists every sentence;\n'
                  '`psd/` contains only sentences with POS tags on every token and a valid full-span\n'
                  'constituency tree. Documents without such trees have no PSD file.\n'
                  'The manifest records source filenames, counts, and SHA-256 digests.\n'
                  'Reimporting the same archive gives identical outputs. The ZIP retains older exports.\n')
        staged.append((target / 'README.md', readme.encode()))
        (target / 'psd').mkdir(parents=True, exist_ok=True)
        for path, content in staged:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        print(f'Imported {len(rows)} documents, {sum(int(r[6]) for r in rows)} sentences, '
              f'{sum(int(r[7]) for r in rows)} PSD trees into {target}')
        for row in rows:
            print(f'{row[0]}: {row[6]} sentences, {row[7]} trees; {row[4]}'
                  + (f' (newest of {row[5]})' if row[5] != '1' else ''))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, zipfile.BadZipFile, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
