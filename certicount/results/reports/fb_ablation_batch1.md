# Feedback ablation (CSCWD): does the checker's diagnosis help the curator?

CS9 settings (Qwen3-8B thinking curator, temperature 0.6, generic prompt core, per-node architecture, simulated choice, own-row check, ε = 2), tighten 0, 3 drafts per release (rows, matrix); the arms differ only in what a redraft's prompt shows: `full` = the rejected drafts with the checker's diagnosis, `binary` = the rejected drafts with the bare verdict, `none` = nothing (independent resampling, the same number of calls). The first draft's prompt is identical in all arms.

## 1. Comparisons (only the datasets both arms ran)

`released_diff_MH`: Mantel-Haenszel risk difference of the released share over the (task, dataset) strata, Wald 95% interval; `p_CMH`: continuity-corrected Cochran-Mantel-Haenszel test. `repair`: design loops whose first draft was rejected that were accepted at draft 2 or 3, difference with a 95% bootstrap interval (4000 replicates, designs resampled within each stratum). `calls_per_released_ratio`: model calls per released design, first arm over second. `full - none` is the primary comparison.

| comparison | tasks | datasets | released | released_diff_MH | odds_ratio_MH | p_CMH | repair | repair_diff | calls_per_released_ratio |
|---|---|---|---|---|---|---|---|---|---|
| full - none (primary) | triangle | CU,EE,ML | 82/90 vs 76/90 | +0.067 [-0.028, +0.161] | 1.9100 | 0.2553 | 58/134 vs 45/136 | +0.102 [-0.002, +0.204] | 0.91 [0.78, 1.05] |
| full - none (primary) | triangle-edge | CU,EE,ML | 39/90 vs 27/90 | +0.133 [-0.004, +0.271] | 1.7800 | 0.0899 | 41/173 vs 15/166 | +0.147 [+0.066, +0.231] | 0.70 [0.45, 1.05] |
| full - none (primary) | triangle+triangle-edge | CU,EE,ML | 121/180 vs 103/180 | +0.100 [+0.017, +0.183] | 1.8200 | 0.0300 | 99/307 vs 60/302 | +0.124 [+0.055, +0.189] | 0.85 [0.73, 0.99] |
| full - binary | triangle | CU,EE,ML | 82/90 vs 62/90 | +0.222 [+0.113, +0.332] | 4.3900 | 0.0004233 | 58/134 vs 27/141 | +0.241 [+0.150, +0.331] | 0.70 [0.57, 0.84] |
| full - binary | triangle-edge | CU,EE,ML | 39/90 vs 26/90 | +0.144 [+0.006, +0.283] | 1.8800 | 0.0646 | 41/173 vs 15/167 | +0.147 [+0.069, +0.228] | 0.67 [0.42, 1.02] |
| full - binary | triangle+triangle-edge | CU,EE,ML | 121/180 vs 88/180 | +0.183 [+0.095, +0.272] | 2.6000 | 0.0001493 | 99/307 vs 42/308 | +0.186 [+0.124, +0.248] | 0.70 [0.58, 0.84] |
| binary - none | triangle | CU,EE,ML | 62/90 vs 76/90 | -0.156 [-0.275, -0.037] | 0.4200 | 0.0226 | 27/141 vs 45/136 | -0.139 [-0.225, -0.053] | 1.30 [1.07, 1.60] |
| binary - none | triangle-edge | CU,EE,ML | 26/90 vs 27/90 | -0.011 [-0.143, +0.120] | 0.9500 | 1.0000 | 15/167 vs 15/166 | -0.001 [-0.062, +0.060] | 1.05 [0.65, 1.74] |
| binary - none | triangle+triangle-edge | CU,EE,ML | 88/180 vs 103/180 | -0.083 [-0.172, +0.005] | 0.6500 | 0.0941 | 42/308 vs 60/302 | -0.062 [-0.115, -0.008] | 1.21 [0.99, 1.48] |

## 2. Yield and budget curve (all datasets of each arm)

