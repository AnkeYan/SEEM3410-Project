# Input Assumptions and Data Provenance

## Document Status

- Project: SEEM3410 Team Project
- Model: Science Park P2 quick-charging subsystem
- Status: Task 3 input specification
- Date: 2026-11-23
- Machine-readable values: [`config/model_inputs.json`](../config/model_inputs.json)

## 1. Evidence Rule

Each input is labelled as one of the following:

1. **Official site-specific data**: a value directly describing Science Park P2;
2. **External empirical reference**: real-world evidence used to shape an assumption, but not treated as P2 observations;
3. **Synthetic assumption**: a value generated or selected for the simulation because the required P2 data are not publicly available.

Synthetic values are not estimates of actual P2 operations. They define transparent planning scenarios that can later be tested through sensitivity analysis.

## 2. Input Assumptions Table

| Input | Adopted value or model | Status | Reason and evidence |
|---|---:|---|---|
| Baseline quick chargers | 26 | Official site-specific data | September 2026 EPD public EV charger database records 26 quick chargers at Science Park P2. |
| Capacity-policy chargers | 27 | Decision variable | Policy A adds one otherwise identical quick charger. |
| Arrival process | Piecewise Poisson; exponential interarrival times within each period | Synthetic model form | Appropriate for independently occurring arrivals and consistent with the course's Poisson-arrival framework. |
| Time-of-day peak windows | 07:00-09:00, 12:00-14:00 and 19:00-21:00 | External empirical reference | A Hong Kong public-charging transaction study using 2022 data identifies these three intraday load peaks. This supports the timing only, not the P2 arrival rates. |
| Arrival rates | 1.2-22.8 vehicles/hour, depending on period | Synthetic assumption | Rates are calibrated from explicit target utilisation levels under the assumed mean charger occupation time; they are not observed P2 counts. |
| Current-utilisation benchmark | Multiply every planning-profile arrival rate by 0.5 | External benchmark plus synthetic scaling | This produces time-weighted utilisation of 16.67%, within the official territory-wide 10%-20% average for fast or quick public chargers. It is a credibility benchmark, not a P2 estimate. |
| Active charging time | Triangular(20, 45, 90) minutes | Synthetic assumption with external anchor | No P2 session records are public. The bounds and mode reflect variation around Hong Kong technical guidance indicating about 30 minutes for a 50 kW DC quick charger to charge a depleted 16 kWh battery to 80%; actual time varies with vehicle and battery conditions. The assumed mean is 51.67 minutes. |
| Baseline post-charging dwell time | Triangular(0, 10, 30) minutes | Synthetic assumption | No public P2 data report the time from charging completion to vehicle departure. The assumed mean is 13.33 minutes. |
| Charge-and-go dwell time | Triangular(0, 2, 5) minutes | Synthetic policy assumption | Represents prompt departure after notification or enforcement. The assumed mean is 2.33 minutes. |
| Primary output | Mean vehicle waiting time, minutes | Approved project measure | Waiting time equals charging-start time minus arrival time, including zero waits. |
| Diagnostic outputs | Utilisation, time-average queue length, maximum queue length and vehicles served | Model-checking only | These help detect implementation or loading errors but are not primary policy-performance measures. |

## 3. Exact Piecewise Arrival Profile

The simulation uses a Poisson arrival count in every time interval. Equivalently, within a period with rate \(\lambda\), interarrival times are exponentially distributed with mean \(1/\lambda\) hours.

| Period | Time | Planning target utilisation | Planning rate (vehicles/hour) | Current-benchmark rate (vehicles/hour) |
|---|---:|---:|---:|---:|
| Overnight | 00:00-07:00 | 5% | 1.2 | 0.6 |
| Morning peak | 07:00-09:00 | 80% | 19.2 | 9.6 |
| Morning shoulder | 09:00-12:00 | 20% | 4.8 | 2.4 |
| Midday peak | 12:00-14:00 | 85% | 20.4 | 10.2 |
| Afternoon shoulder | 14:00-19:00 | 25% | 6.0 | 3.0 |
| Evening peak | 19:00-21:00 | 95% | 22.8 | 11.4 |
| Late evening | 21:00-24:00 | 20% | 4.8 | 2.4 |

