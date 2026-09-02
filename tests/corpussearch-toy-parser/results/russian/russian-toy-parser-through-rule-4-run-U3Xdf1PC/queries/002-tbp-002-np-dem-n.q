/*
Execution rule: 2
Original TBP rule: 2
Name: np-dem-n
*/

node: $ROOT

query: (IP-MAT iDoms [1]{1}DEM)
AND (IP-MAT iDoms [2]{2}N)
AND ([1]DEM iPrecedes [2]N)
AND ([1]DEM hasSister [2]N)

add_internal_node{1, 2}: NP