| task | arm | datasets | designs | released | released_rate | released_ci95 | loop_at_1 | loop_at_2 | loop_at_3 | design_at_1 | design_at_2 | design_at_3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| triangle | full | CU,EE,ML | 90 | 82 | 0.9111 | [0.83, 0.95] | 0.2556 | 0.4556 | 0.5778 | 0.5000 | 0.7889 | 0.9111 |
| triangle | binary | CU,EE,ML | 90 | 62 | 0.6889 | [0.59, 0.78] | 0.2167 | 0.3056 | 0.3667 | 0.4111 | 0.5778 | 0.6889 |
| triangle | none | CU,EE,ML | 90 | 76 | 0.8444 | [0.76, 0.91] | 0.2444 | 0.4222 | 0.4944 | 0.4667 | 0.7667 | 0.8444 |
| triangle-edge | full | CU,EE,ML | 90 | 39 | 0.4333 | [0.34, 0.54] | 0.0389 | 0.1389 | 0.2667 | 0.0667 | 0.2444 | 0.4333 |
| triangle-edge | binary | CU,EE,ML | 90 | 26 | 0.2889 | [0.21, 0.39] | 0.0722 | 0.1167 | 0.1556 | 0.1333 | 0.2222 | 0.2889 |
| triangle-edge | none | CU,EE,ML | 90 | 27 | 0.3000 | [0.22, 0.40] | 0.0778 | 0.1333 | 0.1611 | 0.1556 | 0.2444 | 0.3000 |

## 3. First draft (randomisation check) and repair

The first draft sees the same prompt in every arm, so its acceptance rate should not differ between arms.

| task | arm | datasets | first_draft_accepted | rate | ci95 | repaired_after_rejected_first | repair_rate |
|---|---|---|---|---|---|---|---|
| triangle | full | CU,EE,ML | 46/180 | 0.2556 | [0.20, 0.32] | 58/134 | 0.4328 |
| triangle | binary | CU,EE,ML | 39/180 | 0.2167 | [0.16, 0.28] | 27/141 | 0.1915 |
| triangle | none | CU,EE,ML | 44/180 | 0.2444 | [0.19, 0.31] | 45/136 | 0.3309 |
| triangle-edge | full | CU,EE,ML | 7/180 | 0.0389 | [0.02, 0.08] | 41/173 | 0.2370 |
| triangle-edge | binary | CU,EE,ML | 13/180 | 0.0722 | [0.04, 0.12] | 15/167 | 0.0898 |
| triangle-edge | none | CU,EE,ML | 14/180 | 0.0778 | [0.05, 0.13] | 15/166 | 0.0904 |

## 4. What the next draft does after a rejection at a stage

`next_gets_past`: the next draft of the same loop stops at a later stage or is accepted (a duplicate does not count); `next_same_stage`: it is rejected at the same stage again.

