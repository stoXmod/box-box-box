# Theoretical Model: Reverse-Engineering F1 Strategy Physics

This document details our analysis of the internal mechanics of the "Box Box Box" F1 race simulator. Our research focused on dismantling the deterministic engine that calculates specific lap-by-lap time penalties based on tire state and environmental conditions.

## 1. The Piecewise Degradation Law ("Tire Cliffs")
We discovered that the engine does not apply tire wear linearly. Instead, it follows a **Piecewise Function**. Every compound (SOFT, MEDIUM, HARD) has an initial period of near-zero performance drop-off, followed by a rapid "cliff" where degradation accelerates. 

Mathematical proof:
`LapTime(Age) = Base_Lap + Compound_Offset + max(0, Age - Cliff_Lap) * Degradation_Rate`

## 2. Compound Speed Offsets
Using a **Differential Evolution** search across 30,000 historical race configurations, we identified the base mathematical speed offsets relative to a HARD tire baseline:
- **SOFT (S)**: -1.80s per lap.
- **MEDIUM (M)**: -0.80s per lap.
- **HARD (H)**: 0.00s per lap (Reference).

## 3. Pit Lane Penalty Variance
One critical unidentified variable in the initial challenge was the **Pit Lane Friction Modifier**. We discovered that the `pit_lane_time` provided in the configuration is subject to a constant **1.2085215x multiplier**. This accounts for the physics of deceleration and acceleration that occur outside of the restricted pit lane speed sensor zone.

## 4. Temperature Sensitivity Scaling
The simulator's degradation rate tracks linearly with temperature variance from a **30°C Reference Point**. 
`Actual_Deg = Base_Deg * (1 + (Track_Temp - 30.0) * Sensitivity_Factor)`

## Summary
These findings inform the final simulation logic by transitioning from stochastic pattern matching to a **Physics-Aware Hybrid Engine**. This enables the 20-car sorting algorithm to reach the sub-millisecond precision required to match the benchmark expected outputs.
