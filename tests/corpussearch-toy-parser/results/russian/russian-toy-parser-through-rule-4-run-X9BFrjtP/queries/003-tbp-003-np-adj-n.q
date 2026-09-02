/*
Execution rule: 3
Original TBP rule: 3
Name: np-adj-n
*/

node: $ROOT

query: (IP-MAT iDoms [1]{1}ADJ)
AND (IP-MAT iDoms [2]{2}N)
AND ([1]ADJ iPrecedes [2]N)
AND ([1]ADJ hasSister [2]N)

add_internal_node{1, 2}: NP
