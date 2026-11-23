# SEEM3410 Presentation Script

**Topic:** Reducing Waiting at Science Park P2 EV Quick Chargers  
**Target duration:** 10 minutes  
**Slides:** 9  

## Suggested speaker allocation

- **Ngan Yuk Kuen:** Slides 1-3, approximately 3 minutes 10 seconds
- **Jundong Mei:** Slides 4-6, approximately 3 minutes 25 seconds
- **Zhiyuan Han:** Slides 7-9, approximately 3 minutes 25 seconds

The timings below are targets rather than strict limits. The team should rehearse once with a timer and shorten examples before removing model assumptions or limitations.

## Slide 1 - Title and project focus (0:00-0:35)

Good morning. Our project studies the electric-vehicle quick-charging subsystem at Science Park Car Park P2. We use discrete-event simulation to compare two possible ways to reduce vehicle waiting: adding one quick charger, or introducing a charge-and-go policy that reduces the time vehicles occupy a space after charging is complete. Our analysis focuses on one primary performance measure, mean vehicle waiting time. We will first explain the system and the assumptions, then present the experiment, results, sensitivity analysis and recommendation.

## Slide 2 - Decision problem (0:35-1:35)

The Environmental Protection Department database lists 26 quick chargers and one medium charger at P2. We model only the 26 quick chargers because combining charger classes would require connector, power and customer-choice data that are not publicly available. A vehicle begins charging immediately if a quick charger is free. Otherwise, it joins one pooled first-come, first-served queue. Importantly, the charger remains occupied during active charging and any post-charging dwell before the driver leaves.

Our improvement question is deliberately narrow: which policy reduces mean vehicle waiting time more effectively? Policy A increases capacity from 26 to 27 quick chargers. Policy B keeps 26 chargers but reduces post-charging occupation through charge-and-go. Queue length and utilisation are useful diagnostic outputs, but mean waiting time is the only primary performance measure.

## Slide 3 - Evidence and synthetic inputs (1:35-3:10)

The most important modelling principle is to separate observed evidence from synthetic assumptions. The official P2-specific fact is the number of quick chargers: 26. A Hong Kong charging-transaction study informs the morning, midday and evening peak windows. A 2026 government reply reports territory-wide fast or quick public-charger utilisation of approximately 10 to 20 percent. These external sources guide timing and calibration, but they are not observations of P2 demand.

Because P2 transaction records are not publicly available, we generate arrivals, charging times and post-charge dwell times randomly. Within each time block, exponentially distributed interarrival times implement a piecewise Poisson process, which is consistent with the stochastic-arrival methods taught in the course. Active charging follows a triangular distribution with minimum 20, mode 45 and maximum 90 minutes. Baseline dwell follows a triangular distribution with minimum zero, mode 10 and maximum 30 minutes.

The high-demand planning profile has 192 expected arrivals per day. The current benchmark halves all arrival rates to 96 per day and is calibrated to 16.67 percent utilisation, within the published Hong Kong-wide range. We do not claim that either synthetic profile is measured P2 performance.

## Slide 4 - DES model and experiment (3:10-4:25)

The model is a terminating discrete-event simulation. On arrival, a vehicle either starts service or joins the FCFS queue. Charging completion does not release the space because post-charge dwell may follow. Departure releases the charger and immediately starts the first queued vehicle, if one exists. Arrivals stop at the measurement boundary, but the event calendar is drained so every admitted vehicle eventually starts service and contributes a waiting-time observation.

For each demand profile, we run 100 independent replications. Every replication has a seven-day warm-up followed by 30 measured days. Scenario means use 95 percent Student-t confidence intervals. The three policies share one simulation engine, and corresponding vehicles use the same arrivals and random quantiles across policies. This common-random-number design makes the paired comparison more precise. Fifteen automated tests passed, including conservation, FCFS ordering, fixed-seed reproducibility and a hand-calculated queue example.

