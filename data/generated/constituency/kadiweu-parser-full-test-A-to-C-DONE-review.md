---
title: "DONE Parser Transition Report"
geometry: margin=20mm
fontsize: 10pt
---

# 1. Introduction

This document compares parser A (BEFORE) with parser C (AFTER) for DONE sentences. It contains every improvement, regression, and persistent structural case recorded in the transition TSV. Improvement and regression sections show both parser trees; the persistent section shows the gold reference together with both parser trees. All trees are provided in LISP and graphical formats for human inspection.

**DONE improvements:** 5.  
**DONE regressions:** 9.

# 2. DONE improvements

<div style="page-break-before: always;"></div>

### ped-gramm,0.40

| Field | Value |
|---|---|
| Dataset | ped-gramm |
| Status | DONE |
| Text | iGeladi digoida weiigi . |
| Portuguese | Minha casa é no rio. |
| A result | STRUCTURAL_DIFFERENCE |
| C result | EXACT_MATCH |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (NP
        (N$ iGeladi))
      (D digoida)
      (N weiigi))
    (PUNC .))
  (ID ped-gramm,0.40))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for ped-gramm,0.40](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.40.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (N$ iGeladi))
    (NP-PRD
      (D digoida)
      (N weiigi))
    (PUNC .))
  (ID ped-gramm,0.40))
```

#### AFTER — parser C — graphical tree

![AFTER tree for ped-gramm,0.40](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.40.after.svg)

<div style="page-break-before: always;"></div>

### ped-gramm,0.47

| Field | Value |
|---|---|
| Dataset | ped-gramm |
| Status | DONE |
| Text | liGeladi ipegitege niweiigi nigotaGa . |
| Portuguese | A casa dele/dela é perto da cidade da lagoa. |
| A result | STRUCTURAL_DIFFERENCE |
| C result | EXACT_MATCH |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ liGeladi))
    (VBAPL ipegitege)
    (NP-APL
      (N niweiigi)
      (N$ nigotaGa))
    (PUNC .))
  (ID ped-gramm,0.47))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for ped-gramm,0.47](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.47.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ liGeladi))
    (VBAPL ipegitege)
    (NP-APL
      (NP
        (N niweiigi))
      (N$ nigotaGa))
    (PUNC .))
  (ID ped-gramm,0.47))
```

#### AFTER — parser C — graphical tree

![AFTER tree for ped-gramm,0.47](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.47.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.1

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | iGeladi digoida weiigi |
| Portuguese | Minha casa é no rio |
| A result | STRUCTURAL_DIFFERENCE |
| C result | EXACT_MATCH |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (NP
        (N$ iGeladi))
      (D digoida)
      (N weiigi)))
  (ID van-data,0.1))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.1](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.1.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (N$ iGeladi))
    (NP-PRD
      (D digoida)
      (N weiigi)))
  (ID van-data,0.1))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.1](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.1.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.43

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | ijo niwigo libinienigi ijowa nigetedi |
| Portuguese | estes ovos da fotografia dela estão bonitos |
| A result | STRUCTURAL_DIFFERENCE |
| C result | EXACT_MATCH |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (NP
        (D ijo)
        (NP
          (N niwigo))
        (N$ libinienigi))
      (D ijowa))
    (NP-PRD
      (N$ nigetedi)))
  (ID van-data,0.43))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.43](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.43.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ijo)
      (NP
        (N niwigo))
      (N$ libinienigi))
    (NP-PRD
      (D ijowa)
      (N$ nigetedi)))
  (ID van-data,0.43))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.43](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.43.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.73

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | ligeladi ipegitege niweiigi nigotaGa |
| Portuguese | a casa dela é perto da cidade do rio |
| A result | STRUCTURAL_DIFFERENCE |
| C result | EXACT_MATCH |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ ligeladi))
    (VBAPL ipegitege)
    (NP-APL
      (N niweiigi)
      (N$ nigotaGa)))
  (ID van-data,0.73))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.73](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.73.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ ligeladi))
    (VBAPL ipegitege)
    (NP-APL
      (NP
        (N niweiigi))
      (N$ nigotaGa)))
  (ID van-data,0.73))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.73](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.73.after.svg)

