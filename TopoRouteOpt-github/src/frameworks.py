import torch
import gurobipy as grb

def calculate_out_threshold_flow(out_threshold_traffic, avail_ikm, use_self):

    pod_num, _, _ = avail_ikm.shape  # [pod_num, pod_num, m]
    idx = torch.arange(pod_num, device=out_threshold_traffic.device)
    i_idx, j_idx, k_idx = torch.meshgrid(idx, idx, idx, indexing='ij')  # [pod_num, pod_num, pod_num]
    mask = (k_idx != i_idx) & (k_idx != j_idx) & (i_idx != j_idx)  # [pod_num, pod_num, pod_num]

    # Compute min(avail_ikm[i, k], avail_ikm[k, j]) for all i, j, k
    # avail_ik[i, j, k, m] = avail_ikm[i, k, m]
    avail_ik = avail_ikm.unsqueeze(1).expand(-1, pod_num, -1, -1)  # [pod_num, pod_num, pod_num, m]
    # avail_kj[i, j, k, m] = avail_ikm[k, j, m]
    avail_kj = avail_ikm.transpose(0, 1).unsqueeze(0).expand(pod_num, -1, -1, -1)  # [pod_num, pod_num, pod_num, m]
    min_avail = torch.minimum(avail_ik, avail_kj)  # [pod_num, pod_num, pod_num, m]
    # import pdb;pdb.set_trace()
    # Apply the mask to exclude invalid paths
    min_avail = min_avail * mask.unsqueeze(-1)  # [pod_num, pod_num, pod_num, m]

    if use_self:
        min_avail = torch.cat((min_avail, avail_ikm.unsqueeze(2)), dim=2)  # [pod_num, pod_num, pod_num + 1, m]

    # Compute the sum of capacities for valid paths
    sum_capacity = min_avail.sum(dim=2)  # [pod_num, pod_num, m]

    # Compute routing weights
    routing_weight = torch.where(
        sum_capacity.unsqueeze(2) > 0,
        min_avail / (sum_capacity.unsqueeze(2) + 1e-8),  # Normalize by sum_capacity
        torch.zeros_like(min_avail)  # If sum_capacity is 0, set routing_weight to 0
    )  # [pod_num, pod_num, pod_num, m] / [pod_num, pod_num, pod_num + 1, m]
    # import pdb; pdb.set_trace()

    two_hop_out_threshold_flow = out_threshold_traffic.unsqueeze(2) * routing_weight[:,:,:pod_num,:]   # [pod_num, pod_num, pod_num, m]
    if use_self:
        single_hop_out_threshold_flow = out_threshold_traffic * routing_weight[:,:,pod_num,:]  # [pod_num, pod_num, m]
    else:
        single_hop_out_threshold_flow = torch.zeros_like(out_threshold_traffic)  # [pod_num, pod_num, m]

    return single_hop_out_threshold_flow, \
           two_hop_out_threshold_flow.sum(dim=1) + two_hop_out_threshold_flow.sum(dim=0).transpose(0, 1)  # [pod_num, pod_num, m]

def calculate_hop_count(traffic, single_hop_traffic):
    two_hop_traffic = torch.clamp(traffic - single_hop_traffic, min=0.0)

    single_hop_count = single_hop_traffic / (traffic + 1e-8)
    two_hop_count = 2 * (two_hop_traffic / (traffic + 1e-8))
    # import pdb; pdb.set_trace()
    i_idx, j_idx = torch.meshgrid(torch.arange(two_hop_count.shape[0]), torch.arange(two_hop_count.shape[1]), indexing='ij')
    src_dst_not_same_mask = (i_idx != j_idx).unsqueeze(-1).expand(-1, -1, two_hop_count.shape[-1])  # [pod_num, pod_num, m]
    hop_count = (two_hop_count + single_hop_count)[src_dst_not_same_mask]
    hop_count = hop_count.clamp(min=1.0)  # Ensure hop count is at least 1
    return hop_count.mean()

