# import numpy as np

# mean = np.loadtxt('Facebook_pod_a_mean_traffic.txt')
# std = np.loadtxt('Facebook_pod_a_std_traffic.txt')

# ratio = std / mean

# np.savetxt('Facebook_pod_a_ratio.txt', ratio, fmt='%.8f')

import pickle as pkl

file_path = "../rawdata/Facebook_pod_a_traffic_matrices_1s/t1.pkl"  # Path to the example file.

with open(file_path, "rb") as f:
    data = pkl.load(f)

print(type(data))   # Inspect the data type.
print(data.shape)   # Inspect the shape for a NumPy array.

