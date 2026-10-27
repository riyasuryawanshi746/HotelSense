# HotelSense - EDA Summary

## STL strength (occupancy)

| segment              |   trend_strength |   seasonal_strength |
|:---------------------|-----------------:|--------------------:|
| 1 & 2 Star Hotels+   |            0.666 |               0.42  |
| 3 Star Hotels+       |            0.769 |               0.553 |
| 4 Star Hotels+       |            0.607 |               0.607 |
| 5 Star Hotels+       |            0.323 |               0.526 |
| Deluxe Apartments+   |            0.881 |               0.43  |
| Qatar+               |            0.514 |               0.505 |
| Standard Apartments+ |            0.558 |               0.164 |


## Stationarity (ADF p-values; KPSS p<0.05 means non-stationary)

| segment              | metric    |   adf_level_p |   adf_diff1_p |   adf_seasdiff12_p |   kpss_level_p | verdict                               |
|:---------------------|:----------|--------------:|--------------:|-------------------:|---------------:|:--------------------------------------|
| 1 & 2 Star Hotels+   | occupancy |        0.0123 |        0.107  |             0.0595 |         0.01   | stationary (level)                    |
| 1 & 2 Star Hotels+   | adr       |        0.32   |        0      |             0.1423 |         0.01   | non-stationary; use d=1               |
| 1 & 2 Star Hotels+   | revpar    |        0.0038 |        0.0151 |             0.056  |         0.0436 | stationary (level)                    |
| 3 Star Hotels+       | occupancy |        0.2528 |        0.0172 |             0.0189 |         0.01   | non-stationary; d=1 and D=1 both work |
| 3 Star Hotels+       | adr       |        0.0005 |        0      |             0.0443 |         0.04   | stationary (level)                    |
| 3 Star Hotels+       | revpar    |        0.0001 |        0.0004 |             0.0547 |         0.1    | stationary (level)                    |
| 4 Star Hotels+       | occupancy |        0.0093 |        0.0228 |             0      |         0.1    | stationary (level)                    |
| 4 Star Hotels+       | adr       |        0.0142 |        0      |             0.0302 |         0.0121 | stationary (level)                    |
| 4 Star Hotels+       | revpar    |        0.0012 |        0.0001 |             0.0573 |         0.01   | stationary (level)                    |
| 5 Star Hotels+       | occupancy |        0.0107 |        0.0008 |             0.005  |         0.1    | stationary (level)                    |
| 5 Star Hotels+       | adr       |        0      |        0      |             0.01   |         0.1    | stationary (level)                    |
| 5 Star Hotels+       | revpar    |        0      |        0      |             0.0109 |         0.0747 | stationary (level)                    |
| Deluxe Apartments+   | occupancy |        0.1873 |        0.0183 |             0.3169 |         0.01   | non-stationary; use d=1               |
| Deluxe Apartments+   | adr       |        0.0014 |        0      |             0.0136 |         0.0966 | stationary (level)                    |
| Deluxe Apartments+   | revpar    |        0      |        0      |             0.0097 |         0.1    | stationary (level)                    |
| Qatar+               | occupancy |        0.0117 |        0.0097 |             0.022  |         0.0848 | stationary (level)                    |
| Qatar+               | adr       |        0      |        0      |             0.012  |         0.1    | stationary (level)                    |
| Qatar+               | revpar    |        0      |        0      |             0.0131 |         0.0902 | stationary (level)                    |
| Standard Apartments+ | occupancy |        0.0166 |        0      |             0.1951 |         0.1    | stationary (level)                    |
| Standard Apartments+ | adr       |        0.0001 |        0      |             0.0073 |         0.1    | stationary (level)                    |
| Standard Apartments+ | revpar    |        0      |        0      |             0.0201 |         0.1    | stationary (level)                    |


## Mean occupancy by period

| segment              |   1. Pre-COVID (2014-01 to 2020-02) |   2. COVID (2020-03 to 2021-12) |   3. Post-COVID (2022-01 on) |
|:---------------------|------------------------------------:|--------------------------------:|-----------------------------:|
| 1 & 2 Star Hotels+   |                                71.6 |                            70.3 |                         88.3 |
| 3 Star Hotels+       |                                66.2 |                            74.9 |                         80   |
| 4 Star Hotels+       |                                64.4 |                            66.3 |                         62.5 |
| 5 Star Hotels+       |                                61.6 |                            59.1 |                         57.7 |
| Deluxe Apartments+   |                                75.9 |                            55.9 |                         64   |
| Qatar+               |                                65.9 |                            61.4 |                         61.8 |
| Standard Apartments+ |                                65.6 |                            71.2 |                         60   |


## Mean ADR by period (QAR)

