import numpy as np
import os
import pickle as pkl

# Use a fixed random seed.
np.random.seed(42)

pod_num = 16
capacity = 400000
demands_factor = 1

nodes = [str(i) for i in range(pod_num)]
edges = {}
for i in range(pod_num):
    for j in range(pod_num):
        if i != j:
            edges[(nodes[i], nodes[j])] = capacity

node_to_n_edges = {}
total_edges_cap = 0.0
for n in nodes: node_to_n_edges[n] = 0
for e in edges:
    node_to_n_edges[e[0]] += 1
    total_edges_cap += float(edges[e])
    if (e[1], e[0]) not in edges:
        node_to_n_edges[e[1]] += 1
        total_edges_cap += float(edges[e])

total_edges = sum(node_to_n_edges.values())
# print("#nodes = {0}, #edges = {1}, total capacity {2}".format(str(len(nodes)), str(len(edges)), str(total_edges_cap)))

total_demands = total_edges_cap / demands_factor
frac_dict = {}
for u in range(len(nodes)):
    for v in range(len(nodes)):
        if u == v:
            frac_dict[(u, v)] = 0.0
        else:
            u_str = str(u)
            v_str = str(v)
            frac_dict[(u, v)] = (node_to_n_edges[u_str] * node_to_n_edges[v_str]) / (total_edges * (total_edges - node_to_n_edges[u_str]))

traffic_len = 1

ai_traffic_log = '../rawdata/traffic_matrix.log'
save_result_dir = '../splitpod_mixtraffic_16pod'
# save_result_dir = '../MixTraffic_16pod'

if not os.path.exists(save_result_dir):
    os.makedirs(save_result_dir)

ai_demands = np.loadtxt(ai_traffic_log, dtype=str, delimiter=',')
ai_demands = ai_demands[:, 1:]  # Skip the first column.
processed_demands = []
last_non_zero_idx = -1
for idx, ai_demand in enumerate(ai_demands): 
    ai_demand = np.array(ai_demand[0].split(' '), dtype=float) 
    ai_demand = ai_demand.reshape(pod_num, pod_num)
    ai_demand[4:, :] = 0 
    ai_demand[:, 4:] = 0
    processed_demands.append(ai_demand)
    
    if np.any(ai_demand != 0):
        last_non_zero_idx = idx

if last_non_zero_idx >= 0:
    ai_demands = processed_demands[:last_non_zero_idx + 1]
else:
    ai_demands = []  # Handle the all-zero matrix case.

for idx, ai_demand in enumerate(ai_demands): 
    ai_demand = ai_demand.flatten()
    dcn_demand = [0.0] * (len(nodes) * len(nodes)) 
    for u in range(len(nodes)): 
        for v in range(len(nodes)): 
            if u == v or u<4 or v<4: 
                continue
            frac = frac_dict[(u, v)] # sample from gaussian with mean = frac, stddev = frac / 4 
            dcn_demand[u * len(nodes) + v] = total_demands * max(np.random.normal(frac, frac / 4), 0.0) 
    dcn_demand = np.array(dcn_demand, dtype=float)
            
    demand = ai_demand + dcn_demand 
    demand = demand.reshape(pod_num, pod_num) 
    # save_path = os.path.join(save_result_dir, str(idx+1) + '.pkl') 
    save_path = os.path.join(save_result_dir, f"t{idx+1}.pkl") 
    
    with open(save_path, 'wb') as f: 
        pkl.dump(demand, f)

# num_lines = ai_demands_raw.shape[0]

# parsed = []
# for row in ai_demands_raw:
#     vec = np.array(row[0].split(' '), dtype=float)  # shape: [pod_num*pod_num]
#     parsed.append(vec)
# parsed = np.vstack(parsed)                           # shape: [T, pod_num*pod_num]
# ai_max_vec = parsed.max(axis=0)        # Take the maximum at each matrix position.

# for idx in range(parsed.shape[0]):
#     ai_demand = ai_max_vec.copy()  # shape: [pod_num*pod_num]


#     dcn_demand = [0.0] * (len(nodes) * len(nodes))
#     for u in range(len(nodes)):
#         for v in range(len(nodes)):
#             if u == v: continue
#             frac = frac_dict[(u, v)]
#             # sample from gaussian with mean = frac, stddev = frac / 4
#             dcn_demand[u * len(nodes) + v] = total_demands * max(np.random.normal(frac, frac / 4), 0.0)
    
#     demand = ai_demand + dcn_demand
#     demand = demand.reshape(pod_num, pod_num)

#     # save_path = os.path.join(save_result_dir, str(idx+1) + '.pkl')
#     save_path = os.path.join(save_result_dir, f"t{idx+1+num_lines}.pkl")


#     with open(save_path, 'wb') as f:
#         pkl.dump(demand, f)