# 3. DONE regressions

<div style="page-break-before: always;"></div>

### hil-data,0.11

| Field | Value |
|---|---|
| Dataset | hil-data |
| Status | DONE |
| Text | NaGajo lomigo niganigawanigi madi niwatece |
| Portuguese | Aquele anzol do menino é na canoa . |
| A result | EXACT_MATCH |
| C result | STRUCTURAL_DIFFERENCE |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D NaGajo)
      (N$ lomigo)
      (NP
        (N niganigawanigi)))
    (CP-me
      (C me@)
      (IP-SUB
        (NP
          (D @adi)
          (N$ niwatece)))))
  (ID hil-data,0.11))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for hil-data,0.11](kadiweu-parser-full-test-A-to-C-DONE-review.assets/hil-data-0.11.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (D NaGajo)
      (N$ lomigo)
      (NP
        (N niganigawanigi)))
    (CP
      (CP-me
        (C me@)
        (IP-SUB
          (NP
            (D @adi)
            (N$ niwatece))))))
  (ID hil-data,0.11))
```

#### AFTER — parser C — graphical tree

![AFTER tree for hil-data,0.11](kadiweu-parser-full-test-A-to-C-DONE-review.assets/hil-data-0.11.after.svg)

<div style="page-break-before: always;"></div>

### hil-data,0.7

| Field | Value |
|---|---|
| Dataset | hil-data |
| Status | DONE |
| Text | Gawenigi eliodi me libinienigi |
| Portuguese | A sua comida é muito bonita . |
| A result | EXACT_MATCH |
| C result | STRUCTURAL_DIFFERENCE |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (N$ Gawenigi))
    (CP-me
      (Q eliodi)
      (C me)
      (IP-SUB
        (NP
          (N$ libinienigi)))))
  (ID hil-data,0.7))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for hil-data,0.7](kadiweu-parser-full-test-A-to-C-DONE-review.assets/hil-data-0.7.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ Gawenigi))
    (CP
      (CP-me
        (Q eliodi)
        (C me)
        (IP-SUB
          (NP
            (N$ libinienigi))))))
  (ID hil-data,0.7))
```

#### AFTER — parser C — graphical tree

![AFTER tree for hil-data,0.7](kadiweu-parser-full-test-A-to-C-DONE-review.assets/hil-data-0.7.after.svg)

<div style="page-break-before: always;"></div>

### ped-gramm,0.35

| Field | Value |
|---|---|
| Dataset | ped-gramm |
| Status | DONE |
| Text | iGeladi ipegitegi naigi ane napioi |
| Portuguese | Minha casa está perto desta rua suja (que está suja) |
| A result | TRACE_EQUIVALENT |
| C result | STRUCTURAL_DIFFERENCE |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ iGeladi))
    (VBAPL ipegitegi)
    (NP-APL
      (N naigi)
      (CP-REL
        (WNP-1
          (WPRO ane))
        (IP-SUB
          (NP-TRACE *T*-1)
          (NP
            (N napioi))))))
  (ID ped-gramm,0.35))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for ped-gramm,0.35](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.35.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ iGeladi))
    (VBAPL ipegitegi)
    (NP-APL
      (N naigi))
    (NP
      (CP-FRL
        (WNP-1
          (WPRO ane))
        (IP-SUB
          (NP-TRACE *T*-1)
          (NP
            (N napioi))))))
  (ID ped-gramm,0.35))
