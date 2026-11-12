import numpy as np
import copy
import math
import gurobipy as gp
from gurobipy import GRB
import torch
from src.utils import normalize_size
from collections import deque


def find_p_percentile(traffic_seq, p, i, j):
    # Extract the i-to-j demand from each historical traffic matrix and compute its percentile.
    record = []
    for tm in traffic_seq:
        record.append(tm[i][j])
    record = np.array(record)
    return np.percentile(record, p)

def _find_delta(rows, cols, ingress_capacity, egress_capacity):
    # Maximum uniform increment for every (i, j) without exceeding any row or column budget.
    # In the first case, there is only a diagonal entry left. Thus,
    # we cannot allocate capacity any more.
    if len(rows) == 1 and len(cols) == 1 and rows[0] == cols[0]:
        return 0
    delta = egress_capacity[rows[0]]
    num_rows = len(rows)
    num_cols = len(cols)
    for row in rows:
        total_gap = egress_capacity[row]
        if row in cols:
            if num_cols > 1:
                delta = min(delta, total_gap / (num_cols - 1))
        else:
            delta = min(delta, total_gap / num_cols)
    for col in cols:
        total_gap = ingress_capacity[col]
        if col in rows:
            if num_rows > 1:
                delta = min(delta, total_gap / (num_rows - 1))
        else:
            delta = min(delta, total_gap / num_rows)
    return delta


def _compute_topology(pods_num, threshold_matrix, r_ingress, r_egress):
    # Set the diagonal entries as 0.
    for pod in range(pods_num):
        threshold_matrix[pod][pod] = 0

    remain_ingress = r_ingress.astype(np.float64)
    remain_egress = r_egress.astype(np.float64)
    remain_rows = [i for i in range(pods_num)]
    remain_cols = [i for i in range(pods_num)]

    d_ij = copy.deepcopy(threshold_matrix)
    for i in range(pods_num):
        for j in range(pods_num):
            if i == j:
                continue
            remain_ingress[j] -= d_ij[i][j]
            remain_egress[i] -= d_ij[i][j]
    for i in range(pods_num):
        if remain_ingress[i] < 0 or remain_egress[i] < 0:
            print("Threshold values are too large!")
            exit()

    while True:
        # Computes the max scaling factor
        delta = _find_delta(remain_rows, remain_cols, remain_ingress, remain_egress)
        if delta < 0.0001:
            break
        # Updates topology
        for row in remain_rows:
            for col in remain_cols:
                if row == col:
                    continue
                remain_egress[row] -= delta
                remain_ingress[col] -= delta
                d_ij[row][col] += delta
        # Remove rows and cols with no capacity
        rows_to_be_removed = []
        for row in remain_rows:
            if remain_egress[row] < 0.0001:
                rows_to_be_removed.append(row)
        for row in rows_to_be_removed:
            remain_rows.remove(row)
        cols_to_be_removed = []
        for col in remain_cols:
            if remain_ingress[col] < 0.0001:
                cols_to_be_removed.append(col)
        for col in cols_to_be_removed:
            remain_cols.remove(col)
        # Break if remain_ingress or remain_egress is empty
        if len(remain_rows) == 0 or len(remain_cols) == 0:
            break
        
    return d_ij


def satisfy_physical_bound(topo_links, pods_num, r_ingress, r_egress):
    """ topo    True
            False
    """
    ingress = topo_links.sum(axis = 0)   #  
    egress = topo_links.sum(axis = 1)  #  
    
    flag = True
    for i in range(pods_num):
        # links    False
        if ingress[i] > r_ingress[i] or egress[i] > r_egress[i]:
            flag = False
            break
    return flag


def to_integer_topo(d_ij, r_egress, r_ingress, pods_num):
    """      
    """
    ori_shape = d_ij.shape

    # Take the fractional part of each fractional-topology entry.
    #  list
    flat_topo = d_ij.flatten().tolist()
    # print(flat_topo)
    #      key
    index_frac_dict = {}
    for i in range(len(flat_topo)):
        index_frac_dict[i] = math.modf(flat_topo[i])[0]

    # Sort by fractional part in descending order.
    #  sorted list  tuple
    index_frac_list = sorted(index_frac_dict.items(), key = lambda x : x[1], reverse = True)
    
    # Start by rounding all entries down.
    integer_topo = np.floor(d_ij)

    # print(integer_topo)
    # Remaining capacity in each row and column budget.
    egress_floor_sum = np.sum(integer_topo, axis=1)
    ingress_floor_sum = np.sum(integer_topo, axis=0)
    res_r_egress = r_egress - egress_floor_sum
    res_r_ingress = r_ingress - ingress_floor_sum
    # print(res_r_egress)
    # print(res_r_ingress)

    # Add one in descending fractional order when both row and column have room; skip the diagonal.
    for (index, _) in index_frac_list:
        row = math.floor(index / pods_num)
        column = index % pods_num
        if row == column:
            continue
        if res_r_egress[row] > 0 and res_r_ingress[column] > 0:
            res_r_egress[row] -= 1
            res_r_ingress[column] -= 1
            integer_topo[row][column] += 1
    if satisfy_physical_bound(integer_topo, pods_num, r_ingress, r_egress) == False:
        print('Error when mapping fractional topology to integer topology!')
        exit(0)

    return integer_topo


