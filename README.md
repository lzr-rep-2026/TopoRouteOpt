# TopoRouteOpt datacenter topology and routing planner

This project compares routing and topology-control strategies in a pod-and-spine data center network. The default workload, `DCNTraffic_16pod_8spine`, is generated locally: 16 pods, 8 simulated spine layers, and 3000 traffic-matrix frames. No Facebook trace is needed for the walkthrough below.

## How the code is organized

The main data flow is `prepare_data.py` → `Data/<dataset>/tN.pkl` → `src.env.Env` → an experiment entry point → `Result/` and `Log/` → `plot_results.py` or `analyze_results.py`.

- `src/data.py` generates the default DCN workload and an alternate demo workload. It can also read the optional Facebook pickle archive (we excluded the raw data here as it's too large but we used it as our main testing data). `Data/manage_data/` contains the original data-generation scripts; some need raw inputs not included here.
- `src/env.py` loads traffic matrices, selects the initial topology, sets the threshold matrix, and calculates link capacities. A two-dimensional traffic matrix is interpreted as pod-to-pod demand and assigned eight spine layers; a three-dimensional matrix supplies its own spine count.
- `src/cal_topology.py` builds demand-aware initial topologies and implements central or distributed link reconfiguration.
- `src/frameworks.py` assigns traffic to direct and two-hop paths, then computes maximum link utilization (MLU) and mean hop count. `src/run_helper.py` defines the command-line options; `src/utils.py` normalizes traffic and capacity units.
- `run_main.py` is the method-selectable simulator. `run_gurobi.py` and `run_jupiter.py` are separate optimization-based routing baselines. `run_comparison.sh` runs the three methods that do not need a Gurobi solve and plots their results.
- `plot_results.py` produces a per-frame MLU plot and distribution plot; `analyze_results.py` prints numerical summaries. `legacy/analysis/` preserves the original plots with experiment-specific paths, and `legacy/experiments/` preserves the original command sets.
- `src/model.py` defines a neural-network class, but the current `run_main.py` path does not instantiate or train it. The default experiment does not train a neural model.

The key arrays are `traffic[i,j]` (demand from pod `i` to pod `j`), `x[i,j,m]` (connections allocated on spine layer `m`), `capacity[i,j,m]`, and `s[i,j]` (a direct-routing threshold). Link utilization is routed flow divided by capacity; MLU is its maximum over links and spine layers.

## Initial topology choices

Select an initial topology with `--init_topo_method` when using a method that accepts it:

- `Uniform_Topo` (default) distributes each pod's port budget evenly across the other pods and eight spine layers. For 16 pods and 512 ports, the simulator starts with `512 / (15 × 8)` connections per directed pod pair per layer. This is a fractional simulation allocation, not an integer hardware wiring plan.
- `TROD_Topo` estimates each pod pair's demand from a percentile of the training traffic, allocates connections subject to ingress and egress port budgets, converts the aggregate topology to integer counts, and splits it across spine layers. It is an initial topology computed from traffic history; it does not by itself turn on later reconfiguration.

Two exceptions matter. `VLB` selects its own uniform topology and zero threshold regardless of `--init_topo_method`. The `split_pod` methods build group-specific initial topologies from `--ai_pods` and their AI/DCN percentile parameters; they likewise do not follow the ordinary `Uniform_Topo`/`TROD_Topo` branch.

## Routing and topology methods

Choose a main method with `python run_main.py --method NAME`:

- `TROD_linkpct` (default): keeps the initial topology fixed. Each pod pair's threshold is its allocated capacity times `--link_percentile` (0.8 by default). Traffic up to the threshold stays direct; excess traffic is spread across feasible two-hop paths in proportion to their remaining capacity.
- `TROD`: uses the threshold returned by the demand-aware `TROD_Topo` construction instead of the simple capacity percentage. It is meaningful with `--init_topo_method TROD_Topo`.
- `VLB`: uses a uniform topology and zero direct threshold, so the common routing function spreads demand across available two-hop paths, including the direct option. It is a fixed-topology load-balancing baseline.
- `TROD_linkpct_centralized_TPE`: observes recent traffic; when the window mean exceeds 60% of the threshold for at least one pod pair, it recomputes a demand-aware topology from recent history, updates capacities and thresholds, and routes the current frame on that topology.
- `TROD_linkpct_distributed_TPE`: keeps recent traffic and link-history windows. At configured intervals it removes links from persistently underused pod pairs and adds links to persistently busy pairs, subject to per-pod port limits and minimum/maximum link settings. It then updates capacity and thresholds. `--add_link_hist_len`, `--remove_link_hist_len`, `--add_thr`, and `--remove_thr` control the windows and triggers.
- `TROD_linkpct_hr` and `TROD_linkpct_hr_std`: experimental fixed-topology variants that reserve two-hop capacity using, respectively, a recent traffic maximum or a recent mean plus a multiple of the standard deviation. These branches have not been validated in the current end-to-end run.
- `TROD_linkpct_split_pod`, `split_pod_distributed_TPE`, and `ideal_split_pod_distributed_TPE`: experimental AI/DCN-group variants. They use `--ai_pods` and group-specific thresholds; the latter two also adjust links and use a split routing evaluator that keeps AI-to-AI traffic direct rather than sending it through two-hop relays. These branches have not been validated in the current end-to-end run.

`run_gurobi.py` fixes the given topology and solves a routing optimization for **each frame**, choosing direct and two-hop fractions to minimize MLU. `run_jupiter.py` uses the peak traffic in a preceding window and a spread-constrained Gurobi optimization to choose path weights, then evaluates the current frame. Both require a valid Gurobi license. The `run_jupiter.py` name describes its routing baseline; it does not automatically select a Jupiter topology.

The main run uses the first `--hist_len` frames (12 by default) to initialize its history and reports the remaining frames. **Evaluation note:** the default training range currently covers the same 3000 generated frames as the test range. For a strict train/test experiment, set non-overlapping `--train_start_idx`, `--train_end_idx`, `--test_start_idx`, and `--test_end_idx` ranges; otherwise the initial topology and statistics can see future test traffic.

## 1. Install

Use Python 3.8 or newer from the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The simulator imports NumPy, PyTorch, tqdm, and Gurobi's Python package. Some methods solve Gurobi models and therefore need a working Gurobi license. Plotting uses Matplotlib. PyTorch can run on CPU if CUDA is unavailable.

## 2. Generate the workload

```bash
python prepare_data.py dcn --frames 3000 --seed 42
```

This generates `Data/DCNTraffic_16pod_8spine/t1.pkl` through `t3000.pkl`. The equivalent original entry point is:

```bash
python Data/manage_data/get_dcn_traffic.py --frames 3000 --seed 42
```

Run **one** of these commands. Both call the same generator: each off-diagonal pod-to-pod demand is drawn from a Gaussian distribution with mean 40,000 and standard deviation 4,000; the diagonal is zero. The fixed seed makes repeated generation reproducible. Preparation refuses to overwrite existing matrices. To regenerate with new parameters, remove that generated directory explicitly first. `python run_main.py` also generates this dataset automatically when it is absent.

The simulator reads the requested frames and calculates the standard-deviation ratio from its training frames. It saves that statistic under `Data/analyse_data/`; no separate analysis-data step is needed. With the default two-dimensional matrices, the simulator sets the spine-layer count to 8. `--init_topo_method` determines the initial topology, while `--port_num_per_pod` and `--bandwidth_per_port` set its capacity. All experiment commands below use the same default settings: `Uniform_Topo`, 512 ports per pod, and bandwidth 2000 per port.

For a shorter trial, generate 64 frames and add `--test_end_idx 64` to **every** experiment command. The main simulator requires more frames than `--hist_len` (12 by default).

## 3. Run comparable experiments

Run each command from the project root. They use the same generated data and topology settings.

For the three methods that do not solve Gurobi models, `bash run_comparison.sh` runs all three commands below and creates `Result/dcn_comparison.png`.

```bash
# Threshold-based traffic engineering on a fixed topology (the default).
python run_main.py --method TROD_linkpct

# Valiant load balancing baseline.
python run_main.py --method VLB

# Distributed traffic-driven topology adaptation.
python run_main.py --method TROD_linkpct_distributed_TPE \
  --add_link_hist_len 1 --remove_link_hist_len 30 \
  --add_thr 0.8 --remove_thr 0.8 --custom_name add1_remove30
```

`run_main.py` accepts other `--method` values used in the original experiments, including `TROD_linkpct_centralized_TPE`; see `legacy/experiments/run_main.sh` for historical parameter sets. The first `--hist_len` frames initialize the main simulator, so its result file has 2988 values when running all 3000 frames.

Two additional baselines have separate entry points:

```bash
# Route each frame optimally on the given topology to minimize maximum link utilization.
python run_gurobi.py

# Route traffic based on the peak demand of the preceding history window.
python run_jupiter.py
```

`run_gurobi.py` solves an optimization problem for every frame and can take considerably longer. `run_jupiter.py` writes zeros for its first 12 warm-up frames. The name of that script refers to its routing baseline; its topology still comes from the supplied topology settings. These scripts also accept shared arguments such as `--topo_name`, `--test_end_idx`, `--init_topo_method`, `--port_num_per_pod`, and `--bandwidth_per_port`.

Outputs are saved as follows (using the default 3000-frame commands):

- Main methods: `Result/DCNTraffic_16pod_8spine/METHOD/Uniform_Topo/512/2000/test_results.txt`. The distributed example has `test_results_add1_remove30.txt` because of `--custom_name`.
- Gurobi baseline: `Result/DCNTraffic_16pod_8spine/Gurobi_te/Uniform_Topo/test_results.txt`.
- Jupiter baseline: `Result/jupiter/jupiter_test_results.txt`.

Main-method result directories also contain `test_hop_count_results*.txt`. Detailed utilization logs go to `Log/`.

## 4. Compare and plot results

The old experiment-specific comparison plots are preserved in `legacy/analysis/`, including `test_mlu_dcntraffic_16pod.py`. They contain historical paths. The new `plot_results.py` accepts paths on the command line, so it works with fresh experiments:

```bash
python plot_results.py \
  --series TROD=Result/DCNTraffic_16pod_8spine/TROD_linkpct/Uniform_Topo/512/2000/test_results.txt \
  --series VLB=Result/DCNTraffic_16pod_8spine/VLB/Uniform_Topo/512/2000/test_results.txt \
  --series Distributed=Result/DCNTraffic_16pod_8spine/TROD_linkpct_distributed_TPE/Uniform_Topo/512/2000/test_results_add1_remove30.txt \
  --output Result/dcn_comparison.png
```

The figure shows per-frame maximum link utilization (MLU) and a boxplot across frames. To include the other two baselines, use:

```bash
python plot_results.py \
  --series TROD=Result/DCNTraffic_16pod_8spine/TROD_linkpct/Uniform_Topo/512/2000/test_results.txt \
  --series VLB=Result/DCNTraffic_16pod_8spine/VLB/Uniform_Topo/512/2000/test_results.txt \
  --series Distributed=Result/DCNTraffic_16pod_8spine/TROD_linkpct_distributed_TPE/Uniform_Topo/512/2000/test_results_add1_remove30.txt \
  --series Gurobi=Result/DCNTraffic_16pod_8spine/Gurobi_te/Uniform_Topo/test_results.txt \
  --series Jupiter=Result/jupiter/jupiter_test_results.txt \
  --skip-first Gurobi=12 --skip-first Jupiter=12 \
  --output Result/dcn_comparison_all.png
```

The two `--skip-first` values align the baselines with the 2988 post-warm-up frames produced by `run_main.py`. The plotter rejects unequal series lengths instead of silently comparing different time windows. To inspect summary statistics without a figure, pass one or more numeric result files to `python analyze_results.py FILE [FILE ...]`.

## Other datasets and project layout

`python prepare_data.py demo --frames 64 --pods 16 --seed 42` creates an alternate synthetic workload; run it with `--topo_name DemoTraffic --test_end_idx 64`. The optional local Facebook archive can be prepared with `python prepare_data.py facebook --frames 3000`, then selected using `--topo_name Facebook_pod_a`. Its matrices use Python pickle, so only load the archive if you trust its source. The archive's original provenance and redistribution terms are not documented; it is ignored by Git until those terms are confirmed.

- `src/`: simulator, topology, routing, and workload helpers.
- `Data/manage_data/`: data-generation scripts; some require raw traces not included in this trimmed project.
- `prepare_data.py`: user-facing workload preparation.
- `run_main.py`, `run_gurobi.py`, `run_jupiter.py`: experiment entry points; `run_comparison.sh` runs and plots the three methods without a Gurobi solve.
- `plot_results.py`, `analyze_results.py`: reusable analysis tools.
- `legacy/analysis/` and `legacy/experiments/`: original plot scripts and experiment commands for reference.

Generated matrices, statistics, logs, results, and models are excluded by `.gitignore`.
