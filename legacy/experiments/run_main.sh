#!/bin/bash

# python3 run_main.py --topo_name splitpod_mixtraffic_16pod \
# --test_start_idx 0 --test_end_idx 1299 \
# --method TROD_linkpct_split_pod --link_percentile 0.8 \
# --ai_link_percentile 0.9 --dcn_link_percentile 0.8 \
# --custom_name ai_0.9_dcn_0.8_floor_aiwithTROD --bandwidth_per_port 210000 \
# --init_topo_method Uniform_Topo \
# --port_num_per_pod 128 --ai_pods 0 1 2 3

# Treat AI and DCN traffic together and allow link counts to drop to zero.
# python3 run_main.py --topo_name SimTraffic_ai \
# --test_start_idx 0 --test_end_idx 15060 \
# --method TROD_linkpct_distributed_TPE --link_percentile 0.8 \
# --init_topo_method TROD_Topo \
# --add_link_hist_len 1 --remove_link_hist_len 12 \
# --add_thr 0.6 --remove_thr 0.9 \
# --custom_name add1_sub12_all0.6_all0.9 --bandwidth_per_port 550000000 \
# --port_num_per_pod 256 --max_links 32 --min_links 1 \
# --change_all 0

# Treat AI and DCN traffic together and keep at least one link.
# python3 run_main.py --topo_name SimTraffic_ai \
# --test_start_idx 0 --test_end_idx 15060 \
# --method TROD_linkpct_distributed_TPE --link_percentile 0.8 \
# --init_topo_method Uniform_Topo \
# --add_link_hist_len 1 --remove_link_hist_len 12 \
# --add_thr 0.8 --remove_thr 0.1 \
# --custom_name add1_sub12_all0.8_all0.6_all1_min1 --bandwidth_per_port 210000 \
# --port_num_per_pod 128 --max_links 32 --min_links 1 \
# --change_all 1

# Treat AI and DCN traffic together with a fixed uniform topology.
# python3 run_main.py --topo_name SimTraffic_ai \
# --test_start_idx 0 --test_end_idx 15060 \
# --method TROD_linkpct --link_percentile 0.8 \
# --init_topo_method Uniform_Topo --bandwidth_per_port 550000000 \
# --port_num_per_pod 256 --max_links 32 --min_links 1 \
# --custom_name threshold_0.8

# Treat AI and DCN traffic together with a fixed TROD topology.
# python3 run_main.py --topo_name SimTraffic_ai \
# --test_start_idx 0 --test_end_idx 15060 \
# --method TROD_linkpct --link_percentile 0.8 \
# --init_topo_method TROD_Topo --bandwidth_per_port 550000000 \
# --port_num_per_pod 256 --max_links 32 --min_links 1 \
# --custom_name threshold_0.8

# python3 run_main.py --topo_name SimTraffic_ai \
# --test_start_idx 0 --test_end_idx 15060 \
# --method TROD_linkpct_centralized_TPE --link_percentile 0.8 \
# --port_num_per_pod 256 --max_links 32 --min_links 1 \
# --init_topo_method Uniform_Topo --bandwidth_per_port 550000000

# python3 run_main.py --topo_name SimTraffic_ai \
# --test_start_idx 0 --test_end_idx 15060 \
# --method VLB --bandwidth_per_port 550000000 \
# --port_num_per_pod 256 --max_links 32 --min_links 1 \
# --init_topo_method Uniform_Topo 

# Separate AI and DCN traffic and keep at least one link.
# python3 run_main.py --topo_name splitpod_mixtraffic_16pod \
# --test_start_idx 0 --test_end_idx 1299 \
# --method split_pod_distributed_TPE --link_percentile 0.8 \
# --add_link_hist_len 1 --remove_link_hist_len 12 \
# --add_thr 0.8 --remove_thr 0.1 \
# --ai_link_percentile 1 --dcn_link_percentile 0.8 \
# --init_topo_method Uniform_Topo \
# --custom_name split_add1_sub12_all0.8_all0.6_all0_min1 --bandwidth_per_port 210000 \
# --port_num_per_pod 128 --max_links 32 --min_links 1 \
# --change_all 0 --remove_strict 0 --ai_pods 0 1 2 3

# python3 run_main.py --topo_name splitpod_mixtraffic_16pod \
# --test_start_idx 0 --test_end_idx 1299 \
# --method ideal_split_pod_distributed_TPE --link_percentile 0.8 \
# --add_link_hist_len 1 --remove_link_hist_len 12 \
# --add_thr 0.8 --remove_thr 0.1 \
# --ai_link_percentile 1 --dcn_link_percentile 0.8 \
# --init_topo_method Uniform_Topo \
# --custom_name ideal_split_aiwithoutTROD --bandwidth_per_port 210000 \
# --port_num_per_pod 128 --max_links 32 --min_links 1 \
# --change_all 0 --remove_strict 0 --ai_pods 0 1 2 3