def get_topology(traffic_seq, percentile, pods_num, bandwidth, port_num):
    threshold = np.zeros((pods_num, pods_num))
    for i in range(pods_num):
        for j in range(pods_num):
            if i == j:
                continue
            #  threshold   bandwidth     bandwidth
            # Historical p-th percentile demand divided by link bandwidth gives the required link fraction.
            threshold[i][j] = find_p_percentile(traffic_seq, percentile*100, i, j) / bandwidth[i][j]
    # import pdb; pdb.set_trace()
    r_ingress = np.ones(pods_num) * port_num
    r_egress = np.ones(pods_num) * port_num
    # Raise the fractional topology uniformly up to the feasible row and column boundary.
    topo = _compute_topology(pods_num, threshold, r_ingress, r_egress)
    # Convert fractional connections to integers with the largest-remainder method.
    topo = to_integer_topo(topo, r_egress, r_ingress, pods_num)

    # Find the smallest positive gap between an integer connection count and its demand threshold.
    min_gap = 10000
    for i in range(pods_num):
        for j in range(pods_num):
            if i != j and topo[i][j] > threshold[i][j]:
                min_gap = min(min_gap, topo[i][j] - threshold[i][j])
    # Update the threshold values (Here we assume that all the links have the same bandwidth.)
    # Recompute the threshold matrix, assuming equal bandwidth on all links.
    _threshold = np.zeros((pods_num, pods_num))
    for i in range(pods_num):
        for j in range(pods_num):
            if i != j:
                #  42 43   topo*bandwidth  topo*bandwidth
                if topo[i][j] > threshold[i][j]:
                    _threshold[i][j] = (topo[i][j] - min_gap) * bandwidth[i][j]
                else:
                    _threshold[i][j] = topo[i][j] * bandwidth[i][j]
    return topo, _threshold


def split_matrix(original, M=4):

    X_rem = original.copy()
    split_results = []
    N = X_rem.shape[0]
    
    for m in range(1, M+1):
        current_rounds = M - m + 1
        
        model = gp.Model(f"Split_Round_{m}")
        model.setParam('OutputFlag', 0)  # Suppress Gurobi output
        
        # Create decision variables.
        x = {}
        for i in range(N):
            for j in range(N):
                if i == j:
                    continue
                lb = X_rem[i,j] // current_rounds
                ub = (X_rem[i,j] + current_rounds-1) // current_rounds
                x[i,j] = model.addVar(lb=lb, ub=ub, vtype=GRB.INTEGER)
        
        # Row constraints.
        for i in range(N):
            row_sum = sum(X_rem[i,j] for j in range(N) if j != i)
            lower = row_sum // current_rounds
            upper = (row_sum + current_rounds-1) // current_rounds
            model.addConstr(sum(x[i,j] for j in range(N) if j != i) <= upper)
            model.addConstr(sum(x[i,j] for j in range(N) if j != i) >= lower)
        
        # Column constraints.
        for j in range(N):
            col_sum = sum(X_rem[i,j] for i in range(N) if i != j)
            lower = col_sum // current_rounds
            upper = (col_sum + current_rounds-1) // current_rounds
            model.addConstr(sum(x[i,j] for i in range(N) if i != j) <= upper)
            model.addConstr(sum(x[i,j] for i in range(N) if i != j) >= lower)
        
        # Objective: minimize maximum utilization.
        u = model.addVar()
        for i in range(N):
            for j in range(N):
                if i == j: continue
                model.addConstr(x[i,j] <= u * current_rounds)
        model.setObjective(u, GRB.MINIMIZE)
        
        model.optimize()
        
        # Store the result.
        Xm = np.zeros_like(original)
        for i in range(N):
            for j in range(N):
                if i != j:
                    Xm[i,j] = int(x[i,j].x)
        
        X_rem -= Xm
        split_results.append(Xm)
        
    return split_results

def trod_tpe(traffic_seq, percentile, pods_num, bandwidth, port_num, spine_num):
    topo, threshold = get_topology(traffic_seq, percentile, pods_num, bandwidth, port_num)
    spine_topo = split_matrix(topo, M=spine_num)
    return spine_topo, threshold


def do_centralized_tpe(inputs, x, s, props, env, history_tms, device):
    mean_inputs = inputs.mean(dim=0)
    need_link_mask = (mean_inputs > s * 0.6)
    history_tms = list(history_tms)
    trigger_flag = False
    if need_link_mask.any():
        trigger_flag = True
        traffic_seq = history_tms[-props.centralized_tpe_len:] if len(history_tms) >= props.centralized_tpe_len else history_tms
        x,_ = trod_tpe(traffic_seq=traffic_seq,
                            percentile=env.percentile,
                            pods_num=env.pod_num,
                            bandwidth=np.ones((env.pod_num, env.pod_num)) * normalize_size(env.bandwidth_per_port),
                            port_num=env.port_num_per_port,
                            spine_num=env.spine_num_per_pod)
        x = torch.from_numpy(np.stack(x, axis=-1)).to(dtype=torch.float32, device=device)
        x = x.reshape(env.pod_num, env.pod_num, env.spine_num_per_pod)
    return x, trigger_flag

