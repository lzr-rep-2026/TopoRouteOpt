import numpy as np
import os
import sys
import pickle as pkl
sys.path.append('../..')
from src.config import DATA_DIR

topo_name = 'DCNTraffic_16pod_8spine_backup'
port_num = 512
bandwidth_per_port = 2000
# bandwidth_per_port = 
Data_dir = os.path.join(DATA_DIR, f'{topo_name}')
file_list = sorted(os.listdir(Data_dir), key=lambda x: int(x.split('.')[0][1:]))
# file_list = sorted(os.listdir(Data_dir), key=lambda x: int(x.split('.')[0]))


workload_list = []
traffic_list = []
path_file = 'test.csv'
# with open(path_file, 'w') as f1:
for file in file_list:
    file_path = os.path.join(Data_dir, file)
    with open(file_path, 'rb') as f:
        traffic = pkl.load(f).astype(np.float64)
        idx = np.arange(traffic.shape[0])
        if len(traffic.shape) == 3:
                traffic[idx,idx,:] = 0.0
                # import pdb; pdb.set_trace()
                pod_traffic = np.sum(traffic, axis=-1)
        elif len(traffic.shape) == 2:
                traffic[idx,idx] = 0.0
                pod_traffic = traffic
        traffic_list.append(pod_traffic)
        # import pdb; pdb.set_trace()
#             f1.write(','.join(map(str, pod_traffic)) + '\n')
# f1.close()
        out_pod_traffic = np.sum(pod_traffic, axis = 0)
        in_pod_traffic = np.sum(pod_traffic, axis = 1)
        max_out_in_traffic = np.max(np.concatenate((out_pod_traffic, in_pod_traffic)))
        workload_list.append(max_out_in_traffic / port_num / bandwidth_per_port)

output_filepath = os.path.join(f'../../Result/{topo_name}/performance_upper_bound/{port_num}/{bandwidth_per_port}/test_results.txt')
# Median is 0.5; a maximum near 0.9 is preferable and should not exceed 1.

if not os.path.exists(os.path.dirname(output_filepath)):
      os.makedirs(os.path.dirname(output_filepath))

with open(output_filepath, 'w') as f:
        for workload in workload_list:
                f.write(f"{workload}\n")

# percentile_90 = np.percentile(np.array(traffic_list), q=80, axis=0)  # Compute a percentile along axis 0.
# print(percentile_90.shape)  # Expected shape is (4, 4).
# print(percentile_90)
# Plot the workload series.
# import matplotlib.pyplot as plt
# plt.plot(workload_list)
# plt.xlabel('Traffic Matrix Index')
# plt.ylabel('Workload')
# plt.tight_layout()
# plt.savefig(f'{topo_name}_workload.pdf')

# print(f"average workload: {np.mean(workload_list)}")
# print(f"max workload: {np.max(workload_list)}")
