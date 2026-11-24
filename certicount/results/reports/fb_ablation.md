# Feedback ablation (CSCWD): does the checker's diagnosis help the curator?

CS9 settings (Qwen3-8B thinking curator, temperature 0.6, generic prompt core, per-node architecture, simulated choice, own-row check, ε = 2), tighten 0, 3 drafts per release (rows, matrix); the arms differ only in what a redraft's prompt shows: `full` = the rejected drafts with the checker's diagnosis, `binary` = the rejected drafts with the bare verdict, `none` = nothing (independent resampling, the same number of calls). The first draft's prompt is identical in all arms.

## 1. Comparisons (only the datasets both arms ran)

`released_diff_MH`: Mantel-Haenszel risk difference of the released share over the (task, dataset) strata, Wald 95% interval; `p_CMH`: continuity-corrected Cochran-Mantel-Haenszel test. `repair`: design loops whose first draft was rejected that were accepted at draft 2 or 3, difference with a 95% bootstrap interval (4000 replicates, designs resampled within each stratum). `calls_per_released_ratio`: model calls per released design, first arm over second. `full - none` is the primary comparison.

| comparison | tasks | datasets | released | released_diff_MH | odds_ratio_MH | p_CMH | repair | repair_diff | calls_per_released_ratio |
|---|---|---|---|---|---|---|---|---|---|
| full - none (primary) | triangle | CS,CU,Do,EE,ML,PM | 164/180 vs 153/180 | +0.061 [-0.005, +0.127] | 1.8200 | 0.1036 | 104/266 vs 89/274 | +0.066 [-0.004, +0.136] | 0.92 [0.83, 1.02] |
| full - none (primary) | triangle-edge | CS,CU,Do,EE,ML,PM | 79/180 vs 57/180 | +0.122 [+0.024, +0.221] | 1.6900 | 0.0229 | 73/342 vs 40/339 | +0.095 [+0.041, +0.152] | 0.72 [0.53, 0.95] |
| full - none (primary) | triangle+triangle-edge | CS,CU,Do,EE,ML,PM | 243/360 vs 210/360 | +0.092 [+0.032, +0.151] | 1.7300 | 0.0039 | 177/608 vs 129/613 | +0.081 [+0.037, +0.126] | 0.85 [0.76, 0.95] |
| full - binary | triangle | CU,EE,ML | 82/90 vs 62/90 | +0.222 [+0.113, +0.332] | 4.3900 | 0.0004233 | 58/134 vs 27/141 | +0.241 [+0.147, +0.333] | 0.70 [0.58, 0.84] |
| full - binary | triangle-edge | CU,EE,ML | 39/90 vs 26/90 | +0.144 [+0.006, +0.283] | 1.8800 | 0.0646 | 41/173 vs 15/167 | +0.147 [+0.066, +0.227] | 0.67 [0.42, 1.02] |
| full - binary | triangle+triangle-edge | CU,EE,ML | 121/180 vs 88/180 | +0.183 [+0.095, +0.272] | 2.6000 | 0.0001493 | 99/307 vs 42/308 | +0.186 [+0.122, +0.248] | 0.70 [0.58, 0.84] |
| binary - none | triangle | CU,EE,ML | 62/90 vs 76/90 | -0.156 [-0.275, -0.037] | 0.4200 | 0.0226 | 27/141 vs 45/136 | -0.139 [-0.228, -0.050] | 1.30 [1.07, 1.61] |
| binary - none | triangle-edge | CU,EE,ML | 26/90 vs 27/90 | -0.011 [-0.143, +0.120] | 0.9500 | 1.0000 | 15/167 vs 15/166 | -0.001 [-0.060, +0.060] | 1.05 [0.64, 1.76] |
| binary - none | triangle+triangle-edge | CU,EE,ML | 88/180 vs 103/180 | -0.083 [-0.172, +0.005] | 0.6500 | 0.0941 | 42/308 vs 60/302 | -0.062 [-0.114, -0.010] | 1.21 [1.00, 1.48] |

## 2. Yield and budget curve (all datasets of each arm)

