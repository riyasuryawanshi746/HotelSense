# HotelSense - Scope and Problem Statement

## Problem statement
Hotel and apartment operators and planners in Qatar need to anticipate demand and pricing months ahead
to plan capacity, staffing and rates. HotelSense forecasts monthly occupancy, ADR and RevPAR per
accommodation segment, compares classical time-series models on the same test period, and turns the
results into transparent planning signals.

## Objectives
1. Clean and validate the Qatar Tourism monthly dataset.
2. Analyse trend, seasonality, structural breaks and stationarity (EDA, decomposition, ADF).
3. Compare at least three models (Seasonal Naive, Holt-Winters, SARIMA) with chronological validation.
4. Evaluate with MAE, RMSE and MAPE; select the best model per segment/metric by evidence.
5. Serve forecasts through a FastAPI backend and a React dashboard (segment, metric, horizon 3/6/12).
6. Generate rule-based decision-support text from the actual forecast output.

## Targets
- **Primary:** monthly occupancy rate (%).
- **Secondary:** RevPAR (and ADR) if time and model performance allow.

## Key data findings that shape the design
- 135 consecutive months per segment, no gaps, no missing values, no duplicates.
- Only 3 occupancy values exceed 100% (all 1 & 2 Star Hotels+, 2024-2025). Kept as published, capped at 100 for modelling.
- COVID-19 (from 2020-03) causes a structural break, and the FIFA World Cup (2022-11/12) causes extreme ADR/RevPAR spikes.
- Only ~11 years of data: classical models only, no deep learning.

## Limitations
- Data is aggregated by segment; no recommendation can target a single hotel.
- Few years of history, and two major shocks (COVID, World Cup) are hard to forecast.
- Forecasts are planning signals, not guaranteed outcomes.
- 12-month horizon is allowed only if validation shows acceptable accuracy.
