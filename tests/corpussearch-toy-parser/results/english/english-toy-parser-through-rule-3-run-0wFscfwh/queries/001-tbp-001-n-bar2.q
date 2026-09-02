/*
Execution rule: 1
Original TBP rule: 1
Name: n-bar2
*/

node: $ROOT

query: (IP-MAT iDoms [1]{1}Color)
AND (IP-MAT iDoms [2]{2}N)

add_internal_node{1, 2}: N-BAR1
