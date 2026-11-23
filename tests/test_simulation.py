"""Verification tests for the EV charging discrete-event simulation."""

from __future__ import annotations

from copy import deepcopy
import unittest

from src.ev_charging_sim import (
    BaselineSimulation,
    ChargingSimulation,
    Event,
    EventType,
    Vehicle,
    load_model_inputs,
)


class BaselineSimulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_model_inputs()

    def test_approved_baseline_capacity_is_loaded(self) -> None:
        self.assertEqual(self.config["resources"]["baseline_quick_chargers"], 26)

    def test_arrival_profile_covers_one_contiguous_day(self) -> None:
        periods = self.config["arrival_process"]["planning_profile"]
        self.assertEqual(periods[0]["start_hour"], 0)
        self.assertEqual(periods[-1]["end_hour"], 24)
        for previous, current in zip(periods, periods[1:]):
            self.assertEqual(previous["end_hour"], current["start_hour"])

    def test_profile_has_documented_expected_daily_arrivals(self) -> None:
        periods = self.config["arrival_process"]["planning_profile"]
        calculated = sum(
            (period["end_hour"] - period["start_hour"])
            * period["arrival_rate_vehicles_per_hour"]
            for period in periods
        )
        self.assertAlmostEqual(calculated, 192.0)
        self.assertAlmostEqual(
            calculated * self.config["arrival_process"]["current_benchmark_multiplier"],
            96.0,
        )

    def test_same_seed_reproduces_identical_result(self) -> None:
        first = BaselineSimulation(self.config, seed=3410).run().to_dict()
        second = BaselineSimulation(self.config, seed=3410).run().to_dict()
        self.assertEqual(first, second)

    def test_all_arrivals_eventually_depart(self) -> None:
        result = BaselineSimulation(self.config, seed=9876, days=3).run()
        self.assertEqual(result.vehicles_arrived, result.vehicles_started_charging)
        self.assertEqual(result.vehicles_arrived, result.vehicles_departed)

    def test_zero_arrivals_produces_zero_outputs(self) -> None:
        config = self._deterministic_config(charging_minutes=10.0, dwell_minutes=0.0)
        result = BaselineSimulation(config, seed=1).run()
        self.assertEqual(result.vehicles_arrived, 0)
        self.assertEqual(result.vehicles_departed, 0)
        self.assertEqual(result.mean_vehicle_waiting_time_minutes, 0.0)
        self.assertEqual(result.charger_utilisation_during_arrival_horizon, 0.0)
        self.assertEqual(result.time_average_queue_length_during_arrival_horizon, 0.0)

    def test_hand_calculated_fcfs_waiting_times(self) -> None:
        # One charger, ten-minute deterministic occupation, arrivals at 0, 2,
        # and 4 minutes. Expected waits are 0, 8, and 16 minutes.
        config = self._deterministic_config(charging_minutes=10.0, dwell_minutes=0.0)
        simulation = BaselineSimulation(config, seed=1)
        self._inject_arrivals(simulation, [0.0, 2.0, 4.0])

        result = simulation.run()

        self.assertAlmostEqual(result.mean_vehicle_waiting_time_minutes, 8.0)
        self.assertEqual(result.maximum_queue_length, 2)
        self.assertEqual(
            [simulation.vehicles[i].charging_start_time for i in (1, 2, 3)],
            [0.0, 10.0, 20.0],
        )
        self.assertEqual(result.vehicles_departed, 3)

    def test_departure_at_same_time_prevents_artificial_wait(self) -> None:
        # The first vehicle releases the only charger exactly when the second
        # arrives. Departure must be processed first, so both waits are zero.
        config = self._deterministic_config(charging_minutes=10.0, dwell_minutes=0.0)
        simulation = BaselineSimulation(config, seed=1)
        self._inject_arrivals(simulation, [0.0, 10.0])

        result = simulation.run()

        self.assertAlmostEqual(result.mean_vehicle_waiting_time_minutes, 0.0)
        self.assertEqual(simulation.vehicles[2].charging_start_time, 10.0)

    def test_fcfs_start_order_matches_arrival_order_under_congestion(self) -> None:
        config = self._deterministic_config(charging_minutes=7.0, dwell_minutes=3.0)
        simulation = BaselineSimulation(config, seed=1)
        self._inject_arrivals(simulation, [0.0, 1.0, 2.0, 3.0, 4.0])

        simulation.run()
        starts = [simulation.vehicles[i].charging_start_time for i in range(1, 6)]

        self.assertEqual(starts, sorted(starts))
        self.assertEqual(starts, [0.0, 10.0, 20.0, 30.0, 40.0])

    def test_capacity_policy_uses_27_chargers_and_baseline_dwell(self) -> None:
        baseline = ChargingSimulation(
            self.config, seed=3410, scenario="baseline"
        )
        capacity = ChargingSimulation(
            self.config, seed=3410, scenario="capacity"
        )
        baseline.run()
        capacity_result = capacity.run()

        self.assertEqual(capacity_result.charger_count, 27)
        self.assertEqual(
            baseline.dwell_parameters,
            capacity.dwell_parameters,
        )

    def test_charge_and_go_uses_26_chargers_and_policy_dwell(self) -> None:
        simulation = ChargingSimulation(
            self.config, seed=3410, scenario="charge_and_go"
        )
        result = simulation.run()

        self.assertEqual(result.charger_count, 26)
        self.assertEqual(simulation.dwell_parameters["maximum_minutes"], 5.0)
        self.assertTrue(
            all(
                vehicle.dwell_duration is not None
                and 0.0 <= vehicle.dwell_duration <= 5.0
                for vehicle in simulation.vehicles.values()
            )
        )

    def test_common_random_numbers_match_vehicle_inputs_across_scenarios(self) -> None:
        simulations = {
            scenario: ChargingSimulation(
                self.config, seed=3410, scenario=scenario
            )
            for scenario in ("baseline", "capacity", "charge_and_go")
        }
        for simulation in simulations.values():
            simulation.run()

        baseline = simulations["baseline"]
        for other_name in ("capacity", "charge_and_go"):
            other = simulations[other_name]
            self.assertEqual(baseline.vehicles.keys(), other.vehicles.keys())
            for vehicle_id, baseline_vehicle in baseline.vehicles.items():
                other_vehicle = other.vehicles[vehicle_id]
                self.assertEqual(
                    baseline_vehicle.arrival_time, other_vehicle.arrival_time
                )
                self.assertEqual(
                    baseline_vehicle.charging_random_quantile,
                    other_vehicle.charging_random_quantile,
                )
                self.assertEqual(
                    baseline_vehicle.dwell_random_quantile,
                    other_vehicle.dwell_random_quantile,
                )
                self.assertEqual(
                    baseline_vehicle.charging_duration,
                    other_vehicle.charging_duration,
                )

        for vehicle_id, baseline_vehicle in baseline.vehicles.items():
            self.assertEqual(
                baseline_vehicle.dwell_duration,
                simulations["capacity"].vehicles[vehicle_id].dwell_duration,
            )

    def test_policies_do_not_increase_wait_in_matched_demonstration(self) -> None:
        results = {
            scenario: ChargingSimulation(
                self.config, seed=3410, scenario=scenario
            ).run()
            for scenario in ("baseline", "capacity", "charge_and_go")
        }
        baseline_wait = results["baseline"].mean_vehicle_waiting_time_minutes
        self.assertLessEqual(
            results["capacity"].mean_vehicle_waiting_time_minutes,
            baseline_wait,
        )
        self.assertLessEqual(
            results["charge_and_go"].mean_vehicle_waiting_time_minutes,
            baseline_wait,
        )

    def test_warmup_arrivals_affect_state_but_are_excluded_from_measurement(self) -> None:
        config = self._deterministic_config(charging_minutes=10.0, dwell_minutes=0.0)
        simulation = ChargingSimulation(
            config,
            seed=1,
            days=1,
            warmup_days=1,
            scenario="baseline",
        )
        self._inject_arrivals(simulation, [0.0, 1440.0])

        result = simulation.run()

        self.assertEqual(result.vehicles_arrived_total, 2)
        self.assertEqual(result.vehicles_arrived_during_measurement, 1)
        self.assertEqual(result.mean_vehicle_waiting_time_minutes, 0.0)
        self.assertAlmostEqual(
            result.charger_utilisation_during_measurement,
            10.0 / 1440.0,
        )

    def test_sensitivity_scales_preserve_quantiles_and_scale_durations(self) -> None:
        default = ChargingSimulation(self.config, seed=3410, scenario="baseline")
        scaled = ChargingSimulation(
            self.config,
            seed=3410,
            scenario="baseline",
            charging_time_scale=1.2,
            baseline_dwell_scale=1.5,
        )
        default.run()
        scaled.run()

        for vehicle_id, default_vehicle in default.vehicles.items():
            scaled_vehicle = scaled.vehicles[vehicle_id]
            self.assertEqual(
                default_vehicle.charging_random_quantile,
                scaled_vehicle.charging_random_quantile,
            )
            self.assertEqual(
                default_vehicle.dwell_random_quantile,
                scaled_vehicle.dwell_random_quantile,
            )
            self.assertAlmostEqual(
                scaled_vehicle.charging_duration,
                default_vehicle.charging_duration * 1.2,
            )
            self.assertAlmostEqual(
                scaled_vehicle.dwell_duration,
                default_vehicle.dwell_duration * 1.5,
            )

    @staticmethod
    def _inject_arrivals(
        simulation: BaselineSimulation, arrival_times: list[float]
    ) -> None:
        for vehicle_id, arrival_time in enumerate(arrival_times, start=1):
            simulation.vehicles[vehicle_id] = Vehicle(vehicle_id, arrival_time)
            simulation._schedule(
                Event(arrival_time, EventType.ARRIVAL, vehicle_id)
            )

    def _deterministic_config(
        self, *, charging_minutes: float, dwell_minutes: float
    ) -> dict:
        config = deepcopy(self.config)
        config["resources"]["baseline_quick_chargers"] = 1
        for period in config["arrival_process"]["planning_profile"]:
            period["arrival_rate_vehicles_per_hour"] = 0.0
        config["active_charging_time"].update(
            {
                "minimum_minutes": charging_minutes,
                "mode_minutes": charging_minutes,
                "maximum_minutes": charging_minutes,
            }
        )
        config["post_charging_dwell_time"]["baseline"].update(
            {
                "minimum_minutes": dwell_minutes,
                "mode_minutes": dwell_minutes,
                "maximum_minutes": dwell_minutes,
            }
        )
        return config


if __name__ == "__main__":
    unittest.main()
