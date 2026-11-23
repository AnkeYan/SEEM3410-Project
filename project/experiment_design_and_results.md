# Experiment Design and Policy Comparison

## 1. Experimental Design

The formal experiment compares the baseline, capacity and charge-and-go scenarios under matched random inputs.

| Design item | Adopted value |
|---|---:|
| Independent replications | 100 per profile and scenario |
| Warm-up period | 7 days |
| Measurement period | 30 days |
| Confidence level | 95% |
| Base seed | 341000 |
| Variance reduction | Vehicle-level common random numbers |
| Primary measure | Mean vehicle waiting time in minutes |
| Main demand case | High-demand planning profile |
| Context case | Current-utilisation benchmark profile |

The seven-day warm-up allows the initially empty system to reach its recurring daily operating pattern. Warm-up vehicles affect the system state but are excluded from measured performance. All arrivals during the subsequent 30 days are measured, including vehicles that begin service after the arrival horizon closes.

Each replication uses the same seed for all three policies. Corresponding vehicles therefore have the same arrival and active-charging inputs, and the same underlying dwell-time quantile. Paired confidence intervals are calculated from the within-seed waiting-time differences.

## 2. Planning-Profile Results

The planning profile is the synthetic high-demand case used to evaluate policy performance. It is not an estimate of current P2 demand.

| Scenario | Mean waiting time (minutes) | 95% CI | Mean utilisation | Mean time-average queue | Mean maximum queue |
|---|---:|---:|---:|---:|---:|
| Baseline | 0.8329 | [0.7942, 0.8716] | 33.354% | 0.1113 | 13.66 |
| Capacity: 27 chargers | 0.5774 | [0.5460, 0.6088] | 32.119% | 0.0772 | 12.52 |
| Charge-and-go | 0.1523 | [0.1385, 0.1660] | 27.711% | 0.0204 | 8.61 |

Mean measured demand was 5,765.77 vehicles per 30-day replication in every scenario.

### Paired improvements from baseline

| Policy | Mean reduction (minutes) | 95% paired CI | Reduction relative to baseline mean |
|---|---:|---:|---:|
| Capacity | 0.2555 | [0.2474, 0.2636] | 30.68% |
| Charge-and-go | 0.6807 | [0.6539, 0.7074] | 81.72% |

Both paired intervals are entirely above zero. Under the planning assumptions, both policies reduce mean waiting time, but charge-and-go produces the larger reduction.

All planning-profile primary confidence-interval half-widths are below 5% of their corresponding means. The approved 100 replications therefore provide adequate precision and no additional replications were required.

## 3. Current-Benchmark Results

The benchmark profile is scaled to a theoretical time-weighted utilisation of 16.67%, within the published Hong Kong-wide 10%-20% quick/fast charger range.

| Scenario | Mean waiting time (minutes) | 95% CI | Approximate mean wait in seconds | Mean utilisation |
|---|---:|---:|---:|---:|
| Baseline | 0.000319 | [-0.000050, 0.000688] | 0.0191 | 16.677% |
| Capacity: 27 chargers | 0.000098 | [-0.000047, 0.000244] | 0.0059 | 16.060% |
| Charge-and-go | 0.000000 | [0.000000, 0.000000] | 0.0000 | 13.851% |

The small negative lower endpoints are an artefact of the symmetric Student-t interval; actual waiting time cannot be negative and should be interpreted as zero at the physical boundary.

The paired reduction for capacity was 0.000220 minutes with a 95% CI of [-0.000009, 0.000450]. For charge-and-go it was 0.000319 minutes with a 95% CI of [-0.000050, 0.000688]. Both intervals contain zero, and baseline waiting is already only about 0.019 seconds. Percentage reductions are therefore deliberately not reported for this profile because they would exaggerate a practically negligible difference.

## 4. Interpretation

The simulation suggests a demand-dependent decision:

- At demand consistent with the territory-wide current benchmark, the 26-charger system has essentially no queue. Neither improvement is justified by waiting-time reduction alone.
- Under the synthetic high-demand planning profile, both policies reduce waiting. Charge-and-go is more effective than adding one charger because the assumed dwell reduction releases capacity on every charging session rather than adding only one server.

This is a conditional result. Charge-and-go's advantage depends strongly on the assumed baseline and policy dwell-time distributions, neither of which is fitted from P2 observations. The conclusion should be presented as a scenario-based planning insight, not as a measured forecast for Science Park P2.

## 5. Reproduction

Run the full experiment with:

```powershell
python -m src.run_experiment --replications 100 --warmup-days 7 --measurement-days 30 --base-seed 341000
```

The exact machine-readable summary is stored in [`results/experiment_summary.json`](../results/experiment_summary.json).
