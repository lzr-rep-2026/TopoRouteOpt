import pandas as pd
import matplotlib.pyplot as plt

# Result files and their labels.
# result_files = [
#     ('../Facebook_pod_a/TROD_linkpct/Uniform_Topo/test_hop_count_results.txt', 'TROD_linkpct'),
#     ('../Facebook_pod_a/VLB/Uniform_Topo/test_hop_count_results.txt', 'VLB'),
#     ('../Facebook_pod_a/TROD_linkpct_centralized_TPE/Uniform_Topo/test_hop_count_results.txt', 'centralized_TPE'),
#     ('../Facebook_pod_a/TROD_linkpct_distributed_TPE/Uniform_Topo/test_hop_count_results_add1_sub1800_all0.8_all0.8.txt', 'dis_1_1800_all0.8_all0.8')
# ]
# result_files = [
#     ('../Facebook_pod_a/TROD_linkpct_distributed_TPE/Uniform_Topo/test_hop_count_results_add60_sub1800_mean0.6_all0.1_mean0.15_mean0.2.txt', 'dis_60_1800_mean0.6_all0.1_mean0.15_mean0.2'),
#     ('../Facebook_pod_a/TROD_linkpct_distributed_TPE/Uniform_Topo/test_hop_count_results_add60_sub1800_mean0.6_mean0.2.txt', 'dis_60_1800_mean0.6_mean0.2'),
#     ('../Facebook_pod_a/TROD_linkpct_distributed_TPE/Uniform_Topo/test_hop_count_results_add12_sub1800_mean0.5_mean0.12_mean0.2.txt', 'dis_12_1800_mean0.5_mean0.12_mean0.2'),
#     ('../Facebook_pod_a/TROD_linkpct_distributed_TPE/Uniform_Topo/test_hop_count_results_add12_sub1800_mean0.5_mean0.45_mean0.12_mean0.2.txt', 'dis_12_1800_mean0.5_mean0.45_mean0.12_mean0.2'),
#     ('../Facebook_pod_a/TROD_linkpct_distributed_TPE/Uniform_Topo/test_hop_count_results_add12_sub1800_mean0.5_mean0.45_mean0.2_mean0.25.txt', 'dis_12_1800_mean0.5_mean0.45_mean0.2_mean0.25'),
#     ('../Facebook_pod_a/TROD_linkpct_distributed_TPE/Uniform_Topo/test_hop_count_results_add1_sub1800_all0.8_all0.8.txt', 'dis_1_1800_all0.8_all0.8')
# ]
# result_files = [
#     ('../Facebook_pod_a/TROD_linkpct/TROD_Topo/test_hop_count_results.txt', 'TROD_linkpct'),
#     ('../Facebook_pod_a/VLB/TROD_Topo/test_hop_count_results.txt', 'VLB'),
#     ('../Facebook_pod_a/TROD_linkpct_centralized_TPE/TROD_Topo/test_hop_count_results.txt', 'centralized_TPE'),
#     ('../Facebook_pod_a/TROD_linkpct_distributed_TPE/TROD_Topo/test_hop_count_results_add1_sub1800_all0.8_all0.8.txt', 'dis_1_1800_all0.8_all0.8')
# ]
result_files = [
    #('../DCNTraffic_16pod_8spine/performance_upper_bound/512/2000/test_results.txt', 'performance_upper_bound'),
    ('../DCNTraffic_16pod_8spine/VLB/Uniform_Topo/512/2000/test_hop_count_results.txt', 'VLB'),
    ('../DCNTraffic_16pod_8spine/TROD_linkpct/Uniform_Topo/512/2000/test_hop_count_results.txt', 'TROD_linkpct'),
    ('../DCNTraffic_16pod_8spine/TROD_linkpct_centralized_TPE/Uniform_Topo/512/2000/test_hop_count_results.txt', 'centralized_TPE'),
    ('../DCNTraffic_16pod_8spine/TROD_linkpct_distributed_TPE/Uniform_Topo/512/2000/test_hop_count_results_add1_sub30_all0.8_all0.8.txt', 'dis_1_30_all0.8_all0.8'),
]

data_list = []
label_list = []

for file, label in result_files:
    
        
    data = pd.read_csv(file, header=None)[0].values
    if label == 'performance_upper_bound':
        data = data[12:]
    elif label == 'TROD_topo_Gurobi_TE':
        data = data[12:80012]
    print(data)
    data_list.append(data)
    label_list.append(label)

plt.figure(figsize=(24, 6))
plt.boxplot(data_list, labels=label_list)
plt.ylabel('hop count')
plt.grid(True)
plt.tight_layout()
plt.savefig('hop_count_DCN_16pod8spine.jpg')