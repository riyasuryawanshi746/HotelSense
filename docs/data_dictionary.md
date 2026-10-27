# Data Dictionary

**Source:** State of Qatar Open Data portal (data.gov.qa), published by Qatar Tourism.
**Licence:** CC BY (attribution required).
**Dataset:** Accommodation data by segment, date and key metrics (supply, demand, occupancy, ADR, RevPAR).
**File format:** CSV, semicolon (`;`) delimited. Original file kept unchanged in `data/accommodation_data.csv`.
**Coverage:** 2014-01 to 2025-03, monthly, 7 segments x 135 months = 945 rows.

| Raw column | Clean name | Type | Meaning |
|---|---|---|---|
| Segment | segment | text | Accommodation category (see below) |
| Date | date | YYYY-MM -> month start | Reporting month |
| Supply | supply | int | Available room-nights in the month |
| Demand | demand | int | Sold room-nights in the month |
| Occupancy Rate | occupancy | float, % | Demand / Supply x 100 |
| Average Daily Rate | adr | float, QAR | Room revenue / sold room-nights |
| Revenue per Available Room | revpar | float, QAR | Room revenue / available room-nights (= ADR x occupancy) |
| Sample Properties / Rooms | sample_* | int | Properties/rooms that reported |
| Census Properties / Rooms | census_* | int | Total properties/rooms in the segment |

**Segments:** 1 & 2 Star Hotels+, 3 Star Hotels+, 4 Star Hotels+, 5 Star Hotels+, Deluxe Apartments+, Standard Apartments+, and Qatar+ (national total; not an exact sum of the six others).

**Derived columns added by `data_loader.py`:** `flag_occ_over_100`, `occupancy_capped`, `flag_world_cup`.
