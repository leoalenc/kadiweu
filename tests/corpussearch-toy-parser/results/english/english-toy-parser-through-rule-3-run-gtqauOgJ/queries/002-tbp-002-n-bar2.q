/*
Execution rule: 2
Original TBP rule: 2
Name: n-bar2
*/

node: $ROOT

query: (IP-MAT iDoms [1]{1}Adj)
AND (IP-MAT iDoms [2]{2}N-BAR1)

add_internal_node{1, 2}: N-BAR2