def TROD_threshold_mlu_loss(s, traffic, x, capacity, \
                            use_self = False, routing_weight_method = 'default',
                            history_params = None, tms_idx=1):
    # sijm = sij * ( xijm / (\sum_m xijm) )
    # for traffic_ijm if traffic_ijm <= sijm, then the flow will be send by the path passing ijm
    # if traffic_ijm > sijm, then the flow will be send by the two hop paths i->k->j,
    # so it will be send by the path passing ikm, kjm; the routing weight on each k will be
    # min(C_{ikm}-s_{ikm}, C_{kjm}-s_{kjm}) / (\sum_k min(C_{ikm}-s_{ikm}, C_{kjm}-s_{kjm}))
    # link utilization is defined by the flow divided by the capacity
    s_ijm = s.unsqueeze(2) * (x / (x.sum(dim=2, keepdim=True) + 1e-8)) # [pod_num, pod_num, m]
    if routing_weight_method == 'default':
        avail_ikm = torch.clamp(capacity - s_ijm, min=0.0)  # [pod_num, pod_num, m]
    elif routing_weight_method == 'hist':
        subthres = torch.minimum(history_params['history_traffic_max'], s_ijm)  # [pod_num, pod_num, m]
        avail_ikm = torch.clamp(capacity - subthres, min=0.0)  # [pod_num, pod_num, m]
    elif routing_weight_method == 'hist_with_std':
        protect_val = history_params['history_traffic_mean'] + \
                      history_params['history_traffic_std'] * history_params['std_multiplier']
        subthres = torch.minimum(protect_val, s_ijm)
        avail_ikm = torch.clamp(capacity - subthres, min=0.0)
    else:
        raise ValueError(f"Unknown routing weight method: {routing_weight_method}")
    
    
    in_threshold_traffic = torch.minimum(traffic, s_ijm)
    out_threshold_traffic = torch.clamp(traffic - s_ijm, min=0.0)
    # if tms_idx - 12 == 917:
    #     import pdb; pdb.set_trace()

    single_hop_out_threshold_flow, two_hop_out_threshold_flow \
        = calculate_out_threshold_flow(out_threshold_traffic, avail_ikm, use_self)
    
    link_flow = in_threshold_traffic + \
        single_hop_out_threshold_flow + two_hop_out_threshold_flow  # [pod_num, pod_num, m]

    link_utilization = link_flow / (capacity + 1e-8) # [pod_num, pod_num, m]
    mlu = link_utilization.max()
    hop_count = calculate_hop_count(traffic, in_threshold_traffic + single_hop_out_threshold_flow)
    
    return mlu, hop_count, link_utilization

def TROD_threshold_mlu_loss_split(s, traffic, x, capacity, \
                                  ai_pods = [], 
                                  use_self = False, routing_weight_method = 'default',
                                  history_params = None, tms_idx=1):
    """
    s:        [P,P]
    traffic:  [P,P,M]
    x:        [P,P,M]
    capacity: [P,P,M]
    ai_pods: list[int], indices of AI-group pods.
    Rules:
      - AI-to-AI traffic remains on direct links; disable two-hop capacity.
      - All other pairs follow TROD_threshold_mlu_loss.
    """
    P = s.shape[0]
    device = s.device
    dtype  = s.dtype

    # Distribute the base threshold in proportion to each layer’s link count.
    s_ijm = s.unsqueeze(2) * (x / (x.sum(dim=2, keepdim=True) + 1e-8))  # [P,P,M]

    # Available capacity for non-AI-to-AI traffic.
    avail_default = torch.clamp(capacity - s_ijm, min=0.0)  # [P,P,M]

    # Build an AI-to-AI mask without diagonal entries.
    ai_set = set(int(v) for v in ai_pods)
    if len(ai_set) == 0:
        ai_mask = torch.zeros((P, P), dtype=torch.bool, device=device)
    else:
        ai_idx = torch.tensor(sorted(ai_set), device=device, dtype=torch.long)
        ai_mask = torch.zeros((P, P), dtype=torch.bool, device=device)
        ii, jj = torch.meshgrid(ai_idx, ai_idx, indexing='ij')
        ai_mask[ii, jj] = True
        ai_mask = ai_mask & (~torch.eye(P, dtype=torch.bool, device=device))  # Clear diagonal entries.

    # --- in/out-threshold traffic ---
    in_th_default  = torch.minimum(traffic, s_ijm)               # [P,P,M]
    out_th_default = torch.clamp(traffic - s_ijm, min=0.0)       # [P,P,M]

    # Override routing rules for AI-to-AI traffic.
    # AI-to-AI traffic stays direct; disable two-hop capacity and threshold overflow.
    ai_mask_3d = ai_mask.unsqueeze(-1)                           # [P,P,1]
    zeros_like = torch.zeros(1, dtype=dtype, device=device).expand_as(traffic)

    avail_ikm = torch.where(ai_mask_3d, torch.zeros_like(avail_default), avail_default)  # [P,P,M]
    in_threshold_traffic  = torch.where(ai_mask_3d, traffic, in_th_default)              # [P,P,M]
    out_threshold_traffic = torch.where(ai_mask_3d, zeros_like, out_th_default)          # [P,P,M]

    # Assign above-threshold traffic to direct or two-hop paths; AI-to-AI overflow is zero.
    single_hop_out_threshold_flow, two_hop_out_threshold_flow = calculate_out_threshold_flow(
        out_threshold_traffic, avail_ikm, use_self
    )

    # Compute total link flow and utilization.
    link_flow = in_threshold_traffic + single_hop_out_threshold_flow + two_hop_out_threshold_flow  # [P,P,M]
    link_utilization = link_flow / (capacity + 1e-8)                                              # [P,P,M]
    mlu = link_utilization.max()

    single_hop_total = in_threshold_traffic + single_hop_out_threshold_flow  # [P,P,M]
    hop_count = calculate_hop_count(traffic, single_hop_total)

    return mlu, hop_count, link_utilization


