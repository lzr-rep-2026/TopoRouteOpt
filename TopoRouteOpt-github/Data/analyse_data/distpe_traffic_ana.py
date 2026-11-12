import os
import sys
import pickle as pkl
import numpy as np
sys.path.append('../..')
from src.config import DATA_DIR

topo_name = 'DCNTraffic_16pod_8spine'
Data_dir = os.path.join(DATA_DIR, f'{topo_name}')
file_list = sorted(os.listdir(Data_dir), key=lambda x: int(x.split('.')[0][1:]))
# file_list = sorted(os.listdir(Data_dir), key=lambda x: int(x.split('.')[0]))

# Use only the first day of data.
# first_day_file_list = [f for f in file_list if int(f.split('.')[0][1:]) <= 43182]
# print(f"Loading {len(first_day_file_list)} traffic matrices from {Data_dir} (first day only)")

all_frames = []
for file in file_list:
    file_path = os.path.join(Data_dir, file)
    with open(file_path, 'rb') as f:
        traffic = pkl.load(f).astype(np.float64)  # [pod, pod, spine]
        idx = np.arange(traffic.shape[0])
        traffic[idx, idx] = 0.0  # Clear self traffic on the diagonal.
        # traffic_agg = traffic.sum(axis=-1)  # [pod, pod]
        all_frames.append(traffic)

all_frames = np.stack(all_frames, axis=0)  # [num_frames, pod, pod]

mean_traffic = all_frames.mean(axis=0)  # [pod, pod]
std_traffic = all_frames.std(axis=0)    # [pod, pod]

# Weight each pod pair by its mean relative to the total.
# sum_mean = mean_traffic.sum()
# weight = mean_traffic / (sum_mean + 1e-8)  # [pod, pod]

std_ratio = std_traffic / (mean_traffic + 1e-8)  # [pod, pod]

# Save the statistics.
# np.save(f"{topo_name}_mean_traffic.npy", mean_traffic)
# np.save(f"{topo_name}_std_traffic.npy", std_traffic)
# np.save(f"{topo_name}_weight.npy", weight)
np.save(f"{topo_name}_std_ratio.npy", std_ratio)
np.savetxt(f"{topo_name}_std_ratio.txt", std_ratio, fmt="%.6f")