@torch.no_grad()
def do_distributed_tpe(links: torch.Tensor, 
                       add_link_history_traffic, add_link_history_links, 
                       remove_link_history_traffic, remove_link_history_links,
                       bandwidth_per_port: float, 
                       std_ratio,
                       max_links: int = 16, min_links: int = 1,
                       frame_idx: int = None, add_link_interval: int = 1, remove_link_interval: int = 1800,
                       add_thr: float = 0.9, remove_thr: float = 0.9, 
                       remove_strict: int = 1, change_all: int = 0):
    # change_all=0: change at most one spine link per (i, j) pair in each round.
    # change_all=1: change all spine links for a pair together when every spine is feasible.
    P, _, M = links.shape
    device, dtype = links.device, links.dtype
    trigger_flag = False
    offdiag = ~torch.eye(P, dtype=bool, device=device)
    norm_bw = torch.tensor(float(normalize_size(bandwidth_per_port)), device=device, dtype=dtype)
    
    # Remove links only when the history window is full and the interval is due.
    remove_ready = (hasattr(remove_link_history_traffic, "maxlen") and len(remove_link_history_traffic) >= remove_link_history_traffic.maxlen)
    remove_due   = (frame_idx is not None and frame_idx > 0 and remove_link_interval > 0 and frame_idx % remove_link_interval == 0)

    if remove_ready and remove_due:
        # [W_rem, P, P, M]
        T_rem = torch.stack(list(remove_link_history_traffic), dim=0)
        L_rem = torch.stack(list(remove_link_history_links),   dim=0)
        C_rem = L_rem * norm_bw

        # Require traffic below remove_thr times capacity throughout the window; then aggregate to [P, P].
        remove_mask = (T_rem < (remove_thr * C_rem)).all(dim=0).any(dim=2) #[P, P]
        remove_mask = remove_mask & offdiag #[P, P]

        if remove_mask.any():
            if change_all == 0:
                if remove_strict == 1:
                    cand_sub = (links > min_links) & remove_mask[:, :, None] # [P, P, M]
                    has_cand = cand_sub.any(dim=2) # [P, P] indicates whether each pair has a spine layer eligible for removal.
                    if has_cand.any():
                        masked   = torch.where(cand_sub, links, torch.full_like(links, float('-inf')))
                        chosen_m = masked.argmax(dim=2)     # [P,P]
                        ii, jj   = torch.where(has_cand)
                        kk       = chosen_m[ii, jj]
                        # Separate entries greater than one from entries equal to one.
                        v = links[ii, jj, kk]
                        gt_mask = v > 1.0
                        eq_mask = v == 1.0

                        # Remove directly when the connection count exceeds one.
                        if gt_mask.any():
                            ii_gt, jj_gt, kk_gt = ii[gt_mask], jj[gt_mask], kk[gt_mask]
                            links[ii_gt, jj_gt, kk_gt] -= 1.0
                            trigger_flag = True

                        # Check connectivity before removing the last connection on a layer.
                        if eq_mask.any():
                            ii_eq, jj_eq, kk_eq = ii[eq_mask], jj[eq_mask], kk[eq_mask]
                            ii_ok, jj_ok, kk_ok = check_connectivity(links, ii_eq, jj_eq, kk_eq)
                            if ii_ok.numel() > 0:
                                links[ii_ok, jj_ok, kk_ok] -= 1.0
                                trigger_flag = True

                elif remove_strict == 0:
                    total_links = links.sum(dim=2) #[P, P]
                    pair_ok = (total_links > min_links) & remove_mask #[P, P]

                    if pair_ok.any():
                        # For each eligible pair, remove from the spine layer with the most connections.
                        chosen_m = links.argmax(dim=2)  # [P,P]
                        ii, jj = torch.where(pair_ok)
                        kk = chosen_m[ii, jj]
                        # Separate entries greater than one from entries equal to one.
                        v = links[ii, jj, kk]
                        gt_mask = v > 1.0
                        eq_mask = v == 1.0

                        # Remove directly when the connection count exceeds one.
                        if gt_mask.any():
                            ii_gt, jj_gt, kk_gt = ii[gt_mask], jj[gt_mask], kk[gt_mask]
                            links[ii_gt, jj_gt, kk_gt] -= 1.0
                            trigger_flag = True

                        # Check connectivity before removing the last connection on a layer.
                        if eq_mask.any():
                            ii_eq, jj_eq, kk_eq = ii[eq_mask], jj[eq_mask], kk[eq_mask]
                            ii_ok, jj_ok, kk_ok = check_connectivity(links, ii_eq, jj_eq, kk_eq)
                            if ii_ok.numel() > 0:
                                links[ii_ok, jj_ok, kk_ok] -= 1.0
                                trigger_flag = True
        
            elif change_all == 1:
                per_m_ok = (links > min_links).all(dim=2) # [P, P]
                pair_ok = remove_mask & per_m_ok # [P, P]
                if pair_ok.any():
                    ii, jj = torch.where(pair_ok)
                    if ii.numel() > 0:
                        # Use the connection count on layer m=0 to divide candidates quickly.
                        v0 = links[ii, jj, 0]                # [B]
                        gt_mask = v0 > 1.0                   # This group can be removed without a connectivity check.
                        eq_mask = v0 == 1.0                  # This group needs a connectivity check before removal.

                        # Remove from every layer directly when the count exceeds one.
                        if gt_mask.any():
                            ii_gt, jj_gt = ii[gt_mask], jj[gt_mask]
                            links[ii_gt, jj_gt, :] -= 1.0
                            trigger_flag = True

                        # Remove from every layer after a connectivity check when the count equals one.
                        if eq_mask.any():
                            ii_eq, jj_eq = ii[eq_mask], jj[eq_mask]
                            k0 = torch.zeros_like(ii_eq)     # Check m=0 as a representative layer.
                            ii_ok, jj_ok, _ = check_connectivity(links, ii_eq, jj_eq, k0)
                            if ii_ok.numel() > 0:
                                links[ii_ok, jj_ok, :] -= 1.0
                                trigger_flag = True

    # Add links.
    # Add links when the history window is full and the interval is due; at most one per pair.
    add_ready = (hasattr(add_link_history_traffic, "maxlen")
                and len(add_link_history_traffic) >= add_link_history_traffic.maxlen)
    add_due   = (frame_idx is not None and frame_idx > 0
                and add_link_interval > 0 and frame_idx % add_link_interval == 0)

    if add_ready and add_due:
        # [W_add, P, P, M]
        T_add = torch.stack(list(add_link_history_traffic), dim=0)
        L_add = torch.stack(list(add_link_history_links),   dim=0)
        L_add = torch.clamp(L_add, min=0.5) # Treat zero-connection links as having 0.5 connections for this capacity check.
        C_add = L_add * norm_bw

        # Require traffic above add_thr times capacity throughout the window; aggregate to [P, P].
        add_mask = (T_add > (add_thr * C_add)).all(dim=0).any(dim=2)  # [P,P]
        add_mask = add_mask & offdiag

        if add_mask.any():
            # Keep row and column connection totals below max_links.
            row_sum = links.sum(dim=1)  # [P,M]
            col_sum = links.sum(dim=0)  # [P,M]
            slack_row = (max_links - row_sum).clone()  # [P,M]
            slack_col = (max_links - col_sum).clone()  # [P,M]

            row_ok = slack_row[:, None, :] >= 1         # [P,1,M] -> will be updated during greediness
            col_ok = slack_col[None, :, :] >= 1         # [1,P,M]

            # A pair is eligible only if its count and row/column budgets have room.
            cand_add = (links < max_links) & row_ok & col_ok          # [P,P,M]
            cand_add = cand_add & add_mask[:, :, None]

            if cand_add.any():
                # Prioritize congested pairs using mean traffic divided by mean capacity.
                T_mean = T_add.mean(dim=0)                  # [P,P,M]
                C_mean = (L_add.mean(dim=0) * norm_bw)      # [P,P,M]
                pair_score = (T_mean / (C_mean + 1e-8)).mean(dim=2) #[P,P]

                # Give a score only to pairs with at least one eligible spine layer.
                pair_has_cand = cand_add.any(dim=2)       # [P,P]
                pair_score = torch.where(pair_has_cand, pair_score,
                                        torch.full_like(pair_score, float('-inf')))

                # Visit eligible pairs in descending congestion-score order.
                score_flat = pair_score.view(-1) # Flatten [P, P] to [P*P].
                pair_idx = torch.nonzero(score_flat > float('-inf'), as_tuple=False).squeeze(1) # One-dimensional tensor.
                sorted_idx = pair_idx[torch.argsort(score_flat[pair_idx], descending=True)]
                # Convert flat indices back to (i, j).
                ii, jj = torch.div(sorted_idx, P, rounding_mode='floor'), sorted_idx % P
                order_pairs = torch.stack([ii, jj], dim=1)        # [N_cand, 2]

                # Mark pairs so each receives at most one addition per round.
                touched_pair = torch.zeros((P, P), dtype=torch.bool, device=device)
                any_added = False

                for i, j in order_pairs:
                    if not add_mask[i, j]:
                        continue
                    if touched_pair[i, j]:
                        continue
                    
                    # change_all=1 requires room on every spine layer for the pair.
                    if change_all == 1:
                        # First check static eligibility on every spine layer.
                        all_ok_cand = cand_add[i, j, :].all()
                        if not all_ok_cand:
                            continue
                        # Recheck current slack and limits after earlier greedy additions.
                        # Each row and column must have at least one unit of slack.
                        # The current (i, j, m) count must remain below max_links.
                        enough_row = (slack_row[i, :] >= 1)               # [M]
                        enough_col = (slack_col[j, :] >= 1)               # [M]
                        below_cap  = (links[i, j, :] < max_links)         # [M]
                        all_ok_now = (enough_row & enough_col & below_cap).all()
                        if not all_ok_now:
                            continue
                        # Add one on every layer and update the remaining budgets.
                        links[i, j, :] += 1.0
                        slack_row[i, :] -= 1
                        slack_col[j, :] -= 1
                        touched_pair[i, j] = True
                        any_added = True

                    elif change_all == 0:
                        # Skip a pair already changed in this round.
                        if touched_pair[i, j]:
                            continue

                        cand_m = cand_add[i, j, :]                    # [M]
                        if not cand_m.any():
                            continue

                        # Choose the eligible spine layer with the fewest existing connections.
                        # Assign infinity to ineligible layers so they cannot be selected.
                        links_ij = links[i, j, :]                     # [M]
                        masked_links = torch.where(cand_m, links_ij, torch.full_like(links_ij, float('inf')))
                        m_star = torch.argmin(masked_links)

                        # Recheck current slack after earlier greedy additions.
                        if (links[i, j, m_star] >= max_links):
                            continue
                        if slack_row[i, m_star] < 1 or slack_col[j, m_star] < 1:
                            continue

                        # Add the connection, update budgets, and mark the pair.
                        links[i, j, m_star] += 1.0
                        slack_row[i, m_star] -= 1
                        slack_col[j, m_star] -= 1
                        touched_pair[i, j] = True
                        any_added = True

                if any_added:
                    trigger_flag = True


    return links, trigger_flag


