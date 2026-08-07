/*

More verbose query:

query:     ((NP* iDoms [1]N)
        AND (NP* iDoms [2]NPR)
        AND ([1]N hasSister [2]NPR))
       OR
           ((NP* iDoms [1]N$)
        AND (NP* iDoms [2]NPR)
        AND ([1]N$ hasSister [2]NPR))

*/

node: NP*

query: (NP* iDoms [1]N|N$)
   AND ([1]N|N$ hasSister {1}[2]NPR)

add_internal_node{1, 1}: NP