# SEEM3410 Team Project

## Team

- Ngan Yuk Kuen - 1155212758
- Jundong Mei - 1155174217
- Zhiyuan Han - 1155176066

## Project Topic

Discrete-event simulation of the quick-charging subsystem at Science Park Car Park P2.

The project compares policies for reducing mean vehicle waiting time under stochastic vehicle arrivals.

## Current Approved Scope

- System: Science Park Car Park P2 quick-charging subsystem
- Baseline resources: 26 identical quick chargers
- Queue: one pooled first-come, first-served queue
- Primary performance measure: mean vehicle waiting time
- Policy A: increase capacity from 26 to 27 quick chargers
- Policy B: reduce post-charging dwell time through a charge-and-go policy
- Random inputs: vehicle interarrival time, active charging time and post-charging dwell time
- Excluded from the initial model: medium charger, queue abandonment, reservations, charger failures, dynamic pricing and grid constraints

Detailed scope: [Model Scope and Assumptions](project/model_scope_and_assumptions.md)

## Work Plan

| Task | Description | Status |
|---|---|---|
| 0 | Review HKSTP and EPD data feasibility | Complete |
| 1 | Confirm model scope, system boundary and policies | Complete |
| 2 | Revise the earlier proposal | Skipped - no second proposal submission required |
| 3 | Define input distributions, parameters, time periods and assumptions table | Complete |
| 4 | Implement the baseline Python discrete-event simulation | Complete |
| 5 | Verify and validate the baseline model | Complete |
| 6 | Implement the capacity and charge-and-go policies | Complete |
| 7 | Finalise experiment design and run policy comparisons | Complete |
| 8 | Perform sensitivity analysis | Complete |
| 9 | Produce report figures, tables, discussion and policy brief | Complete |
| 10 | Complete the reproducibility package, final PDF and presentation | Complete |

Input specification: [Input Assumptions and Data Provenance](project/input_assumptions.md)

Verification record: [Baseline Model Verification and Validation](project/verification_and_validation.md)

Formal experiment: [Experiment Design and Policy Comparison](project/experiment_design_and_results.md)

Sensitivity analysis: [Sensitivity Analysis](project/sensitivity_analysis.md)

Report draft: [English Report Draft](report/report_draft.md)

Final report: [Eight-page PDF](output/pdf/SEEM3410_EV_Charging_Report.pdf)

Presentation script: [Ten-minute English Script](presentation/presentation_script.md)

Presentation previews: [Nine reviewed slide images](presentation/slides)

Reproducibility package: [GitHub Sharing ZIP](output/package/SEEM3410_EV_Charging_Reproducibility.zip)

## Progress Log

### 2026-11-23 - Task 0 completed

- Reviewed the HKSTP parking page and the September 2026 EPD public EV charger database.
- Confirmed that the HKSTP page establishes the existence of EV charging facilities but does not provide charger counts or operational demand data.
- Confirmed the EPD records for Science Park P2: one medium charger and 26 quick chargers.
- Determined that EPD data can define physical capacity but not arrival, charging-time or dwell-time distributions.

### 2026-11-23 - Task 1 completed

- Limited the model boundary to the 26 quick chargers at Science Park P2.
- Excluded the single medium charger to avoid unnecessary charger-class and compatibility logic.
- Fixed one pooled first-come, first-served queue as an operating rule rather than a decision lever.
- Confirmed mean vehicle waiting time as the only primary performance measure.
- Defined the baseline, capacity policy and charge-and-go policy.
- Identified interarrival time, charging time and post-charging dwell time as random inputs.
- Documented all current inclusions, exclusions and unresolved decisions in `project/model_scope_and_assumptions.md`.

### 2026-11-23 - Task 2 skipped

- Decided not to rewrite the earlier proposal because no second proposal will be submitted.
- The approved model specification supersedes the earlier proposal for implementation purposes.
- Skipping this task reduces duplicated work without affecting the simulation, experiments or final report.

### 2026-11-23 - Task 3 completed

- Classified every model input as official site-specific data, an external empirical reference or a synthetic assumption.
- Retained the official P2 baseline capacity of 26 quick chargers and the capacity-policy value of 27.
- Defined piecewise Poisson arrivals with exponentially distributed interarrival times and Hong Kong-informed morning, midday and evening peak periods.
- Created a transparent high-demand planning profile with 192 expected arrivals per day and a 0.5-times benchmark profile with 96 expected arrivals per day.
- Calibrated the benchmark profile to 16.67% time-weighted utilisation, within the published Hong Kong-wide 10%-20% average for fast or quick public chargers; this is not represented as a P2 observation.
- Defined synthetic triangular active-charging and post-charging dwell-time distributions because P2 transaction records are not publicly available.
- Recorded every exact parameter and derived value in `config/model_inputs.json` and documented the evidence and limitations in `project/input_assumptions.md`.
- Kept mean vehicle waiting time as the only primary performance measure; utilisation and queue statistics remain diagnostic outputs only.