```

#### AFTER — parser C — graphical tree

![AFTER tree for ped-gramm,0.35](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.35.after.svg)

<div style="page-break-before: always;"></div>

### ped-gramm,0.56

| Field | Value |
|---|---|
| Dataset | ped-gramm |
| Status | DONE |
| Text | IiGeladi midi akiidi |
| Portuguese | A casa dele/dela é no rio. |
| A result | EXACT_MATCH |
| C result | STRUCTURAL_DIFFERENCE |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (N$ IiGeladi))
    (CP-me
      (C me@)
      (IP-SUB
        (NP
          (D @idi)
          (N akiidi)))))
  (ID ped-gramm,0.56))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for ped-gramm,0.56](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.56.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ IiGeladi))
    (CP
      (CP-me
        (C me@)
        (IP-SUB
          (NP
            (D @idi)
            (N akiidi))))))
  (ID ped-gramm,0.56))
```

#### AFTER — parser C — graphical tree

![AFTER tree for ped-gramm,0.56](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.56.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.10

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | Gawenigi eliodi me libinienigi |
| Portuguese | a sua comida é muito bonita |
| A result | EXACT_MATCH |
| C result | STRUCTURAL_DIFFERENCE |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (N$ Gawenigi))
    (CP-me
      (Q eliodi)
      (C me)
      (IP-SUB
        (NP
          (N$ libinienigi)))))
  (ID van-data,0.10))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.10](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.10.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ Gawenigi))
    (CP
      (CP-me
        (Q eliodi)
        (C me)
        (IP-SUB
          (NP
            (N$ libinienigi))))))
  (ID van-data,0.10))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.10](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.10.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.14

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | naGajo lomiigo nigaanigawaanigi manitaGa niwatece |
| Portuguese | Aquele anzol do menino está na canoa. |
| A result | EXACT_MATCH |
| C result | STRUCTURAL_DIFFERENCE |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D naGajo)
      (N$ lomiigo)
      (NP
        (N nigaanigawaanigi)))
    (CP-me
      (C me@)
      (IP-SUB
        (NP
          (DAPL @anitaGa)
          (N niwatece)))))
  (ID van-data,0.14))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.14](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.14.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (D naGajo)
      (N$ lomiigo)
      (NP
        (N nigaanigawaanigi)))
    (CP
      (CP-me
        (C me@)
        (IP-SUB
          (NP
            (DAPL @anitaGa)
            (N niwatece))))))
  (ID van-data,0.14))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.14](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.14.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.18

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | Eyo manitaGa nigotaGa |
| Portuguese | Estou na cidade |
| A result | EXACT_MATCH |
| C result | STRUCTURAL_DIFFERENCE |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (PRO Eyo))
    (CP-me
      (C me@)
      (IP-SUB
        (NP
          (DAPL @anitaGa)
          (N nigotaGa)))))
  (ID van-data,0.18))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.18](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.18.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (PRO Eyo))
    (CP
      (CP-me
        (C me@)
        (IP-SUB
          (NP
            (DAPL @anitaGa)
            (N nigotaGa))))))
  (ID van-data,0.18))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.18](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.18.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.61

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | aGeewi mica iniKGigi |
| Portuguese | não sou muito feliz (não é verdade que eu sou feliz) |
| A result | EXACT_MATCH |
| C result | STRUCTURAL_DIFFERENCE |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NEG aG@)
    (NP
      (PRO @ee))
    (ADJ @ewi)
    (CP-me
      (C me@)
      (IP-SUB
        (NP
          (D @ica)
          (N$ iniKGigi)))))
  (ID van-data,0.61))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.61](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.61.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NEG aG@)
    (NP
      (PRO @ee))
    (ADJ @ewi)
    (CP
      (CP-me
        (C me@)
        (IP-SUB
          (NP
            (D @ica)
            (N$ iniKGigi))))))
  (ID van-data,0.61))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.61](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.61.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.62

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | aGeyo mica inikGigi |
| Portuguese | não sou muito feliz |
| A result | EXACT_MATCH |
| C result | STRUCTURAL_DIFFERENCE |

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NEG aG@)
    (NP-SBJ
      (PRO @eyo))
    (CP-me
      (C me@)
      (IP-SUB
        (NP
          (D @ica)
          (N$ inikGigi)))))
  (ID van-data,0.62))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.62](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.62.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NEG aG@)
    (NP
      (PRO @eyo))
    (CP
      (CP-me
        (C me@)
        (IP-SUB
          (NP
            (D @ica)
            (N$ inikGigi))))))
  (ID van-data,0.62))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.62](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.62.after.svg)

