# Tausug finite-state morphology examples

These XFST-compatible scripts illustrate two stages in the implementation of
Tausug realis infixation, following Beck (2017, pp. 332-333). They run in Foma
and `hfst-xfst`.

## Files

| File | Purpose |
| --- | --- |
| `tausug-infixation.xfst` | Isolates the rewrite rule that inserts `iy` immediately before the first vowel. It does not contain a lexicon or morphological tags. |
| `tausug-lexical-infixation.xfst` | Integrates the rule into a bidirectional lexical transducer with a finite root inventory and the analyses `LEMMA+V+INF` and `LEMMA+V+R`. |

The shorter script is useful for introducing the syntax and behavior of an
epenthesis rule. The lexical script is the complete model for the assignment:
it represents both infinitive and realis forms and supports surface analysis as
well as lexical generation.

Run either script with:

```bash
foma -f SCRIPT.xfst
hfst-xfst -F SCRIPT.xfst
```

## Reference

Beck, D. (2017). The typology of morphological processes: Form and function.
In A. Y. Aikhenvald & R. M. W. Dixon (Eds.), *The Cambridge handbook of
linguistic typology* (pp. 325-360). Cambridge University Press.
https://doi.org/10.1017/9781316135716.011

## Acknowledgement of generative AI use

These teaching materials were developed by Leonel Figueiredo de Alencar with
assistance from ChatGPT 5.6. The instructor supplied the linguistic analyses,
selected the data, designed the tasks, specified the expected behavior and
constraints, and made the final pedagogical and technical decisions. ChatGPT
assisted in drafting documentation and code examples, proposing alternative
implementations, and supporting debugging and verification. The instructor
tested, corrected, and revised the generated material in Foma and HFST before
including it in the course and takes full responsibility for the final content
and any remaining errors.
