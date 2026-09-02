/*
Execution rule: 1
Original TBP rule: 1
Name: np-dem-adj-n
*/

node: $ROOT

query: (IP-MAT iDoms [1]{1}DEM)
AND (IP-MAT iDoms [2]{2}ADJ)
AND (IP-MAT iDoms [3]{3}N)
AND ([1]DEM iPrecedes [2]ADJ)
AND ([2]ADJ iPrecedes [3]N)
AND ([1]DEM hasSister [2]ADJ)
AND ([2]ADJ hasSister [3]N)

add_internal_node{1, 3}: NP