| task | arm | datasets | designs | released | released_rate | released_ci95 | loop_at_1 | loop_at_2 | loop_at_3 | design_at_1 | design_at_2 | design_at_3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| triangle | full | CS,CU,Do,EE,ML,PM | 180 | 164 | 0.9111 | [0.86, 0.94] | 0.2611 | 0.4194 | 0.5500 | 0.5000 | 0.7444 | 0.9111 |
| triangle | binary | CU,EE,ML | 90 | 62 | 0.6889 | [0.59, 0.78] | 0.2167 | 0.3056 | 0.3667 | 0.4111 | 0.5778 | 0.6889 |
| triangle | none | CS,CU,Do,EE,ML,PM | 180 | 153 | 0.8500 | [0.79, 0.89] | 0.2389 | 0.4083 | 0.4861 | 0.4556 | 0.7500 | 0.8500 |
| triangle-edge | full | CS,CU,Do,EE,ML,PM | 180 | 79 | 0.4389 | [0.37, 0.51] | 0.0500 | 0.1528 | 0.2528 | 0.0944 | 0.2833 | 0.4444 |
| triangle-edge | binary | CU,EE,ML | 90 | 26 | 0.2889 | [0.21, 0.39] | 0.0722 | 0.1167 | 0.1556 | 0.1333 | 0.2222 | 0.2889 |
| triangle-edge | none | CS,CU,Do,EE,ML,PM | 180 | 57 | 0.3167 | [0.25, 0.39] | 0.0583 | 0.1194 | 0.1694 | 0.1167 | 0.2278 | 0.3167 |

## 3. First draft (randomisation check) and repair

The first draft sees the same prompt in every arm, so its acceptance rate should not differ between arms.

| task | arm | datasets | first_draft_accepted | rate | ci95 | repaired_after_rejected_first | repair_rate |
|---|---|---|---|---|---|---|---|
| triangle | full | CS,CU,Do,EE,ML,PM | 94/360 | 0.2611 | [0.22, 0.31] | 104/266 | 0.3910 |
| triangle | binary | CU,EE,ML | 39/180 | 0.2167 | [0.16, 0.28] | 27/141 | 0.1915 |
| triangle | none | CS,CU,Do,EE,ML,PM | 86/360 | 0.2389 | [0.20, 0.29] | 89/274 | 0.3248 |
| triangle-edge | full | CS,CU,Do,EE,ML,PM | 18/360 | 0.0500 | [0.03, 0.08] | 73/342 | 0.2135 |
| triangle-edge | binary | CU,EE,ML | 13/180 | 0.0722 | [0.04, 0.12] | 15/167 | 0.0898 |
| triangle-edge | none | CS,CU,Do,EE,ML,PM | 21/360 | 0.0583 | [0.04, 0.09] | 40/339 | 0.1180 |

## 4. What the next draft does after a rejection at a stage

`next_gets_past`: the next draft of the same loop stops at a later stage or is accepted (a duplicate does not count); `next_same_stage`: it is rejected at the same stage again.

| task | arm | rejected_at | next_drafts | next_gets_past | next_accepted | next_same_stage | next_duplicate |
|---|---|---|---|---|---|---|---|
| triangle | full | parse | 198 | 0.4697 | 0.0859 | 0.5303 | 0.0000 |
| triangle | full | own_row | 70 | 0.7286 | 0.1857 | 0.0000 | 0.0000 |
| triangle | full | gs_loose | 79 | 0.8608 | 0.3418 | 0.0633 | 0.0000 |
| triangle | full | semantic | 122 | 0.3852 | 0.3852 | 0.3197 | 0.1066 |
| triangle | binary | parse | 101 | 0.2079 | 0.0495 | 0.7921 | 0.0000 |
| triangle | binary | own_row | 44 | 0.1364 | 0.0455 | 0.6136 | 0.1591 |
| triangle | binary | gs_loose | 86 | 0.2674 | 0.1744 | 0.5814 | 0.0581 |
| triangle | binary | semantic | 30 | 0.1667 | 0.1667 | 0.3333 | 0.2000 |
| triangle | none | parse | 195 | 0.5692 | 0.1179 | 0.4308 | 0.0000 |
| triangle | none | own_row | 101 | 0.2772 | 0.0891 | 0.2970 | 0.0099 |
| triangle | none | gs_loose | 115 | 0.4435 | 0.3130 | 0.2435 | 0.0174 |
| triangle | none | semantic | 72 | 0.2500 | 0.2500 | 0.0417 | 0.0000 |
| triangle-edge | full | parse | 278 | 0.4317 | 0.0360 | 0.5647 | 0.0036 |
| triangle-edge | full | own_row | 105 | 0.8095 | 0.3048 | 0.0381 | 0.0190 |
| triangle-edge | full | gs_loose | 88 | 0.7500 | 0.1250 | 0.0568 | 0.0114 |
| triangle-edge | full | semantic | 173 | 0.1156 | 0.1156 | 0.5896 | 0.0867 |
| triangle-edge | binary | parse | 155 | 0.1548 | 0.0194 | 0.8387 | 0.0065 |
| triangle-edge | binary | own_row | 48 | 0.2083 | 0.0625 | 0.3542 | 0.3750 |
| triangle-edge | binary | gs_loose | 56 | 0.0893 | 0.0179 | 0.5357 | 0.1250 |
| triangle-edge | binary | semantic | 43 | 0.1628 | 0.1628 | 0.3721 | 0.2326 |
| triangle-edge | none | parse | 331 | 0.5227 | 0.0514 | 0.4713 | 0.0060 |
| triangle-edge | none | own_row | 117 | 0.2308 | 0.0598 | 0.2906 | 0.0171 |
| triangle-edge | none | gs_loose | 118 | 0.2288 | 0.0593 | 0.2119 | 0.0169 |
| triangle-edge | none | semantic | 83 | 0.0964 | 0.0964 | 0.1566 | 0.0120 |

