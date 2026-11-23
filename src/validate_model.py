"""Reproducible statistical checks for the approved input model."""

from __future__ import annotations

import json
import math
import random
import statistics

from .ev_charging_sim import BaselineSimulation, ChargingSimulation, load_model_inputs


REPLICATIONS = 500
TRIANGULAR_SAMPLES = 200_000


def triangular_sample_mean(parameters: dict, seed: int) -> float:
    rng = random.Random(seed)
    minimum = float(parameters["minimum_minutes"])
    mode = float(parameters["mode_minutes"])
    maximum = float(parameters["maximum_minutes"])
    samples = (
        ChargingSimulation._triangular_inverse_cdf(parameters, rng.random())
        for _ in range(TRIANGULAR_SAMPLES)
    )
    return statistics.fmean(samples)


def main() -> None:
    config = load_model_inputs()

    planning_counts: list[int] = []
    conservation_passed = True
    for replication in range(REPLICATIONS):
        result = BaselineSimulation(
            config,
            seed=50_000 + replication,
            profile="planning",
        ).run()
        planning_counts.append(result.vehicles_arrived)
        conservation_passed &= (
            result.vehicles_arrived
            == result.vehicles_started_charging
            == result.vehicles_departed
        )

    expected_arrivals = float(
        config["arrival_process"]["expected_planning_arrivals_per_day"]
    )
    observed_arrival_mean = statistics.fmean(planning_counts)
    arrival_mean_standard_error = math.sqrt(expected_arrivals / REPLICATIONS)
    arrival_z_score = (
        observed_arrival_mean - expected_arrivals
    ) / arrival_mean_standard_error

    charging = config["active_charging_time"]
    dwell = config["post_charging_dwell_time"]["baseline"]
    observed_charging_mean = triangular_sample_mean(charging, seed=70_001)
    observed_dwell_mean = triangular_sample_mean(dwell, seed=70_002)

    # A long continuous run makes the empty initial state negligible. The
    # utilisation target is not asserted exactly because end-of-horizon work is
    # deliberately excluded from the horizon utilisation statistic.
    benchmark_result = BaselineSimulation(
        config,
        seed=80_001,
        days=120,
        profile="current_benchmark",
    ).run()
    expected_benchmark_utilisation = float(
        config["arrival_process"]["current_benchmark_time_weighted_utilisation"]
    )

    checks = {
        "vehicle_conservation_all_500_replications": conservation_passed,
        "poisson_arrival_mean_within_four_standard_errors": abs(arrival_z_score) <= 4.0,
        "charging_sample_mean_within_0_20_minutes": abs(
            observed_charging_mean - float(charging["theoretical_mean_minutes"])
        )
        <= 0.20,
        "dwell_sample_mean_within_0_10_minutes": abs(
            observed_dwell_mean - float(dwell["theoretical_mean_minutes"])
        )
        <= 0.10,
        "benchmark_utilisation_within_0_02": abs(
            benchmark_result.charger_utilisation_during_arrival_horizon
            - expected_benchmark_utilisation
        )
        <= 0.02,
    }

    output = {
        "settings": {
            "replications": REPLICATIONS,
            "triangular_samples_per_input": TRIANGULAR_SAMPLES,
            "long_run_days": 120,
        },
        "observations": {
            "expected_planning_arrivals_per_day": expected_arrivals,
            "observed_planning_arrivals_mean": observed_arrival_mean,
            "arrival_mean_standard_error": arrival_mean_standard_error,
            "arrival_mean_z_score": arrival_z_score,
            "theoretical_charging_mean_minutes": charging["theoretical_mean_minutes"],
            "observed_charging_sample_mean_minutes": observed_charging_mean,
            "theoretical_dwell_mean_minutes": dwell["theoretical_mean_minutes"],
            "observed_dwell_sample_mean_minutes": observed_dwell_mean,
            "target_benchmark_utilisation": expected_benchmark_utilisation,
            "observed_120_day_benchmark_utilisation": (
                benchmark_result.charger_utilisation_during_arrival_horizon
            ),
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }
    print(json.dumps(output, indent=2))

    if not output["all_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