# python3 run_main.py --topo_name splitpod_mixtraffic_16pod \
# --test_start_idx 0 --test_end_idx 1299 \
# --method split_pod_distributed_TPE --link_percentile 0.8 \
# --add_link_hist_len 1 --remove_link_hist_len 12 \
# --add_thr 0.8 --remove_thr 0.6 \
# --ai_link_percentile 0.999 --dcn_link_percentile 0.8 \
# --custom_name add1_sub12_all0.8_all0.6_all1_min0 --bandwidth_per_port 210000 \
# --port_num_per_pod 128 --max_links 32 --min_links 0 \
# --change_all 1 --ai_pods 0 1 2 3

# python3 run_main.py --topo_name splitpod_mixtraffic_16pod \
# --test_start_idx 0 --test_end_idx 1299 \
# --method split_pod_distributed_TPE --link_percentile 0.8 \
# --add_link_hist_len 1 --remove_link_hist_len 12 \
# --add_thr 0.8 --remove_thr 0.6 \
# --ai_link_percentile 0.9 --dcn_link_percentile 0.8 \
# --custom_name add1_sub12_all0.8_all0.6_all1_min1_notall --bandwidth_per_port 210000 \
# --port_num_per_pod 128 --max_links 32 --min_links 1 \
# --change_all 0 --remove_strict 1 --ai_pods 0 1 2 3

# python3 run_main.py --topo_name Facebook_pod_a \
# --test_start_idx 0 --test_end_idx 80 \
# --method TROD_linkpct_distributed_TPE --link_percentile 0.8 \
# --bandwidth_per_port 6000 --init_topo_method Uniform_Topo \
# --add_link_hist_len 12 --remove_link_hist_len 18 \
# --hist_len 12 \
# --custom_name test

# python3 run_main.py --topo_name Facebook_pod_a \
# --test_start_idx 0 --test_end_idx 80000 \
# --method TROD_linkpct_distributed_TPE --link_percentile 0.8 \
# --init_topo_method TROD_Topo \
# --add_link_hist_len 1 --remove_link_hist_len 1800 \
# --custom_name add1_sub1800_all0.8_all_0.8

# python3 run_main.py --topo_name Facebook_pod_a \
# --test_start_idx 0 --test_end_idx 80000 \
# --method TROD_linkpct --link_percentile 0.8 \
# --init_topo_method TROD_Topo 

# python3 run_main.py --topo_name Facebook_pod_a \
# --test_start_idx 0 --test_end_idx 80000 \
# --method VLB --bandwidth_per_port 6000 \
# --init_topo_method TROD_Topo 

# python3 run_main.py --topo_name Facebook_pod_a \
# --mode test --test_start_idx 0 --test_end_idx 80000 \
# --method TROD_linkpct_centralized_TPE --link_percentile 0.8 \
# --init_topo_method Uniform_Topo --bandwidth_per_port 4600

# python3 run_main.py --topo_name MixTraffic_16pod \
# --test_start_idx 0 --test_end_idx 2393 \
# --method TROD_linkpct --link_percentile 0.8 \
# --init_topo_method Uniform_Topo --bandwidth_per_port 350000 \
# --custom_name 1

# python3 run_main.py --topo_name MixTraffic_16pod \
# --test_start_idx 0 --test_end_idx 2393 \
# --method TROD_linkpct --link_percentile 0.8 \
# --init_topo_method TROD_Topo \
# --bandwidth_per_port 170000 --port_num_per_pod 128

# python3 run_main.py --topo_name MixTraffic_16pod \
# --test_start_idx 0 --test_end_idx 2393 \
# --method TROD_linkpct --link_percentile 0.8 \
# --init_topo_method Uniform_Topo \
# --bandwidth_per_port 340000 --port_num_per_pod 64

python3 run_main.py --topo_name DCNTraffic_16pod_8spine \
--test_start_idx 0 --test_end_idx 2999 \
--init_topo_method Uniform_Topo \
--method VLB --port_num_per_pod 512 \
--bandwidth_per_port 1500 --max_links 64

# python3 run_main.py --topo_name DCNTraffic_16pod_8spine \
# --test_start_idx 0 --test_end_idx 2999 \
# --method TROD_linkpct --link_percentile 0.8 \
# --init_topo_method Uniform_Topo --port_num_per_pod 512 \
# --bandwidth_per_port 2000 --max_links 64

# python3 run_main.py --topo_name DCNTraffic_16pod \
# --test_start_idx 0 --test_end_idx 2393 \
# --method VLB --bandwidth_per_port 100000

# python3 run_main.py --topo_name DCNTraffic_16pod_8spine \
# --test_start_idx 0 --test_end_idx 2999 \
# --method TROD_linkpct_centralized_TPE --link_percentile 0.8 \
# --init_topo_method Uniform_Topo --port_num_per_pod 512 \
# --bandwidth_per_port 2000 --max_links 64

