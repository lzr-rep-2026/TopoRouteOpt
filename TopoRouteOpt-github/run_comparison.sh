#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python}"
mkdir -p Log/experiment_cli

"$PYTHON" run_main.py --method TROD_linkpct > Log/experiment_cli/trod.log 2>&1
"$PYTHON" run_main.py --method VLB > Log/experiment_cli/vlb.log 2>&1
"$PYTHON" run_main.py --method TROD_linkpct_distributed_TPE \
  --add_link_hist_len 1 --remove_link_hist_len 30 \
  --add_thr 0.8 --remove_thr 0.8 --custom_name add1_remove30 \
  > Log/experiment_cli/distributed.log 2>&1

"$PYTHON" plot_results.py \
  --series TROD=Result/DCNTraffic_16pod_8spine/TROD_linkpct/Uniform_Topo/512/2000/test_results.txt \
  --series VLB=Result/DCNTraffic_16pod_8spine/VLB/Uniform_Topo/512/2000/test_results.txt \
  --series Distributed=Result/DCNTraffic_16pod_8spine/TROD_linkpct_distributed_TPE/Uniform_Topo/512/2000/test_results_add1_remove30.txt \
  --output Result/dcn_comparison.png