| task | arm | rejected_at | next_drafts | next_gets_past | next_accepted | next_same_stage | next_duplicate |
|---|---|---|---|---|---|---|---|
| triangle | full | parse | 103 | 0.4078 | 0.1068 | 0.5922 | 0.0000 |
| triangle | full | own_row | 34 | 0.7353 | 0.1471 | 0.0000 | 0.0000 |
| triangle | full | gs_loose | 41 | 0.8537 | 0.4390 | 0.0488 | 0.0000 |
| triangle | full | semantic | 52 | 0.4615 | 0.4615 | 0.2692 | 0.0769 |
| triangle | binary | parse | 101 | 0.2079 | 0.0495 | 0.7921 | 0.0000 |
| triangle | binary | own_row | 44 | 0.1364 | 0.0455 | 0.6136 | 0.1591 |
| triangle | binary | gs_loose | 86 | 0.2674 | 0.1744 | 0.5814 | 0.0581 |
| triangle | binary | semantic | 30 | 0.1667 | 0.1667 | 0.3333 | 0.2000 |
| triangle | none | parse | 90 | 0.5889 | 0.1000 | 0.4111 | 0.0000 |
| triangle | none | own_row | 57 | 0.2632 | 0.0877 | 0.2456 | 0.0175 |
| triangle | none | gs_loose | 60 | 0.4833 | 0.3667 | 0.2667 | 0.0000 |
| triangle | none | semantic | 32 | 0.2812 | 0.2812 | 0.0000 | 0.0000 |
| triangle-edge | full | parse | 152 | 0.4276 | 0.0395 | 0.5724 | 0.0000 |
| triangle-edge | full | own_row | 61 | 0.7869 | 0.2951 | 0.0492 | 0.0328 |
| triangle-edge | full | gs_loose | 40 | 0.7500 | 0.1500 | 0.0500 | 0.0000 |
| triangle-edge | full | semantic | 75 | 0.1467 | 0.1467 | 0.5600 | 0.0800 |
| triangle-edge | binary | parse | 155 | 0.1548 | 0.0194 | 0.8387 | 0.0065 |
| triangle-edge | binary | own_row | 48 | 0.2083 | 0.0625 | 0.3542 | 0.3750 |
| triangle-edge | binary | gs_loose | 56 | 0.0893 | 0.0179 | 0.5357 | 0.1250 |
| triangle-edge | binary | semantic | 43 | 0.1628 | 0.1628 | 0.3721 | 0.2326 |
| triangle-edge | none | parse | 160 | 0.4688 | 0.0500 | 0.5188 | 0.0125 |
| triangle-edge | none | own_row | 53 | 0.2264 | 0.0566 | 0.2642 | 0.0377 |
| triangle-edge | none | gs_loose | 62 | 0.2419 | 0.0161 | 0.2097 | 0.0000 |
| triangle-edge | none | semantic | 45 | 0.0444 | 0.0444 | 0.1778 | 0.0000 |

## 5. Cost

| task | arm | datasets | calls_per_design | calls_per_released | out_tokens_per_design | out_tokens_per_released | tokens_missing | drafts | duplicate_share |
|---|---|---|---|---|---|---|---|---|---|
| triangle | full | CU,EE,ML | 4.5778 | 5.0244 | 2.409e+04 | 2.644e+04 | 0 | 412 | 0.0146 |
| triangle | binary | CU,EE,ML | 4.9556 | 7.1935 | 2.668e+04 | 3.872e+04 | 0 | 446 | 0.0426 |
| triangle | none | CU,EE,ML | 4.6667 | 5.5263 | 2.577e+04 | 3.052e+04 | 0 | 420 | 0.0024 |
| triangle-edge | full | CU,EE,ML | 5.6444 | 13.0256 | 4.261e+04 | 9.833e+04 | 0 | 508 | 0.0157 |
| triangle-edge | binary | CU,EE,ML | 5.6222 | 19.4615 | 4.359e+04 | 1.509e+05 | 0 | 506 | 0.0929 |
| triangle-edge | none | CU,EE,ML | 5.5778 | 18.5926 | 4.67e+04 | 1.557e+05 | 0 | 502 | 0.0080 |

## 6. Draft outcomes and released programs

| task | arm | draft_stages | distinct_programs | semantic_pass | sound | mean_RE | design_error_vs_GT_DSL |
|---|---|---|---|---|---|---|---|
| triangle | full | parse=140, accepted=104, semantic=77, gs_loose=47, own_row=38, duplicate=6 | 75 | 1.0000 | 1.0000 | 0.4960 | -0.0539 |
| triangle | binary | parse=149, gs_loose=106, accepted=66, own_row=60, semantic=46, duplicate=19 | 57 | 1.0000 | 1.0000 | 0.4521 | -0.0150 |
| triangle | none | parse=128, accepted=89, own_row=81, gs_loose=77, semantic=44, duplicate=1 | 69 | 1.0000 | 1.0000 | 0.5114 | -0.0398 |
| triangle-edge | full | parse=197, semantic=130, own_row=74, gs_loose=50, accepted=48, duplicate=8, truncated=1 | 26 | 1.0000 | 1.0000 | 0.3821 | -0.0317 |
| triangle-edge | binary | parse=224, gs_loose=80, own_row=63, semantic=61, duplicate=47, accepted=28, release=2, truncated=1 | 25 | 1.0000 | 1.0000 | 0.3903 | -0.0243 |
| triangle-edge | none | parse=235, gs_loose=92, own_row=76, semantic=63, accepted=29, duplicate=4, truncated=2, release=1 | 24 | 1.0000 | 1.0000 | 0.4325 | -0.0133 |

