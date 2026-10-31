# Cost

## Measured (transcripts)

| source | runs | task | method | role | phase | calls | input_tokens | output_tokens | output_share | elapsed | usage_missing |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt41mini-node_gpt41-curator_exp1_CU_3-star_r10_PSC | 10 | 3-star | PSC | curator | aggregate | 10 | 6230 | 13610 | 0.2059 | 90.8100 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_3-star_r10_PSC | 10 | 3-star | PSC | curator | design | 10 | 4350 | 2144 | 0.0324 | 36.8300 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_3-star_r10_PSC | 10 | 3-star | PSC | node | update | 490 | 145090 | 50198 | 0.7595 | 1259.0900 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_3-star_r10_PSC | 10 | 3-star | PSC | privacycontroller | select | 10 | 4000 | 140 | 0.0021 | 40.5400 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_degree_r10_PSC | 10 | degree | PSC | curator | aggregate | 10 | 5770 | 8891 | 0.2243 | 59.2600 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_degree_r10_PSC | 10 | degree | PSC | curator | design | 10 | 3770 | 1164 | 0.0294 | 14.3500 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_degree_r10_PSC | 10 | degree | PSC | node | update | 490 | 112260 | 29450 | 0.7430 | 742.8600 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_degree_r10_PSC | 10 | degree | PSC | privacycontroller | select | 10 | 3420 | 130 | 0.0033 | 19.8000 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC | 10 | triangle | PSC | curator | aggregate | 10 | 5720 | 13838 | 0.0308 | 124.3700 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC | 10 | triangle | PSC | curator | design | 10 | 3760 | 1339 | 0.0030 | 33.1600 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC | 10 | triangle | PSC | node | send | 490 | 150802 | 104892 | 0.2333 | 1491.1500 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC | 10 | triangle | PSC | node | update | 490 | 676298 | 329497 | 0.7327 | 3106.0500 | 0 |
| gpt41mini-node_gpt41-curator_exp1_CU_triangle_r10_PSC | 10 | triangle | PSC | privacycontroller | select | 10 | 3410 | 130 | 0.0002891 | 34.5800 | 0 |

## LLM calls per run by execution mode

| dataset | n | task | mode | select | design | send | update | aggregate | total | node |
|---|---|---|---|---|---|---|---|---|---|---|
| CU | 49 | degree | baseline / bind / guard | 1 | 1 | 0 | 49 | 1 | 52 | 49 |
| CU | 49 | degree | code send + code aggregate | 1 | 1 | 0 | 49 | 0 | 51 | 49 |
| CU | 49 | degree | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| CU | 49 | degree | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CU | 49 | 3-star | baseline / bind / guard | 1 | 1 | 0 | 49 | 1 | 52 | 49 |
| CU | 49 | 3-star | code send + code aggregate | 1 | 1 | 0 | 49 | 0 | 51 | 49 |
| CU | 49 | 3-star | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| CU | 49 | 3-star | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CU | 49 | triangle | baseline / bind / guard | 1 | 1 | 49 | 49 | 1 | 101 | 98 |
| CU | 49 | triangle | code send + code aggregate | 1 | 1 | 0 | 49 | 0 | 51 | 49 |
| CU | 49 | triangle | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| CU | 49 | triangle | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Do | 62 | degree | baseline / bind / guard | 1 | 1 | 0 | 62 | 1 | 65 | 62 |
| Do | 62 | degree | code send + code aggregate | 1 | 1 | 0 | 62 | 0 | 64 | 62 |
| Do | 62 | degree | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| Do | 62 | degree | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Do | 62 | 3-star | baseline / bind / guard | 1 | 1 | 0 | 62 | 1 | 65 | 62 |
| Do | 62 | 3-star | code send + code aggregate | 1 | 1 | 0 | 62 | 0 | 64 | 62 |
| Do | 62 | 3-star | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| Do | 62 | 3-star | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Do | 62 | triangle | baseline / bind / guard | 1 | 1 | 62 | 62 | 1 | 127 | 124 |
| Do | 62 | triangle | code send + code aggregate | 1 | 1 | 0 | 62 | 0 | 64 | 62 |
| Do | 62 | triangle | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| Do | 62 | triangle | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ML | 77 | degree | baseline / bind / guard | 1 | 1 | 0 | 77 | 1 | 80 | 77 |
| ML | 77 | degree | code send + code aggregate | 1 | 1 | 0 | 77 | 0 | 79 | 77 |
| ML | 77 | degree | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| ML | 77 | degree | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ML | 77 | 3-star | baseline / bind / guard | 1 | 1 | 0 | 77 | 1 | 80 | 77 |
| ML | 77 | 3-star | code send + code aggregate | 1 | 1 | 0 | 77 | 0 | 79 | 77 |
| ML | 77 | 3-star | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| ML | 77 | 3-star | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ML | 77 | triangle | baseline / bind / guard | 1 | 1 | 77 | 77 | 1 | 157 | 154 |
| ML | 77 | triangle | code send + code aggregate | 1 | 1 | 0 | 77 | 0 | 79 | 77 |
| ML | 77 | triangle | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| ML | 77 | triangle | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CS | 86 | degree | baseline / bind / guard | 1 | 1 | 0 | 86 | 1 | 89 | 86 |
| CS | 86 | degree | code send + code aggregate | 1 | 1 | 0 | 86 | 0 | 88 | 86 |
| CS | 86 | degree | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| CS | 86 | degree | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CS | 86 | 3-star | baseline / bind / guard | 1 | 1 | 0 | 86 | 1 | 89 | 86 |
| CS | 86 | 3-star | code send + code aggregate | 1 | 1 | 0 | 86 | 0 | 88 | 86 |
| CS | 86 | 3-star | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| CS | 86 | 3-star | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CS | 86 | triangle | baseline / bind / guard | 1 | 1 | 86 | 86 | 1 | 175 | 172 |
| CS | 86 | triangle | code send + code aggregate | 1 | 1 | 0 | 86 | 0 | 88 | 86 |
| CS | 86 | triangle | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| CS | 86 | triangle | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EE | 143 | degree | baseline / bind / guard | 1 | 1 | 0 | 143 | 1 | 146 | 143 |
| EE | 143 | degree | code send + code aggregate | 1 | 1 | 0 | 143 | 0 | 145 | 143 |
| EE | 143 | degree | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| EE | 143 | degree | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EE | 143 | 3-star | baseline / bind / guard | 1 | 1 | 0 | 143 | 1 | 146 | 143 |
| EE | 143 | 3-star | code send + code aggregate | 1 | 1 | 0 | 143 | 0 | 145 | 143 |
| EE | 143 | 3-star | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| EE | 143 | 3-star | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EE | 143 | triangle | baseline / bind / guard | 1 | 1 | 143 | 143 | 1 | 289 | 286 |
| EE | 143 | triangle | code send + code aggregate | 1 | 1 | 0 | 143 | 0 | 145 | 143 |
| EE | 143 | triangle | program (first run) | 0 | 1 | 0 | 0 | 0 | 1 | 0 |
| EE | 143 | triangle | program (design cached) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Forbidden optimisations (side channels or unaccounted interaction): batch several nodes into one prompt; choose the model / route a node by private information (degree, neighbour list)
