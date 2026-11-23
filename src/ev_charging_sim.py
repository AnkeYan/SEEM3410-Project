"""Baseline discrete-event simulation for Science Park P2 quick charging.

The model uses only the Python standard library. All numerical assumptions are
loaded from ``config/model_inputs.json`` so that the documented input table and
the executable model cannot silently diverge.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from enum import Enum
import heapq
import json
from pathlib import Path
import random
from typing import Any, Deque


MINUTES_PER_HOUR = 60.0
MINUTES_PER_DAY = 24.0 * MINUTES_PER_HOUR


class EventType(str, Enum):
    """Events that can change the state of the charging system."""

    DEPARTURE = "departure"
    CHARGING_COMPLETE = "charging_complete"
    ARRIVAL = "arrival"


# When two events have exactly the same timestamp, a departure releases its
# charger before a new arrival is handled. This convention avoids an artificial
# wait caused solely by event ordering.
EVENT_PRIORITY = {
    EventType.DEPARTURE: 0,
    EventType.CHARGING_COMPLETE: 1,
    EventType.ARRIVAL: 2,
}


@dataclass(frozen=True)
class Event:
    """A scheduled model event."""

    time: float
    event_type: EventType
    vehicle_id: int


@dataclass
class Vehicle:
    """State retained for each simulated vehicle."""

    vehicle_id: int
    arrival_time: float
    charging_random_quantile: float | None = None
    dwell_random_quantile: float | None = None
    charging_duration: float | None = None
    dwell_duration: float | None = None
    charging_start_time: float | None = None
    charging_end_time: float | None = None
    departure_time: float | None = None


@dataclass(frozen=True)
class SimulationResult:
    """Summary statistics from one scenario replication."""

    seed: int
    scenario: str
    profile: str
    warmup_days: int
    measurement_days: int
    simulated_arrival_days: int
    arrival_horizon_minutes: float
    measurement_start_minutes: float
    measurement_horizon_minutes: float
    drain_end_time_minutes: float
    charger_count: int
    vehicles_arrived_total: int
    vehicles_arrived_during_measurement: int
    vehicles_started_charging_total: int
    vehicles_departed_total: int
    mean_vehicle_waiting_time_minutes: float
    charger_utilisation_during_measurement: float
    time_average_queue_length_during_measurement: float
    maximum_queue_length_during_measurement: int

    def to_dict(self) -> dict[str, int | float | str]:
        return asdict(self)

    # Compatibility aliases retained for the one-day demonstration and older
    # checks. Formal experiments should use the explicitly named fields above.
    @property
    def vehicles_arrived(self) -> int:
        return self.vehicles_arrived_total

    @property
    def vehicles_started_charging(self) -> int:
        return self.vehicles_started_charging_total

    @property
    def vehicles_departed(self) -> int:
        return self.vehicles_departed_total

    @property
    def charger_utilisation_during_arrival_horizon(self) -> float:
        return self.charger_utilisation_during_measurement

    @property
    def time_average_queue_length_during_arrival_horizon(self) -> float:
        return self.time_average_queue_length_during_measurement

    @property
    def maximum_queue_length(self) -> int:
        return self.maximum_queue_length_during_measurement


def load_model_inputs(path: str | Path | None = None) -> dict[str, Any]:
    """Load and minimally validate the approved model-input file."""

    if path is None:
        path = Path(__file__).resolve().parents[1] / "config" / "model_inputs.json"
    path = Path(path)
    with path.open("r", encoding="utf-8") as file:
        config: dict[str, Any] = json.load(file)

    required_sections = {
        "resources",
        "arrival_process",
        "active_charging_time",
        "post_charging_dwell_time",
    }
    missing = required_sections.difference(config)
    if missing:
        raise ValueError(f"Missing required configuration sections: {sorted(missing)}")

    periods = config["arrival_process"]["planning_profile"]
    if not periods:
        raise ValueError("The arrival profile must contain at least one period.")
    if float(periods[0]["start_hour"]) != 0.0 or float(periods[-1]["end_hour"]) != 24.0:
        raise ValueError("The arrival profile must cover the full 24-hour day.")
    for previous, current in zip(periods, periods[1:]):
        if float(previous["end_hour"]) != float(current["start_hour"]):
            raise ValueError("Arrival-profile periods must be contiguous.")

    return config


class ChargingSimulation:
    """One replication of an approved FCFS charging scenario."""

    def __init__(
        self,
        config: dict[str, Any],
        *,
        seed: int = 3410,
        days: int = 1,
        warmup_days: int = 0,
        profile: str = "planning",
        scenario: str = "baseline",
        arrival_rate_multiplier: float = 1.0,
        charging_time_scale: float = 1.0,
        baseline_dwell_scale: float = 1.0,
        policy_dwell_scale: float = 1.0,
    ) -> None:
        if days < 1:
            raise ValueError("days must be at least 1")
        if warmup_days < 0:
            raise ValueError("warmup_days cannot be negative")
        if profile not in {"planning", "current_benchmark"}:
            raise ValueError("profile must be 'planning' or 'current_benchmark'")
        if scenario not in {"baseline", "capacity", "charge_and_go"}:
            raise ValueError(
                "scenario must be 'baseline', 'capacity', or 'charge_and_go'"
            )
        scale_values = {
            "arrival_rate_multiplier": arrival_rate_multiplier,
            "charging_time_scale": charging_time_scale,
            "baseline_dwell_scale": baseline_dwell_scale,
            "policy_dwell_scale": policy_dwell_scale,
        }
        for name, value in scale_values.items():
            if value <= 0.0:
                raise ValueError(f"{name} must be positive")

        self.config = config
        self.seed = seed
        self.days = days
        self.warmup_days = warmup_days
        self.total_arrival_days = warmup_days + days
        self.profile = profile
        self.scenario = scenario
        self.arrival_rate_multiplier = arrival_rate_multiplier
        self.charging_time_scale = charging_time_scale
        self.baseline_dwell_scale = baseline_dwell_scale
        self.policy_dwell_scale = policy_dwell_scale
        if scenario == "capacity":
            self.charger_count = int(
                config["resources"]["capacity_policy_quick_chargers"]
            )
        else:
            self.charger_count = int(config["resources"]["baseline_quick_chargers"])

        self.dwell_parameters = config["post_charging_dwell_time"][
            "charge_and_go_policy" if scenario == "charge_and_go" else "baseline"
        ]
        self.measurement_start = warmup_days * MINUTES_PER_DAY
        self.measurement_horizon = days * MINUTES_PER_DAY
        self.measurement_end = self.measurement_start + self.measurement_horizon
        self.arrival_horizon = self.total_arrival_days * MINUTES_PER_DAY

        # Separate streams make later common-random-number policy comparisons
        # easier and stop one input process from changing another by accident.
        self.arrival_rng = random.Random(seed)
        self.charging_rng = random.Random(seed + 1_000_003)
        self.dwell_rng = random.Random(seed + 2_000_003)

        self.event_calendar: list[tuple[float, int, int, Event]] = []
        self.event_sequence = 0
        self.vehicles: dict[int, Vehicle] = {}
        self.waiting_queue: Deque[int] = deque()
        self.busy_chargers = 0

        self.clock = 0.0
        self.last_event_time = 0.0
        self.busy_charger_time_within_measurement = 0.0
        self.queue_time_within_measurement = 0.0
        self.maximum_queue_length_during_measurement = 0
        self.measurement_waiting_times: list[float] = []
        self.total_starts = 0
        self.departures = 0

    def run(self) -> SimulationResult:
        """Generate arrivals, process all events, and drain the final queue."""

        self._schedule_all_arrivals()

        while self.event_calendar:
            _, _, _, event = heapq.heappop(self.event_calendar)
            self._integrate_time_averages(event.time)
            self.clock = event.time

            if event.event_type is EventType.ARRIVAL:
                self._handle_arrival(event)
            elif event.event_type is EventType.CHARGING_COMPLETE:
                self._handle_charging_complete(event)
            elif event.event_type is EventType.DEPARTURE:
                self._handle_departure(event)
            else:  # pragma: no cover - defensive guard for future event types
                raise RuntimeError(f"Unsupported event type: {event.event_type}")

        if self.busy_chargers != 0 or self.waiting_queue:
            raise RuntimeError("The event calendar ended before the system drained.")

        arrivals = len(self.vehicles)
        measured_arrivals = sum(
            self.measurement_start <= vehicle.arrival_time < self.measurement_end
            for vehicle in self.vehicles.values()
        )
        measured_starts = len(self.measurement_waiting_times)
        if measured_starts != measured_arrivals:
            raise RuntimeError("Not every measurement-period arrival received service.")
        mean_wait = (
            sum(self.measurement_waiting_times) / measured_starts
            if measured_starts
            else 0.0
        )
        utilisation_denominator = self.charger_count * self.measurement_horizon

        return SimulationResult(
            seed=self.seed,
            scenario=self.scenario,
            profile=self.profile,
            warmup_days=self.warmup_days,
            measurement_days=self.days,
            simulated_arrival_days=self.total_arrival_days,
            arrival_horizon_minutes=self.arrival_horizon,
            measurement_start_minutes=self.measurement_start,
            measurement_horizon_minutes=self.measurement_horizon,
            drain_end_time_minutes=self.clock,
            charger_count=self.charger_count,
            vehicles_arrived_total=arrivals,
            vehicles_arrived_during_measurement=measured_arrivals,
            vehicles_started_charging_total=self.total_starts,
            vehicles_departed_total=self.departures,
            mean_vehicle_waiting_time_minutes=mean_wait,
            charger_utilisation_during_measurement=(
                self.busy_charger_time_within_measurement / utilisation_denominator
            ),
            time_average_queue_length_during_measurement=(
                self.queue_time_within_measurement / self.measurement_horizon
            ),
            maximum_queue_length_during_measurement=(
                self.maximum_queue_length_during_measurement
            ),
        )

    def _schedule_all_arrivals(self) -> None:
        periods = self.config["arrival_process"]["planning_profile"]
        multiplier = 1.0
        if self.profile == "current_benchmark":
            multiplier = float(
                self.config["arrival_process"]["current_benchmark_multiplier"]
            )

        next_vehicle_id = 1
        for day in range(self.total_arrival_days):
            day_offset = day * MINUTES_PER_DAY
            for period in periods:
                period_start = day_offset + float(period["start_hour"]) * MINUTES_PER_HOUR
                period_end = day_offset + float(period["end_hour"]) * MINUTES_PER_HOUR
                hourly_rate = float(period["arrival_rate_vehicles_per_hour"]) * multiplier
                hourly_rate *= self.arrival_rate_multiplier
                if hourly_rate <= 0.0:
                    continue

                time = period_start
                rate_per_minute = hourly_rate / MINUTES_PER_HOUR
                while True:
                    time += self.arrival_rng.expovariate(rate_per_minute)
                    if time >= period_end:
                        break
                    vehicle = Vehicle(next_vehicle_id, time)
                    self._assign_vehicle_random_inputs(vehicle)
                    self.vehicles[next_vehicle_id] = vehicle
                    self._schedule(Event(time, EventType.ARRIVAL, next_vehicle_id))
                    next_vehicle_id += 1

    def _schedule(self, event: Event) -> None:
        self.event_sequence += 1
        heapq.heappush(
            self.event_calendar,
            (
                event.time,
                EVENT_PRIORITY[event.event_type],
                self.event_sequence,
                event,
            ),
        )

    def _integrate_time_averages(self, next_time: float) -> None:
        if next_time < self.last_event_time:
            raise RuntimeError("Event times moved backwards.")

        interval_start = max(self.last_event_time, self.measurement_start)
        interval_end = min(next_time, self.measurement_end)
        elapsed_within_measurement = max(0.0, interval_end - interval_start)
        self.busy_charger_time_within_measurement += (
            self.busy_chargers * elapsed_within_measurement
        )
        self.queue_time_within_measurement += (
            len(self.waiting_queue) * elapsed_within_measurement
        )
        if elapsed_within_measurement > 0.0:
            self.maximum_queue_length_during_measurement = max(
                self.maximum_queue_length_during_measurement,
                len(self.waiting_queue),
            )
        self.last_event_time = next_time

    def _handle_arrival(self, event: Event) -> None:
        if self.busy_chargers < self.charger_count:
            self._start_charging(event.vehicle_id)
        else:
            self.waiting_queue.append(event.vehicle_id)
            if self.measurement_start <= self.clock < self.measurement_end:
                self.maximum_queue_length_during_measurement = max(
                    self.maximum_queue_length_during_measurement,
                    len(self.waiting_queue),
                )

    def _start_charging(self, vehicle_id: int) -> None:
        vehicle = self.vehicles[vehicle_id]
        self._assign_vehicle_random_inputs(vehicle)
        vehicle.charging_start_time = self.clock
        waiting_time = self.clock - vehicle.arrival_time
        if waiting_time < -1e-9:
            raise RuntimeError("A vehicle started charging before it arrived.")
        self.total_starts += 1
        if self.measurement_start <= vehicle.arrival_time < self.measurement_end:
            self.measurement_waiting_times.append(max(0.0, waiting_time))
        self.busy_chargers += 1
        if self.busy_chargers > self.charger_count:
            raise RuntimeError("Busy charger count exceeded installed capacity.")

        if vehicle.charging_duration is None:  # defensive type narrowing
            raise RuntimeError("Vehicle charging duration was not generated.")
        charging_time = vehicle.charging_duration
        vehicle.charging_end_time = self.clock + charging_time
        self._schedule(
            Event(vehicle.charging_end_time, EventType.CHARGING_COMPLETE, vehicle_id)
        )

    def _handle_charging_complete(self, event: Event) -> None:
        vehicle = self.vehicles[event.vehicle_id]
        self._assign_vehicle_random_inputs(vehicle)
        if vehicle.dwell_duration is None:  # defensive type narrowing
            raise RuntimeError("Vehicle dwell duration was not generated.")
        dwell_time = vehicle.dwell_duration
        vehicle.departure_time = self.clock + dwell_time
        self._schedule(
            Event(vehicle.departure_time, EventType.DEPARTURE, event.vehicle_id)
        )

    def _handle_departure(self, event: Event) -> None:
        self.departures += 1
        self.busy_chargers -= 1
        if self.busy_chargers < 0:
            raise RuntimeError("Busy charger count became negative.")

        if self.waiting_queue:
            next_vehicle_id = self.waiting_queue.popleft()
            self._start_charging(next_vehicle_id)

    def _assign_vehicle_random_inputs(self, vehicle: Vehicle) -> None:
        """Assign inputs once, preserving vehicle-level common random numbers."""

        if vehicle.charging_random_quantile is None:
            vehicle.charging_random_quantile = self.charging_rng.random()
        if vehicle.dwell_random_quantile is None:
            vehicle.dwell_random_quantile = self.dwell_rng.random()
        if vehicle.charging_duration is None:
            vehicle.charging_duration = (
                self._triangular_inverse_cdf(
                    self.config["active_charging_time"],
                    vehicle.charging_random_quantile,
                )
                * self.charging_time_scale
            )
        if vehicle.dwell_duration is None:
            dwell_scale = (
                self.policy_dwell_scale
                if self.scenario == "charge_and_go"
                else self.baseline_dwell_scale
            )
            vehicle.dwell_duration = (
                self._triangular_inverse_cdf(
                    self.dwell_parameters,
                    vehicle.dwell_random_quantile,
                )
                * dwell_scale
            )

    @staticmethod
    def _triangular_inverse_cdf(parameters: dict[str, Any], quantile: float) -> float:
        minimum = float(parameters["minimum_minutes"])
        mode = float(parameters["mode_minutes"])
        maximum = float(parameters["maximum_minutes"])
        if not minimum <= mode <= maximum:
            raise ValueError("Triangular parameters must satisfy minimum <= mode <= maximum")
        if not 0.0 <= quantile <= 1.0:
            raise ValueError("quantile must be between zero and one")
        if minimum == maximum:
            return minimum

        mode_fraction = (mode - minimum) / (maximum - minimum)
        if quantile < mode_fraction:
            return minimum + (
                quantile * (maximum - minimum) * (mode - minimum)
            ) ** 0.5
        return maximum - (
            (1.0 - quantile) * (maximum - minimum) * (maximum - mode)
        ) ** 0.5


class BaselineSimulation(ChargingSimulation):
    """Backward-compatible convenience class for the baseline scenario."""

    def __init__(
        self,
        config: dict[str, Any],
        *,
        seed: int = 3410,
        days: int = 1,
        warmup_days: int = 0,
        profile: str = "planning",
    ) -> None:
        super().__init__(
            config,
            seed=seed,
            days=days,
            warmup_days=warmup_days,
            profile=profile,
            scenario="baseline",
        )