Expected demand is 192 vehicles/day in the planning profile and 96 vehicles/day in the current-utilisation benchmark.

The planning profile is intentionally a high-demand scenario for comparing improvement policies. The benchmark profile checks model behaviour under a load level consistent with the published Hong Kong-wide average. Neither profile is claimed to be measured P2 demand.

## 4. Parameter Derivation

### 4.1 Baseline charger occupation time

The mean active charging time under a triangular distribution is:

\[
E[T_c] = \frac{20+45+90}{3} = 51.67\text{ minutes}
\]

The mean baseline dwell time is:

\[
E[T_d] = \frac{0+10+30}{3} = 13.33\text{ minutes}
\]

Therefore, mean baseline charger occupation is:

\[
E[S] = E[T_c]+E[T_d] = 65\text{ minutes}=1.0833\text{ hours}
\]

With 26 chargers, nominal system capacity is:

\[
\frac{26}{1.0833}=24\text{ vehicles/hour}
\]

For a target utilisation \(\rho\), the synthetic arrival rate is calculated as:

\[
\lambda = \rho \times 24
\]

For example, the evening target of 95% gives \(\lambda=0.95\times24=22.8\) vehicles/hour.

### 4.2 Charge-and-go occupation time

The policy dwell-time mean is:

\[
E[T_{d,\,policy}] = \frac{0+2+5}{3}=2.33\text{ minutes}
\]

The resulting mean occupation time is 54 minutes and the corresponding nominal capacity is 28.89 vehicles/hour. Arrival and active-charging distributions remain unchanged so that the policy comparison is fair.

## 5. What the Computer Randomly Generates

For each replication, the computer will generate:

- arrival times from the piecewise Poisson process;
- one active charging time for every vehicle from the triangular charging distribution;
- one post-charging dwell time for every vehicle from the relevant triangular dwell distribution.

Waiting time, queue length and realised utilisation are outputs calculated from the simulated events. They are not independently generated input data.

## 6. Sources and Limitations

- [Hong Kong Science and Technology Parks Corporation parking information](https://www.hkstp.org/zh-hk/visit/parking): confirms that charging facilities are available but provides no counts or operating records.
- [Environmental Protection Department public EV charger location archive](https://www.epd.gov.hk/epd/tc_chi/environmentinhk/air/promotion_ev/locations_ev_chargers.html): source of the P2 charger count.
- [Electrical and Mechanical Services Department technical guidelines](https://www.emsd.gov.hk/filemanager/en/content_2/EV_guidelines.pdf): gives an illustrative DC quick-charging time and warns that actual time depends on vehicle design and settings.
- [Hong Kong public-charging transaction study](https://repository.hkust.edu.hk/ir/bitstream/1783.1-152584/1/1783.1-152584.pdf): identifies Hong Kong intraday charging-load peaks and documents transaction fields and cleaning rules; its values are not site-specific to P2.
- [Hong Kong Government reply on public charging facilities, 28 October 2026](https://www.info.gov.hk/gia/general/202610/28/P2026102800314p.htm): reports an average 10%-20% utilisation rate for fast or quick public chargers across districts.

The largest limitation is the absence of P2 transaction-level data. If the team later obtains anonymised arrival, charging-completion and departure timestamps, the synthetic distributions should be replaced or fitted using those observations without changing the DES structure.

## 7. Items Reserved for Later Tasks

Task 3 does not decide the warm-up period, replication length, number of replications, random seeds or confidence-interval procedure. Those belong to the experiment-design task and should be selected after the baseline implementation is verified.
