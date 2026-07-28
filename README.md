# Kadiwéu treebank conversion tools

This repository contains the data-processing and conversion pipeline and the
current development version of
[UD_Kadiweu-UNICAMP](https://github.com/UniversalDependencies/UD_Kadiweu-UNICAMP),
a Universal Dependencies (UD) treebank for Kadiwéu (`kbc`), an endangered
Waikurúan language spoken in Brazil.

The pipeline converts syntactically annotated Kadiwéu data from the
Tycho Brahe Platform into draft CoNLL-U annotations, which support the
development of the manually revised UD treebank. Manually revised UD annotations are fed back into converter development, while
problems detected in the source data may be corrected on the Tycho Brahe
Platform before new exports are generated.

The principal sources are the developing constituency treebanks
*Corpus Kadiwéu – gramática pedagógica* (Sandalo et al. 2024b) and
*Corpus Kadiwéu* (Sandalo et al. 2024a). The former contains mostly elicited sentences, whereas the latter
contains orally narrated myths. Their syntactic annotation extends the Penn
Treebank scheme to the analysis of Kadiwéu (Galves et al. 2017; Sandalo &
Galves 2023).

This work is part of the FAPESP project [Digitally annotated corpora of
Brazilian Indigenous languages with automatic translations
(DACILAT)](https://bv.fapesp.br/57063) (grant 22/09158-5). We gratefully
acknowledge the Kadiwéu speakers who contributed linguistic data, translations,
and acceptability judgments.

## Repository structure

- `src/` — conversion, inspection, evaluation, and reporting scripts.
- `data/` — Tycho Brahe exports, linguistic resources, generated reports,
  draft converter outputs, and the manually revised UD treebank.
- `tests/` — tests for the converter and linguistic mappings.
- `corpussearch/` — CorpusSearch queries and constituency-tree experiments.
- `releases/` — archived or prepared pipeline releases.

The current development version of the manually revised UD treebank is
`data/treebank/kbc_unicamp-ud-test.conllu`. Files named `draft-*.conllu` are
automatically generated or experimental converter outputs. Stable versions of
the treebank are periodically synchronized with the separate
[UD_Kadiweu-UNICAMP](https://github.com/UniversalDependencies/UD_Kadiweu-UNICAMP)
distribution repository.


## License

The software in this repository is distributed under the terms stated in
`LICENSE`. Source data and generated linguistic resources may be subject to
their own licences. Distributed versions of the UD treebank are licensed in the
[UD_Kadiweu-UNICAMP repository](https://github.com/UniversalDependencies/UD_Kadiweu-UNICAMP).

## References

- Galves, C., Sandalo, F., Sena, T. A. de, & Veronesi, L. (2017).
  Annotating a polysynthetic language: From Portuguese to Kadiwéu.
  *Cadernos de Estudos Linguísticos, 59*(3), 631–648.
  https://doi.org/10.20396/cel.v59i3.8651003
- Sandalo, F., & Galves, C. (2023). Anotando sintaticamente uma língua
  originária do Brasil: O problema de Anchieta. *Cadernos de Estudos
  Linguísticos, 65*, e023007. https://doi.org/10.20396/cel.v65i00.8673592
- Sandalo, F., Pires, V., Galves, C., Silva, H., Francisco, O., & Silva, S.
  (2024a). *Corpus Kadiwéu*. In L. Veronesi & C. Galves (Eds.), *The Tycho
  Brahe Platform*. https://www.tycho.iel.unicamp.br/
- Sandalo, F., Pires, V., Galves, C., Silva, H., Francisco, O., & Silva, S.
  (2024b). *Corpus Kadiwéu – gramática pedagógica*. In L. Veronesi &
  C. Galves (Eds.), *The Tycho Brahe Platform*.
  https://www.tycho.iel.unicamp.br/
