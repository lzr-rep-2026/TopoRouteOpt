import sys
import numpy as np
from tqdm import tqdm
import torch
from collections import deque
import os

from src.env import Env
from src.run_helper import parse_args
from src.frameworks import TROD_threshold_mlu_loss, TROD_threshold_mlu_loss_split
from src.cal_topology import do_centralized_tpe, do_distributed_tpe, do_distributed_tpe_split_pod, do_distributed_tpe_split_ideal
from src.config import RESULT_DIR, LOG_DIR
from src.utils import normalize_size

props = parse_args(sys.argv[1:])
env = Env(props)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

env.x = env.x.to(device)
env.capacity = env.capacity.to(device)

centralized_tpe_history_tms = deque(maxlen=props.centralized_tpe_len) 
history_tms = deque(maxlen=props.hist_len)  
dis_add_link_history_tms = deque(maxlen=props.add_link_hist_len)
dis_remove_link_history_tms = deque(maxlen=props.remove_link_hist_len)
dis_add_link_history_links = deque(maxlen=props.add_link_hist_len)
dis_remove_link_history_links = deque(maxlen=props.remove_link_hist_len)
split_weights = env.x / (env.x.sum(dim=-1, keepdim=True) + 1e-8)
for idx in range(props.hist_len):
    centralized_tpe_history_tms.append(env.test_pod_traffics[idx]) 
    history_tms.append(env.test_pod_traffics[idx])
    
    spine_traffic_t = torch.as_tensor(env.test_pod_traffics[idx], device=device, dtype=env.x.dtype)[:, :, None] * split_weights
    dis_add_link_history_tms.append(spine_traffic_t)
    dis_remove_link_history_tms.append(spine_traffic_t)
    dis_add_link_history_links.append(env.x.clone())
    dis_remove_link_history_links.append(env.x.clone())

flattened_x = env.x.flatten().cpu().numpy()
trigger_toe_log = f'{" ".join(map(str, flattened_x.astype(int)))}\n'
loss_vals = []
hop_count_vals = []

suffix = f'_{props.custom_name}' if props.custom_name else ''

util_log_dir = os.path.join(
    LOG_DIR, props.topo_name, props.method, props.init_topo_method, f'{props.port_num_per_pod}', f'{props.bandwidth_per_port}'
)
os.makedirs(util_log_dir, exist_ok=True)
raw_util_path = os.path.join(util_log_dir, f'util_raw{suffix}.txt')         # spine_traffic / capacity
eff_util_path = os.path.join(util_log_dir, f'util_effective{suffix}.txt')   # link utilization computed by frameworks.py
raw_util_f = open(raw_util_path, 'w')
eff_util_f = open(eff_util_path, 'w')

