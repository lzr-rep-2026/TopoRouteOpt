import sys
import numpy as np
from tqdm import tqdm

from src.env import Env
from src.run_helper import parse_args
from src.frameworks import Spread_traffic_engineering, Get_MLU
from src.utils import normalize_size
from src.config import RESULT_DIR
import os

props = parse_args(sys.argv[1:])
env = Env(props)

result_dir = os.path.join(RESULT_DIR, "jupiter")
os.makedirs(result_dir, exist_ok=True)
result_file = os.path.join(result_dir, "jupiter_test_results.txt")

all_spine_topologys = []
all_spine_capacitys = []
all_spine_edges = []
all_spine_paths = []
all_spine_capacitys = []
all_spine_edge_to_paths = []
mlu_list = []

for spine_id in range(env.spine_num_per_pod):
    topology = env.x[:,:, spine_id].detach().cpu().numpy()
    capacity = normalize_size(topology * env.bandwidth_per_port)
    edges = {}
    for i in range(env.pod_num):
        for j in range(env.pod_num):
            if i != j and topology[i][j] > 0:
                edges[(i, j)] = {'capacity': capacity[i][j]}
    paths = {}
    for i in range(env.pod_num):
        for j in range(env.pod_num):
            if i != j:
                if topology[i][j] > 0:
                    paths[(i,j)] = [[(i,j)]]
                for k in range(env.pod_num):
                    if i != k and j != k and topology[i][k] > 0 and topology[k][j] > 0:
                        if (i,j) not in paths:
                            paths[(i,j)] = []
                        paths[(i,j)].append( [(i,k), (k,j)] )
    edge_to_path = {}
    for i in range(env.pod_num):
        for j in range(env.pod_num):
            if i != j:
                if (i,j) in paths:
                    for k, path in enumerate(paths[(i,j)]):
                        for edge in path:
                            if edge not in edge_to_path:
                                edge_to_path[edge] = []
                            edge_to_path[edge].append( (i,j,k) )

    path_capacity = {}
    for i in range(env.pod_num):
        for j in range(env.pod_num):
            if i != j:
                for k, path in enumerate(paths.get((i,j), [])):
                    min_cap = float('inf')
                    for edge in path:
                        if edges[edge]['capacity'] < min_cap:
                            min_cap = edges[edge]['capacity']
                    path_capacity[(i,j,k)] = min_cap
    

    all_spine_topologys.append(topology)
    all_spine_capacitys.append(capacity)
    all_spine_edges.append(edges)
    all_spine_paths.append(paths)
    all_spine_capacitys.append(path_capacity)
    all_spine_edge_to_paths.append(edge_to_path)



all_spine_hist_traffics = []
for spine_id in range(env.spine_num_per_pod):
    all_spine_hist_traffics.append([])

with tqdm(env.test_pod_traffics) as tepoch:
    for tms_idx, tms in enumerate(tepoch):
        frame_mlus = [] # MLU on every spine layer for this frame.
        for spine_id in range(env.spine_num_per_pod):
            hist_traffic = all_spine_hist_traffics[spine_id]
            now_traffic = tms / env.spine_num_per_pod
            if len(hist_traffic) >= props.hist_len:
                topology = all_spine_topologys[spine_id]
                capacity = all_spine_capacitys[spine_id]
                edges = all_spine_edges[spine_id]
                paths = all_spine_paths[spine_id]
                edge_to_path = all_spine_edge_to_paths[spine_id]
                print(edge_to_path[(0,1)])

                peak_demand = np.max(np.array(hist_traffic), axis=0)
                _, path_routing_weights = Spread_traffic_engineering(
                    env.pod_num,
                    edges,
                    paths,
                    path_capacity,
                    edge_to_path,
                    peak_demand,
                    Spread=props.spread
                )
                mlu = Get_MLU(
                    env.pod_num,
                    edges,
                    edge_to_path,
                    path_routing_weights,
                    now_traffic
                )
                frame_mlus.append(mlu)
                hist_traffic.pop(0)
            hist_traffic.append(now_traffic)
        if frame_mlus:
            mlu_list.append(max(frame_mlus))
        else:
            mlu_list.append(0.0)
with open(result_file, 'w') as f:
    for m in mlu_list:
        f.write(f"{m}\n")
print(f"Saved per-frame MLU to {result_file}")




            