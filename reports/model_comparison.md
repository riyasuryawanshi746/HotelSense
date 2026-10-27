# HotelSense - Model Comparison

Rolling-origin backtest: first training cut-off 2022-12, a new origin every 2 months, forecast up to 12 months ahead, 80% prediction intervals. Scored against published values.

## Winning model count (lowest RMSE)

|   horizon |   Combination |   Holt-Winters |   SARIMA |   Seasonal Naive |
|----------:|--------------:|---------------:|---------:|-----------------:|
|         3 |             2 |              2 |        7 |               10 |
|         6 |             2 |              4 |        4 |               11 |
|        12 |             1 |              4 |        8 |                8 |


## Median RMSE skill vs Seasonal Naive (%, positive = better than baseline)

|   horizon |   Combination |   Holt-Winters |   SARIMA |
|----------:|--------------:|---------------:|---------:|
|         3 |          -0.6 |           -0.2 |      0.9 |
|         6 |          -6.3 |           -5   |     -3.6 |
|        12 |          -2.3 |           -2.2 |     -8.5 |


## % of series where the winner beats the baseline by at least 5%

|   horizon |   pct |
|----------:|------:|
|         3 |    43 |
|         6 |    38 |
|        12 |    48 |


## Median MAPE (%) by metric, horizon and model

|                   |   Combination |   Holt-Winters |   SARIMA |   Seasonal Naive |
|:------------------|--------------:|---------------:|---------:|-----------------:|
| ('adr', 3)        |          10.7 |           11   |     10.4 |             10.9 |
| ('adr', 6)        |          12.4 |           12.8 |     11.9 |             11.4 |
| ('adr', 12)       |          11.8 |           12.4 |     11   |             11.3 |
| ('occupancy', 3)  |          10.5 |           12   |     10   |             13.3 |
| ('occupancy', 6)  |          11.4 |           12.4 |     11.5 |             13.3 |
| ('occupancy', 12) |          14.6 |           14.5 |     14.7 |             14.8 |
| ('revpar', 3)     |          18.2 |           20.6 |     18.2 |             18.9 |
| ('revpar', 6)     |          20.5 |           23.3 |     19.3 |             19.3 |
| ('revpar', 12)    |          20   |           24.1 |     20.4 |             20.7 |


## Mean empirical coverage of the nominal 80% interval (%)

|   horizon |   Combination |   Holt-Winters |   SARIMA |   Seasonal Naive |
|----------:|--------------:|---------------:|---------:|-----------------:|
|         3 |          66.5 |           61.4 |     69.4 |             81.8 |
|         6 |          66.3 |           61.9 |     68.5 |             82.7 |
|        12 |          69.5 |           66.9 |     70.1 |             79.8 |


## Best model per segment, metric and horizon

|                                       | 3              | 6              | 12             |
|:--------------------------------------|:---------------|:---------------|:---------------|
| ('1 & 2 Star Hotels+', 'adr')         | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('1 & 2 Star Hotels+', 'occupancy')   | Combination    | Combination    | Combination    |
| ('1 & 2 Star Hotels+', 'revpar')      | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('3 Star Hotels+', 'adr')             | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('3 Star Hotels+', 'occupancy')       | SARIMA         | SARIMA         | SARIMA         |
| ('3 Star Hotels+', 'revpar')          | SARIMA         | Seasonal Naive | SARIMA         |
| ('4 Star Hotels+', 'adr')             | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('4 Star Hotels+', 'occupancy')       | Holt-Winters   | Holt-Winters   | Holt-Winters   |
| ('4 Star Hotels+', 'revpar')          | Seasonal Naive | Holt-Winters   | Holt-Winters   |
| ('5 Star Hotels+', 'adr')             | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('5 Star Hotels+', 'occupancy')       | SARIMA         | SARIMA         | SARIMA         |
| ('5 Star Hotels+', 'revpar')          | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('Deluxe Apartments+', 'adr')         | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('Deluxe Apartments+', 'occupancy')   | Holt-Winters   | Holt-Winters   | Holt-Winters   |
| ('Deluxe Apartments+', 'revpar')      | SARIMA         | Holt-Winters   | SARIMA         |
| ('Qatar+', 'adr')                     | Seasonal Naive | Seasonal Naive | Seasonal Naive |
| ('Qatar+', 'occupancy')               | SARIMA         | Combination    | SARIMA         |
| ('Qatar+', 'revpar')                  | Seasonal Naive | Seasonal Naive | SARIMA         |
| ('Standard Apartments+', 'adr')       | SARIMA         | SARIMA         | SARIMA         |
| ('Standard Apartments+', 'occupancy') | Combination    | Seasonal Naive | Holt-Winters   |
| ('Standard Apartments+', 'revpar')    | SARIMA         | SARIMA         | SARIMA         |


## Chosen SARIMA specifications

| series                         | order     | seasonal      |   val_rmse |
|:-------------------------------|:----------|:--------------|-----------:|
| 1 & 2 Star Hotels+|occupancy   | [1, 1, 1] | [1, 0, 0, 12] |      9.492 |
| 1 & 2 Star Hotels+|adr         | [1, 0, 1] | [0, 1, 1, 12] |     32.248 |
| 1 & 2 Star Hotels+|revpar      | [1, 0, 0] | [1, 0, 0, 12] |     17.261 |
| 3 Star Hotels+|occupancy       | [1, 0, 0] | [0, 1, 1, 12] |      7.525 |
| 3 Star Hotels+|adr             | [1, 0, 1] | [1, 0, 0, 12] |     40.029 |
| 3 Star Hotels+|revpar          | [1, 0, 0] | [0, 1, 1, 12] |     44.868 |
| 4 Star Hotels+|occupancy       | [1, 0, 0] | [1, 0, 0, 12] |     11.208 |
| 4 Star Hotels+|adr             | [1, 0, 1] | [1, 0, 0, 12] |     24.533 |
| 4 Star Hotels+|revpar          | [1, 0, 0] | [1, 0, 0, 12] |     33.056 |
| 5 Star Hotels+|occupancy       | [1, 0, 0] | [0, 1, 1, 12] |     12.364 |
| 5 Star Hotels+|adr             | [1, 0, 1] | [1, 0, 0, 12] |     47.435 |
| 5 Star Hotels+|revpar          | [1, 0, 0] | [1, 0, 0, 12] |     77.653 |
| Deluxe Apartments+|occupancy   | [1, 1, 0] | [0, 1, 1, 12] |      7.805 |
| Deluxe Apartments+|adr         | [1, 0, 1] | [0, 1, 1, 12] |     35.652 |
| Deluxe Apartments+|revpar      | [1, 0, 0] | [0, 1, 1, 12] |     47.717 |
| Qatar+|occupancy               | [1, 0, 0] | [0, 1, 1, 12] |     10.167 |
| Qatar+|adr                     | [1, 0, 1] | [1, 0, 0, 12] |     32.81  |
| Qatar+|revpar                  | [1, 0, 0] | [0, 1, 1, 12] |     52.002 |
| Standard Apartments+|occupancy | [1, 0, 0] | [1, 0, 0, 12] |     16.577 |
| Standard Apartments+|adr       | [1, 0, 0] | [0, 1, 1, 12] |     11.374 |
| Standard Apartments+|revpar    | [1, 0, 0] | [0, 1, 1, 12] |     49.06  |

