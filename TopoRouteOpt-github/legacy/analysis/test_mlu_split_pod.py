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
    ('../splitpod_mixtraffic_16pod/performance_upper_bound/128/210000/test_results.txt', 'performance_upper_bound'),
    ('../splitpod_mixtraffic_16pod/TROD_linkpct_split_pod/Uniform_Topo/128/210000/test_results_ai_0.9_dcn_0.8_floor_aiwithTROD.txt', 'linkpct_Uniform_Topo_floor_allTROD'),
     ('../splitpod_mixtraffic_16pod/TROD_linkpct_split_pod/Uniform_Topo/128/210000/test_results_ai_0.9_dcn_0.8_floor_aiwithoutTROD.txt', 'linkpct_Uniform_Topo_floor_aiNoTROD'),
    #('../splitpod_mixtraffic_16pod/split_pod_distributed_TPE/Uniform_Topo/128/210000/test_results_split_add1_sub12_all0.8_all0.6_all0_min1.txt', 'distributed_tpe_TROD'),
    ('../splitpod_mixtraffic_16pod/ideal_split_pod_distributed_TPE/Uniform_Topo/128/210000/test_results_ideal_split_aiwithoutTROD.txt', 'ideal_distributed_tpe_ai_without_TROD')
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
plt.savefig('Split_pod.jpg')