# Adjudication of structural differences in the expanded parser test

## Scope

This adjudication records the outcome of the latest 36-sentence emulator run, after correcting TBP Rule 119 (`cp-me-q`) so that it recognizes both `me` and `me@`:

```text
AND (C iDoms me|me@)
```

The latest result is:

| `struct_status` | Exact | Trace-equivalent | Structural difference | Total |
|---|---:|---:|---:|---:|
| DONE | 11 | 7 | 0 | 18 |
| REVIEW | 11 | 4 | 3 | 18 |
| TOTAL | 22 | 11 | 3 | 36 |

All remaining structural differences have now been adjudicated below.

## Adjudication summary

| Sentence | Status | Correction target | Decision |
|---|---|---|---|
| `hil-data,0.34` | REVIEW | Reference tree | Accept the parser output: project the possessor `niganigawanigi` as an embedded `NP`. |
| `hil-data,0.7` | REVIEW | Reference tree | Accept the parser output: replace duplicated `CP-me-me` with `CP-me`, label the first NP `NP-SBJ`, and project the complement of `C me` as `IP-SUB`. |
| `van-data,0.10` | REVIEW | Reference tree | Apply the same correction as for `hil-data,0.7`; the two records contain the same Kadiwéu sentence and construction. |

No remaining difference requires a correction to the runner or to rule emulation.

## Individual notes

### `hil-data,0.34`

Text: `liwigo niganigawanigi libinienigi`

Portuguese translation: `Esta fotografia da criança é bonita.`

Reference:

```lisp
(IP-MAT
  (NP-SBJ
    (N$ liwigo)
    (N niganigawanigi))
  (NP-PRD (N$ libinienigi)))
```

Parser output:

```lisp
(IP-MAT
  (NP-SBJ
    (N$ liwigo)
    (NP (N niganigawanigi)))
  (NP-PRD (N$ libinienigi)))
```

**Adjudication: correct the reference tree.** `niganigawanigi` is the nominal possessor in the possessum-possessor expression translated as `fotografia da criança`. It should project its own `NP` under the larger subject NP. This is also the intended analysis previously established for this sentence. The parser output therefore preserves the relevant internal constituency, while the provisional REVIEW reference leaves the possessor as a bare sister `N`.

Required reference correction:

```diff
- (N niganigawanigi)
+ (NP (N niganigawanigi))
```

### `hil-data,0.7`

Text: `Gawenigi eliodi me libinienigi`

Portuguese translation: `A sua comida é muito bonita.`

Reference:

```lisp
(IP-MAT
  (NP (N$ Gawenigi))
  (CP-me-me
    (Q eliodi)
    (C me)
    (NP (N$ libinienigi))))
```

Parser output:

```lisp
(IP-MAT
  (NP-SBJ (N$ Gawenigi))
  (CP-me
    (Q eliodi)
    (C me)
    (IP-SUB
      (NP (N$ libinienigi)))))
```

**Adjudication: correct the reference tree.** The duplicated suffix in `CP-me-me` is an overgenerated label, not a distinct syntactic category. The initial nominal is the subject of the matrix predication and should be `NP-SBJ`. The constituent selected by complementizer `me` is clausal and should be projected as `IP-SUB`, with the predicate nominal inside it. The parser output gives the intended structure.

Required reference corrections:

```diff
- (NP (N$ Gawenigi))
+ (NP-SBJ (N$ Gawenigi))

- (CP-me-me ... (NP (N$ libinienigi)))
+ (CP-me ... (IP-SUB (NP (N$ libinienigi))))
```

### `van-data,0.10`

Text: `Gawenigi eliodi me libinienigi`

Portuguese translation: `a sua comida é muito bonita`

The reference and parser output are structurally identical to those shown for `hil-data,0.7`.

**Adjudication: correct the reference tree.** This is the same sentence and construction as `hil-data,0.7`, stored in a second dataset. Consistency requires the same corrections: `NP-SBJ`, a single `-me` suffix on `CP-me`, and an `IP-SUB` projection around the predicate NP. The duplicated occurrence is corroborating evidence for one analysis, not an independent construction requiring a different rule.

## Resolved earlier difference

`hil-data,0.25` is no longer a structural difference. The controlled Rule 119 correction from:

```text
AND (C iDoms me)
```

to:

```text
AND (C iDoms me|me@)
```

made the emulator output exactly match the reference. Its adjudication target was therefore the rule emulation/rule compatibility layer, and that correction has already been applied to the run summarized here.

## Closure assessment

- [x] Every structural difference in the latest run has an explicit adjudication note.
- [x] Every note identifies whether to correct the parser output, reference tree, or runner/rule emulation.
- [x] The three remaining differences require reference-tree corrections.
- [x] No DONE sentence has an unresolved structural difference.
- [x] The earlier `hil-data,0.25` emulation discrepancy was corrected and is now an exact match.

The issue acceptance criterion is satisfied. The three REVIEW reference trees still need to be edited in the source treebank (two distinct sentence records, with `hil-data,0.7` and `van-data,0.10` sharing the same analysis), after which the expanded benchmark is expected to contain no structural differences.
