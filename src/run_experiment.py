"""Run the approved paired policy experiment and report 95% intervals."""

from __future__ import annotations

import argparse
import json
from statistics import NormalDist, fmean, stdev

from .ev_charging_sim import ChargingSimulation, load_model_inputs


SCENARIOS = ("baseline", "capacity", "charge_and_go")
PROFILES = ("planning", "current_benchmark")


def t_critical_95(degrees_of_freedom: int) -> float:
    """Approximate the two-sided 95% Student-t critical value."""

    if degrees_of_freedom < 1:
        raise ValueError("degrees_of_freedom must be positive")
    z = NormalDist().inv_cdf(0.975)
    v = float(degrees_of_freedom)
    return (
        z
        + (z**3 + z) / (4.0 * v)
        + (5.0 * z**5 + 16.0 * z**3 + 3.0 * z) / (96.0 * v**2)
        + (3.0 * z**7 + 19.0 * z**5 + 17.0 * z**3 - 15.0 * z)
        / (384.0 * v**3)
    )


def confidence_summary(values: list[float]) -> dict[str, float | int]:
    """Return a replication mean and two-sided 95% confidence interval."""

    if len(values) < 2:
        raise ValueError("At least two replications are required.")
    mean = fmean(values)
    sample_standard_deviation = stdev(values)
    standard_error = sample_standard_deviation / len(values) ** 0.5
    half_width = t_critical_95(len(values) - 1) * standard_error
    return {
        "replications": len(values),
        "mean": mean,
        "sample_standard_deviation": sample_standard_deviation,
        "standard_error": standard_error,
        "ci_95_lower": mean - half_width,
        "ci_95_upper": mean + half_width,
        "ci_95_half_width": half_width,
    }


def run_experiment(
    *,
    replications: int,
    warmup_days: int,
    measurement_days: int,
    base_seed: int,
) -> dict:
    if replications < 2:
        raise ValueError("replications must be at least 2")

    config = load_model_inputs()
    output: dict = {
        "design": {
            "replications": replications,
            "warmup_days": warmup_days,
            "measurement_days": measurement_days,
            "confidence_level": 0.95,
            "base_seed": base_seed,
            "profiles": list(PROFILES),
            "scenarios": list(SCENARIOS),
            "common_random_numbers": True,
            "primary_measure": "mean_vehicle_waiting_time_minutes",
        },
        "profiles": {},
    }

    for profile_index, profile in enumerate(PROFILES):
        scenario_records = {scenario: [] for scenario in SCENARIOS}
        profile_seed_offset = profile_index * 1_000_000

        for replication in range(replications):
            seed = base_seed + profile_seed_offset + replication
            for scenario in SCENARIOS:
                result = ChargingSimulation(
                    config,
                    seed=seed,
                    days=measurement_days,
                    warmup_days=warmup_days,
                    profile=profile,
                    scenario=scenario,
                ).run()
                scenario_records[scenario].append(
                    {
                        "seed": seed,
                        "mean_wait": result.mean_vehicle_waiting_time_minutes,
                        "utilisation": result.charger_utilisation_during_measurement,
                        "average_queue": result.time_average_queue_length_during_measurement,
                        "maximum_queue": result.maximum_queue_length_during_measurement,
                        "measured_arrivals": result.vehicles_arrived_during_measurement,
                    }
                )

        summaries = {}
        for scenario in SCENARIOS:
            records = scenario_records[scenario]
            summaries[scenario] = {
                "mean_waiting_time_minutes": confidence_summary(
                    [record["mean_wait"] for record in records]
                ),
                "mean_charger_utilisation": fmean(
                    record["utilisation"] for record in records
                ),
                "mean_time_average_queue_length": fmean(
                    record["average_queue"] for record in records
                ),
                "mean_maximum_queue_length": fmean(
                    record["maximum_queue"] for record in records
                ),
                "mean_measured_arrivals": fmean(
                    record["measured_arrivals"] for record in records
                ),
            }

        comparisons = {}
        baseline_records = scenario_records["baseline"]
        baseline_mean = summaries["baseline"]["mean_waiting_time_minutes"]["mean"]
        for policy in ("capacity", "charge_and_go"):
            differences = [
                baseline["mean_wait"] - treatment["mean_wait"]
                for baseline, treatment in zip(
                    baseline_records, scenario_records[policy]
                )
            ]
            difference_summary = confidence_summary(differences)
            comparisons[policy] = {
                "paired_waiting_time_reduction_minutes": difference_summary,
                "reduction_percentage_of_baseline_mean": (
                    100.0 * difference_summary["mean"] / baseline_mean
                    if baseline_mean >= 0.01
                    else None
                ),
                "replications_with_nonnegative_reduction": sum(
                    difference >= -1e-12 for difference in differences
                ),
            }

        output["profiles"][profile] = {
            "scenario_summaries": summaries,
            "paired_comparisons": comparisons,
        }

    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the formal policy experiment.")
    parser.add_argument("--replications", type=int, default=100)
    parser.add_argument("--warmup-days", type=int, default=7)
    parser.add_argument("--measurement-days", type=int, default=30)
    parser.add_argument("--base-seed", type=int, default=341000)
    parser.add_argument("--json", action="store_true", help="print full JSON")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output = run_experiment(
        replications=args.replications,
        warmup_days=args.warmup_days,
        measurement_days=args.measurement_days,
        base_seed=args.base_seed,
    )

    if args.json:
        print(json.dumps(output, indent=2))
        return

    design = output["design"]
    print("Formal Paired Policy Experiment")
    print(
        f"{design['replications']} replications | {design['warmup_days']} warm-up days | "
        f"{design['measurement_days']} measurement days | 95% confidence intervals"
    )
    for profile in PROFILES:
        profile_output = output["profiles"][profile]
        print(f"\nProfile: {profile}")
        print(
            f"{'Scenario':<16} {'Mean wait':>12} {'95% CI':>25} "
            f"{'Utilisation':>12}"
        )
        for scenario in SCENARIOS:
            summary = profile_output["scenario_summaries"][scenario]
            wait = summary["mean_waiting_time_minutes"]
            print(
                f"{scenario:<16} {wait['mean']:>12.4f} "
                f"[{wait['ci_95_lower']:.4f}, {wait['ci_95_upper']:.4f}]".rjust(25)
                + f" {summary['mean_charger_utilisation']:>11.3%}"
            )
        print("Paired reductions from baseline:")
        for policy in ("capacity", "charge_and_go"):
            comparison = profile_output["paired_comparisons"][policy]
            reduction = comparison["paired_waiting_time_reduction_minutes"]
            print(
                f"  {policy}: {reduction['mean']:.4f} minutes "
                f"(95% CI [{reduction['ci_95_lower']:.4f}, "
                f"{reduction['ci_95_upper']:.4f}])"
            )


if __name__ == "__main__":
    main()
