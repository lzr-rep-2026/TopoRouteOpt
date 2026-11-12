import pandas as pd
import matplotlib.pyplot as plt
# result_files = [
#     ('../splitpod_mixtraffic_16pod/performance_upper_bound/128/210000/test_results.txt', 'performance_upper_bound'),
#     ('../splitpod_mixtraffic_16pod/TROD_linkpct_split_pod/TROD_Topo/128/210000/test_results_ai_0.9_dcn_0.8.txt', 'linkpct_Uniform_Topo_floor'),
#     ('../splitpod_mixtraffic_16pod/TROD_linkpct_split_pod/TROD_Topo/128/210000/test_results_ai_0.9_dcn_0.8_0.txt', 'linkpct_Uniform_Topo'),
#     ('../splitpod_mixtraffic_16pod/split_pod_distributed_TPE/TROD_Topo/128/210000/test_results_add1_sub12_all0.8_all0.6_all1_min1.txt', 'TPE_changeall_min1'),
#     ('../splitpod_mixtraffic_16pod/split_pod_distributed_TPE/TROD_Topo/128/210000/test_results_add1_sub12_all0.8_all0.6_all1_min1_notall.txt', 'TPE_min1')
# ]
result_files = [
    ('../SimTraffic_ai/performance_upper_bound/256/550000000/test_results.txt', 'performance_upper_bound'),
    ('../SimTraffic_ai/TROD_linkpct/TROD_Topo/256/550000000/test_results_threshold_0.8.txt', 'linkpct_TROD_topo'),
    ('../SimTraffic_ai/TROD_linkpct/Uniform_Topo/256/550000000/test_results_threshold_0.8.txt', 'linkpct_Uniform_topo'),
    ('../SimTraffic_ai/TROD_linkpct_centralized_TPE/Uniform_Topo/256/550000000/test_results.txt', 'CentralizedTPE'),
    ('../SimTraffic_ai/TROD_linkpct_distributed_TPE/TROD_Topo/256/550000000/test_results_add1_sub12_all0.6_all0.9.txt', 'DistributedTPE'),
    ('../SimTraffic_ai/VLB/Uniform_Topo/256/550000000/test_results.txt', 'VLB')
]

data_list = []
label_list = []

for file, label in result_files:
    data = pd.read_csv(file, header=None)[0].values
    if label == 'performance_upper_bound':
        data = data[12:]
    elif label == 'TROD_topo_Gurobi_TE':
        data = data[12:]
    print(data)
    data_list.append(data)
    label_list.append(label)

plt.figure(figsize=(25, 10))
plt.boxplot(data_list, labels=label_list)
plt.ylabel('MLU')
plt.grid(True)
plt.tight_layout()
plt.savefig('SimTrafic_16pod.jpg')