python3 run_main.py --topo_name DCNTraffic_16pod_8spine \
--test_start_idx 0 --test_end_idx 2999 \
--method TROD_linkpct_distributed_TPE --link_percentile 0.8 \
--init_topo_method Uniform_Topo \
--add_link_hist_len 1 --remove_link_hist_len 30 \
--add_thr 0.5 --remove_thr 0.8 --port_num_per_pod 512 \
--custom_name add1_sub30_all0.5_all0.8 --bandwidth_per_port 1500 \
--max_links 64

# python3 run_main.py --topo_name MixTraffic_16pod \
# --test_start_idx 0 --test_end_idx 2393 \
# --method TROD_linkpct_distributed_TPE --link_percentile 0.8 \
# --init_topo_method Uniform_Topo \
# --add_link_hist_len 1 --remove_link_hist_len 12 \
# --add_thr 0.8 --remove_thr 0.5 \
# --custom_name add1_sub12_all0.8_all0.5_all1 --bandwidth_per_port 170000 \
# --port_num_per_pod 128 --max_links 32 --min_links 0 \
# --change_all 1

# python3 run_main.py --topo_name MixTraffic_16pod \
# --test_start_idx 0 --test_end_idx 2393 \
# --method TROD_linkpct_distributed_TPE --link_percentile 0.8 \
# --init_topo_method Uniform_Topo \
# --add_link_hist_len 1 --remove_link_hist_len 180 \
# --add_thr 0.8 --remove_thr 0.8 \
# --custom_name add1_sub180_all0.8_all0.8_rem0 --bandwidth_per_port 340000 \
# --port_num_per_pod 64 --max_links 16 --min_links 1 \
# --remove_strict 0

# python3 run_main.py --topo_name Facebook_pod_b \
# --test_start_idx 0 --test_end_idx 80000 \
# --method TROD_linkpct_distributed_TPE --link_percentile 0.8 \
# --init_topo_method Uniform_Topo \
# --add_link_hist_len 1 --remove_link_hist_len 1800 \
# --custom_name add1_sub1800_all0.8_all_0.8

# python3 run_main.py --topo_name Facebook_pod_b \
# --test_start_idx 0 --test_end_idx 80000 \
# --method TROD_linkpct --link_percentile 0.8 \
# --init_topo_method TROD_Topo

# python3 run_main.py --topo_name Facebook_pod_b \
# --test_start_idx 0 --test_end_idx 80000 \
# --method VLB --bandwidth_per_port 6000 \

# python3 run_main.py --topo_name Facebook_pod_b \
# --mode test --test_start_idx 0 --test_end_idx 80000 \
# --method TROD_linkpct_centralized_TPE --link_percentile 0.8 \
# --init_topo_method Uniform_Topo

# uniform_top

# python3 run_main.py --topo_name Facebook_pod_a_two_days \
# --train_start_idx 0 --train_end_idx 43182 \
# --test_start_idx 43182 --test_end_idx 86364 \
# --method TROD_linkpct --link_percentile 0.8 \
# --bandwidth_per_port 3000

# python3 run_main.py --topo_name Facebook_pod_a_two_days \
# --train_start_idx 0 --train_end_idx 43182 \
# --test_start_idx 43182 --test_end_idx 86364 \
# --method VLB --bandwidth_per_port 3000

# python3 run_main.py --topo_name Facebook_pod_a_two_days \
# --train_start_idx 0 --train_end_idx 43182 \
# --test_start_idx 43182 --test_end_idx 86364 \
# --method TROD_linkpct_centralized_TPE --link_percentile 0.8 \
# --bandwidth_per_port 3000

# python3 run_main.py --topo_name Facebook_pod_a_two_days \
# --train_start_idx 0 --train_end_idx 43182 \
# --test_start_idx 43182 --test_end_idx 86364 \
# --method TROD_linkpct_distributed_TPE --link_percentile 0.8 \
# --bandwidth_per_port 3000

# python3 run_main.py --topo_name Facebook_pod_a_two_days \
# --train_start_idx 0 --train_end_idx 10 \
# --test_start_idx 43182 --test_end_idx 86364 \
# --method TROD_linkpct --link_percentile 0.8 \
# --bandwidth_per_port 6000

# python3 run_main.py --topo_name Facebook_pod_a_two_days \
# --train_start_idx 0 --train_end_idx 43182 \
# --test_start_idx 43182 --test_end_idx 86364 \
# --method VLB --bandwidth_per_port 6000

# python3 run_main.py --topo_name Facebook_pod_a_two_days \
# --train_start_idx 0 --train_end_idx 43182 \
# --test_start_idx 43182 --test_end_idx 86364 \
# --method TROD_linkpct_centralized_TPE --link_percentile 0.8 \
# --bandwidth_per_port 6000

# python3 run_main.py --topo_name Facebook_pod_a_two_days \
# --train_start_idx 0 --train_end_idx 10 \
# --test_start_idx 43182 --test_end_idx 86364 \
# --method TROD_linkpct_distributed_TPE --link_percentile 0.8 \
# --bandwidth_per_port 6000