## Slide 5 - Main planning-demand results (4:25-5:40)

Under the high-demand planning profile, baseline mean waiting is 0.833 minutes. Adding one charger lowers the mean to 0.577 minutes. Charge-and-go lowers it much further, to 0.152 minutes. The confidence intervals shown below the chart are narrow relative to the means.

Using paired differences, adding one charger reduces waiting by 0.256 minutes, or 30.7 percent. Charge-and-go reduces waiting by 0.681 minutes, or 81.7 percent. Both paired 95 percent confidence intervals exclude zero under the planning assumptions.

The mechanism explains the difference. Capacity expansion adds only one server. Charge-and-go releases capacity earlier after every charging session. However, this is a waiting-time comparison, not a benefit-cost analysis. We do not have reliable equipment, installation, enforcement or customer-compliance cost data.

## Slide 6 - Current benchmark versus planning case (5:40-6:35)

The recommendation changes when demand changes. Under the lower current benchmark, baseline waiting is only 0.000319 minute, or about 0.019 second. The paired confidence intervals for both improvements include zero. Therefore, neither policy has a meaningful waiting-time justification at that demand level, and percentage reductions would be misleading because the baseline is almost zero.

Under the high-demand planning case, the differences become operationally visible. The correct conclusion is conditional: if measured P2 demand resembles the benchmark, retain the 26 chargers and collect local data. If it resembles the high-demand case, pilot charge-and-go before installing an additional charger.

## Slide 7 - Sensitivity analysis (6:35-7:45)

Sensitivity analysis shows that congestion grows nonlinearly. At half of planning demand, all three scenarios have essentially zero waiting. At 1.2 times planning demand, baseline waiting rises to 3.09 minutes. Adding a charger reduces it to 2.37 minutes, while charge-and-go reduces it to 0.85 minutes.

We varied demand, active charging time, baseline dwell and charge-and-go dwell one factor at a time. Across 12 unique settings, charge-and-go has lower mean waiting than added capacity in 11 settings. The remaining low-demand setting is a practical tie, and capacity is not preferred in any tested setting. The closest substantive result occurs when baseline dwell is halved, which shows that the benefit of charge-and-go depends strongly on how long vehicles actually remain after charging.

## Slide 8 - Recommendation (7:45-8:55)

We recommend a staged decision. First, collect anonymised P2 timestamps for arrival, charging completion and departure. These three timestamps directly reveal the missing arrival, active-charging and post-charge dwell distributions. Second, refit the model with local empirical inputs. Third, match the action to observed demand.

If demand is low and waiting remains negligible, retain the current 26 chargers. If peak demand and post-charge dwell are both material, pilot charge-and-go. A practical pilot could combine automatic completion notifications, clear signage, a short grace period and an overstay rule. Adding another charger remains a fallback if the pilot is infeasible, customer acceptance is poor or the updated simulation changes the policy ranking.

## Slide 9 - Limitations and conclusion (8:55-10:00)

The main limitation is that P2-specific transaction records are unavailable, so arrivals, charging times and dwell times are synthetic. We also do not model implementation cost, customer compliance, charger failures, reservations, compatibility or grid constraints. The one-factor sensitivity analysis does not test every interaction. For these reasons, the model supports a pilot and further data collection rather than an immediate permanent commitment.

The central takeaway is still clear. Under high demand, improving turnover affects every session and outperforms adding one charger across the tested assumptions. Under demand consistent with the current benchmark, waiting is already negligible and neither intervention is justified by waiting time. Therefore, Science Park should verify local demand and dwell, then choose the least costly policy that achieves the required service level. Thank you.

## Rehearsal checklist

- Keep the distinction between **official data**, **external references** and **synthetic assumptions** explicit.
- Do not describe the planning profile as actual P2 demand.
- State that the result is based on **mean waiting time**, not total cost.
- Explain why charging completion and departure are separate events.
- If time is short, shorten examples and transitions, but retain the limitations and conditional recommendation.