@torch.no_grad()
def do_distributed_tpe_split_pod(
    links: torch.Tensor, 
    add_link_history_traffic, add_link_history_links, 
    remove_link_history_traffic, remove_link_history_links,
    bandwidth_per_port: float, 
    std_ratio,
    max_links: int = 16, min_links: int = 1,
    frame_idx: int = None, add_link_interval: int = 1, remove_link_interval: int = 1800,
    add_thr: float = 0.9, remove_thr: float = 0.9, 
    remove_strict: int = 1, change_all: int = 0,
    history_tms=None,            
    cur_tms=None               
):
    """
    After the existing add/remove logic in do_distributed_tpe:
    - Find newly active (i,j) pairs with positive current demand and zero history.
    - change_all == 1:
        * k_all = floor(cur[i,j] / (M * bw)); try to add equally on all layers.
        * Add k_all where feasible; otherwise allocate evenly per layer and
          use the minimum feasible count across layers for the pair.
    - change_all == 0:
        * k_pair = floor(cur[i,j] / bw) total new connections.
          Allocate layer by layer subject to row/column budgets, gaps, and
          remaining demand.
    """
    device, dtype = links.device, links.dtype
    P, _, M = links.shape
    triggered = False

    # First run the existing distributed topology adaptation.
    links, base_triggered = do_distributed_tpe(
        links,
        add_link_history_traffic, add_link_history_links,
        remove_link_history_traffic, remove_link_history_links,
        bandwidth_per_port, std_ratio,
        max_links=max_links, min_links=min_links,
        frame_idx=frame_idx,
        add_link_interval=add_link_interval,
        remove_link_interval=remove_link_interval,
        add_thr=add_thr, remove_thr=remove_thr,
        remove_strict=remove_strict, change_all=change_all
    )
    if base_triggered:
        triggered = True

    # Return early if history/current traffic is missing or no postprocessing is needed.
    if history_tms is None or cur_tms is None:
        return links, triggered

    # Build current and historical [P, P] demand matrices.
    cur = torch.as_tensor(cur_tms, device=device, dtype=dtype)
    if cur.ndim == 3:
        cur = cur.sum(dim=-1)

    hist_stack = []
    for tm in list(history_tms):
        t = torch.as_tensor(tm, device=device, dtype=dtype)
        if t.ndim == 3:
            t = t.sum(dim=-1)
        hist_stack.append(t)
    if len(hist_stack) == 0:
        return links, triggered
    H = torch.stack(hist_stack, dim=0)  # [W,P,P]

    # Identify newly active (i, j) pairs.
    eye = torch.eye(P, dtype=torch.bool, device=device)
    new_pair_mask = (cur > 0) & (H == 0).all(dim=0) & (~eye)  # [P,P]
    if not new_pair_mask.any():
        return links, triggered

    # Shared connection budget.
    bw = float(normalize_size(bandwidth_per_port))
    row_sum = links.sum(dim=1)                               # [P,M]
    col_sum = links.sum(dim=0)                               # [P,M]
    slack_row = (max_links - row_sum).clamp(min=0).to(torch.long)   # [P,M]
    slack_col = (max_links - col_sum).clamp(min=0).to(torch.long)   # [P,M]
    gap_ijm   = (max_links - links).clamp(min=0).to(torch.long)     # [P,P,M]

    add_ijm_total = torch.zeros_like(links)  # Accumulate new connections.

    # Branch A: change_all == 1.
    if change_all == 1:
        # Add the same number on every spine layer.
        denom = (M * bw) if bw > 0 else 1.0
        k_target = torch.floor(cur / denom).to(torch.long)   # [P,P]
        k_target = torch.where(new_pair_mask, k_target, torch.zeros_like(k_target))
        if (k_target > 0).any():
            # Desired number of new connections.
            k_broadcast = k_target[:, :, None].expand(P, P, M)
            want_ijm = torch.minimum(k_broadcast, gap_ijm)
            want_ijm = torch.where(new_pair_mask[:, :, None], want_ijm, torch.zeros_like(want_ijm))

            # Detect budget conflicts.
            row_demand = want_ijm.sum(dim=1)  # [P,M]
            col_demand = want_ijm.sum(dim=0)  # [P,M]
            no_conflict = (row_demand <= slack_row).all() and (col_demand <= slack_col).all()

            if no_conflict:
                add_ijm_total = want_ijm.to(add_ijm_total.dtype)
            else:
                # Distribute evenly across layers and take the minimum for each (i, j).
                add_tmp = torch.zeros_like(links)
                want_long = want_ijm.clone()
                for m in range(M):
                    pair_m = new_pair_mask & (want_long[:, :, m] > 0)
                    if not pair_m.any():
                        continue
                    row_budget = slack_row[:, m].clone()
                    col_budget = slack_col[:, m].clone()
                    w = want_long[:, :, m].clone()

                    row_share = torch.zeros((P, P), dtype=torch.long, device=device)
                    for i in range(P):
                        js = torch.where(pair_m[i])[0]
                        if js.numel() == 0 or row_budget[i] == 0:
                            continue
                        k = js.numel()
                        base = row_budget[i] // k
                        rem  = row_budget[i] %  k
                        row_share[i, js] = base
                        if rem > 0:
                            row_share[i, js[:int(rem.item())]] += 1
                        row_share[i, js] = torch.minimum(row_share[i, js], w[i, js])

                    col_share = torch.zeros((P, P), dtype=torch.long, device=device)
                    for j in range(P):
                        is_ = torch.where(pair_m[:, j])[0]
                        if is_.numel() == 0 or col_budget[j] == 0:
                            continue
                        k = is_.numel()
                        base = col_budget[j] // k
                        rem  = col_budget[j] %  k
                        col_share[is_, j] = base
                        if rem > 0:
                            col_share[is_[:int(rem.item())], j] += 1
                        col_share[is_, j] = torch.minimum(col_share[is_, j], w[is_, j])

                    share_m = torch.minimum(w, torch.minimum(row_share, col_share))
                    add_tmp[:, :, m] = share_m.to(add_tmp.dtype)

                per_pair_inc = add_tmp.min(dim=2, keepdim=True).values.to(torch.long)
                per_pair_inc = torch.minimum(per_pair_inc, gap_ijm.min(dim=2, keepdim=True).values)
                add_ijm_total = per_pair_inc.expand(-1, -1, M).to(add_tmp.dtype)

    # Branch B: change_all == 0.
    else:
        # Each new pair needs floor(current demand / bandwidth) connections in total.
        denom = bw if bw > 0 else 1.0
        k_pair = torch.floor(cur / denom).to(torch.long)  # [P,P]
        k_pair = torch.where(new_pair_mask, k_pair, torch.zeros_like(k_pair))

        if (k_pair > 0).any():
            k_rem = k_pair.clone()  # Remaining demand.
            add_tmp = torch.zeros_like(links)

            # Allocate across spine layers while consuming the remaining demand.
            for m in range(M):
                # New pairs with remaining demand and available gap.
                pair_m = new_pair_mask & (k_rem > 0) & (gap_ijm[:, :, m] > 0)
                if not pair_m.any():
                    continue

                row_budget = slack_row[:, m].clone()
                col_budget = slack_col[:, m].clone()

                # Maximum allocation on this layer is bounded by gap and remaining demand.
                w = torch.minimum(gap_ijm[:, :, m], k_rem)  # [P,P]
                w = torch.where(pair_m, w, torch.zeros_like(w))

                # Distribute across rows without exceeding w.
                row_share = torch.zeros((P, P), dtype=torch.long, device=device)
                for i in range(P):
                    js = torch.where(pair_m[i])[0]
                    if js.numel() == 0 or row_budget[i] == 0:
                        continue
                    k = js.numel()
                    base = row_budget[i] // k
                    rem  = row_budget[i] %  k
                    row_share[i, js] = base
                    if rem > 0:
                        row_share[i, js[:int(rem.item())]] += 1
                    row_share[i, js] = torch.minimum(row_share[i, js], w[i, js])

                # Distribute across columns without exceeding w.
                col_share = torch.zeros((P, P), dtype=torch.long, device=device)
                for j in range(P):
                    is_ = torch.where(pair_m[:, j])[0]
                    if is_.numel() == 0 or col_budget[j] == 0:
                        continue
                    k = is_.numel()
                    base = col_budget[j] // k
                    rem  = col_budget[j] %  k
                    col_share[is_, j] = base
                    if rem > 0:
                        col_share[is_[:int(rem.item())], j] += 1
                    col_share[is_, j] = torch.minimum(col_share[is_, j], w[is_, j])

                # Final allocation respects row/column budgets, gap, and remaining demand.
                share_m = torch.minimum(w, torch.minimum(row_share, col_share))  # [P,P]

                # Apply additions to the accumulator and update budgets and remaining demand.
                add_tmp[:, :, m] = share_m.to(add_tmp.dtype)
                # Update row and column budgets.
                row_budget -= share_m.sum(dim=1)
                col_budget -= share_m.sum(dim=0)
                # Update remaining demand for each pair.
                k_rem -= share_m

                # Stop early when all demand is met.
                if (k_rem <= 0).all():
                    break

            add_ijm_total = add_tmp

    # Apply the additions.
    if (add_ijm_total > 0).any():
        links = links + add_ijm_total
        triggered = True

    return links, triggered

