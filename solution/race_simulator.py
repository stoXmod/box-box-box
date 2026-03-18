#!/usr/bin/env python3
"""
Box Box Box Strategy Challenge - Final Submission
Hybrid KNN-Interpolation Strategy Predictor
"""

import glob
import json
import os
import sys

import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler


def get_profile_key(s, n_laps):
    """
    Generates a unique signature for a driver's strategy profile.
    This signature buckets identical stint strategies across the historical dataset.
    """
    counts = {"SOFT": 0, "MEDIUM": 0, "HARD": 0}
    age_sums = {"SOFT": 0, "MEDIUM": 0, "HARD": 0}
    prev_lap = 0
    cur_tire = s["starting_tire"]

    # Iterate through pit stop history
    for stop in sorted(s["pit_stops"], key=lambda x: x["lap"]):
        stint_len = stop["lap"] - prev_lap
        counts[cur_tire] += stint_len
        age_sums[cur_tire] += stint_len * (stint_len + 1) / 2
        cur_tire = stop["to_tire"]
        prev_lap = stop["lap"]

    # Final stint calculation
    stint_len = n_laps - prev_lap
    counts[cur_tire] += stint_len
    age_sums[cur_tire] += stint_len * (stint_len + 1) / 2

    # Signature serialization
    sig_parts = [
        counts["SOFT"],
        counts["MEDIUM"],
        counts["HARD"],
        int(age_sums["SOFT"]),
        int(age_sums["MEDIUM"]),
        int(age_sums["HARD"]),
        len(s["pit_stops"]),
    ]
    return "_".join(map(str, sig_parts))


def main():
    # 1. Read test case from stdin
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            return
        test_case = json.loads(raw_input)
    except Exception:
        return

    race_id = test_case.get("race_id")
    race_config = test_case.get("race_config", {})
    strategies = test_case.get("strategies", {})

    # Extract target configuration constants
    n_target = int(race_config.get("total_laps", 0))
    temp_target = float(race_config.get("track_temp", 30))
    base_target = float(race_config.get("base_lap_time", 90))
    pit_target = float(race_config.get("pit_lane_time", 20))

    # 2. Pattern Discovery - Scanning historical data for matching strategy profiles
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hist_path = os.path.join(script_dir, "data", "historical_races", "*.json")
    
    # Pre-profile all incoming strategies
    dids = list(strategies.keys())
    profs = {d: get_profile_key(strategies[d], n_target) for d in dids}

    needed_pairs = set()
    for i in range(len(dids)):
        for j in range(i + 1, len(dids)):
            pk1, pk2 = profs[dids[i]], profs[dids[j]]
            if pk1 != pk2:
                needed_pairs.add(tuple(sorted([pk1, pk2])))

    pair_data = {p: [] for p in needed_pairs}

    # Iterate through available historical JSON records
    for f in sorted(glob.glob(hist_path)):
        with open(f) as fp:
            for r in json.load(fp):
                hrc = r["race_config"]
                # Only analyze races with identical length (primary physical constraint)
                if int(hrc["total_laps"]) == n_target:
                    s_map = {
                        s["driver_id"]: get_profile_key(s, n_target)
                        for s in r["strategies"].values()
                    }
                    drs = r["finishing_positions"]
                    for idx_w in range(len(drs)):
                        for idx_l in range(idx_w + 1, len(drs)):
                            wa, la = drs[idx_w], drs[idx_l]
                            if wa in s_map and la in s_map:
                                pk_w, pk_l = s_map[wa], s_map[la]
                                if pk_w != pk_l:
                                    pair_key = tuple(sorted([pk_w, pk_l]))
                                    if pair_key in needed_pairs:
                                        # Record outcome: 1 if pair[0] beats pair[1]
                                        w_flag = 1 if pk_w == pair_key[0] else 0
                                        pair_data[pair_key].append(
                                            [hrc["base_lap_time"], hrc["track_temp"], w_flag]
                                        )

    # 3. AI Inference - Predict winners using Weighted K-Nearest Neighbors
    wins = {d: 0.0 for d in dids}
    for i in range(len(dids)):
        for j in range(i + 1, len(dids)):
            d1, d2 = dids[i], dids[j]
            pk1, pk2 = profs[d1], profs[d2]

            if pk1 != pk2:
                pair_key = tuple(sorted([pk1, pk2]))
                data = pair_data[pair_key]
                win_prob = 0.5
                
                if len(data) >= 3:
                    # ML Model: Interpolate historical wins over base/temp space
                    X = np.array([d[:2] for d in data])
                    y = np.array([d[2] for d in data])
                    if len(set(y)) == 1:
                        win_prob = y[0]
                    else:
                        scaler = StandardScaler()
                        X_s = scaler.fit_transform(X)
                        X_t = scaler.transform([[base_target, temp_target]])
                        # Weighted KNN ensures closer track conditions carry more weight
                        knn = KNeighborsClassifier(n_neighbors=min(5, len(data)), weights="distance")
                        knn.fit(X_s, y)
                        win_prob = knn.predict_proba(X_t)[0][1]
                    if pk1 != pair_key[0]: win_prob = 1 - win_prob
                elif len(data) > 0:
                    # Sparse fall-through
                    avg_w = sum(d[2] for d in data) / len(data)
                    win_prob = avg_w if pk1 == pair_key[0] else (1 - avg_w)
                else:
                    # Pure HeuristicFallback
                    v1 = (len(strategies[d1]["pit_stops"]) * (pit_target + 2))
                    v2 = (len(strategies[d2]["pit_stops"]) * (pit_target + 2))
                    win_prob = 1.0 if v1 < v2 else (0.0 if v2 < v1 else 0.5)

                if win_prob > 0.5: wins[d1] += 1
                elif win_prob < 0.5: wins[d2] += 1
                else: wins[d1] += 0.5; wins[d2] += 0.5
            else:
                # Mirror strategy tie-handling
                wins[d1] += 0.5; wins[d2] += 0.5

    # 4. Final Ordering - Combine wins with numerical Driver ID stability
    winners_sorted = sorted(dids, key=lambda d: (-wins[d], int(d[3:])))
    finishing_positions = [strategies[d]["driver_id"] for d in winners_sorted]

    # Output result to stdout
    output = {
        "race_id": race_id,
        "finishing_positions": finishing_positions
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
