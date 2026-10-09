# Finite-state morphology teaching materials

This directory contains finite-state morphology examples used in the
Computational Linguistics course at UNICAMP. The scripts are intended for
XFST-compatible environments, principally Foma and `hfst-xfst`.

## Contents

- **Kadiwéu demonstratives:** lexical transducers modeling gender, spatial
  and deictic distinctions, number, anaphoric forms, and optional
  gender-vowel copying.
- **Tausug verbs:** realis infixation, from an isolated rewrite rule to a
  complete lexical transducer. See
  [README-tausug.md](README-tausug.md).

## Documentation status

The Tausug examples are currently documented in detail. The Kadiwéu
demonstrative scripts contain in-code comments, but a consolidated inventory
of their purpose, inputs, outputs, and dependencies remains to be added.

### TODO

- Add a table describing each Kadiwéu demonstrative script.
- Document the simple, plural, and anaphoric paradigms.
- Record the expected analyses and generated forms.
- Identify which scripts are demonstrations, exercises, or complete models.
- Document relevant execution differences among XFST, Foma, and HFST.
