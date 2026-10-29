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

**Reporting scopes.** Every score is attached to one horizon (3, 6 or 12 months, pooling steps 1..h), so the
12-month score also contains the 1-3 month errors. Summaries across series are either *by horizon* (median or
share over the 7 segments or 21 series at that horizon) or *all horizons* (median or share over the 3-, 6- and
12-month results together). An all-horizons figure is not the score of any single horizon, and the app and
reports label the two separately ("6-month horizon" vs "All horizons").

**Selection rule.** Lowest RMSE per segment, metric and horizon. The winner is called a real improvement
only if it beats the baseline by at least 5%; otherwise the app should say the forecast is no better than
"same as last year".

**Clear-change rule (decision support R1).** Question: is the average over the forecast months materially
different from the same calendar months last year, for the same segment and metric? Last year's values are
published, so the uncertainty is that of the forecast *average*. We take it from the backtest: for each origin
with h months of future data, average its h errors; the 80th percentile of the absolute averages is the
uncertainty. Taking whole origins keeps the observed correlation between monthly errors (median 0.2-0.45 at the
3- and 6-month horizons), so we do not divide by sqrt(h); per metric and horizon the measured width was a
median 0.3-0.9x the single-month half-width, in every case above 1/sqrt(h). A change is "supported" only if it exceeds this uncertainty and a planning
threshold (2 pts occupancy, 3% ADR/RevPAR). These thresholds are provisional business assumptions, not
statistically validated or optimised values. The previous rule compared the
average change with the single-month half-width, which overstates the uncertainty of an average.
Out-of-sample check (leak-free, `reports/change_rule_validation.md`): coverage of the average error was 77.8%
at the 3-month horizon and 90.1% at the 6-month horizon (nominal 80%). Directional accuracy of "supported" calls,
for the model the app uses, was 11 of 16 calls (3-month) and 1 of 2 (6-month); across all four models 39 of 68
and 8 of 16. These counts are small and the results only indicative: forecast windows overlap, the hotel series
are correlated, and few origins are eligible. The 12-month rule, including its directional calls, is untested
out of sample because there are too few eligible origins. A supported change is therefore a prompt to
investigate, not an automatic pricing recommendation, and no clear-change signal does not prove that
performance will stay the same.

**Limitations.** Backtest origins overlap, so scores are not independent. The test window (2023-2025) is
short. COVID months remain in the training data. Combination intervals are an approximation.
