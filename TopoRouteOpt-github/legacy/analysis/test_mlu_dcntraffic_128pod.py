import pandas as pd
import matplotlib.pyplot as plt

# Result files and their labels.
result_files = [
    ('../DCNTraffic_128pod/performance_upper_bound/1024/10000/test_results.txt', 'performance_upper_bound'),
    ('../DCNTraffic_128pod/TROD_linkpct/Uniform_Topo/1024/10000/test_results.txt', 'TROD_linkpct'),
    ('../DCNTraffic_128pod/VLB/Uniform_Topo/1024/10000/test_results.txt', 'VLB'),
    #('../DCNTraffic_16pod/TROD_linkpct_centralized_TPE/Uniform_Topo/100000/test_results.txt', 'centralized_TPE'),
    ('../DCNTraffic_128pod/TROD_linkpct_distributed_TPE/Uniform_Topo/1024/10000/test_results_add1_sub30_all0.8_all0.85.txt', 'dis_1_30_all0.8_all0.85')
]

data_list = []
label_list = []

for file, label in result_files:
    
        
    data = pd.read_csv(file, header=None)[0].values
    if label == 'performance_upper_bound':
        data = data[12:3000]
    elif label == 'TROD_topo_Gurobi_TE':
        data = data[12:3000]
    print(data)
    data_list.append(data)
    label_list.append(label)

plt.figure(figsize=(24, 6))
plt.boxplot(data_list, labels=label_list)
plt.ylabel('MLU')
plt.grid(True)
plt.tight_layout()
plt.savefig('dcntraffic_128pod.jpg')