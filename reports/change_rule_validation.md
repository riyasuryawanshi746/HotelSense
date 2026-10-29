# HotelSense - Validation of the clear-change rule (R1)

## Summary

**Out-of-sample coverage** of the horizon-average error (nominal 80%): 3-month horizon 77.8% (504 cells); 6-month horizon 90.1% (252 cells).

**Directional accuracy of 'supported' calls** (out-of-sample; the actual average moved the same way as the call): 3-month horizon 11 of 16 calls for the model the app uses, 39 of 68 calls across all four models; 6-month horizon 1 of 2 calls for the model the app uses, 8 of 16 calls across all four models. These are small numbers of calls, so the rates are very uncertain.

**Not tested:** 12-month horizon. There are not enough eligible historical forecast origins (each needs 6 earlier origins whose whole window had already ended), so the 12-month rule and its directional calls remain unvalidated out of sample.

### How to read the results
- The figures are **indicative only**: origins are 2 months apart, so h-month forecast windows overlap and test cells are correlated; the hotel series are correlated with each other (Qatar+ contains the others); and the number of eligible origins is small.
- The 'model the app uses' rows use the best model chosen on the full backtest, so they are mildly optimistic.
- A **supported change is a prompt to investigate**, not an automatic pricing recommendation.
- **No clear-change signal does not prove that performance will stay the same**; it only means the forecast change is not larger than past forecast errors of such averages (or is below the planning threshold).
- The planning thresholds (occupancy 2 pts, ADR 3%, RevPAR 3%) are **provisional business assumptions**, not statistically validated or optimised values.

## Method

Nominal level: 80%. 'old' = mean single-month calibrated half-width (previous rule); 'new' = 80% quantile of past horizon-average errors (current rule). All four models, all 21 series.

Out-of-sample rows are leak-free: the threshold for origin k uses only origins whose whole h-month window ended on or before k, and needs at least 6 such origins. That leaves no out-of-sample test for the 12-month horizon (origins run only from 2022-12, so too few complete 12-month windows exist).

## A. Coverage of the horizon-average error (%)

|                      |   cells |   coverage_new_% |   coverage_old_% |   median_new/old_width |
|:---------------------|--------:|-----------------:|-----------------:|-----------------------:|
| ('in-sample', 3)     |    1092 |             76.9 |             86.4 |                    0.8 |
| ('in-sample', 6)     |     924 |             81.8 |             88   |                    0.8 |
| ('in-sample', 12)    |     672 |             75   |             96.1 |                    0.6 |
| ('out-of-sample', 3) |     504 |             77.8 |             81.7 |                    0.9 |
| ('out-of-sample', 6) |     252 |             90.1 |             95.2 |                    0.8 |


### Out-of-sample coverage by metric (%)

|                  |   cov_new |   cov_old |
|:-----------------|----------:|----------:|
| ('adr', 3)       |      76.8 |      81.5 |
| ('adr', 6)       |      88.1 |      98.8 |
| ('occupancy', 3) |      80.4 |      85.7 |
| ('occupancy', 6) |      91.7 |      91.7 |
| ('revpar', 3)    |      76.2 |      78   |
| ('revpar', 6)    |      90.5 |      95.2 |


## B. Out-of-sample decisions (all models)

'..._calls' = the rule says increase/decrease; '..._correct_direction' = the actual average moved the same way; 'actual_material_change' = the actual change was at least the planning threshold. The 12-month horizon has no rows because it could not be tested out of sample.

|                  |   origins_tested |   old_rule_calls |   old_correct_direction |   new_rule_calls |   new_correct_direction |   actual_material_change |
|:-----------------|-----------------:|-----------------:|------------------------:|-----------------:|------------------------:|-------------------------:|
| ('adr', 3)       |              168 |               17 |                       6 |               16 |                       6 |                      124 |
| ('adr', 6)       |               84 |                2 |                       2 |                5 |                       3 |                       52 |
| ('occupancy', 3) |              168 |               20 |                      12 |               29 |                      18 |                      132 |
| ('occupancy', 6) |               84 |                1 |                       0 |                7 |                       5 |                       60 |
| ('revpar', 3)    |              168 |               21 |                      10 |               23 |                      15 |                      160 |
| ('revpar', 6)    |               84 |                0 |                       0 |                4 |                       0 |                       68 |


### Only the best model per series and horizon (what the app shows)

|                  |   origins_tested |   old_rule_calls |   old_correct_direction |   new_rule_calls |   new_correct_direction |   actual_material_change |
|:-----------------|-----------------:|-----------------:|------------------------:|-----------------:|------------------------:|-------------------------:|
| ('adr', 3)       |               42 |                2 |                       2 |                2 |                       2 |                       31 |
| ('adr', 6)       |               21 |                1 |                       1 |                1 |                       1 |                       13 |
| ('occupancy', 3) |               42 |                8 |                       5 |               10 |                       6 |                       33 |
| ('occupancy', 6) |               21 |                0 |                       0 |                1 |                       0 |                       15 |
| ('revpar', 3)    |               42 |                7 |                       3 |                4 |                       3 |                       40 |
| ('revpar', 6)    |               21 |                0 |                       0 |                0 |                       0 |                       17 |


Caveats: origins are 2 months apart, so h-month windows overlap and test cells are correlated; series are also correlated with each other (Qatar+ contains the others). Treat the figures as indicative.
