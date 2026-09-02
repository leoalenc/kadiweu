/*
Execution rule: 1
Original TBP rule: 1
Name: np-d-n
*/

node: $ROOT

query: (IP-MAT iDoms [1]{1}D)
    AND (IP-MAT iDoms [2]{2}N|N$)
    AND ([1]D iPrecedes [2]N|N$)
    AND ([1]D hasSister [2]N|N$)

add_internal_node{1, 2}: NP