### 2026-11-23 - Task 4 completed

- Implemented a standard-library Python discrete-event simulation for the approved 26-charger baseline.
- Modelled vehicle arrival, charging completion and vehicle departure as separate time-ordered events.
- Implemented one pooled first-come, first-served queue and retained the charger throughout active charging and post-charging dwell time.
- Loaded all numerical inputs from `config/model_inputs.json`; no duplicate model parameters are hard-coded in the simulation.
- Added separate seeded random-number streams for arrivals, charging times and dwell times to support reproducibility and later common-random-number comparisons.
- Added both the high-demand planning profile and the current-utilisation benchmark as selectable demand inputs; neither changes the baseline operating policy.
- Added mean vehicle waiting time as the primary output and utilisation, queue length and throughput as diagnostic outputs.
- Allowed arrivals to stop at the selected horizon and then drained the system so every admitted vehicle receives service and contributes a waiting-time observation.
- Completed one-day smoke runs with seed 3410: the planning profile generated 189 arrivals, all 189 departed, and mean waiting time was 1.804 minutes; the benchmark profile generated 91 arrivals, all 91 departed, and mean waiting time was zero. These were implementation checks before the Task 6 vehicle-level common-random-number refactor, not final experimental estimates.

### 2026-11-23 - Task 5 completed

- Added nine automated logic tests covering configuration, reproducibility, vehicle conservation, an empty system, a hand-calculated queue, simultaneous events and FCFS ordering.
- Confirmed the hand-calculated one-charger example returns waiting times of 0, 8 and 16 minutes and the correct 8-minute mean.
- Ran 500 planning-profile replications; all replications conserved vehicles and the observed mean arrival count was 192.388 against the theoretical value of 192.
- Drew 200,000 samples from each baseline triangular input; the observed charging and dwell means were 51.668 and 13.341 minutes against theoretical values of 51.667 and 13.333 minutes.
- Ran a 120-day current-benchmark simulation; realised utilisation was 16.751% against the 16.667% target.
- Recorded all evidence, commands and validation limitations in `project/verification_and_validation.md`.
- Classified the result as verified implementation with conditional validity: conclusions apply under the documented assumptions and are not measured P2 performance.

### 2026-11-23 - Task 6 completed

- Refactored the model so the baseline, capacity and charge-and-go scenarios use one shared simulation engine rather than duplicated code.
- Implemented the capacity policy with 27 quick chargers while retaining the baseline arrival, charging and dwell inputs.
- Implemented charge-and-go with 26 quick chargers and the approved Triangular(0, 2, 5) minute dwell distribution while retaining baseline arrivals and active charging.
- Assigned every vehicle the same arrival time, active-charging random quantile and dwell random quantile across scenarios. This establishes vehicle-level common random numbers for fair paired comparisons.
- Expanded the automated suite from nine to 13 tests; all tests and the existing statistical validation passed after the refactor.
- Added a matched-scenario runner for technical demonstrations. With seed 3410 and one planning-profile day, illustrative mean waits were 1.839 minutes for baseline, 1.295 for capacity and 0.232 for charge-and-go.
- Did not implement the optional combined policy because it is outside the currently approved core comparison.
- Did not treat the one-day demonstration as a formal experiment or policy conclusion; run length, warm-up, replications and confidence intervals remain Task 7 decisions.

### 2026-11-23 - Task 7 completed

- Implemented a seven-day warm-up followed by a 30-day measurement period; warm-up vehicles affect state but are excluded from performance estimates.
- Ran 100 independent paired replications for the planning and current-benchmark profiles using vehicle-level common random numbers across all policies.
- Calculated Student-t 95% confidence intervals for scenario means and paired policy reductions.
- Under the planning profile, baseline mean waiting was 0.8329 minutes, capacity was 0.5774 and charge-and-go was 0.1523.
- Planning-profile capacity reduced mean waiting by 0.2555 minutes or 30.68% with paired 95% CI [0.2474, 0.2636].
- Planning-profile charge-and-go reduced mean waiting by 0.6807 minutes or 81.72% with paired 95% CI [0.6539, 0.7074].
- All planning-profile primary interval half-widths were below 5% of their means, so the approved 100 replications were sufficiently precise.
- Under the current benchmark, baseline mean waiting was approximately 0.019 seconds and both paired improvement intervals contained zero; no practical waiting-time benefit was established.
- Suppressed percentage-improvement reporting for the current benchmark because division by an almost-zero baseline would be misleading.
- Stored exact numerical results in `results/experiment_summary.json` and interpretation in `project/experiment_design_and_results.md`.