## 5. Cost

| task | arm | datasets | calls_per_design | calls_per_released | out_tokens_per_design | out_tokens_per_released | tokens_missing | drafts | duplicate_share |
|---|---|---|---|---|---|---|---|---|---|
| triangle | full | CS,CU,Do,EE,ML,PM | 4.6389 | 5.0915 | 2.51e+04 | 2.754e+04 | 0 | 835 | 0.0180 |
| triangle | binary | CU,EE,ML | 4.9556 | 7.1935 | 2.668e+04 | 3.872e+04 | 0 | 446 | 0.0426 |
| triangle | none | CS,CU,Do,EE,ML,PM | 4.7056 | 5.5359 | 2.592e+04 | 3.05e+04 | 0 | 847 | 0.0035 |
| triangle-edge | full | CS,CU,Do,EE,ML,PM | 5.5944 | 12.7468 | 4.304e+04 | 9.807e+04 | 0 | 1007 | 0.0199 |
| triangle-edge | binary | CU,EE,ML | 5.6222 | 19.4615 | 4.359e+04 | 1.509e+05 | 0 | 506 | 0.0929 |
| triangle-edge | none | CS,CU,Do,EE,ML,PM | 5.6444 | 17.8246 | 4.727e+04 | 1.493e+05 | 0 | 1016 | 0.0069 |

## 6. Draft outcomes and released programs

| task | arm | draft_stages | distinct_programs | semantic_pass | sound | mean_RE | design_error_vs_GT_DSL |
|---|---|---|---|---|---|---|---|
| triangle | full | parse=262, accepted=198, semantic=186, gs_loose=92, own_row=78, duplicate=15, truncated=2, gs_failed=2 | 136 | 1.0000 | 1.0000 | 0.6340 | -0.0423 |
| triangle | binary | parse=149, gs_loose=106, accepted=66, own_row=60, semantic=46, duplicate=19 | 57 | 1.0000 | 1.0000 | 0.4521 | -0.0150 |
| triangle | none | parse=270, accepted=175, own_row=155, gs_loose=151, semantic=92, duplicate=3, gs_failed=1 | 120 | 1.0000 | 1.0000 | 0.6609 | -0.0323 |
| triangle-edge | full | parse=362, semantic=296, own_row=132, gs_loose=103, accepted=91, duplicate=20, truncated=3 | 50 | 1.0000 | 1.0000 | 0.4585 | 0.0017 |
| triangle-edge | binary | parse=224, gs_loose=80, own_row=63, semantic=61, duplicate=47, accepted=28, release=2, truncated=1 | 25 | 1.0000 | 1.0000 | 0.3903 | -0.0243 |
| triangle-edge | none | parse=470, gs_loose=176, own_row=169, semantic=126, accepted=61, duplicate=7, truncated=5, release=1 | 45 | 1.0000 | 1.0000 | 0.4548 | 0.0014 |

## 7. Per dataset

