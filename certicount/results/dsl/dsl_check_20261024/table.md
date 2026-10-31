# DSL check

n = 49; falsifier on n = 5, dmax = 3; designer = mock (flawed first draft)

## Derived vs hand GS

| task | library | D=dmax | derived_gs | hand_gs | equal | facts_used |
|---|---|---|---|---|---|---|
| degree | True | 2 | 1.0000 | 1.0000 | True |  |
| degree | True | 5 | 1.0000 | 1.0000 | True |  |
| degree | True | 8 | 1.0000 | 1.0000 | True |  |
| degree | True | 16 | 1.0000 | 1.0000 | True |  |
| degree | True | 36 | 1.0000 | 1.0000 | True |  |
| 2-star | True | 2 | 1.0000 | 1.0000 | True |  |
| 2-star | True | 5 | 4.0000 | 4.0000 | True |  |
| 2-star | True | 8 | 7.0000 | 7.0000 | True |  |
| 2-star | True | 16 | 15.0000 | 15.0000 | True |  |
| 2-star | True | 36 | 35.0000 | 35.0000 | True |  |
| 3-star | True | 2 | 0.0000 | 0.0000 | True |  |
| 3-star | True | 5 | 6.0000 | 6.0000 | True |  |
| 3-star | True | 8 | 21.0000 | 21.0000 | True |  |
| 3-star | True | 16 | 105.0000 | 105.0000 | True |  |
| 3-star | True | 36 | 595.0000 | 595.0000 | True |  |
| triangle | True | 2 | 1.0000 | 1.0000 | True | rows_bounded,self_not_in_private,symmetric_rows |
| triangle | True | 5 | 4.0000 | 4.0000 | True | rows_bounded,self_not_in_private,symmetric_rows |
| triangle | True | 8 | 7.0000 | 7.0000 | True | rows_bounded,self_not_in_private,symmetric_rows |
| triangle | True | 16 | 15.0000 | 15.0000 | True | rows_bounded,self_not_in_private,symmetric_rows |
| triangle | True | 36 | 35.0000 | 35.0000 | True | rows_bounded,self_not_in_private,symmetric_rows |
| 4-star | False | 2 | 0.0000 | 0.0000 | True |  |
| 4-star | False | 5 | 4.0000 | 4.0000 | True |  |
| 4-star | False | 8 | 35.0000 | 35.0000 | True |  |
| 4-star | False | 16 | 455.0000 | 455.0000 | True |  |
| 4-star | False | 36 | 6545.0000 | 6545.0000 | True |  |
| 5-star | False | 2 | 0.0000 | 0.0000 | True |  |
| 5-star | False | 5 | 1.0000 | 1.0000 | True |  |
| 5-star | False | 8 | 35.0000 | 35.0000 | True |  |
| 5-star | False | 16 | 1365.0000 | 1365.0000 | True |  |
| 5-star | False | 36 | 5.236e+04 | 5.236e+04 | True |  |
| degree-moment2 | False | 2 | 3.0000 | 3.0000 | True |  |
| degree-moment2 | False | 5 | 9.0000 | 9.0000 | True |  |
| degree-moment2 | False | 8 | 15.0000 | 15.0000 | True |  |
| degree-moment2 | False | 16 | 31.0000 | 31.0000 | True |  |
| degree-moment2 | False | 36 | 71.0000 | 71.0000 | True |  |

## Public facts used by the triangle derivation

| task | facts | D=dmax | derived_gs |
|---|---|---|---|
| triangle | all facts | 2 | 1.0000 |
| triangle | all facts | 5 | 4.0000 |
| triangle | all facts | 8 | 7.0000 |
| triangle | all facts | 16 | 15.0000 |
| triangle | all facts | 36 | 35.0000 |
| triangle | no symmetry | 2 | 2.0000 |
| triangle | no symmetry | 5 | 5.0000 |
| triangle | no symmetry | 8 | 8.0000 |
| triangle | no symmetry | 16 | 16.0000 |
| triangle | no symmetry | 36 | 36.0000 |
| triangle | no self-not-in-P | 2 | 2.0000 |
| triangle | no self-not-in-P | 5 | 5.0000 |
| triangle | no self-not-in-P | 8 | 8.0000 |
| triangle | no self-not-in-P | 16 | 16.0000 |
| triangle | no self-not-in-P | 36 | 36.0000 |
| triangle | neither | 2 | 2.0000 |
| triangle | neither | 5 | 5.0000 |
| triangle | neither | 8 | 8.0000 |
| triangle | neither | 16 | 16.0000 |
| triangle | neither | 36 | 36.0000 |

## Falsifier (node 0, every P, every flip)

| task | graph | derived_gs | max_delta | refuted | tight | checked | seconds |
|---|---|---|---|---|---|---|---|
| degree | symmetric (exhaustive) | 1.0000 | 1.0000 | False | True | 64 | 0.0000 |
| 2-star | symmetric (exhaustive) | 2.0000 | 2.0000 | False | True | 64 | 0.0000 |
| 3-star | symmetric (exhaustive) | 1.0000 | 1.0000 | False | True | 64 | 0.0000 |
| triangle | symmetric (exhaustive) | 2.0000 | 2.0000 | False | True | 49152 | 0.1000 |
| triangle | asymmetric rows (sampled) | 2.0000 | 2.5000 | True | - | 128000 | - |
| 4-star | symmetric (exhaustive) | 0.0000 | 0.0000 | False | True | 64 | 0.0000 |
| 5-star | symmetric (exhaustive) | 0.0000 | 0.0000 | False | True | 64 | 0.0000 |
| degree-moment2 | symmetric (exhaustive) | 5.0000 | 5.0000 | False | True | 64 | 0.0000 |

## Utility test (no noise, no truncation, random public graphs)

| task | graphs | passed |
|---|---|---|
| degree | 30 | True |
| 2-star | 30 | True |
| 3-star | 30 | True |
| triangle | 30 | True |
| 4-star | 30 | True |
| 5-star | 30 | True |
| degree-moment2 | 30 | True |

## Design loop

| task | accepted | iterations | program | feedback |
|---|---|---|---|---|
| degree | True | 1 | return size(P) ; aggregate: total / n | accepted |
| 2-star | True | 2 | return comb(size(project(P, D)), 2) ; aggregate: total | sensitivity GS = 47 is too loose: comb(..., 2) of a count bounded only by n-1 = 48: the bo | accepted |
| 3-star | True | 2 | return comb(size(project(P, D)), 3) ; aggregate: total | sensitivity GS = 1081 is too loose: comb(..., 3) of a count bounded only by n-1 = 48: the  | accepted |
| triangle | True | 1 | S = P & N(self) ; return 0.5 * sum(size(P & N(j)) for j in S) ; aggregate: total / 3 | accepted |
| 4-star | True | 2 | return comb(size(project(P, D)), 4) ; aggregate: total | sensitivity GS = 16215 is too loose: comb(..., 4) of a count bounded only by n-1 = 48: the | accepted |
| 5-star | True | 2 | return comb(size(project(P, D)), 5) ; aggregate: total | sensitivity GS = 178365 is too loose: comb(..., 5) of a count bounded only by n-1 = 48: th | accepted |
| degree-moment2 | True | 1 | return pow(size(project(P, D)), 2) ; aggregate: total | accepted |
