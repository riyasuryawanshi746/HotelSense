# HotelSense - Model Comparison

Rolling-origin backtest: first training cut-off 2022-12, a new origin every 2 months, forecast up to 12 months ahead, 80% prediction intervals. Scored against published values.

## Winning model count (lowest RMSE)

|   horizon |   Combination |   Holt-Winters |   SARIMA |   Seasonal Naive |
|----------:|--------------:|---------------:|---------:|-----------------:|
|         3 |            10 |              1 |        2 |                8 |
|         6 |             9 |              1 |        3 |                8 |
|        12 |             8 |              1 |        4 |                8 |


## Median RMSE skill vs Seasonal Naive (%, positive = better than baseline)

|   horizon |   Combination |   Holt-Winters |   SARIMA |
|----------:|--------------:|---------------:|---------:|
|         3 |           7.2 |           -0.2 |     -1.7 |
|         6 |           4.3 |           -5   |     -2.5 |
|        12 |           5.4 |           -2.2 |     -0.5 |


## % of series where the winner beats the baseline by at least 5%

|   horizon |   pct |
|----------:|------:|
|         3 |    52 |
|         6 |    48 |
|        12 |    52 |


## Median MAPE (%) by metric, horizon and model

|                   |   Combination |   Holt-Winters |   SARIMA |   Seasonal Naive |
|:------------------|--------------:|---------------:|---------:|-----------------:|
| ('adr', 3)        |          10.6 |           11   |     10.4 |             10.9 |
| ('adr', 6)        |          11.6 |           12.8 |     11.2 |             11.4 |
| ('adr', 12)       |          11   |           12.4 |     11   |             11.3 |
| ('occupancy', 3)  |          12.2 |           12   |     14.9 |             13.3 |
| ('occupancy', 6)  |          12.3 |           12.4 |     14.2 |             13.3 |
| ('occupancy', 12) |          14.5 |           14.5 |     15.5 |             14.8 |
| ('revpar', 3)     |          16.9 |           20.6 |     18.7 |             18.9 |
| ('revpar', 6)     |          17.5 |           23.3 |     21   |             19.3 |
| ('revpar', 12)    |          18.7 |           24.1 |     22.8 |             20.7 |


## Mean empirical coverage of the nominal 80% interval (%)

|   horizon |   Combination |   Holt-Winters |   SARIMA |   Seasonal Naive |
|----------:|--------------:|---------------:|---------:|-----------------:|
|         3 |          67.3 |           61.4 |     68.7 |             81.8 |
|         6 |          67.7 |           61.9 |     68.9 |             82.7 |
|        12 |          70.1 |           66.9 |     66.6 |             79.8 |


## Best model per segment, metric and horizon

|                                       | 3              | 6              | 12             |
|:--------------------------------------|:---------------|:---------------|:---------------|
| ('1 & 2 Star Hotels+', 'adr')         | SARIMA         | SARIMA         | SARIMA         |
| ('1 & 2 Star Hotels+', 'occupancy')   | Combination    | Combination    | Combination    |
| ('1 & 2 Star Hotels+', 'revpar')      | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('3 Star Hotels+', 'adr')             | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('3 Star Hotels+', 'occupancy')       | SARIMA         | SARIMA         | SARIMA         |
| ('3 Star Hotels+', 'revpar')          | Combination    | Combination    | Combination    |
| ('4 Star Hotels+', 'adr')             | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('4 Star Hotels+', 'occupancy')       | Combination    | Combination    | Combination    |
| ('4 Star Hotels+', 'revpar')          | Combination    | Combination    | Combination    |
| ('5 Star Hotels+', 'adr')             | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('5 Star Hotels+', 'occupancy')       | Combination    | Combination    | Combination    |
| ('5 Star Hotels+', 'revpar')          | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('Deluxe Apartments+', 'adr')         | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('Deluxe Apartments+', 'occupancy')   | Holt-Winters   | Holt-Winters   | Holt-Winters   |
| ('Deluxe Apartments+', 'revpar')      | Combination    | Combination    | Combination    |
| ('Qatar+', 'adr')                     | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('Qatar+', 'occupancy')               | Combination    | Combination    | Combination    |
| ('Qatar+', 'revpar')                  | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('Standard Apartments+', 'adr')       | Combination    | Combination    | Combination    |
| ('Standard Apartments+', 'occupancy') | Combination    | Combination    | SARIMA         |
| ('Standard Apartments+', 'revpar')    | Combination    | SARIMA         | SARIMA         |


## Chosen SARIMA specifications

| series                         | order     | seasonal      |   val_rmse |
|:-------------------------------|:----------|:--------------|-----------:|
| 1 & 2 Star Hotels+|occupancy   | [2, 1, 0] | [1, 0, 0, 12] |      8.579 |
| 1 & 2 Star Hotels+|adr         | [0, 0, 1] | [1, 1, 0, 12] |     29.329 |
| 1 & 2 Star Hotels+|revpar      | [1, 0, 0] | [1, 0, 0, 12] |     17.261 |
| 3 Star Hotels+|occupancy       | [1, 0, 0] | [0, 1, 1, 12] |      7.525 |
| 3 Star Hotels+|adr             | [0, 0, 1] | [1, 0, 0, 12] |     27.726 |
| 3 Star Hotels+|revpar          | [0, 0, 1] | [1, 0, 1, 12] |     34.913 |
| 4 Star Hotels+|occupancy       | [0, 0, 1] | [1, 0, 1, 12] |     10.866 |
| 4 Star Hotels+|adr             | [0, 0, 1] | [0, 1, 1, 12] |     18.239 |
| 4 Star Hotels+|revpar          | [0, 0, 1] | [1, 0, 1, 12] |     26.066 |
| 5 Star Hotels+|occupancy       | [0, 0, 0] | [1, 0, 1, 12] |      9.635 |
| 5 Star Hotels+|adr             | [1, 0, 1] | [1, 0, 1, 12] |     45.194 |
| 5 Star Hotels+|revpar          | [0, 0, 1] | [1, 0, 0, 12] |     67.682 |
| Deluxe Apartments+|occupancy   | [0, 0, 1] | [1, 0, 1, 12] |      5.085 |
| Deluxe Apartments+|adr         | [2, 0, 1] | [0, 1, 1, 12] |     31.077 |
| Deluxe Apartments+|revpar      | [0, 0, 1] | [1, 1, 0, 12] |     22.155 |
| Qatar+|occupancy               | [0, 0, 0] | [1, 0, 1, 12] |      6.076 |
| Qatar+|adr                     | [1, 0, 1] | [1, 0, 0, 12] |     32.81  |
| Qatar+|revpar                  | [0, 0, 1] | [1, 0, 0, 12] |     42.173 |
| Standard Apartments+|occupancy | [0, 0, 0] | [0, 1, 1, 12] |     12.427 |
| Standard Apartments+|adr       | [0, 0, 0] | [0, 1, 1, 12] |     10.507 |
| Standard Apartments+|revpar    | [0, 0, 0] | [1, 0, 1, 12] |     33.357 |

