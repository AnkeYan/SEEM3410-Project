# Baseline Model Verification and Validation

## Document Status

- Project: SEEM3410 Team Project
- Model: Science Park P2 quick-charging subsystem
- Task: 5 - Baseline verification and validation
- Date: 2026-11-23
- Result: All implemented checks passed

## 1. Purpose

Verification asks whether the program correctly implements the approved model. Validation asks whether the model and its inputs are sufficiently credible for the study purpose.

Passing these checks demonstrates internal consistency and correct implementation. It does not turn synthetic inputs into observed Science Park P2 data.

## 2. Logic Verification

The baseline was initially checked with nine automated tests using Python's standard `unittest` framework. Four policy-integrity tests were added during Task 6, bringing the current total to 13.

| Test | Expected result | Outcome |
|---|---|---|
| Approved capacity | Baseline loads 26 quick chargers | Pass |
| Arrival-profile coverage | Seven periods are contiguous from 00:00 to 24:00 | Pass |
| Expected demand calculation | Planning and benchmark means are 192 and 96 arrivals/day | Pass |
| Seed reproducibility | Identical seeds produce identical complete outputs | Pass |
| Vehicle conservation | Arrivals = charging starts = departures after draining | Pass |
| Empty system | Zero arrivals produce zero waiting, queue and utilisation | Pass |
| Hand-calculated FCFS case | With one charger, arrivals at 0, 2 and 4 minutes and ten-minute service produce waits of 0, 8 and 16 minutes | Pass |
| Simultaneous departure and arrival | A charger released at the arrival instant creates no artificial wait | Pass |
| Congested FCFS order | Vehicles begin service in arrival order | Pass |
| Capacity-policy isolation | Capacity policy uses 27 chargers and retains baseline dwell inputs | Pass |
| Charge-and-go isolation | Charge-and-go retains 26 chargers and uses only the policy dwell distribution | Pass |
| Common random numbers | Corresponding vehicles share arrivals, charging inputs and dwell quantiles across scenarios | Pass |
| Policy-direction check | Neither approved improvement increases waiting in the matched demonstration | Pass |

The hand-calculated case has mean waiting time:

\[
\bar W=\frac{0+8+16}{3}=8\text{ minutes}
\]

The model returned exactly 8 minutes and a maximum queue length of two vehicles.

## 3. Statistical Input Checks

The reproducible statistical validation used 500 one-day planning-profile replications, 200,000 samples from each triangular input distribution and one continuous 120-day benchmark run.

| Quantity | Theoretical target | Observed value | Outcome |
|---|---:|---:|---|
| Planning arrivals/day | 192.000 | 192.388 | Pass |
| Arrival-mean z-score | Approximately within +/-4 | 0.626 | Pass |
| Active charging mean | 51.667 minutes | 51.668 minutes | Pass |
| Baseline dwell mean | 13.333 minutes | 13.341 minutes | Pass |
| Benchmark utilisation | 16.667% | 16.751% | Pass |
| Vehicle conservation | 500/500 replications | 500/500 replications | Pass |

For a Poisson count with mean 192 over 500 replications, the standard error of the sample mean is:

\[
SE=\sqrt{\frac{192}{500}}=0.620
\]

The difference between 192.388 and 192 is only 0.626 standard errors, which is consistent with the specified Poisson process.

## 4. Validation Status

### Supported

- The physical baseline capacity of 26 P2 quick chargers is based on official site-specific data.
- The model boundary, pooled FCFS rule, events and performance measure match the team's approved conceptual model.
- The timing of the morning, midday and evening demand peaks is informed by a Hong Kong public-charging transaction study.
- The benchmark demand profile produces long-run utilisation consistent with the published 10%-20% Hong Kong-wide quick/fast charger range.
- Random inputs reproduce their stated mathematical means.

### Not supported by current data

- The model has not been calibrated against actual P2 arrival timestamps.
- Charging-time and post-charging dwell-time distributions are not fitted from P2 sessions.
- The planning profile is a high-demand policy-testing scenario, not a forecast or observation of current P2 demand.
- Mean waiting-time outputs cannot presently be compared with observed P2 waiting times.

The model therefore has **verified implementation and conditional validity**: its conclusions will be valid under the documented assumptions, but must not be presented as measured P2 performance.

## 5. Reproducing the Checks

Run the logic tests:

```powershell
python -m unittest discover -s tests -v
```

Run the statistical validation:

```powershell
python -m src.validate_model
```

Both commands use fixed seeds and require only the Python standard library.
