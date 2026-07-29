begin_remark:
Relabel determiner-only preverbal NPs as NP-SBJ.

Intended structure:

(IP-MAT
    (NP (D ...))
    (VB ...)
    (NP ...))

The first NP must dominate exactly one word.
end_remark


begin_remark:
copy_corpus: true

end_remark


node: IP-MAT

query:
(IP-MAT iDominates {1}[1]NP)
AND (IP-MAT iDominates VB)
AND (IP-MAT iDominates [2]NP)
AND ([1]NP iPrecedes VB)
AND (VB iPrecedes [2]NP)
AND ([1]NP iDominates D)
AND ([1]NP domsWords 1)

replace_label{1}: NP-SBJ