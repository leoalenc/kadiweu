/*
Execution rule: 3
Original TBP rule: 3
Name: np-possessor-complement
*/

node: $ROOT

query: (IP-MAT iDoms [1]{1}NP)
    AND (IP-MAT iDoms [2]{2}NP)
    AND ([1]NP iDoms N$)
    AND ([2]NP iDoms N|N$)
    AND ([1]NP iPrecedes [2]NP)
    AND ([1]NP hasSister [2]NP)

extend_span{1, 2}:
