node: IP*
copy_corpus: true

query:     (NP* iDoms [1]{1}N$)
       AND (NP* iDoms [2]{2}N$)
       AND ([1]N$ iPrecedes [2]N$)

add_internal_node{2, 2}: NP