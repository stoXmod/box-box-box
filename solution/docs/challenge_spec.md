# F1 Strategy Challenge: Project Specification

This specification defines the problem and technical requirements of the F1 Strategy Simulator, as drafted before the implementation phase.

## 1. Objective
Develop a deterministic simulator to predict the exact finishing order (1st–20th) of a Formula 1 race. This requires calculating total race times for 20 drivers based on a track's `base_lap_time`, `pit_lane_time`, and `track_temp`, while accounting for each driver's tire choice and pit strategy.

## 2. Technical Requirements
- **Input Format**: JSON data containing `race_config` and `strategies`.
- **Output Format**: JSON with `race_id` and an ordered list of 20 `driver_id`s.
- **Constraints**:
    - Each car races independently; there are no car-to-car interactions.
    - Sorting by **Total Time** (ascending).
    - **Stability**: Alphabetical tie-breaking (e.g., D01 beats D02 if times are identical).

## 3. Key Variables for Analysis
- **Compound Speeds**: Differentiating between SOFT, MEDIUM, and HARD.
- **Degradation Scaling**: Understanding how tire age increases lap times.
- **Temperature Effects**: How track heat accelerates tire wear.
- **Wait Time Costs**: Correctly applying the provided `pit_lane_time` constants.

## 4. Success Criteria
A successful solution must demonstrate 100% precision on the 100 benchmark test cases provided. The algorithm must be robust enough to handle any configuration from the historical 30,000-race dataset.
