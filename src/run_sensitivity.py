"""One-factor-at-a-time sensitivity analysis for synthetic model inputs."""

from __future__ import annotations

import argparse
import json

from .ev_charging_sim import ChargingSimulation, load_model_inputs
from .run_experiment import SCENARIOS, confidence_summary


FACTOR_LEVELS = {
    "demand_multiplier": [0.5, 0.75, 1.0, 1.1, 1.2],
    "charging_time_scale": [0.8, 1.0, 1.2],
    "baseline_dwell_scale": [0.5, 1.0, 1.5, 2.0],
    "policy_dwell_scale": [1.0, 2.0, 3.0],
}
PRACTICAL_TIE_MINUTES = 0.01


def setting_for(factor: str, level: float) -> dict[str, float]:
    setting = {
        "arrival_rate_multiplier": 1.0,
        "charging_time_scale": 1.0,
        "baseline_dwell_scale": 1.0,
        "policy_dwell_scale": 1.0,
    }
    key_map = {
        "demand_multiplier": "arrival_rate_multiplier",
        "charging_time_scale": "charging_time_scale",
        "baseline_dwell_scale": "baseline_dwell_scale",
        "policy_dwell_scale": "policy_dwell_scale",
    }
    setting[key_map[factor]] = level
    return setting


def run_sensitivity(
    *,
    replications: int,
    warmup_days: int,
    measurement_days: int,
    base_seed: int,
) -> dict:
    config = load_model_inputs()
    cache: dict[tuple[float, float, float, float], dict] = {}

    def evaluate(setting: dict[str, float]) -> dict:
        cache_key = (
            setting["arrival_rate_multiplier"],
            setting["charging_time_scale"],
            setting["baseline_dwell_scale"],
            setting["policy_dwell_scale"],
        )
        if cache_key in cache:
            return cache[cache_key]

        waits = {scenario: [] for scenario in SCENARIOS}
        for replication in range(replications):
            seed = base_seed + replication
            for scenario in SCENARIOS:
                result = ChargingSimulation(
                    config,
                    seed=seed,
                    days=measurement_days,
                    warmup_days=warmup_days,
                    profile="planning",
                    scenario=scenario,
                    **setting,
                ).run()
                waits[scenario].append(result.mean_vehicle_waiting_time_minutes)

        scenario_summaries = {
            scenario: confidence_summary(values)
            for scenario, values in waits.items()
        }
        baseline_mean = scenario_summaries["baseline"]["mean"]
        comparisons = {}
        for policy in ("capacity", "charge_and_go"):
            paired_reductions = [
                baseline - treatment
                for baseline, treatment in zip(waits["baseline"], waits[policy])
            ]
            reduction = confidence_summary(paired_reductions)
            comparisons[policy] = {
                "paired_reduction_minutes": reduction,
                "reduction_percentage": (
                    100.0 * reduction["mean"] / baseline_mean
                    if baseline_mean >= 0.01
                    else None
                ),
            }

        policy_means = {
            policy: scenario_summaries[policy]["mean"]
            for policy in ("capacity", "charge_and_go")
        }
        charge_and_go_advantage = (
            policy_means["capacity"] - policy_means["charge_and_go"]
        )
        if abs(charge_and_go_advantage) < PRACTICAL_TIE_MINUTES:
            lower_wait_policy = "practical_tie"
        elif charge_and_go_advantage > 0.0:
            lower_wait_policy = "charge_and_go"
        else:
            lower_wait_policy = "capacity"
        result = {
            "setting": setting,
            "mean_waiting_time_minutes": scenario_summaries,
            "paired_comparisons": comparisons,
            "lower_wait_policy": lower_wait_policy,
            "charge_and_go_advantage_over_capacity_minutes": charge_and_go_advantage,
        }
        cache[cache_key] = result
        return result

    factors = {}
    for factor, levels in FACTOR_LEVELS.items():
        factors[factor] = [
            {"level": level, "result": evaluate(setting_for(factor, level))}
            for level in levels
        ]

    unique_results = list(cache.values())
    output = {
        "design": {
            "method": "one_factor_at_a_time",
            "profile": "planning",
            "replications_per_setting": replications,
            "warmup_days": warmup_days,
            "measurement_days": measurement_days,
            "base_seed": base_seed,
            "common_random_numbers": True,
            "unique_settings": len(cache),
            "practical_tie_threshold_minutes": PRACTICAL_TIE_MINUTES,
        },
        "factors": factors,
        "robustness_summary": {
            "unique_settings_evaluated": len(unique_results),
            "settings_where_charge_and_go_has_lower_wait_than_capacity": sum(
                result["lower_wait_policy"] == "charge_and_go"
                for result in unique_results
            ),
            "settings_where_capacity_has_lower_wait_than_charge_and_go": sum(
                result["lower_wait_policy"] == "capacity"
                for result in unique_results
            ),
            "settings_with_practical_tie": sum(
                result["lower_wait_policy"] == "practical_tie"
                for result in unique_results
            ),
            "minimum_charge_and_go_advantage_over_capacity_minutes": min(
                result["charge_and_go_advantage_over_capacity_minutes"]
                for result in unique_results
            ),
        },
    }
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run sensitivity analysis.")
    parser.add_argument("--replications", type=int, default=50)
    parser.add_argument("--warmup-days", type=int, default=7)
    parser.add_argument("--measurement-days", type=int, default=30)
    parser.add_argument("--base-seed", type=int, default=841000)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output = run_sensitivity(
        replications=args.replications,
        warmup_days=args.warmup_days,
        measurement_days=args.measurement_days,
        base_seed=args.base_seed,
    )
    if args.json:
        print(json.dumps(output, indent=2))
        return

    print("One-Factor-at-a-Time Sensitivity Analysis")
    print(
        f"{args.replications} paired replications per setting | "
        f"{args.warmup_days} warm-up days | {args.measurement_days} measurement days"
    )
    for factor, entries in output["factors"].items():
        print(f"\nFactor: {factor}")
        print(
            f"{'Level':>8} {'Baseline':>12} {'Capacity':>12} "
            f"{'Charge-go':>12} {'Lower-wait policy':>20}"
        )
        for entry in entries:
            result = entry["result"]
            means = result["mean_waiting_time_minutes"]
            print(
                f"{entry['level']:>8.2f} "
                f"{means['baseline']['mean']:>12.4f} "
                f"{means['capacity']['mean']:>12.4f} "
                f"{means['charge_and_go']['mean']:>12.4f} "
                f"{result['lower_wait_policy']:>20}"
            )
    robustness = output["robustness_summary"]
    print(
        "\nCharge-and-go has lower mean waiting than capacity in "
        f"{robustness['settings_where_charge_and_go_has_lower_wait_than_capacity']} "
        f"of {robustness['unique_settings_evaluated']} unique settings; "
        f"{robustness['settings_with_practical_tie']} setting(s) are practical ties."
    )


if __name__ == "__main__":
    main()
