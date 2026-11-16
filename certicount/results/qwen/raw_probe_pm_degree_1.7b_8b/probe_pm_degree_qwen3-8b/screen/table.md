# Screen

pairs screened 9924 / 9924, candidates (observed |Δ| > GS) 5525 — descriptive, no statistical claim

## Per degree bin (all screen trials)

| bin | trials | inputs | exec_error | abs_err_mean | json | number | failed | length_cut | tok_mean | tok_p95 | jitter_inputs |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-10 | 1112 | 548 | 0 | 0 | 1 | 0 | 0 | 0 | 97.2 | 120 | 0 |
| 11-30 | 2430 | 1198 | 0.0317 | 0.0317 | 1 | 0 | 0 | 0 | 150 | 208 | 0.00334 |
| 31-60 | 7462 | 3725 | 0.749 | 2.35 | 1 | 0 | 0 | 0 | 289 | 379 | 0.188 |
| 61-120 | 7154 | 3571 | 0.999 | 13.4 | 1 | 0 | 0 | 0 | 450 | 635 | 0.265 |
| >120 | 1954 | 970 | 0.999 | 56.1 | 1 | 0 | 0 | 0 | 582 | 1.22e+03 | 0.497 |

## Per kind × bin × family / tag

| kind | bin | family | pairs | candidates | cand_rate | delta_max | exec_error_x | exec_error_x2 | jitter | json | number | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| constructed | 1-10 | L | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 1-10 | tag:consecutive | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 1-10 | tag:digit_sim | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 1-10 | tag:len_boundary | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 1-10 | tag:middle | 3 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 1-10 | tag:near_self | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 1-10 | tag:tail | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 11-30 | L | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 11-30 | tag:digit_sim | 3 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 11-30 | tag:head | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 11-30 | tag:len_boundary | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 11-30 | tag:middle | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 11-30 | tag:tail | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| constructed | 31-60 | L | 4 | 0 | 0 | 0 | 0.5 | 1 | 0 | 1 | 0 | 0 |
| constructed | 31-60 | tag:consecutive | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |
| constructed | 31-60 | tag:digit_sim | 4 | 0 | 0 | 0 | 0.5 | 1 | 0 | 1 | 0 | 0 |
| constructed | 31-60 | tag:len_boundary | 4 | 0 | 0 | 0 | 0.5 | 1 | 0 | 1 | 0 | 0 |
| constructed | 31-60 | tag:middle | 4 | 0 | 0 | 0 | 0.5 | 1 | 0 | 1 | 0 | 0 |
| constructed | 61-120 | L | 4 | 2 | 0.5 | 406 | 1 | 0.75 | 0.5 | 1 | 0 | 0 |
| constructed | 61-120 | tag:digit_sim | 4 | 2 | 0.5 | 406 | 1 | 0.75 | 0.5 | 1 | 0 | 0 |
| constructed | 61-120 | tag:len_boundary | 4 | 2 | 0.5 | 406 | 1 | 0.75 | 0.5 | 1 | 0 | 0 |
| constructed | 61-120 | tag:middle | 4 | 2 | 0.5 | 406 | 1 | 0.75 | 0.5 | 1 | 0 | 0 |
| constructed | >120 | L | 4 | 2 | 0.5 | 324 | 1 | 0.75 | 0.25 | 1 | 0 | 0 |
| constructed | >120 | X | 48 | 16 | 0.333 | 352 | 1 | 1 | 0.271 | 1 | 0 | 0 |
| constructed | >120 | tag:consecutive | 37 | 9 | 0.243 | 352 | 1 | 1 | 0.189 | 1 | 0 | 0 |
| constructed | >120 | tag:digit_sim | 52 | 18 | 0.346 | 352 | 1 | 0.981 | 0.269 | 1 | 0 | 0 |
| constructed | >120 | tag:head | 7 | 3 | 0.429 | 20 | 1 | 1 | 0.143 | 1 | 0 | 0 |
| constructed | >120 | tag:len_boundary | 41 | 13 | 0.317 | 324 | 1 | 0.976 | 0.22 | 1 | 0 | 0 |
| constructed | >120 | tag:middle | 40 | 13 | 0.325 | 352 | 1 | 0.975 | 0.275 | 1 | 0 | 0 |
| constructed | >120 | tag:near_self | 4 | 3 | 0.75 | 20 | 1 | 1 | 0.5 | 1 | 0 | 0 |
| constructed | >120 | tag:tail | 5 | 2 | 0.4 | 28 | 1 | 1 | 0.4 | 1 | 0 | 0 |
| real | 1-10 | C | 61 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| real | 1-10 | P | 70 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| real | 1-10 | R | 168 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| real | 1-10 | S | 192 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| real | 1-10 | tag:consecutive | 83 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| real | 1-10 | tag:digit_sim | 290 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| real | 1-10 | tag:head | 77 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| real | 1-10 | tag:middle | 261 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| real | 1-10 | tag:near_self | 86 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| real | 1-10 | tag:tail | 153 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| real | 11-30 | C | 240 | 5 | 0.0208 | 2 | 0.0333 | 0.05 | 0.00833 | 1 | 0 | 0 |
| real | 11-30 | P | 180 | 2 | 0.0111 | 2 | 0.0333 | 0.0417 | 0.0167 | 1 | 0 | 0 |
| real | 11-30 | R | 329 | 8 | 0.0243 | 2 | 0.0334 | 0.0517 | 0.00608 | 1 | 0 | 0 |
| real | 11-30 | S | 480 | 12 | 0.025 | 2 | 0.0333 | 0.0521 | 0 | 1 | 0 | 0 |
| real | 11-30 | tag:consecutive | 378 | 10 | 0.0265 | 2 | 0.0317 | 0.0556 | 0.0106 | 1 | 0 | 0 |
| real | 11-30 | tag:digit_sim | 1005 | 27 | 0.0269 | 2 | 0.0328 | 0.0537 | 0.00597 | 1 | 0 | 0 |
| real | 11-30 | tag:head | 150 | 4 | 0.0267 | 2 | 0.02 | 0.0433 | 0.00667 | 1 | 0 | 0 |
| real | 11-30 | tag:len_boundary | 44 | 0 | 0 | 1 | 0 | 0.0114 | 0.0227 | 1 | 0 | 0 |
| real | 11-30 | tag:middle | 817 | 22 | 0.0269 | 2 | 0.0306 | 0.049 | 0.0049 | 1 | 0 | 0 |
| real | 11-30 | tag:near_self | 132 | 5 | 0.0379 | 2 | 0.00758 | 0.0455 | 0 | 1 | 0 | 0 |
| real | 11-30 | tag:tail | 262 | 1 | 0.00382 | 2 | 0.0496 | 0.0573 | 0.00763 | 1 | 0 | 0 |
| real | 31-60 | E | 3616 | 1577 | 0.436 | 31 | 0.75 | 0.752 | 0.342 | 1 | 0 | 0 |
| real | 31-60 | tag:consecutive | 604 | 263 | 0.435 | 31 | 0.786 | 0.741 | 0.407 | 1 | 0 | 0 |
| real | 31-60 | tag:digit_sim | 3065 | 1310 | 0.427 | 31 | 0.771 | 0.741 | 0.361 | 1 | 0 | 0 |
| real | 31-60 | tag:head | 234 | 146 | 0.624 | 21 | 0.782 | 0.684 | 0.346 | 1 | 0 | 0 |
| real | 31-60 | tag:len_boundary | 786 | 748 | 0.952 | 23 | 1 | 0.575 | 0.673 | 1 | 0 | 0 |
| real | 31-60 | tag:middle | 2819 | 1186 | 0.421 | 21 | 0.782 | 0.758 | 0.361 | 1 | 0 | 0 |
| real | 31-60 | tag:near_self | 254 | 100 | 0.394 | 21 | 0.799 | 0.734 | 0.339 | 1 | 0 | 0 |
| real | 31-60 | tag:tail | 563 | 245 | 0.435 | 31 | 0.575 | 0.75 | 0.243 | 1 | 0 | 0 |
| real | 61-120 | E | 3616 | 2997 | 0.829 | 47 | 1 | 0.993 | 0.812 | 1 | 0 | 0 |
| real | 61-120 | tag:consecutive | 1036 | 851 | 0.821 | 47 | 1 | 0.986 | 0.792 | 1 | 0 | 0 |
| real | 61-120 | tag:digit_sim | 3478 | 2878 | 0.827 | 47 | 1 | 0.993 | 0.811 | 1 | 0 | 0 |
| real | 61-120 | tag:head | 271 | 202 | 0.745 | 31 | 1 | 0.978 | 0.756 | 1 | 0 | 0 |
| real | 61-120 | tag:len_boundary | 343 | 27 | 0.0787 | 28 | 1 | 1 | 0.07 | 1 | 0 | 0 |
| real | 61-120 | tag:middle | 2758 | 2312 | 0.838 | 47 | 1 | 0.994 | 0.817 | 1 | 0 | 0 |
| real | 61-120 | tag:near_self | 214 | 171 | 0.799 | 47 | 1 | 0.979 | 0.799 | 1 | 0 | 0 |
| real | 61-120 | tag:tail | 587 | 483 | 0.823 | 47 | 1 | 0.992 | 0.811 | 1 | 0 | 0 |
| real | >120 | E | 904 | 904 | 1 | 329 | 1 | 1 | 1 | 1 | 0 | 0 |
| real | >120 | tag:consecutive | 536 | 536 | 1 | 329 | 1 | 1 | 1 | 1 | 0 | 0 |
| real | >120 | tag:digit_sim | 904 | 904 | 1 | 329 | 1 | 1 | 1 | 1 | 0 | 0 |
| real | >120 | tag:head | 92 | 92 | 1 | 329 | 1 | 1 | 1 | 1 | 0 | 0 |
| real | >120 | tag:middle | 716 | 716 | 1 | 329 | 1 | 1 | 1 | 1 | 0 | 0 |
| real | >120 | tag:near_self | 69 | 69 | 1 | 329 | 1 | 1 | 1 | 1 | 0 | 0 |
| real | >120 | tag:tail | 96 | 96 | 1 | 92 | 1 | 1 | 1 | 1 | 0 | 0 |

