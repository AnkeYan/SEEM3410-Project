"""Run one matched replication of every approved policy scenario."""

from __future__ import annotations

import argparse
import json

from .ev_charging_sim import ChargingSimulation, load_model_inputs


SCENARIOS = ("baseline", "capacity", "charge_and_go")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run matched baseline and policy scenario demonstrations."
    )
    parser.add_argument("--seed", type=int, default=3410, help="common random seed")
    parser.add_argument("--days", type=int, default=1, help="arrival days")
    parser.add_argument("--warmup-days", type=int, default=0, help="warm-up days")
    parser.add_argument(
        "--profile",
        choices=("planning", "current_benchmark"),
        default="planning",
        help="arrival-demand profile",
    )
    parser.add_argument("--json", action="store_true", help="print JSON output")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_model_inputs()
    results = [
        ChargingSimulation(
            config,
            seed=args.seed,
            days=args.days,
            warmup_days=args.warmup_days,
            profile=args.profile,
            scenario=scenario,
        ).run()
        for scenario in SCENARIOS
    ]

    if args.json:
        print(json.dumps([result.to_dict() for result in results], indent=2))
        return

    print("Matched Policy Demonstration (not final experiment)")
    print(
        f"Common seed: {args.seed} | Profile: {args.profile} | "
        f"Warm-up: {args.warmup_days} | Measurement days: {args.days}"
    )
    print()
    print(
        f"{'Scenario':<16} {'Chargers':>8} {'Arrivals':>9} "
        f"{'Mean wait (min)':>16} {'Utilisation':>12} {'Max queue':>10}"
    )
    for result in results:
        print(
            f"{result.scenario:<16} {result.charger_count:>8} "
            f"{result.vehicles_arrived_during_measurement:>9} "
            f"{result.mean_vehicle_waiting_time_minutes:>16.3f} "
            f"{result.charger_utilisation_during_measurement:>11.3%} "
            f"{result.maximum_queue_length_during_measurement:>10}"
        )


if __name__ == "__main__":
    main()
