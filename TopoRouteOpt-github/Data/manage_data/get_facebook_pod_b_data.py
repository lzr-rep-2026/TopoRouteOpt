import numpy as np
import os
import pickle as pkl

raw_data_filepath = '../rawdata/hadoop_traffic.csv'
output_data_dirpath = '../Facebook_pod_b'
if not os.path.exists(output_data_dirpath):
    os.makedirs(output_data_dirpath)
with open(raw_data_filepath, 'r') as f:
    lines = f.readlines()
    for idx, line in enumerate(lines):
        flatten_traffic = line.strip().split(',')
        traffic = np.array(flatten_traffic, dtype=np.float32)
        traffic = traffic.reshape((9, 9))
        output_filepath = os.path.join(output_data_dirpath, f't{idx+1}.pkl')
        with open(output_filepath, 'wb') as fw:
            pkl.dump(traffic, fw)