@torch.no_grad()
def do_distributed_tpe_split_ideal(
    links: torch.Tensor,
    add_link_history_traffic,
    add_link_history_links,
    remove_link_history_traffic,
    remove_link_history_links,
    bandwidth_per_port: float,
    std_ratio,
    max_links: int = 16,
    min_links: int = 1,
    frame_idx: int = None,
    add_link_interval: int = 1,
    remove_link_interval: int = 1800,
    add_thr: float = 0.9,
    remove_thr: float = 0.9,
    remove_strict: int = 1,
    change_all: int = 0,
    history_tms=None,            
    cur_tms=None,                # Used for trod_tpe on the AI subgraph.
    ai_pods=None                 # AI pod indices.
):
    """
    Apply do_distributed_tpe to the DCN subgraph and trod_tpe to the AI
    subgraph using the current traffic frame and percentile 1.0. Keep the
    groups disconnected and combine their resulting links.
    Returns: (new_links, trigger_flag).
    """
    device, dtype = links.device, links.dtype
    P, _, M = links.shape
    trigger_flag = False

    # 1. Partition AI and DCN pods.
    if ai_pods is None:
        ai_pods = []
    ai_set  = set(int(i) for i in ai_pods)
    all_set = set(range(P))
    dcn_set = all_set - ai_set

    ai_idx  = torch.tensor(sorted(ai_set),  device=device, dtype=torch.long)
    dcn_idx = torch.tensor(sorted(dcn_set), device=device, dtype=torch.long)

    # Return early when all pods belong to one group.
    only_ai  = (len(ai_idx)  == P)
    only_dcn = (len(dcn_idx) == P)

    # 2. Run do_distributed_tpe on the DCN subgraph.
    # Slice links and history from [P, P, M] to [DCN, DCN, M].
    def _slice_hist_deque(hist_deq, rows, cols):
        if hist_deq is None:
            return None
        out = deque(maxlen=getattr(hist_deq, "maxlen", None))
        for t in hist_deq:
            # Each history entry is a [P, P, M] torch tensor.
            out.append(t.index_select(0, rows).index_select(1, cols))
        return out

    new_links_dcn_full = torch.zeros_like(links)

    if len(dcn_idx) >= 2:
        links_dcn = links.index_select(0, dcn_idx).index_select(1, dcn_idx).clone()

        add_hist_t_dcn = _slice_hist_deque(add_link_history_traffic, dcn_idx, dcn_idx)
        add_hist_l_dcn = _slice_hist_deque(add_link_history_links,   dcn_idx, dcn_idx)
        rem_hist_t_dcn = _slice_hist_deque(remove_link_history_traffic, dcn_idx, dcn_idx)
        rem_hist_l_dcn = _slice_hist_deque(remove_link_history_links,   dcn_idx, dcn_idx)

        # Run the existing do_distributed_tpe on the DCN subgraph.
        dcn_updated, dcn_trigger = do_distributed_tpe(
            links_dcn,
            add_hist_t_dcn, add_hist_l_dcn,
            rem_hist_t_dcn, rem_hist_l_dcn,
            bandwidth_per_port, std_ratio,
            max_links=max_links, min_links=min_links,
            frame_idx=frame_idx,
            add_link_interval=add_link_interval,
            remove_link_interval=remove_link_interval,
            add_thr=add_thr, remove_thr=remove_thr,
            remove_strict=remove_strict,
            change_all=change_all
        )
        trigger_flag = trigger_flag or bool(dcn_trigger)

        # Embed the DCN result back into the full graph.
        new_links_dcn_full.index_copy_(0, dcn_idx, new_links_dcn_full.index_select(0, dcn_idx)
                                       .index_copy(1, dcn_idx, dcn_updated))
    # With fewer than two DCN pods, the DCN subgraph stays empty.

    # 3. Build the AI subgraph using trod_tpe on current AI-to-AI traffic at percentile 1.0.
    new_links_ai_full = torch.zeros_like(links)
    if len(ai_idx) >= 2:
        if cur_tms is None:
            # Keep the AI subgraph unchanged if current traffic is unavailable.
            x_ai_embed = torch.zeros_like(links)
        else:
            # Prepare the AI-only current traffic matrix as NumPy.
            cur_tms_t = torch.as_tensor(cur_tms, device=device, dtype=dtype)
            tms_ai   = cur_tms_t.index_select(0, ai_idx).index_select(1, ai_idx).detach().cpu().numpy()

            # Parameters expected by trod_tpe.
            pod_num_ai = len(ai_idx)
            spine_num  = M
            # total_ports_ai = links.index_select(0, ai_idx).sum(dim=(1,2))  
            # port_num_per_pod_ai = int(round(float(total_ports_ai.mean().item())))
            port_num_per_pod_ai = max_links * spine_num

            # Bandwidth matrix in the same normalized units as the traffic.
            bw_ai = np.ones((pod_num_ai, pod_num_ai), dtype=np.float32) * float(normalize_size(bandwidth_per_port))

            # trod_tpe accepts a sequence; use only the current frame here.
            spine_topo_list_ai, _ = trod_tpe(
                [tms_ai],              # Current frame.
                1,                   # percentile = 1
                pod_num_ai,
                bw_ai,
                port_num_per_pod_ai,
                spine_num
            )
            # Stack results into [AI, AI, M].
            x_ai_np = np.stack(spine_topo_list_ai, axis=-1)  # (Ai,Ai,M)
            x_ai    = torch.from_numpy(x_ai_np).to(device=device, dtype=dtype)

            # Embed the AI result back into the full graph.
            x_ai_embed = torch.zeros_like(links)
            x_ai_embed.index_copy_(0, ai_idx, x_ai_embed.index_select(0, ai_idx)
                                   .index_copy(1, ai_idx, x_ai))

        new_links_ai_full = x_ai_embed

    # 4. Combine AI and DCN subgraphs; leave cross-group links at zero.
    # Boolean within-group mask.
    ai_mask_full  = torch.zeros((P, P), dtype=torch.bool, device=device)
    dcn_mask_full = torch.zeros((P, P), dtype=torch.bool, device=device)
    if len(ai_idx) >= 2:
        ii, jj = torch.meshgrid(ai_idx, ai_idx, indexing='ij')
        ai_mask_full[ii, jj] = True
    if len(dcn_idx) >= 2:
        ii, jj = torch.meshgrid(dcn_idx, dcn_idx, indexing='ij')
        dcn_mask_full[ii, jj] = True
    # Clear the diagonal.
    eye = torch.eye(P, dtype=torch.bool, device=device)
    ai_mask_full  &= ~eye
    dcn_mask_full &= ~eye

    # Apply the mask.
    result = torch.zeros_like(links)
    if ai_mask_full.any():
        result = result + new_links_ai_full * ai_mask_full.unsqueeze(-1)
    if dcn_mask_full.any():
        result = result + new_links_dcn_full * dcn_mask_full.unsqueeze(-1)

    # 5. Set the trigger flag.
    if not trigger_flag:
        trigger_flag = bool((result - links).abs().max() > 1e-6)

    return result, trigger_flag




