import pandas as pd
import matplotlib.pyplot as plt

# Result files and their labels.
result_files = [
    ('../Facebook_pod_b/performance_upper_bound/135000/test_results.txt', 'performance_upper_bound'),
    ('../Facebook_pod_b/TROD_linkpct/TROD_Topo/135000/test_results.txt', 'TROD_linkpct'),
    ('../Facebook_pod_b/TROD_linkpct_centralized_TPE/Uniform_Topo/135000/test_results.txt', 'centralized_TPE'),
    ('../Facebook_pod_b/TROD_linkpct_distributed_TPE/Uniform_Topo/135000/test_results_add1_sub1800_all0.9_all0.92.txt', 'dis_1_1800_all0.9_all0.92'),
    ('../Facebook_pod_b/VLB/TROD_Topo/135000/test_results.txt', 'VLB')
]

data_list = []
label_list = []

for file, label in result_files:
    
        
    data = pd.read_csv(file, header=None)[0].values
    if label == 'performance_upper_bound':
        data = data[12:80012]
    elif label == 'TROD_topo_Gurobi_TE':
        data = data[12:80012]
    print(data)
    data_list.append(data)
    label_list.append(label)

plt.figure(figsize=(24, 6))
plt.boxplot(data_list, labels=label_list)
plt.ylabel('MLU')
plt.grid(True)
plt.tight_layout()
plt.savefig('pod_b_135000.jpg')