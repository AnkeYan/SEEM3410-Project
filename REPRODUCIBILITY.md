# Reproducing the SEEM3410 EV Charging Results

## Software

- Python 3.10 or later
- No third-party Python packages
- Operating system independent

Run every command from the folder containing this file.

## 1. Verify the model

```text
python -m unittest discover -s tests -v
python -m src.validate_model
```

The first command should report 15 passing tests. The validation command should finish with `"all_checks_passed": true`.

## 2. Run the formal experiment

```text
python -m src.run_experiment --replications 100 --warmup-days 7 --measurement-days 30 --base-seed 341000
```

The planning-profile means should reproduce approximately:

- Baseline: 0.8329 minutes
- Capacity: 0.5774 minutes
- Charge-and-go: 0.1523 minutes

Exact saved results are in `results/experiment_summary.json`.

## 3. Run the sensitivity analysis

```text
python -m src.run_sensitivity --replications 50 --warmup-days 7 --measurement-days 30 --base-seed 841000
```

The analysis should report 12 unique settings: charge-and-go has lower mean waiting in 11 settings and the 0.50 demand setting is a practical tie.

Exact saved results are in `results/sensitivity_summary.json`.

## File Map

- `config/model_inputs.json`: model parameters and data provenance labels
- `src/ev_charging_sim.py`: discrete-event simulation engine
- `src/run_experiment.py`: formal paired experiment
- `src/run_sensitivity.py`: one-factor sensitivity analysis
- `src/validate_model.py`: statistical input checks
- `tests/test_simulation.py`: automated verification tests
- `project/`: scope, assumptions, validation and interpretation records
- `README.md`: project history and detailed commands

## Randomness and Reproducibility

The code uses Python's seeded `random.Random` streams. Arrivals, active charging and dwell use separate streams. The same vehicle ID receives matched random quantiles across policies, providing common random numbers for paired comparisons.
