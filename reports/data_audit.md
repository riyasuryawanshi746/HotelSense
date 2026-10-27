# HotelSense - Data Audit Report

## 1. Shape and types

- Rows: 945, columns: 11
- Missing values (total): 0
- Duplicate (segment, date) rows: 0
- Segments: 1 & 2 Star Hotels+, 3 Star Hotels+, 4 Star Hotels+, 5 Star Hotels+, Deluxe Apartments+, Qatar+, Standard Apartments+

## 2. Date continuity per segment

| segment              | start   | end     |   n_obs |   expected |   missing_months |
|:---------------------|:--------|:--------|--------:|-----------:|-----------------:|
| 1 & 2 Star Hotels+   | 2014-01 | 2025-03 |     135 |        135 |                0 |
| 3 Star Hotels+       | 2014-01 | 2025-03 |     135 |        135 |                0 |
| 4 Star Hotels+       | 2014-01 | 2025-03 |     135 |        135 |                0 |
| 5 Star Hotels+       | 2014-01 | 2025-03 |     135 |        135 |                0 |
| Deluxe Apartments+   | 2014-01 | 2025-03 |     135 |        135 |                0 |
| Qatar+               | 2014-01 | 2025-03 |     135 |        135 |                0 |
| Standard Apartments+ | 2014-01 | 2025-03 |     135 |        135 |                0 |

## 3. Occupancy anomalies (> 100%)

| segment            | date    |   supply |   demand |   occupancy |
|:-------------------|:--------|---------:|---------:|------------:|
| 1 & 2 Star Hotels+ | 2024-01 |    18166 |    18220 |       100.3 |
| 1 & 2 Star Hotels+ | 2024-11 |    17580 |    17939 |       102   |
| 1 & 2 Star Hotels+ | 2025-02 |    17668 |    18171 |       102.8 |

Demand exceeds supply in these rows, which is physically impossible for room-nights but is how the source published them (likely survey/reporting timing). Decision: keep the raw value, and use `occupancy_capped` (max 100) for modelling.

## 4. Internal consistency checks

- Occupancy vs Demand/Supply, rows differing by >0.5 pt: 0
- RevPAR vs ADR x Occupancy, rows differing by >1 QAR: 1
  - 5 Star Hotels+ 2022-12: published 1748.8, computed 1747.30 (rounding)
- Rows with demand > supply: 3

## 5. Extreme values / events

| segment            | date    |   occupancy |     adr |   revpar |
|:-------------------|:--------|------------:|--------:|---------:|
| 5 Star Hotels+     | 2022-12 |        56.7 | 3081.65 |  1748.8  |
| 5 Star Hotels+     | 2022-11 |        52.6 | 2595.12 |  1365.81 |
| Qatar+             | 2022-12 |        59.7 | 2103.59 |  1256.69 |
| Qatar+             | 2022-11 |        55.9 | 1839.25 |  1027.6  |
| Deluxe Apartments+ | 2022-12 |        60.5 | 1655.47 |  1001.61 |
| Deluxe Apartments+ | 2022-11 |        58.1 | 1552.05 |   902.13 |

All top ADR values are Nov-Dec 2022 (FIFA World Cup). These are real events, not errors: flag them, do not delete them.

## 6. Is Qatar+ the sum of the other segments?

- Max |Qatar+ supply - sum of 6 segments|: 7843 room-nights (mean 4586). Not an exact sum, so treat Qatar+ as its own national series.

## 7. Descriptive statistics

|       |          supply |           demand |   occupancy |     adr |   revpar |
|:------|----------------:|-----------------:|------------:|--------:|---------:|
| count |    945          |    945           |      945    |  945    |   945    |
| mean  | 236517          | 150010           |       67.16 |  350.12 |   229.49 |
| std   | 286700          | 181899           |       12.76 |  217.92 |   132.27 |
| min   |   4648          |   2645           |       17    |  136.57 |    45.37 |
| 25%   |  31403          |  19368           |       57.9  |  227.64 |   147.84 |
| 50%   | 145830          |  95952           |       67.3  |  298.05 |   199.89 |
| 75%   | 301165          | 186902           |       76    |  404.65 |   271.17 |
| max   |      1.2665e+06 |      1.01549e+06 |      102.8  | 3081.65 |  1748.8  |