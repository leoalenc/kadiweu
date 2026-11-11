# Parser C error classification

This table classifies the 14 `DONE` sentences in the parser C regression and persistent structural cases documented in the 25 September 2026, 10:55 parser transition report.

Here, **ambiguity** means that the parser produced a plausible alternative structure that does not match the reference analysis or intended interpretation. **Invalid tree** means that its output violates the adopted Kadiwéu annotation scheme. In particular, `NP-SBJ-PRD` is invalid: an NP cannot be both a subject and a predicate in this scheme. The labels *regression* and *persistent* refer to the comparison with parser A and the reference tree, respectively.

| Sentence ID | Group | Error type | Explanation |
|---|---|---|---|
| `hil-data,0.11` | Regression | Ambiguity (attachment) | Parser C places the `CP-me` inside the nominal phrase, allowing it to be read as modifying that phrase. The reference attaches it at clause level, corresponding to the intended analysis. |
| `ped-gramm,0.56` | Regression | Ambiguity (attachment) | Parser C embeds the `CP-me` within the phrase headed by `liGeladi`. This is a possible Kadiwéu structure, but it does not express the intended “His/her house is in the river” reading. |
| `van-data,0.14` | Regression | Ambiguity (attachment) | Parser C groups the `CP-me` with the subject pronoun `Eyo`, rather than attaching it at clause level as in the reference analysis. |
| `van-data,0.18` | Regression | Ambiguity (attachment) | Parser C groups the `CP-me` with the subject pronoun. This yields a different grouping from the reference and the intended “I am in the city” interpretation. |
| `van-data,0.62` | Regression | Ambiguity (attachment/scope) | Parser C places the `CP-me` inside the subject phrase under sentential negation. This differs from the intended analysis of “I am not very happy” and changes the relationship between negation and the clause. |
| `ped-gramm,0.20` | Persistent | Invalid tree (X-bar scheme) | Parser C inserts an inner `NP` around `niwigo` inside `NP-SBJ`. Under the adopted minimal X-bar scheme, `N` heads `NP-SBJ` directly. |
| `ped-gramm,0.26` | Persistent | Ambiguity (possessor vs. predicate) | Parser C analyzes `João` as the subject and the phrase headed by `liGeladi` as a predicate, rather than analyzing `João` as the possessor within one nominal phrase. This alternative would need to be evaluated as a distinct nominal-predication reading. |
| `ped-gramm,0.47` | Persistent | Ambiguity (constituent/valency) | Parser C splits the reference's applied-object phrase, placing `niweiigi` in `NP-APL` and `nigotaGa` in a separate `NP`. Because the parser lacks valency information, it cannot rule out the possibility that a `VBAPL` governs both an `NP-APL` and an `NP`; classify this as ambiguity rather than invalidity. |
| `van-data,0.30` | Persistent | Invalid tree (`NP-SBJ-PRD`) | Parser C assigns `NP-SBJ-PRD` to the phrase headed by `ajo lodowa`. This label is invalid in the adopted scheme because an NP cannot be both subject and predicative at the same time. |
| `van-data,0.32` | Persistent | Invalid tree (X-bar scheme) | As in `ped-gramm,0.20`, Parser C inserts an inner `NP` around the noun inside `NP-SBJ`, contrary to the adopted minimal X-bar scheme. |
| `van-data,0.37` | Persistent | Invalid tree (unsupported clause structure) | Parser C attaches `CP-me` at clause level immediately before `VBAPL`, alongside `NP-APL`. There is no evidence in the adopted analysis that a `VBAPL` can govern both an `NP-APL` and a `CP-me` in this configuration. |
| `van-data,0.44` | Persistent | Invalid tree (`NP-SBJ-PRD`) | Parser C assigns `NP-SBJ-PRD` to the phrase headed by `niwigo`. This label is invalid in the adopted scheme because an NP cannot be both subject and predicative at the same time. |
| `van-data,0.72` | Persistent | Invalid tree (constituent structure) | Parser C analyzes `idi` as `NP-PRD` while leaving `CAPL` `metaGa` as a bare daughter of `IP-MAT`. The reference groups these elements in a `CP`; the parser output does not preserve that constituent structure. |
| `van-data,0.73` | Persistent | Ambiguity (constituent/valency) | As in `ped-gramm,0.47`, Parser C splits the reference's applied-object phrase into `NP-APL` (`niweiigi`) and a separate `NP` (`nigotaGa`). Since the parser does not have valency information, a `VBAPL` governing both NPs cannot be excluded; classify this as ambiguity. |

## Summary

The two-category hypothesis covers these cases: **8 ambiguity cases** and **6 invalid trees**. The invalid cases include two X-bar scheme violations (`ped-gramm,0.20` and `van-data,0.32`), two uses of the prohibited `NP-SBJ-PRD` label (`van-data,0.30` and `van-data,0.44`), the unsupported `CP-me` configuration in `van-data,0.37`, and the constituent-structure error in `van-data,0.72`.
