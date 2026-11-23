# Model Scope and Assumptions

## Document Status

- Project: SEEM3410 Team Project
- System: Quick-charging subsystem at Science Park Car Park P2
- Status: Scope approved by the team
- Approval date: 2026-11-23
- Purpose: Freeze the model boundary before input modelling and Python implementation

## 1. Study Objective

The project will use discrete-event simulation to compare feasible policies for reducing the mean waiting time of vehicles using the quick-charging facilities at Science Park Car Park P2.

The model will answer the following question:

> Under stochastic vehicle arrivals, which policy reduces mean vehicle waiting time more effectively: adding one quick charger or reducing post-charging occupation time?

## 2. System Boundary

The model begins when a vehicle requiring quick charging arrives at the P2 quick-charging area. It ends when the vehicle leaves its charging space after charging and any post-charging dwell time.

The model includes:

- Vehicle arrivals to the quick-charging subsystem;
- A first-come, first-served queue;
- Assignment to an available quick charger;
- Active charging time;
- Post-charging dwell time;
- Release of the charger after the vehicle leaves.

The model excludes:

- The single medium charger at P2;
- General car-park entry, exit and parking-space allocation;
- Travel time to Science Park;
- Connector compatibility differences among quick chargers;
- Customer balking or queue abandonment;
- Reservations and priority classes;
- Charger failures and repairs;
- Electricity-grid capacity and dynamic charging power;
- Monetary costs and charging prices.

These exclusions keep the initial model focused and manageable. Excluded behaviours may be discussed as limitations or added later only if the core model is complete and the team approves the expansion.

## 3. Entities, Resources and Queue

### Entity

An electric vehicle arriving for quick-charging service.

### Resources

- Baseline: 26 identical quick chargers;
- Capacity-policy scenario: 27 identical quick chargers.

The model treats the quick chargers as statistically identical parallel servers.

### Queue Rule

- One pooled first-come, first-served queue;
- A vehicle begins service immediately when a charger is available;
- If all chargers are occupied, the vehicle waits in the queue;
- A waiting vehicle does not abandon the queue in the approved baseline scope.

The pooled queue is a fixed operating rule. Queue assignment is not a decision lever in this project.

## 4. Events and State Changes

### Vehicle Arrival

- A new vehicle enters the system;
- If a charger is available, charging starts immediately;
- Otherwise, the vehicle joins the end of the queue.

### Charging Start

- The assigned charger becomes busy;
- The vehicle's waiting time is recorded as charging start time minus arrival time;
- A charging-completion event is scheduled.

### Charging Completion

- Active charging ends;
- The charger remains occupied during the vehicle's post-charging dwell time;
- A vehicle-departure event is scheduled.

### Vehicle Departure

- The vehicle leaves the charging space;
- The charger becomes available;
- If the queue is non-empty, the first waiting vehicle starts charging.

## 5. Random Inputs

The approved model structure will later use computer-generated random inputs for:

- Vehicle interarrival times;
- Active charging times;
- Post-charging dwell times.

The specific probability distributions and parameter values have not yet been approved. They will be defined in the input-modelling task.

The provisional approach is:

- Piecewise Poisson vehicle arrivals, implemented using exponentially distributed interarrival times within each time period;
- A non-negative probability distribution for active charging time;
- A non-negative probability distribution for post-charging dwell time.

## 6. Performance Measure

The only primary performance measure is mean vehicle waiting time.

For vehicle \(i\):

\[
W_i = \text{charging start time}_i - \text{arrival time}_i
\]

For \(n\) measured vehicles:

\[
\bar{W} = \frac{1}{n}\sum_{i=1}^{n} W_i
\]

Vehicles that begin charging immediately have a waiting time of zero and remain part of the mean.

Charger utilisation and queue length may be collected as diagnostic statistics for model checking, but they are not primary policy-performance measures.

## 7. Policies

### Baseline Policy

- 26 quick chargers;
- First-come, first-served pooled queue;
- Baseline post-charging dwell-time distribution.

### Policy A: Capacity Increase

- Increase the number of quick chargers from 26 to 27;
- Keep arrivals, charging times and dwell-time assumptions unchanged.

### Policy B: Charge-and-Go

- Keep 26 quick chargers;
- Reduce post-charging dwell time;
- Keep arrivals and active charging-time assumptions unchanged.

### Optional Policy C: Combined Policy

- 27 quick chargers;
- Reduced post-charging dwell time.

The combined policy will be implemented only if the core comparison is complete and the team approves the additional scenario.

## 8. Fair-Comparison Principle

All policies will be evaluated under the same demand and active charging-time assumptions. Policy comparisons will later use common random numbers so that corresponding replications face matched random inputs.

The random-input assumptions must be fixed before examining which policy performs better. Parameters must not be adjusted after seeing results to favour a policy.

## 9. Confirmed Data Source

The baseline quick-charger count is taken from the September 2026 Environmental Protection Department public EV charger database. The relevant Science Park P2 records indicate 26 quick chargers and one medium charger. The medium charger is outside the approved model boundary.

## 10. Decisions Still Required

The following items remain deliberately undecided:

1. Simulation operating period and time-of-day intervals;
2. Arrival rates for each time period;
3. Active charging-time distribution and parameters;
4. Baseline post-charging dwell-time distribution and parameters;
5. Reduced dwell-time parameters under Policy B;
6. Initial system condition;
7. Warm-up period, run length and number of replications;
8. Random seeds and common-random-number implementation;
9. Whether to include the optional combined policy.

These decisions will be handled in later approved tasks rather than assumed in advance.
