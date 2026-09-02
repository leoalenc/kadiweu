/*
Execution rule: 3
Original TBP rule: 3
Name: NP
*/

node: $ROOT

query: (IP-MAT iDoms [1]{1}D)
AND (IP-MAT iDoms [2]{2}N-BAR2)

add_internal_node{1, 2}: NP
