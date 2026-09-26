# Griffiths (2002) determiner-paradigm audit

## Result

No—not quite. For the canonical inventory tested here, Griffiths provides a headword for 35/36 simple and copied-anaphoric forms. The canonical form(s) not found as a headword or exact-form in-entry mention are: `ada`.

All twelve plural candidates (six simple and six copied anaphoric forms) are headwords. In particular, the forms raised in the question—`niǥijoa` and `niǥinoa`—are explicitly printed as plural partners in the headwords `niǥijo niǥijoa` and `niǥina niǥinoa`.

The dictionary also gives direct evidence for **gender syncretism in the plural**. For example, it prints both `niǥida niǥidoa dem masc ...` and `naǥada niǥidoa dem fem ...`: masculine singular `niǥida` and feminine singular `naǥada` share plural `niǥidoa`. Five feminine anaphoric headword lines explicitly use the corresponding `niǥi-` plural. The +AB feminine entry `naǥaca` omits a plural on its own line, although the masculine entry explicitly supplies `niǥicoa`; treating that plural as gender-syncretic therefore involves a small paradigm-based inference.

The optional-rule outputs without vowel copying (`nǥida`, `nǥada`, etc.) are not found as headwords or exact-form mentions in the dictionary-entry section. This absence is evidence about the dictionary's coverage and spelling, not by itself a claim of ungrammaticality.

## Orthography and extraction

Griffiths's PDF uses `º` for the Kadiwéu letter represented here as `ǥ`; some extractors may return `°`. Scripts and teaching materials may instead use `G`. The audit normalizes `º`, `°`, and `G` to `ǥ` before exact-token comparison.

## Coverage by series

| Series | Candidates | Headwords | Mentioned only | Absent from entries |
|---|---:|---:|---:|---:|
| Simple | 18 | 17 | 0 | 1 |
| Copied anaphoric | 18 | 18 | 0 | 0 |
| Uncopied anaphoric | 18 | 0 | 0 | 18 |
| User-supplied variant | 1 | 0 | 0 | 1 |

## Canonical paradigms

| Tag | Meaning | Simple M.SG | Simple F.SG | Simple PL | Anaphoric M.SG | Anaphoric F.SG | Anaphoric PL |
|---|---|---|---|---|---|---|---|
| +ST | standing/vertically extended | `ida` ✓ | `ada` — | `idoa` ✓ | `niǥida` ✓ | `naǥada` ✓ | `niǥidoa` ✓ |
| +SI | sitting/non-extended | `ini` ✓ | `ani` ✓ | `iniwa` ✓ | `niǥini` ✓ | `naǥani` ✓ | `niǥiniwa` ✓ |
| +CO | coming/approaching | `ina` ✓ | `ana` ✓ | `inoa` ✓ | `niǥina` ✓ | `naǥana` ✓ | `niǥinoa` ✓ |
| +LY | lying/horizontally extended | `idi` ✓ | `adi` ✓ | `idiwa` ✓ | `niǥidi` ✓ | `naǥadi` ✓ | `niǥidiwa` ✓ |
| +GO | going away | `ijo` ✓ | `ajo` ✓ | `ijoa` ✓ | `niǥijo` ✓ | `naǥajo` ✓ | `niǥijoa` ✓ |
| +AB | absent/out of sight | `ica` ✓ | `aca` ✓ | `icoa` ✓ | `niǥica` ✓ | `naǥaca` ✓ | `niǥicoa` ✓ |

## Headwords, mentions, and omissions

- Headwords that are also mentioned inside other entries: `ida`, `niǥida`, `naǥada`, `ini`, `ani`, `niǥini`, `naǥani`, `ina`, `ana`, `niǥina`, `naǥana`, `idi`, `niǥidi`, `naǥadi`, `ijo`, `ajo`, `niǥijo`, `naǥajo`, `ica`, `aca`, `icoa`, `niǥica`, `naǥaca`.
- Forms mentioned inside an entry but lacking their own headword: None.
- Canonical forms absent from dictionary entries: `ada`.
- The JSON keeps these categories non-destructive: a form can be a headword and also be mentioned elsewhere.

## Uncopied optional-rule outputs

The following exact forms were not found in the Kadiwéu–Portuguese dictionary entries:

`nǥida`, `nǥada`, `nǥidoa`, `nǥini`, `nǥani`, `nǥiniwa`, `nǥina`, `nǥana`, `nǥinoa`, `nǥidi`, `nǥadi`, `nǥidiwa`, `nǥijo`, `nǥajo`, `nǥijoa`, `nǥica`, `nǥaca`, `nǥicoa`

The uncopied plurals in this list are extrapolations from the optional-copy analysis plus the attested plural allomorphs; the supplied XFST scripts do not yet implement a plural layer.

## The spelling `ifo`

The user-supplied form is classified as **absent_from_dictionary_entries**. The six-root script generates `ijo`, not `ifo`, for +GO. The PDF audit therefore treats `ifo` as a form requiring independent verification rather than silently correcting it.

## Method and limitations

- Exact forms are matched after the restricted orthographic normalization described above.
- Entry headers are detected through the PDF's font information: the primary Kadiwéu headword is large bold type, and a paired plural is bold on the same header line.
- A form may have a headword and also occur inside other entries; the JSON preserves both kinds of evidence.
- `absent_from_dictionary_entries` means that this searchable PDF contains no exact-form entry evidence. It does not prove that a form is impossible in Kadiwéu.
- Appendix D confirms the six orientation/movement roots and the gender-bearing portions `naǥa-` and `niǥi-`, but it does not itself print a complete demonstrative plural table.

## Reproduction

```bash
python griffiths_determiner_audit.py KDDict.pdf --json griffiths_determiners.json --report griffiths_determiners_report.md
```

The JSON records page-level excerpts for every detected headword and mention.