## 7. Per dataset

| task | arm | dataset | designs | released_rate | released_ci95 | loop_at_1 | loop_at_3 | calls_per_released | mean_RE |
|---|---|---|---|---|---|---|---|---|---|
| triangle | full | CU | 30 | 0.9667 | [0.83, 0.99] | 0.2000 | 0.5833 | 4.8966 | 0.9835 |
| triangle | full | EE | 30 | 0.8667 | [0.70, 0.95] | 0.3167 | 0.5667 | 5.1154 | 0.2348 |
| triangle | full | ML | 30 | 0.9000 | [0.74, 0.97] | 0.2500 | 0.5833 | 5.0741 | 0.2238 |
| triangle | binary | CU | 30 | 0.5333 | [0.36, 0.70] | 0.1667 | 0.2667 | 9.8125 | 1.1088 |
| triangle | binary | EE | 30 | 0.7667 | [0.59, 0.88] | 0.2000 | 0.4167 | 6.4348 | 0.2186 |
| triangle | binary | ML | 30 | 0.7667 | [0.59, 0.88] | 0.2833 | 0.4167 | 6.1304 | 0.2289 |
| triangle | none | CU | 30 | 0.9000 | [0.74, 0.97] | 0.2000 | 0.5333 | 5.2593 | 1.0144 |
| triangle | none | EE | 30 | 0.8000 | [0.63, 0.90] | 0.2000 | 0.4833 | 6.0417 | 0.2312 |
| triangle | none | ML | 30 | 0.8333 | [0.66, 0.93] | 0.3333 | 0.4667 | 5.3200 | 0.2372 |
| triangle-edge | full | CU | 30 | 0.4667 | [0.30, 0.64] | 0.0333 | 0.2500 | 12.1429 | 0.5240 |
| triangle-edge | full | EE | 30 | 0.4667 | [0.30, 0.64] | 0.0667 | 0.2833 | 11.7143 | 0.2964 |
| triangle-edge | full | ML | 30 | 0.3667 | [0.22, 0.54] | 0.0167 | 0.2667 | 15.8182 | 0.3104 |
| triangle-edge | binary | CU | 30 | 0.3000 | [0.17, 0.48] | 0.0667 | 0.1667 | 18.7778 | 0.5506 |
| triangle-edge | binary | EE | 30 | 0.2667 | [0.14, 0.44] | 0.0333 | 0.1333 | 21.6250 | 0.2870 |
| triangle-edge | binary | ML | 30 | 0.3000 | [0.17, 0.48] | 0.1167 | 0.1667 | 18.2222 | 0.3219 |
| triangle-edge | none | CU | 30 | 0.4000 | [0.25, 0.58] | 0.1167 | 0.2000 | 13.5833 | 0.5685 |
| triangle-edge | none | EE | 30 | 0.1667 | [0.07, 0.34] | 0.0500 | 0.0833 | 34.4000 | 0.2933 |
| triangle-edge | none | ML | 30 | 0.3333 | [0.19, 0.51] | 0.0667 | 0.2000 | 16.7000 | 0.3389 |

## 8. Runs

| tag | finished | designs | datasets | api_errors |
|---|---|---|---|---|
| fb_full_triangle | True | 90 | CU,EE,ML | 2 |
| fb_binary_triangle | True | 90 | CU,EE,ML | 0 |
| fb_none_triangle | True | 90 | CU,EE,ML | 3 |
| fb_full_triangle_edge | True | 90 | CU,EE,ML | 6 |
| fb_binary_triangle_edge | True | 90 | CU,EE,ML | 4 |
| fb_none_triangle_edge | True | 90 | CU,EE,ML | 7 |
