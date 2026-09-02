/*
Execution rule: 1
Original TBP rule: 1
Name: np-bare-noun
*/

node: $METAROOT

query: (IP-MAT iDoms {1}N|N$)

add_internal_node{1, 1}: NP
