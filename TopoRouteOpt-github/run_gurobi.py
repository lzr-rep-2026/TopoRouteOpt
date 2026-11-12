import os
import gurobipy as gp
from gurobipy import GRB
from src.config import RESULT_DIR
import sys
import numpy as np
import torch
from tqdm import tqdm

from src.env import Env
from src.run_helper import parse_args
from src.frameworks import TROD_threshold_mlu_loss
from src.cal_topology import do_centralized_tpe, do_distributed_tpe
from src.config import RESULT_DIR, LOG_DIR
from src.utils import normalize_size

def calculate_hop_count_numpy(traffic, single_hop_traffic):
    two_hop_traffic = np.maximum(traffic - single_hop_traffic, 0.0)

    single_hop_count = single_hop_traffic / (traffic + 1e-8)
    two_hop_count = 2 * (two_hop_traffic / (traffic + 1e-8))
    
    i_idx, j_idx = np.meshgrid(np.arange(two_hop_count.shape[0]), 
                               np.arange(two_hop_count.shape[1]), 
                               indexing='ij')
    src_dst_not_same_mask = (i_idx != j_idx)[..., np.newaxis]  # [pod_num, pod_num, 1]
    src_dst_not_same_mask = np.broadcast_to(src_dst_not_same_mask, two_hop_count.shape)  # [pod_num, pod_num, m]
    
    hop_count = (two_hop_count + single_hop_count)[src_dst_not_same_mask]
    hop_count = np.maximum(hop_count, 1.0)  # Ensure hop count is at least 1
    return hop_count.mean()

props = parse_args(sys.argv[1:])

env = Env(props)
pod_num = env.pod_num
m = env.spine_num_per_pod
capacity = env.capacity.cpu().numpy()  # [pod_num, pod_num, m]
mlu_results = []
hop_count_results = []
with tqdm(env.test_pod_traffics) as tepoch:
    for tms_idx, tms in enumerate(tepoch):
        split_weights = (env.x / (env.x.sum(dim=-1, keepdim=True) + 1e-8)).cpu().numpy()
        spine_traffic = tms[:, :, np.newaxis] * split_weights # [pod_num, pod_num, m]
        model = gp.Model("Gurobi_Model")
        model.setParam('OutputFlag', 0)  # Disable Gurobi output
        split_weights_vars = model.addVars(pod_num, pod_num, pod_num+1, m, vtype=GRB.CONTINUOUS, name="split_weights")

        for spine in range(m):
            for i in range(pod_num):
                for j in range(pod_num):
                    for k in range(pod_num):
                        if k == i or k == j or i == j:
                            
                            model.addConstr(split_weights_vars[i, j, k, spine] == 0.0)

                    model.addConstr(
                        gp.quicksum(split_weights_vars[i, j, k, spine] for k in range(pod_num+1)) == 1.0,
                        name=f"sum_split_weights_{i}_{j}"
                    )

        # Create intermediate variables for routed traffic.
        two_hop_flow_vars = model.addVars(pod_num, pod_num, pod_num, m, vtype=GRB.CONTINUOUS, name="two_hop_flow")
        one_hop_flow_vars = model.addVars(pod_num, pod_num, m, vtype=GRB.CONTINUOUS, name="one_hop_flow")
        link_flow_vars = model.addVars(pod_num, pod_num, m, vtype=GRB.CONTINUOUS, name="link_flow")
        
        # Add flow-conservation constraints.
        for i in range(pod_num):
            for j in range(pod_num):
                for k in range(pod_num):
                    for spine in range(m):
                        model.addConstr(two_hop_flow_vars[i, j, k, spine] == 
                                      spine_traffic[i, j, spine] * split_weights_vars[i, j, k, spine])
                
                for spine in range(m):
                    model.addConstr(one_hop_flow_vars[i, j, spine] == 
                                  spine_traffic[i, j, spine] * split_weights_vars[i, j, pod_num, spine])
                    
                    model.addConstr(link_flow_vars[i, j, spine] == 
                                  one_hop_flow_vars[i, j, spine] + 
                                  gp.quicksum(two_hop_flow_vars[k, j, i, spine] for k in range(pod_num)) +
                                  gp.quicksum(two_hop_flow_vars[i, k, j, spine] for k in range(pod_num)))

        # Create the maximum-link-utilization variable.
        max_util = model.addVar(vtype=GRB.CONTINUOUS, name="max_util")
        
        # Bound each link load by maximum utilization.
        for i in range(pod_num):
            for j in range(pod_num):
                for spine in range(m):
                    model.addConstr(max_util * capacity[i, j, spine] >= link_flow_vars[i, j, spine])

        # Minimize maximum link utilization.
        model.setObjective(max_util, GRB.MINIMIZE)
        model.optimize()
        
        if model.status == GRB.OPTIMAL:
            print(f"Optimal objective value: {model.ObjVal}")
            mlu_results.append(model.ObjVal)

            one_hop_flow = np.array([one_hop_flow_vars[i, j, spine].X for i in range(pod_num) for j in range(pod_num) for spine in range(m)]).reshape(pod_num, pod_num, m)
            hop_count = calculate_hop_count_numpy(spine_traffic, one_hop_flow)
            hop_count_results.append(hop_count)
            
        else:
            print(f"Model not solved to optimality at index {tms_idx}, status: {model.status}")
        
result_path = os.path.join(RESULT_DIR, f'{props.topo_name}', 'Gurobi_te', props.init_topo_method, 'test_results.txt')
os.makedirs(os.path.dirname(result_path), exist_ok=True)

hop_count_result_path = result_path.replace('test_results.txt', 'test_hop_count_results.txt')
os.makedirs(os.path.dirname(hop_count_result_path), exist_ok=True)

with open(result_path, 'w') as f:
    for mlu in mlu_results:
        f.write(f"{mlu}\n")
f.close()
with open(hop_count_result_path, 'w') as f:
    for hc in hop_count_results:
        f.write(f"{hc}\n")
f.close()