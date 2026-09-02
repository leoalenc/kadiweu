/*
Execution rule: 2
Original TBP rule: 2
Name: np-bare-noun
*/

node: $ROOT

query: (IP-MAT iDoms {1}N|N$)

add_internal_node{1, 1}: NP