| segment              |   1. Pre-COVID (2014-01 to 2020-02) |   2. COVID (2020-03 to 2021-12) |   3. Post-COVID (2022-01 on) |
|:---------------------|------------------------------------:|--------------------------------:|-----------------------------:|
| 1 & 2 Star Hotels+   |                               226.7 |                           161.2 |                        181.8 |
| 3 Star Hotels+       |                               231   |                           188.4 |                        224.7 |
| 4 Star Hotels+       |                               311.3 |                           224.7 |                        279.8 |
| 5 Star Hotels+       |                               652.1 |                           506.8 |                        708.2 |
| Deluxe Apartments+   |                               332.8 |                           345   |                        434.4 |
| Qatar+               |                               454.8 |                           373.8 |                        504.3 |
| Standard Apartments+ |                               268.2 |                           238.5 |                        300.8 |


## Mean RevPAR by period (QAR)

| segment              |   1. Pre-COVID (2014-01 to 2020-02) |   2. COVID (2020-03 to 2021-12) |   3. Post-COVID (2022-01 on) |
|:---------------------|------------------------------------:|--------------------------------:|-----------------------------:|
| 1 & 2 Star Hotels+   |                               161.3 |                           115.3 |                        161.4 |
| 3 Star Hotels+       |                               152.4 |                           143.3 |                        178.7 |
| 4 Star Hotels+       |                               203.6 |                           149.8 |                        175.4 |
| 5 Star Hotels+       |                               405.6 |                           300.1 |                        409.3 |
| Deluxe Apartments+   |                               253.3 |                           193.4 |                        275.8 |
| Qatar+               |                               302.4 |                           230.6 |                        311.3 |
| Standard Apartments+ |                               175.1 |                           169.6 |                        176.3 |


## Segment comparison (occupancy, capped)

| segment              |   mean |   std |   min |   max |   cv_% |
|:---------------------|-------:|------:|------:|------:|-------:|
| 1 & 2 Star Hotels+   |   76.2 |  14.5 |  35.7 | 100   |   19   |
| 3 Star Hotels+       |   71.6 |  12.2 |  37   |  94.8 |   17   |
| 4 Star Hotels+       |   64.2 |  10.4 |  38.3 |  87   |   16.2 |
| 5 Star Hotels+       |   60   |  10.3 |  37.8 |  84   |   17.2 |
| Deluxe Apartments+   |   69.2 |  12.5 |  42.4 |  94.4 |   18.1 |
| Qatar+               |   64   |   9.5 |  43.2 |  85.4 |   14.8 |
| Standard Apartments+ |   64.9 |  11.9 |  17   |  85.8 |   18.3 |


## STL residual outliers (|robust z| > 4): 302 found

| segment              | metric   | date    |   robust_z |
|:---------------------|:---------|:--------|-----------:|
| 4 Star Hotels+       | adr      | 2022-12 |      191.7 |
| Standard Apartments+ | adr      | 2022-12 |      183.3 |
| Deluxe Apartments+   | adr      | 2022-12 |      178.8 |
| Standard Apartments+ | adr      | 2022-11 |      173   |
| 4 Star Hotels+       | adr      | 2022-11 |      170.8 |
| Deluxe Apartments+   | adr      | 2022-11 |      162.9 |
| Qatar+               | adr      | 2022-12 |      125.4 |
| 5 Star Hotels+       | adr      | 2022-12 |      118.4 |
| 3 Star Hotels+       | adr      | 2022-12 |      110.5 |
| Qatar+               | adr      | 2022-11 |      107.2 |
| 3 Star Hotels+       | adr      | 2022-11 |       98.9 |
| 5 Star Hotels+       | adr      | 2022-11 |       98.1 |
| Deluxe Apartments+   | revpar   | 2022-12 |       85.9 |
| Deluxe Apartments+   | revpar   | 2022-11 |       76.1 |
| Qatar+               | revpar   | 2022-12 |       61.1 |
| Standard Apartments+ | revpar   | 2022-12 |       59.4 |
| Standard Apartments+ | revpar   | 2022-11 |       56   |
| 5 Star Hotels+       | revpar   | 2022-12 |       51.9 |
| 4 Star Hotels+       | revpar   | 2022-12 |       49.2 |
| Qatar+               | revpar   | 2022-11 |       46.6 |
| 1 & 2 Star Hotels+   | adr      | 2022-12 |       44.3 |
| 4 Star Hotels+       | revpar   | 2022-11 |       39.7 |
| 1 & 2 Star Hotels+   | adr      | 2022-11 |       38.2 |
| 5 Star Hotels+       | revpar   | 2022-11 |       37.5 |
| 3 Star Hotels+       | revpar   | 2022-12 |       31.9 |


Figures are in reports/figures/.
