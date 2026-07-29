node: NP*

query:     ((NP* iDoms [1]N)
        AND (NP* iDoms [2]NPR)
        AND ([1]N hasSister [2]NPR))
       OR
           ((NP* iDoms [1]N$)
        AND (NP* iDoms [2]NPR)
        AND ([1]N$ hasSister [2]NPR))