# 4. DONE persistent structural cases

In these cases, both parsers remain structurally different from the gold tree. The A and C outputs may nevertheless be identical to or different from one another.

<div style="page-break-before: always;"></div>

### hil-data,0.8

| Field | Value |
|---|---|
| Dataset | hil-data |
| Status | DONE |
| Text | NiGijo liwenigi libinienigi |
| Portuguese | Aquela comida dela é bonita . |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D NiGijo)
      (N$ liwenigi))
    (NP-PRD
      (N$ libinienigi)))
  (ID hil-data,0.8))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for hil-data,0.8](kadiweu-parser-full-test-A-to-C-DONE-review.assets/hil-data-0.8.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (D NiGijo)
      (N$ liwenigi)
      (NP
        (N$ libinienigi))))
  (ID hil-data,0.8))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for hil-data,0.8](kadiweu-parser-full-test-A-to-C-DONE-review.assets/hil-data-0.8.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (D NiGijo)
      (N$ liwenigi)
      (NP
        (N$ libinienigi))))
  (ID hil-data,0.8))
```

#### AFTER — parser C — graphical tree

![AFTER tree for hil-data,0.8](kadiweu-parser-full-test-A-to-C-DONE-review.assets/hil-data-0.8.after.svg)

<div style="page-break-before: always;"></div>

### ped-gramm,0.12

| Field | Value |
|---|---|
| Dataset | ped-gramm |
| Status | DONE |
| Text | ica looligi lidi |
| Portuguese | A comida está/é deliciosa (A gostosura da comida da Maria) |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ica)
      (N$ looligi))
    (NP-PRD
      (N$ lidi)))
  (ID ped-gramm,0.12))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for ped-gramm,0.12](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.12.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (D ica)
      (N$ looligi)
      (NP
        (N$ lidi))))
  (ID ped-gramm,0.12))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for ped-gramm,0.12](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.12.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (D ica)
      (N$ looligi)
      (NP
        (N$ lidi))))
  (ID ped-gramm,0.12))
```

#### AFTER — parser C — graphical tree

![AFTER tree for ped-gramm,0.12](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.12.after.svg)

<div style="page-break-before: always;"></div>

### ped-gramm,0.15

| Field | Value |
|---|---|
| Dataset | ped-gramm |
| Status | DONE |
| Text | ica looligi lideGegi |
| Portuguese | A comida é deliciosa (a gostosura da comida dela) |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ica)
      (N$ looligi))
    (NP-PRD
      (N$ lideGegi)))
  (ID ped-gramm,0.15))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for ped-gramm,0.15](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.15.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (D ica)
      (N$ looligi)
      (NP
        (N$ lideGegi))))
  (ID ped-gramm,0.15))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for ped-gramm,0.15](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.15.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (D ica)
      (N$ looligi)
      (NP
        (N$ lideGegi))))
  (ID ped-gramm,0.15))
```

#### AFTER — parser C — graphical tree

![AFTER tree for ped-gramm,0.15](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.15.after.svg)

<div style="page-break-before: always;"></div>

### ped-gramm,0.16

| Field | Value |
|---|---|
| Dataset | ped-gramm |
| Status | DONE |
| Text | loigipodi libinienigipi |
| Portuguese | A comunidade dele/dela é bonita |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (N$ loigipodi))
    (NP-PRD
      (N$ libinienigipi)))
  (ID ped-gramm,0.16))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for ped-gramm,0.16](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.16.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ loigipodi)
      (NP
        (N$ libinienigipi))))
  (ID ped-gramm,0.16))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for ped-gramm,0.16](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.16.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (N$ loigipodi)
      (NP
        (N$ libinienigipi))))
  (ID ped-gramm,0.16))
```