## Top 40 candidates

| pair_id | kind | bin | family | delta_max | frac_far |
|---|---|---|---|---|---|
| n14-d99-60495914b2a7|add76 | constructed | 61-120 | L | 406 | 0.667 |
| n14-d150-b1c54ece05d4|add400 | constructed | >120 | X | 352 | 0.833 |
| n14-d237-ef095c6ea966|remove113 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove121 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove134 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove149 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove15 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove179 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove182 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove186 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove249 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove282 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove333 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove347 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove348 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove355 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove359 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove365 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove399 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove78 | real | >120 | E | 329 | 1 |
| n14-d237-ef095c6ea966|remove187 | real | >120 | E | 329 | 0.833 |
| n14-d199-d19632b16837|add55 | constructed | >120 | L | 324 | 0.5 |
| n1-d199-06974fcf2036|add327 | constructed | >120 | L | 252 | 1 |
| n1-d450-12710aba289b|remove57 | constructed | >120 | X | 197 | 1 |
| n14-d237-ef095c6ea966|remove441 | real | >120 | E | 92 | 1 |
| n14-d237-ef095c6ea966|remove107 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove108 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove119 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove122 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove125 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove137 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove139 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove140 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove144 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove155 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove178 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove188 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove239 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove246 | real | >120 | E | 87 | 1 |
| n14-d237-ef095c6ea966|remove266 | real | >120 | E | 87 | 1 |
