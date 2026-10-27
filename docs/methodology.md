# Methodology (Phase 3)

**Series.** Monthly, 2014-01 to 2025-03, one series per segment x metric (7 x 3).
Occupancy is capped at 100. For ADR and RevPAR the World Cup months (2022-11, 2022-12) are
replaced by linear interpolation in the *training* series only; scoring uses published values.

**Why a rolling origin.** One train/test split on ~27 post-shock months gives a single noisy score.
We instead refit at many cut-off months (first 2022-12, then every 2 months) and score every forecast
against what really happened. The first cut-off is 2022-12 so no test month lies before the COVID and
World Cup shocks. Training always starts at 2014-01 (full history) because only 12 months exist between
2022-01 and the first cut-off, fewer than the two seasonal cycles the models need.

**Leakage control.** Every model is fitted on data up to the origin only. SARIMA orders are chosen once per
series using data up to 2022-12 (last 12 of those months held out as validation), then refitted at each origin.

**Models.** Seasonal Naive (baseline), Holt-Winters (additive ETS, damped trend optional, chosen by AICc),
SARIMA (grid, validation RMSE), Combination (mean of Holt-Winters and SARIMA).

**Metrics.** MAE, RMSE, MAPE (valid: all series are strictly positive), 80% interval coverage, and
RMSE skill vs Seasonal Naive = 1 - RMSE / RMSE_snaive. Horizon-h scores pool steps 1..h from every origin
that has h months of future data; all models are scored on identical cells.

**Selection rule.** Lowest RMSE per segment, metric and horizon. The winner is called a real improvement
only if it beats the baseline by at least 5%; otherwise the app should say the forecast is no better than
"same as last year".

**Limitations.** Backtest origins overlap, so scores are not independent. The test window (2023-2025) is
short. COVID months remain in the training data. Combination intervals are an approximation.
