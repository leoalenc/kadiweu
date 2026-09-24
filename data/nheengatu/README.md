# Nheengatu TBP imports

Run `python3 src/import_nheengatu_tbp.py ARCHIVE --repo ~/kadiweu`.
The newest ZIP member timestamp per document UID is selected; ties use filename order.
`tycho/` stores byte-identical selected JSON exports; `txt/` lists every sentence;
`psd/` contains only sentences with POS tags on every token and a valid full-span
constituency tree. Documents without such trees have no PSD file.
The manifest records source filenames, counts, and SHA-256 digests.
Reimporting the same archive gives identical outputs. The ZIP retains older exports.
