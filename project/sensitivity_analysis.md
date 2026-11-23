# Sensitivity Analysis

## 1. Purpose and Design

The main experiment relies on synthetic demand, active-charging and dwell-time inputs. This analysis tests whether the policy ranking changes when those assumptions are varied.

The analysis uses a one-factor-at-a-time design under the planning profile. Each unique setting uses 50 paired replications, a seven-day warm-up, a 30-day measurement period and common random numbers. All non-tested inputs remain at their base values.

| Factor | Tested levels |
|---|---|
| Demand multiplier | 0.50, 0.75, 1.00, 1.10, 1.20 |
| Active charging-time scale | 0.80, 1.00, 1.20 |
| Baseline dwell-time scale | 0.50, 1.00, 1.50, 2.00 |
| Charge-and-go dwell-time scale | 1.00, 2.00, 3.00 |

A difference smaller than 0.01 minute is classified as a practical tie. The repeated base level is computed once, giving 12 unique settings.

## 2. Demand Sensitivity

| Demand multiplier | Baseline wait | Capacity wait | Charge-and-go wait | Lower-wait policy |
|---:|---:|---:|---:|---|
| 0.50 | 0.0001 | 0.0000 | 0.0000 | Practical tie |
| 0.75 | 0.0514 | 0.0294 | 0.0052 | Charge-and-go |
| 1.00 | 0.8221 | 0.5745 | 0.1607 | Charge-and-go |
| 1.10 | 1.6739 | 1.2250 | 0.3748 | Charge-and-go |
| 1.20 | 3.0854 | 2.3657 | 0.8467 | Charge-and-go |

Waiting increases nonlinearly as demand approaches the system's peak capacity. At half demand, both policies are practically irrelevant because the baseline already has almost no queue. At higher demand, charge-and-go has the lower mean waiting time.

## 3. Active Charging-Time Sensitivity

| Charging-time scale | Baseline wait | Capacity wait | Charge-and-go wait | Charge-and-go advantage over capacity |
|---:|---:|---:|---:|---:|
| 0.80 | 0.1851 | 0.1173 | 0.0157 | 0.1016 |
| 1.00 | 0.8221 | 0.5745 | 0.1607 | 0.4138 |
| 1.20 | 2.2629 | 1.6995 | 0.7402 | 0.9593 |

Longer active charging sharply increases congestion. Charge-and-go remains the lower-wait policy at all three charging-time levels, although it cannot remove congestion caused by active charging itself.

## 4. Baseline Dwell-Time Sensitivity

| Baseline dwell scale | Baseline wait | Capacity wait | Charge-and-go wait | Charge-and-go advantage over capacity |
|---:|---:|---:|---:|---:|
| 0.50 | 0.3323 | 0.2186 | 0.1607 | 0.0579 |
| 1.00 | 0.8221 | 0.5745 | 0.1607 | 0.4138 |
| 1.50 | 1.6560 | 1.2154 | 0.1607 | 1.0547 |
| 2.00 | 2.8598 | 2.1879 | 0.1607 | 2.0272 |

This is the most important uncertainty for interpreting charge-and-go. When actual baseline dwell is only half the assumed value, charge-and-go still has lower waiting, but its advantage over capacity narrows to 0.0579 minute, about 3.5 seconds. Its benefit grows substantially when baseline post-charging occupation is longer.

## 5. Charge-and-Go Effectiveness Sensitivity

The base policy dwell mean is 2.33 minutes. Scales of two and three increase it to approximately 4.67 and 7.00 minutes.

| Policy dwell scale | Baseline wait | Capacity wait | Charge-and-go wait | Charge-and-go advantage over capacity |
|---:|---:|---:|---:|---:|
| 1.00 | 0.8221 | 0.5745 | 0.1607 | 0.4138 |
| 2.00 | 0.8221 | 0.5745 | 0.2415 | 0.3330 |
| 3.00 | 0.8221 | 0.5745 | 0.3498 | 0.2246 |

Even when charge-and-go dwell is three times the base policy assumption, it retains lower mean waiting than adding one charger. Its advantage decreases as compliance becomes weaker.

## 6. Robustness Conclusion

Across 12 unique settings:

- Charge-and-go has lower mean waiting than capacity in 11 settings;
- Capacity has lower mean waiting in zero settings;
- One setting, the 0.50 demand multiplier, is a practical tie because both policies produce essentially zero waiting.

The policy ranking is therefore robust across the tested one-factor ranges. The conclusion remains conditional: the analysis does not examine all possible interactions among demand, charging time and dwell behaviour. More importantly, the uncertain P2 dwell-time data determine how large the practical advantage is, even though the ranking did not reverse in the tested ranges.

## 7. Reproduction

```powershell
python -m src.run_sensitivity --replications 50 --warmup-days 7 --measurement-days 30 --base-seed 841000
```

The compact machine-readable results are stored in [`results/sensitivity_summary.json`](../results/sensitivity_summary.json).