| task | arm | dataset | designs | released_rate | released_ci95 | loop_at_1 | loop_at_3 | calls_per_released | mean_RE |
|---|---|---|---|---|---|---|---|---|---|
| triangle | full | CS | 30 | 0.8000 | [0.63, 0.90] | 0.2000 | 0.4500 | 6.2083 | 1.5217 |
| triangle | full | CU | 30 | 0.9667 | [0.83, 0.99] | 0.2000 | 0.5833 | 4.8966 | 0.9835 |
| triangle | full | Do | 30 | 1.0000 | [0.89, 1.00] | 0.3500 | 0.5667 | 4.3333 | 0.7104 |
| triangle | full | EE | 30 | 0.8667 | [0.70, 0.95] | 0.3167 | 0.5667 | 5.1154 | 0.2348 |
| triangle | full | ML | 30 | 0.9000 | [0.74, 0.97] | 0.2500 | 0.5833 | 5.0741 | 0.2238 |
| triangle | full | PM | 30 | 0.9333 | [0.79, 0.98] | 0.2500 | 0.5500 | 5.1429 | 0.1953 |
| triangle | binary | CU | 30 | 0.5333 | [0.36, 0.70] | 0.1667 | 0.2667 | 9.8125 | 1.1088 |
| triangle | binary | EE | 30 | 0.7667 | [0.59, 0.88] | 0.2000 | 0.4167 | 6.4348 | 0.2186 |
| triangle | binary | ML | 30 | 0.7667 | [0.59, 0.88] | 0.2833 | 0.4167 | 6.1304 | 0.2289 |
| triangle | none | CS | 30 | 0.8333 | [0.66, 0.93] | 0.2167 | 0.4667 | 5.8000 | 1.5385 |
| triangle | none | CU | 30 | 0.9000 | [0.74, 0.97] | 0.2000 | 0.5333 | 5.2593 | 1.0144 |
| triangle | none | Do | 30 | 0.8667 | [0.70, 0.95] | 0.2333 | 0.4833 | 5.5000 | 0.7159 |
| triangle | none | EE | 30 | 0.8000 | [0.63, 0.90] | 0.2000 | 0.4833 | 6.0417 | 0.2312 |
| triangle | none | ML | 30 | 0.8333 | [0.66, 0.93] | 0.3333 | 0.4667 | 5.3200 | 0.2372 |
| triangle | none | PM | 30 | 0.8667 | [0.70, 0.95] | 0.2500 | 0.4833 | 5.3462 | 0.1991 |
| triangle-edge | full | CS | 30 | 0.4333 | [0.27, 0.61] | 0.0500 | 0.2167 | 13.0000 | 0.8722 |
| triangle-edge | full | CU | 30 | 0.4667 | [0.30, 0.64] | 0.0333 | 0.2500 | 12.1429 | 0.5240 |
| triangle-edge | full | Do | 30 | 0.4333 | [0.27, 0.61] | 0.0667 | 0.2167 | 12.7692 | 0.5082 |
| triangle-edge | full | EE | 30 | 0.4667 | [0.30, 0.64] | 0.0667 | 0.2833 | 11.7143 | 0.2964 |
| triangle-edge | full | ML | 30 | 0.3667 | [0.22, 0.54] | 0.0167 | 0.2667 | 15.8182 | 0.3104 |
| triangle-edge | full | PM | 30 | 0.4667 | [0.30, 0.64] | 0.0667 | 0.2833 | 11.7143 | 0.2409 |
| triangle-edge | binary | CU | 30 | 0.3000 | [0.17, 0.48] | 0.0667 | 0.1667 | 18.7778 | 0.5506 |
| triangle-edge | binary | EE | 30 | 0.2667 | [0.14, 0.44] | 0.0333 | 0.1333 | 21.6250 | 0.2870 |
| triangle-edge | binary | ML | 30 | 0.3000 | [0.17, 0.48] | 0.1167 | 0.1667 | 18.2222 | 0.3219 |
| triangle-edge | none | CS | 30 | 0.2333 | [0.12, 0.41] | 0.0000 | 0.1167 | 25.1429 | 0.8544 |
| triangle-edge | none | CU | 30 | 0.4000 | [0.25, 0.58] | 0.1167 | 0.2000 | 13.5833 | 0.5685 |
| triangle-edge | none | Do | 30 | 0.3667 | [0.22, 0.54] | 0.0500 | 0.2000 | 15.5455 | 0.5072 |
| triangle-edge | none | EE | 30 | 0.1667 | [0.07, 0.34] | 0.0500 | 0.0833 | 34.4000 | 0.2933 |
| triangle-edge | none | ML | 30 | 0.3333 | [0.19, 0.51] | 0.0667 | 0.2000 | 16.7000 | 0.3389 |
| triangle-edge | none | PM | 30 | 0.4000 | [0.25, 0.58] | 0.0667 | 0.2167 | 13.9167 | 0.2241 |

## 8. Runs

| tag | finished | designs | datasets | api_errors |
|---|---|---|---|---|
| fb_full_triangle | True | 90 | CU,EE,ML | 2 |
| fb_full_triangle_ext | True | 90 | CS,Do,PM | 24 |
| fb_binary_triangle | True | 90 | CU,EE,ML | 0 |
| fb_none_triangle | True | 90 | CU,EE,ML | 3 |
| fb_none_triangle_ext | True | 90 | CS,Do,PM | 15 |
| fb_full_triangle_edge | True | 90 | CU,EE,ML | 6 |
| fb_full_triangle_edge_ext | True | 90 | CS,Do,PM | 2 |
| fb_binary_triangle_edge | True | 90 | CU,EE,ML | 4 |
| fb_none_triangle_edge | True | 90 | CU,EE,ML | 7 |
| fb_none_triangle_edge_ext | True | 90 | CS,Do,PM | 2 |