try:
    with torch.no_grad():
        with tqdm(env.test_pod_traffics[props.hist_len:]) as tepoch:
            for tms_idx, tms in enumerate(tepoch, props.hist_len):
                inputs = torch.stack(
                    [torch.as_tensor(x) for x in list(history_tms)[-props.hist_len:]],
                    dim=0
                ).to(device)

                tepoch.set_description(f"Testing {props.topo_name}")

                if props.method == 'TROD_linkpct' or props.method == 'TROD' or props.method == 'TROD_linkpct_split_pod':
                    use_self = None
                    routing_weight_method = 'default'
                    history_params = None
                    x = env.x.to(device)
                    s = env.s.to(device)
                
                elif props.method == 'TROD_linkpct_hr':
                    use_self = None
                    routing_weight_method = 'hist'
                    history_params = {
                        'history_traffic_max': inputs.max(dim=0).values,
                    }
                    x = env.x.to(device)
                    s = env.s.to(device)
                
                elif props.method == 'TROD_linkpct_hr_std':
                    use_self = None
                    routing_weight_method = 'hist_with_std'
                    history_params = {
                        'history_traffic_mean': inputs.mean(dim=0),
                        'history_traffic_std': inputs.std(dim=0),
                        'std_multiplier': props.std_multiplier,
                    }
                    x = env.x.to(device)
                    s = env.s.to(device)

                elif props.method == 'VLB':
                    use_self = True
                    routing_weight_method = 'default'
                    history_params = None
                    x = env.x.to(device)
                    s = torch.zeros_like(env.s).to(device)

                elif props.method == 'TROD_linkpct_centralized_TPE':
                    use_self = None
                    routing_weight_method = 'default'
                    history_params = None
                    x = env.x.to(device)
                    s = env.s.to(device)

                    x, trigger_flag = do_centralized_tpe(inputs, x, s, props, env, centralized_tpe_history_tms, device)
                    if trigger_flag:
                        print(f"Centralized TPE triggered at index {tms_idx}")
                        trigger_toe_log += f"Centralized TPE triggered at index {tms_idx}\n"
                        flattened_x = x.flatten().cpu().numpy()
                        trigger_toe_log += f'{" ".join(map(str, flattened_x.astype(int)))}\n'
                        env.x = x
                        env.s = normalize_size(env.x.sum(dim=-1) * env.bandwidth_per_port * env.percentile)
                        env.capacity = normalize_size(env.x * env.bandwidth_per_port)
                        s = env.s.to(device)

                elif props.method == 'TROD_linkpct_distributed_TPE':
                    use_self = None
                    routing_weight_method = 'default'
                    history_params = None
                    x = env.x.to(device)
                    s = env.s.to(device)

                    x, trigger_flag = do_distributed_tpe(x, dis_add_link_history_tms, dis_add_link_history_links,
                                                        dis_remove_link_history_tms, dis_remove_link_history_links,
                                                        env.bandwidth_per_port, env.std_ratio,
                                                        max_links=props.max_links, min_links=props.min_links,
                                                        frame_idx=tms_idx, add_link_interval=props.add_link_hist_len, remove_link_interval=props.remove_link_hist_len, 
                                                        add_thr=props.add_thr, remove_thr=props.remove_thr, remove_strict=props.remove_strict, change_all=props.change_all)
                    if trigger_flag:
                        print(f"Distributed TPE triggered at index {tms_idx}")
                        trigger_toe_log += f"Distributed TPE triggered at index {tms_idx}\n"
                        flattened_x = x.flatten().cpu().numpy()
                        trigger_toe_log += f'{" ".join(map(str, flattened_x.astype(int)))}\n'
                        env.x = x
                        env.s = normalize_size(env.x.sum(dim=-1) * env.bandwidth_per_port * env.percentile)
                        env.capacity = normalize_size(env.x * env.bandwidth_per_port)
                        s = env.s.to(device)
                    dis_add_link_history_links.append(x.clone())
                    dis_remove_link_history_links.append(x.clone())
                
                elif props.method == 'split_pod_distributed_TPE':
                    use_self = None
                    routing_weight_method = 'default'
                    history_params = None
                    x = env.x.to(device)
                    s = env.s.to(device)

                    x, trigger_flag = do_distributed_tpe_split_pod(x, dis_add_link_history_tms, dis_add_link_history_links,
                                                        dis_remove_link_history_tms, dis_remove_link_history_links,
                                                        env.bandwidth_per_port, env.std_ratio,
                                                        max_links=props.max_links, min_links=props.min_links,
                                                        frame_idx=tms_idx, add_link_interval=props.add_link_hist_len, remove_link_interval=props.remove_link_hist_len, 
                                                        add_thr=props.add_thr, remove_thr=props.remove_thr, remove_strict=props.remove_strict, change_all=props.change_all, 
                                                        history_tms=history_tms, cur_tms=tms)
                    
                    if trigger_flag:
                        print(f"Distributed TPE triggered at index {tms_idx}")
                        trigger_toe_log += f"Distributed TPE triggered at index {tms_idx}\n"
                        flattened_x = x.flatten().cpu().numpy()
                        trigger_toe_log += f'{" ".join(map(str, flattened_x.astype(int)))}\n'
                        env.x = x
                        # --- Recompute s with group-specific percentiles (AI/DCN) ---
                        P = env.x.shape[0]
                        dtype = env.x.dtype
                        dev = env.x.device

                        # indices
                        ai = sorted(set(getattr(props, 'ai_pods', [])))
                        all_idx = set(range(P))
                        dcn = sorted(all_idx - set(ai))

                        # percentiles (fallback to global link_percentile if not provided)
                        ai_pct  = float(getattr(props, 'ai_link_percentile', None) or props.link_percentile)
                        dcn_pct = float(getattr(props, 'dcn_link_percentile', None) or props.link_percentile)

                        # build masks
                        ai_mask  = torch.zeros((P, P), dtype=torch.bool, device=dev)
                        dcn_mask = torch.zeros((P, P), dtype=torch.bool, device=dev)
                        if len(ai) >= 2:
                            ai_tensor = torch.tensor(ai, device=dev)
                            ai_mesh_i, ai_mesh_j = torch.meshgrid(ai_tensor, ai_tensor, indexing='ij')
                            ai_mask[ai_mesh_i, ai_mesh_j] = True
                        if len(dcn) >= 2:
                            dcn_tensor = torch.tensor(dcn, device=dev)
                            dcn_mesh_i, dcn_mesh_j = torch.meshgrid(dcn_tensor, dcn_tensor, indexing='ij')
                            dcn_mask[dcn_mesh_i, dcn_mesh_j] = True

                        # remove diagonal
                        eye = torch.eye(P, dtype=torch.bool, device=dev)
                        ai_mask  = ai_mask  & ~eye
                        dcn_mask = dcn_mask & ~eye

                        # percentile matrix
                        pct_mat = torch.zeros((P, P), dtype=dtype, device=dev)
                        if ai_mask.any():
                            pct_mat = pct_mat + ai_mask.float()  * ai_pct
                        if dcn_mask.any():
                            pct_mat = pct_mat + dcn_mask.float() * dcn_pct
                        # cross-group remains 0

                        # s = normalize_size( sum_m x_ijm * bandwidth_per_port * pct_ij )
                        sum_links = env.x.sum(dim=-1)                               # [P,P]
                        base = sum_links * float(env.bandwidth_per_port) * pct_mat  # [P,P]
                        env.s = normalize_size(base)                                
                        env.capacity = normalize_size(env.x * env.bandwidth_per_port)
                        s = env.s.to(device)
                    dis_add_link_history_links.append(x.clone())
                    dis_remove_link_history_links.append(x.clone())

                elif props.method == 'ideal_split_pod_distributed_TPE':
                    use_self = None
                    routing_weight_method = 'default'
                    history_params = None
                    x = env.x.to(device)
                    s = env.s.to(device)
                    # import pdb; pdb.set_trace()

                    x, trigger_flag = do_distributed_tpe_split_ideal(x, dis_add_link_history_tms, dis_add_link_history_links,
                                                        dis_remove_link_history_tms, dis_remove_link_history_links,
                                                        env.bandwidth_per_port, env.std_ratio,
                                                        max_links=props.max_links, min_links=props.min_links,
                                                        frame_idx=tms_idx, add_link_interval=props.add_link_hist_len, remove_link_interval=props.remove_link_hist_len, 
                                                        add_thr=props.add_thr, remove_thr=props.remove_thr, remove_strict=props.remove_strict, change_all=props.change_all, 
                                                        history_tms=history_tms, cur_tms=tms, 
                                                        ai_pods = env.ai_pods)
                    # import pdb; pdb.set_trace()
                    
                    if trigger_flag:
                        print(f"Distributed TPE triggered at index {tms_idx}")
                        trigger_toe_log += f"Distributed TPE triggered at index {tms_idx}\n"
                        flattened_x = x.flatten().cpu().numpy()
                        trigger_toe_log += f'{" ".join(map(str, flattened_x.astype(int)))}\n'
                        env.x = x
                        # --- Recompute s with group-specific percentiles (AI/DCN) ---
                        P = env.x.shape[0]
                        dtype = env.x.dtype
                        dev = env.x.device

                        # indices
                        ai = sorted(set(getattr(props, 'ai_pods', [])))
                        all_idx = set(range(P))
                        dcn = sorted(all_idx - set(ai))

                        # percentiles (fallback to global link_percentile if not provided)
                        ai_pct  = float(getattr(props, 'ai_link_percentile', None) or props.link_percentile)
                        dcn_pct = float(getattr(props, 'dcn_link_percentile', None) or props.link_percentile)

                        # build masks
                        ai_mask  = torch.zeros((P, P), dtype=torch.bool, device=dev)
                        dcn_mask = torch.zeros((P, P), dtype=torch.bool, device=dev)
                        if len(ai) >= 2:
                            ai_tensor = torch.tensor(ai, device=dev)
                            ai_mesh_i, ai_mesh_j = torch.meshgrid(ai_tensor, ai_tensor, indexing='ij')
                            ai_mask[ai_mesh_i, ai_mesh_j] = True
                        if len(dcn) >= 2:
                            dcn_tensor = torch.tensor(dcn, device=dev)
                            dcn_mesh_i, dcn_mesh_j = torch.meshgrid(dcn_tensor, dcn_tensor, indexing='ij')
                            dcn_mask[dcn_mesh_i, dcn_mesh_j] = True

                        # remove diagonal
                        eye = torch.eye(P, dtype=torch.bool, device=dev)
                        ai_mask  = ai_mask  & ~eye
                        dcn_mask = dcn_mask & ~eye

                        # percentile matrix
                        pct_mat = torch.zeros((P, P), dtype=dtype, device=dev)
                        if ai_mask.any():
                            pct_mat = pct_mat + ai_mask.float()  * ai_pct
                        if dcn_mask.any():
                            pct_mat = pct_mat + dcn_mask.float() * dcn_pct
                        # cross-group remains 0

                        # s = normalize_size( sum_m x_ijm * bandwidth_per_port * pct_ij )
                        sum_links = env.x.sum(dim=-1)                               # [P,P]
                        base = sum_links * float(env.bandwidth_per_port) * pct_mat  # [P,P]
                        env.s = normalize_size(base)                                
                        env.capacity = normalize_size(env.x * env.bandwidth_per_port)
                        s = env.s.to(device)
                    dis_add_link_history_links.append(x.clone())
                    dis_remove_link_history_links.append(x.clone())
                
                total_connections = env.x.sum(dim=-1, keepdim=True)
                mask = (total_connections == 0)
                split_weights = torch.where(
                    mask,
                    1.0 / env.x.shape[-1],
                    env.x / total_connections
                )
                
                spine_traffic = torch.as_tensor(tms, device=device, dtype=env.x.dtype)[:, :, None] * split_weights
                # spine_traffic = torch.as_tensor(tms)[:, :, np.newaxis].to(device) * split_weights
                dis_add_link_history_tms.append(spine_traffic)
                dis_remove_link_history_tms.append(spine_traffic)
                if props.method == 'split_pod_distributed_TPE' or props.method == 'ideal_split_pod_distributed_TPE':
                    loss_val, hop_count_val, link_util = TROD_threshold_mlu_loss_split(s, spine_traffic, x, env.capacity, 
                                                                    ai_pods = env.ai_pods,
                                                                    use_self=use_self,
                                                                    routing_weight_method=routing_weight_method,
                                                                    history_params=history_params, tms_idx = tms_idx)
                else:
                    loss_val, hop_count_val, link_util = TROD_threshold_mlu_loss(s, spine_traffic, x, env.capacity,
                                                                    use_self=use_self,
                                                                    routing_weight_method=routing_weight_method,
                                                                    history_params=history_params, tms_idx = tms_idx)
                
                raw_util = (spine_traffic / (env.capacity + 1e-8)).detach().flatten().cpu().numpy()
                raw_util_f.write(" ".join("{:.3f}".format(x) for x in raw_util) + "\n")

                eff_util = link_util.detach().flatten().cpu().numpy()
                eff_util_f.write(" ".join("{:.3f}".format(x) for x in eff_util) + "\n")

                loss_vals.append(loss_val.item())
                hop_count_vals.append(hop_count_val.item())
                tepoch.set_postfix(loss=sum(loss_vals) / len(loss_vals))
                history_tms.append(tms)
                centralized_tpe_history_tms.append(tms)

                # if tms_idx - 12 == 0:
                #     print(loss_vals[-1])
                #     import pdb; pdb.set_trace()
                # if tms_idx - 12 == 164:
                #     print(loss_vals[-1])
                #     import pdb; pdb.set_trace()