def check_connectivity(links, i, j, k):
    """
    Vectorized check for each (i, j, k) in a batch: whether an intermediate
    node t exists with links[i,t,k] > 0 and links[t,j,k] > 0.
    links: [P, P, M]
    i, j, k: [B]
    Returns a [B] boolean vector.
    """
    P, _, M = links.shape
    B = i.shape[0]

    # Build the intermediate-node mask [B, P].
    intermediate_mask = torch.ones(B, P, dtype=torch.bool, device=links.device)
    intermediate_mask[torch.arange(B), i] = False
    intermediate_mask[torch.arange(B), j] = False

    # Extract edges for the selected batch.
    # outgoing: [B, P]  (i -> t)
    outgoing = links[i, :, k] > 0
    # incoming: [B, P]  (t -> j)
    incoming = links[:, j, k].T > 0   # Transpose to [B, P].

    # Combine the masks.
    valid_intermediate = intermediate_mask & outgoing & incoming  # [B, P]
    mask = valid_intermediate.any(dim=1)
    return i[mask], j[mask], k[mask]

if __name__ == "__main__":
    traffic_seq = np.random.rand(10, 4, 4) * 1000  # Example traffic sequence
    percentile = 80
    pods_num = 4
    bandwidth = np.ones((pods_num, pods_num)) * 1000  # Example
    port_num = 64  # Example port number
    topo, threshold = get_topology(traffic_seq, percentile, pods_num, bandwidth, port_num)
    spine_topo = split_matrix(topo, M=4)
    print("Topology:\n", topo)
    print("Spine Topology:", spine_topo)
    print("Threshold:\n", threshold)
    spine_topo = trod_tpe(traffic_seq, percentile, pods_num, bandwidth, port_num)
    print("Centralized TPE Spine Topology:", spine_topo)