#### AFTER — parser C — graphical tree

![AFTER tree for ped-gramm,0.16](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.16.after.svg)

<div style="page-break-before: always;"></div>

### ped-gramm,0.19

| Field | Value |
|---|---|
| Dataset | ped-gramm |
| Status | DONE |
| Text | ica liwigo libinienigi |
| Portuguese | a fotografia dela/dele é/está bonita |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ica)
      (N$ liwigo))
    (NP-PRD
      (N$ libinienigi)))
  (ID ped-gramm,0.19))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for ped-gramm,0.19](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.19.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (D ica)
      (N$ liwigo)
      (NP
        (N$ libinienigi))))
  (ID ped-gramm,0.19))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for ped-gramm,0.19](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.19.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (D ica)
      (N$ liwigo)
      (NP
        (N$ libinienigi))))
  (ID ped-gramm,0.19))
```

#### AFTER — parser C — graphical tree

![AFTER tree for ped-gramm,0.19](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.19.after.svg)

<div style="page-break-before: always;"></div>

### ped-gramm,0.20

| Field | Value |
|---|---|
| Dataset | ped-gramm |
| Status | DONE |
| Text | ica niwigo libinienigi |
| Portuguese | a fotografia é/está bonita |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ica)
      (N niwigo))
    (NP-PRD
      (N$ libinienigi)))
  (ID ped-gramm,0.20))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for ped-gramm,0.20](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.20.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ica)
      (NP
        (N niwigo)))
    (NP-PRD
      (N$ libinienigi)))
  (ID ped-gramm,0.20))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for ped-gramm,0.20](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.20.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ica)
      (NP
        (N niwigo)))
    (NP-PRD
      (N$ libinienigi)))
  (ID ped-gramm,0.20))
```

#### AFTER — parser C — graphical tree