### 2026-11-23 - Task 8 completed

- Implemented a one-factor-at-a-time sensitivity analysis for demand, active charging time, baseline dwell time and charge-and-go dwell time.
- Evaluated 12 unique settings using 50 paired replications, seven warm-up days, 30 measurement days and common random numbers.
- Defined differences below 0.01 minute as practical ties so negligible low-demand differences are not presented as policy wins.
- Found charge-and-go had lower mean waiting than capacity in 11 settings, capacity won in zero settings and the 0.50 demand case was a practical tie.
- Confirmed congestion increases nonlinearly with demand and active charging time.
- Found baseline dwell time is the most important assumption for the size of the charge-and-go advantage; halving baseline dwell narrows its advantage over capacity to 0.0579 minute.
- Confirmed charge-and-go retains lower waiting even when its policy dwell mean is tripled from 2.33 to approximately 7.00 minutes.
- Documented the one-factor-at-a-time limitation: untested interactions could still affect the result.
- Stored compact exact results in `results/sensitivity_summary.json` and interpretation in `project/sensitivity_analysis.md`.

### 2026-11-23 - Task 9 completed

- Re-read all three pages of the professor's project guidelines and mapped the report to the seven suggested sections.
- Kept the draft within a concise structure intended for the eight-page A4 limit, including title information, figures, tables and references.
- Distinguished official P2 capacity data, external empirical references and synthetic assumptions in the report.
- Explained event logic, initial conditions, warm-up treatment, draining after the arrival boundary, common random numbers and confidence intervals.
- Created three vector figures: the system event flow, the main waiting-time comparison with 95% confidence intervals and demand sensitivity.
- Reported both the high-demand planning result and the practically zero-wait current benchmark to avoid overstating the need for intervention.
- Discussed equipment, space, power, enforcement and compliance trade-offs without inventing unavailable cost figures.
- Included sensitivity limitations and identified P2 arrival, charging-completion and departure timestamps as the highest-value future data.
- Drafted a 197-word policy brief, within the required approximate 150-200 word range.
- Stored the complete English draft in `report/report_draft.md` and the standalone brief in `report/policy_brief.md`.

### 2026-11-24 - Task 10 completed

- Produced the final eight-page A4 PDF report with the three team members' names and student IDs.
- Rendered and visually inspected every PDF page, then verified the page count and required report content programmatically.
- Created a nine-slide English presentation with editable native charts and embedded speaker notes for an approximately ten-minute delivery.
- Rendered and visually inspected every slide, corrected canvas scaling and repaired text-spacing issues before finalising the deck.
- Added a standalone timed English presentation script with a suggested three-person speaker allocation and rehearsal checklist.
- Added `REPRODUCIBILITY.md` and `requirements.txt`; the simulation uses Python 3.10 or later and only the standard library.
- Built a compact reproducibility ZIP containing source code, configuration, tests, exact result summaries and project documentation.
- Extracted the ZIP into a clean temporary directory and confirmed that all 15 automated tests pass from the packaged copy.

## Running the Baseline Model

The project requires Python 3.10 or later and uses only the Python standard library. From the project directory, run:

```powershell
python -m src.run_baseline --profile planning --seed 3410 --days 1
```

For the lower-demand benchmark:

```powershell
python -m src.run_baseline --profile current_benchmark --seed 3410 --days 1
```

Add `--json` to return machine-readable output. The one-day run is currently a technical demonstration only; the final run length, warm-up and replication count will be decided during experiment design.

## Running the Matched Policy Demonstration

```powershell
python -m src.run_scenarios --profile planning --seed 3410 --days 1
```

This command uses one common seed for all three scenarios. Its output is a technical demonstration, not the final experiment.

## Running the Formal Experiment

```powershell
python -m src.run_experiment --replications 100 --warmup-days 7 --measurement-days 30 --base-seed 341000
```

## Running the Sensitivity Analysis

```powershell
python -m src.run_sensitivity --replications 50 --warmup-days 7 --measurement-days 30 --base-seed 841000
```

## Running Verification and Validation

```powershell
python -m unittest discover -s tests -v
python -m src.validate_model
```

## Working Rule

Before each task begins, its objective, modelling principle, expected output and required decisions will be explained to the team. Implementation starts only after team approval.

After each task is completed, skipped or materially changed, this README will be updated so that the GitHub history remains understandable to all team members.