def Spread_traffic_engineering(num_nodes, edges, candidate_path, path_capacity, edge_to_path, demand, Spread):
    """Compute the traffic engineering solutions for a single demand to minimize the worst-case MLU with Google's hedging mechanism.

    Args:
        demand: the traffic demand, shape: (number_of_nodes * number_of_nodes)
        Spread: the spread factor
    """
    if demand.shape != (num_nodes, num_nodes):
        demand = demand.reshape((num_nodes, num_nodes))
    else:
        demand = demand
    m = grb.Model('traffic_engineering_grb')
    m.Params.OutputFlag = 0

    mlu = m.addVar(lb = 0, vtype=grb.GRB.CONTINUOUS, name='mlu')
    name_path_weight = [f'w_{i}_{j}_{k}'
        for i in range(num_nodes)
        for j in range(num_nodes)
        if j != i
        for k in range(len(candidate_path[(i, j)]))
        ]
    path_weight = m.addVars(name_path_weight, lb=0, ub = 1, vtype=grb.GRB.CONTINUOUS, name='path_weight')
    
    m.addConstrs(
        grb.quicksum(
            path_weight[f'w_{i}_{j}_{k}'] for k in range(len(candidate_path[(i, j)]))
        ) == 1
        for i in range(num_nodes)
        for j in range(num_nodes)
        if j != i
    )
    m.addConstrs(
        grb.quicksum(
            path_weight[f'w_{src}_{dst}_{k}'] * demand[src][dst] for (src, dst, k) in edge_to_path[edge]
        ) <= mlu * edges[edge]['capacity']
        for edge in edges
    )
    m.addConstrs(
        path_weight[f'w_{i}_{j}_{k}'] * (Spread * grb.quicksum(
                path_capacity[(i, j, k)] for k in range(len(candidate_path[(i, j)]))
            )) <=  
            path_capacity[(i, j, k)] 
        for i in range(num_nodes)
        for j in range(num_nodes)
        if j != i
        for k in range(len(candidate_path[(i, j)]))
    )
    m.setObjective(mlu, grb.GRB.MINIMIZE)
    m.optimize()
    
    if m.status == grb.GRB.Status.OPTIMAL:
        solution = m.getAttr('x', path_weight)
        path_weight_routing = {}
        for w_name in name_path_weight:
            path_weight_routing[w_name] = solution[w_name]
        return m.objVal, path_weight_routing
    else:
        print('No solution')

def Get_MLU(num_nodes, edges, edge_to_path, path_weights, demand):
    """Get the MLU of the traffic engineering solution.

    Args:
        path_weights: the routing weights of the paths
        demand: the traffic demand, shape: (number_of_nodes * number_of_nodes)
    """
    if demand.shape != (num_nodes, num_nodes):
        demand = demand.reshape((num_nodes, num_nodes))
    mlu = 0
    for edge in edges:
        edge_lu = 0
        for (src, dst, k) in edge_to_path[edge]:
            edge_lu += path_weights[f'w_{src}_{dst}_{k}'] * demand[src][dst] / float(edges[edge]['capacity'])
        mlu = max(mlu, edge_lu)
    return mlu