![AFTER tree for ped-gramm,0.20](kadiweu-parser-full-test-A-to-C-DONE-review.assets/ped-gramm-0.20.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.11

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | niGida liwenigi libinienigi |
| Portuguese | aquela comida dela é bonita |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D niGida)
      (N$ liwenigi))
    (NP-PRD
      (N$ libinienigi)))
  (ID van-data,0.11))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for van-data,0.11](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.11.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (D niGida)
      (N$ liwenigi)
      (NP
        (N$ libinienigi))))
  (ID van-data,0.11))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.11](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.11.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (D niGida)
      (N$ liwenigi)
      (NP
        (N$ libinienigi))))
  (ID van-data,0.11))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.11](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.11.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.30

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | niGijo lodaajo ajo lodowa aGica digoida liGeladi |
| Portuguese | esta faca da esposa dele não está na casa |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D niGijo)
      (N$ lodaajo)
      (NP
        (D ajo)
        (N$ lodowa)))
    (NEG aG@)
    (NP-PRD
      (Q @ica)
      (D digoida)
      (N$ liGeladi)))
  (ID van-data,0.30))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for van-data,0.30](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.30.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (NP
        (D niGijo)
        (N$ lodaajo))
      (D ajo)
      (N$ lodowa))
    (NEG aG@)
    (NP-PRD
      (Q @ica)
      (D digoida)
      (N$ liGeladi)))
  (ID van-data,0.30))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.30](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.30.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D niGijo)
      (N$ lodaajo))
    (NP-SBJ-PRD
      (D ajo)
      (N$ lodowa))
    (NEG aG@)
    (NP-PRD
      (Q @ica)
      (D digoida)
      (N$ liGeladi)))
  (ID van-data,0.30))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.30](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.30.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.32

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | naGani wetiGa liwaGatena |
| Portuguese | esta pedra está muito pesada |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D naGani)
      (N wetiGa))
    (NP-PRD
      (N$ liwaGatena)))
  (ID van-data,0.32))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for van-data,0.32](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.32.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D naGani)
      (NP
        (N wetiGa)))
    (NP-PRD
      (N$ liwaGatena)))
  (ID van-data,0.32))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.32](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.32.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D naGani)
      (NP
        (N wetiGa)))
    (NP-PRD
      (N$ liwaGatena)))
  (ID van-data,0.32))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.32](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.32.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.37

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | ani wetiGa me iwaGadi eniteloco iGonagi |
| Portuguese | esta pedra que é pesada caiu no meu pé |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP
      (D ani)
      (N wetiGa)
      (CP-me
        (C me)
        (IP-SUB
          (VB iwaGadi))))
    (VBAPL eniteloco)
    (NP-APL
      (N$ iGonagi)))
  (ID van-data,0.37))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for van-data,0.37](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.37.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP
      (D ani)
      (N wetiGa))
    (CP-me
      (C me)
      (IP-SUB
        (VB iwaGadi)))
    (VBAPL eniteloco)
    (NP-APL
      (N$ iGonagi)))
  (ID van-data,0.37))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.37](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.37.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP
      (D ani)
      (N wetiGa))
    (CP-me
      (C me)
      (IP-SUB
        (VB iwaGadi)))
    (VBAPL eniteloco)
    (NP-APL
      (N$ iGonagi)))
  (ID van-data,0.37))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.37](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.37.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.44

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | ijoa nigetedi niwigo libinienigipi |
| Portuguese | estes ovos da fotografia estão bonitos |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ijoa)
      (N nigetedi)
      (NP
        (N niwigo)))
    (NP-PRD
      (N$ libinienigipi)))
  (ID van-data,0.44))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for van-data,0.44](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.44.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ijoa)
      (N nigetedi))
    (NP-PRD
      (N niwigo)
      (N$ libinienigipi)))
  (ID van-data,0.44))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.44](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.44.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ijoa)
      (N nigetedi))
    (NP-PRD
      (NP
        (N niwigo))
      (N$ libinienigipi)))
  (ID van-data,0.44))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.44](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.44.after.svg)

<div style="page-break-before: always;"></div>

### van-data,0.72

| Field | Value |
|---|---|
| Dataset | van-data |
| Status | DONE |
| Text | ijowa leonigipi iwaalo idi metaGa |
| Portuguese | os filhos da mulher estão com ele |
| A result | STRUCTURAL_DIFFERENCE |
| C result | STRUCTURAL_DIFFERENCE |

#### REFERENCE — GOLD — LISP

```lisp
(
  (IP-MAT
    (NP
      (D ijowa)
      (N$ leonigipi)
      (NP
        (N iwaalo)))
    (CP
      (NP
        (D idi))
      (CAPL metaGa)))
  (ID van-data,0.72))
```

#### REFERENCE — GOLD — graphical tree

![REFERENCE tree for van-data,0.72](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.72.gold.svg)

#### BEFORE — parser A — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ijowa)
      (N$ leonigipi)
      (NP
        (N iwaalo)))
    (CP-me
      (IP-SUB
        (NP
          (D idi)))
      (CAPL metaGa)))
  (ID van-data,0.72))
```

#### BEFORE — parser A — graphical tree

![BEFORE tree for van-data,0.72](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.72.before.svg)

#### AFTER — parser C — LISP

```lisp
(
  (IP-MAT
    (NP-SBJ
      (D ijowa)
      (N$ leonigipi)
      (NP
        (N iwaalo)))
    (NP-PRD
      (D idi))
    (CP
      (CAPL metaGa)))
  (ID van-data,0.72))
```

#### AFTER — parser C — graphical tree

![AFTER tree for van-data,0.72](kadiweu-parser-full-test-A-to-C-DONE-review.assets/van-data-0.72.after.svg)
