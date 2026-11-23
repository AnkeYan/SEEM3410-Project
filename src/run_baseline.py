"""Command-line runner for one baseline DES replication."""

from __future__ import annotations

import argparse
import json

from .ev_charging_sim import BaselineSimulation, load_model_inputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Science Park P2 baseline charging simulation."
    )
    parser.add_argument("--seed", type=int, default=3410, help="random seed")
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="number of 24-hour arrival days before the system drains",
    )
    parser.add_argument(
        "--warmup-days",
        type=int,
        default=0,
        help="days simulated before measurement begins",
    )
    parser.add_argument(
        "--profile",
        choices=("planning", "current_benchmark"),
        default="planning",
        help="arrival-demand profile",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON instead of a formatted summary",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_model_inputs()
    result = BaselineSimulation(
        config,
        seed=args.seed,
        days=args.days,
        warmup_days=args.warmup_days,
        profile=args.profile,
    ).run()

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("Science Park P2 Baseline DES")
    print(f"Seed: {result.seed}")
    print(f"Scenario: {result.scenario}")
    print(f"Demand profile: {result.profile}")
    print(f"Warm-up days: {result.warmup_days}")
    print(f"Measurement days: {result.measurement_days}")
    print(f"Quick chargers: {result.charger_count}")
    print(f"Total vehicles arrived: {result.vehicles_arrived_total}")
    print(
        "Measurement-period vehicles: "
        f"{result.vehicles_arrived_during_measurement}"
    )
    print(f"Vehicles departed after draining: {result.vehicles_departed_total}")
    print(
        "Mean vehicle waiting time: "
        f"{result.mean_vehicle_waiting_time_minutes:.3f} minutes"
    )
    print(
        "Charger utilisation during arrival horizon: "
        f"{result.charger_utilisation_during_measurement:.3%}"
    )
    print(
        "Time-average queue length during arrival horizon: "
        f"{result.time_average_queue_length_during_measurement:.3f} vehicles"
    )
    print(
        "Maximum queue length: "
        f"{result.maximum_queue_length_during_measurement} vehicles"
    )


if __name__ == "__main__":
    main()