finally:
    raw_util_f.close()
    eff_util_f.close()
    print(f"Per-frame raw util saved to {raw_util_path}")
    print(f"Per-frame effective util saved to {eff_util_path}")

# suffix = f'_{props.custom_name}' if props.custom_name else ''
result_file = os.path.join(RESULT_DIR, props.topo_name, props.method, props.init_topo_method, f'{props.port_num_per_pod}', f'{props.bandwidth_per_port}', f'test_results{suffix}.txt')
if not os.path.exists(os.path.dirname(result_file)):
    os.makedirs(os.path.dirname(result_file))
with open(result_file, 'w') as f:
    for loss_val in loss_vals:
        f.write(f"{loss_val}\n")
print(f"Results saved to {result_file}")


hop_count_file = result_file.replace('test_results', 'test_hop_count_results')
if not os.path.exists(os.path.dirname(hop_count_file)):
    os.makedirs(os.path.dirname(hop_count_file))
with open(hop_count_file, 'w') as f:
    for hop_count_val in hop_count_vals:
        f.write(f"{hop_count_val}\n")
print(f"Results saved to {hop_count_file}")

if props.method == 'TROD_linkpct_centralized_TPE' or props.method == 'TROD_linkpct_distributed_TPE' or props.method == 'split_pod_distributed_TPE' or props.method == 'ideal_split_pod_distributed_TPE':
    trigger_log_file = os.path.join(LOG_DIR, props.topo_name, props.method, props.init_topo_method, f'{props.port_num_per_pod}', f'{props.bandwidth_per_port}', f'{props.method}{suffix}_log.txt')
    if not os.path.exists(os.path.dirname(trigger_log_file)):
        os.makedirs(os.path.dirname(trigger_log_file))
    with open(trigger_log_file, 'w') as f:
        f.write(trigger_toe_log)
    print(f"Trigger log saved to {trigger_log_file}")