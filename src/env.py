import os
import pickle as pkl
import torch
import numpy as np

from src.config import DATA_DIR
from src.data import make_dcn, make_demo
from src.utils import normalize_size
from src.cal_topology import trod_tpe

def get_topology_and_threshold(props, method, pod_num, port_num_per_pod, spine_num, traffic_seq,
                               percentile, bandwidth, init_topo_method='TROD_Topo',
                               ai_pods=None, ai_link_percentile=None, dcn_link_percentile=None):
    """
    Returns:
      x: [P, P, M] connection counts on each spine layer (possibly fractional).
      s: [P, P] routing thresholds.
    """
    if ai_pods is None:
        ai_pods = []
    ai_pods = sorted(list(set(ai_pods)))
    all_pods = set(range(pod_num))
    dcn_pods = sorted(list(all_pods - set(ai_pods)))

    if method == 'VLB' or method == 'Jupiter':
        spine_topology = []
        for _ in range(spine_num):
            spine_topology.append(np.ones((pod_num, pod_num)) * port_num_per_pod / spine_num / (pod_num-1))
            np.fill_diagonal(spine_topology[-1], 0)
        spine_topology = np.stack(spine_topology, axis=-1)
        x = torch.from_numpy(spine_topology).to(dtype=torch.float32)
        s = torch.zeros((pod_num, pod_num), dtype=torch.float32)

    elif method == 'split_pod_distributed_TPE' or method == 'TROD_linkpct_split_pod' or method == 'ideal_split_pod_distributed_TPE':
        # Use group-specific percentiles, falling back to the global percentile.
        ai_pct  = float(ai_link_percentile if ai_link_percentile is not None else percentile)
        dcn_pct = float(dcn_link_percentile if dcn_link_percentile is not None else percentile)

        # Partition pods into groups.
        AI  = ai_pods
        DCN = dcn_pods

        # Use torch tensors; move them to the target device later.
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        dtype  = torch.float32

        # Build within-group masks without diagonal entries.
        ai_mask  = torch.zeros((pod_num, pod_num), dtype=dtype, device=device)
        dcn_mask = torch.zeros((pod_num, pod_num), dtype=dtype, device=device)

        if len(AI) >= 2:
            ai_idx = torch.tensor(sorted(AI), dtype=torch.long, device=device)
            ii, jj = torch.meshgrid(ai_idx, ai_idx, indexing='ij')
            ai_mask[ii, jj] = 1.0

        if len(DCN) >= 2:
            dcn_idx = torch.tensor(sorted(DCN), dtype=torch.long, device=device)
            ii, jj = torch.meshgrid(dcn_idx, dcn_idx, indexing='ij')
            dcn_mask[ii, jj] = 1.0

        eye = torch.eye(pod_num, dtype=dtype, device=device)
        ai_mask  = ai_mask  * (1.0 - eye)  # Clear diagonal entries.
        dcn_mask = dcn_mask * (1.0 - eye)

        # Build each spine layer with uniform AI and DCN within-group links; no cross-group links.
        spine_topology = []  # Stack into [P, P, M].

        for _ in range(spine_num):
            topo = torch.zeros((pod_num, pod_num), dtype=dtype, device=device)

            # Distribute each AI pod’s per-layer ports evenly across its AI peers.
            if len(AI) >= 2:
                val_ai = port_num_per_pod / spine_num / (len(AI) - 1)
                topo = topo + ai_mask * val_ai

            # Distribute each DCN pod’s per-layer ports evenly across its DCN peers.
            if len(DCN) >= 2:
                val_dcn = port_num_per_pod / spine_num / (len(DCN) - 1)
                topo = topo + dcn_mask * val_dcn

            # Clear diagonal entries.
            topo.fill_diagonal_(0.0)

            # Split-pod methods require integer connection counts; round down.
            if method == 'split_pod_distributed_TPE' or method == 'ideal_split_pod_distributed_TPE' or method == 'TROD_linkpct_split_pod':
                topo = torch.floor(topo)

            # import pdb; pdb.set_trace()
            spine_topology.append(topo)
            

        # [P, P, M]
        x = torch.stack(spine_topology, dim=-1)
        # import pdb; pdb.set_trace()

        # Compute thresholds from group-specific percentiles; leave cross-group thresholds at zero.
        pct_mat = torch.zeros((pod_num, pod_num), dtype=dtype, device=device)
        if (ai_mask > 0).any():
            pct_mat = pct_mat + (ai_mask > 0).to(dtype) * ai_pct
        if (dcn_mask > 0).any():
            pct_mat = pct_mat + (dcn_mask > 0).to(dtype) * dcn_pct
        # The diagonal is already zero.

        # Accept bandwidth as NumPy or torch and convert to torch.
        if isinstance(bandwidth, np.ndarray):
            bw_t = torch.from_numpy(bandwidth).to(dtype=dtype, device=device)
        else:
            bw_t = bandwidth.to(dtype=dtype, device=device)

        # s = (sum_m x_ijm) * bandwidth_ij * pct_ij
        s = x.sum(dim=-1) * bw_t * pct_mat

        return x, s


    else:
        if init_topo_method == 'TROD_Topo':
            spine_topology, threshold = trod_tpe(traffic_seq,
                                                percentile,pod_num,
                                                bandwidth,
                                                port_num_per_pod,
                                                spine_num)
            x = torch.from_numpy(np.stack(spine_topology, axis=-1)).to(dtype=torch.float32)
            if method == 'TROD':
                s = threshold
            else:
                s = x.sum(dim=-1) * bandwidth * percentile
        elif init_topo_method == 'Uniform_Topo':
            #if method == 'TROD_linkpct_distributed_TPE' or method == 'TROD_linkpct':
            spine_topology = []
            for _ in range(spine_num):
                topo = np.ones((pod_num, pod_num)) * port_num_per_pod / spine_num / (pod_num-1)
                np.fill_diagonal(topo, 0)
                # topo = np.floor(topo)
                spine_topology.append(topo)
            spine_topology = np.stack(spine_topology, axis=-1)
            x = torch.from_numpy(spine_topology).to(dtype=torch.float32)
            s = x.sum(dim=-1) * bandwidth * percentile
            # else:
            #     spine_topology = []
            #     for _ in range(spine_num):
            #         spine_topology.append(np.ones((pod_num, pod_num)) * port_num_per_pod / spine_num / (pod_num-1))
            #         np.fill_diagonal(spine_topology[-1], 0)
            #     spine_topology = np.stack(spine_topology, axis=-1)
            #     x = torch.from_numpy(spine_topology).to(dtype=torch.float32)
            #     s = x.sum(dim=-1) * bandwidth * percentile

    return x, s

class Env():
    def __init__(self, props):
        """
        Initialize the environment with the given properties.
        """
        self.topo_name = props.topo_name
        if self.topo_name == 'DCNTraffic_16pod_8spine' and not os.path.exists(os.path.join(DATA_DIR, self.topo_name, 't1.pkl')):
            destination, count = make_dcn()
            print(f'Prepared {count} DCN traffic matrices in {destination}')
        if self.topo_name == 'DemoTraffic' and not os.path.exists(os.path.join(DATA_DIR, 'DemoTraffic', 't1.pkl')):
            destination, count = make_demo()
            print(f'Prepared {count} synthetic traffic matrices in {destination}')
        self.train_pod_traffics = []
        self.val_spine_traffics = []
        self.test_pod_traffics = []
        self.bandwidth_per_port = props.bandwidth_per_port
        self.port_num_per_port = props.port_num_per_pod
        self.percentile = props.link_percentile

        self.ai_pods = sorted(list(set(props.ai_pods))) if hasattr(props, 'ai_pods') and props.ai_pods is not None else []
        self.ai_link_percentile  = getattr(props, 'ai_link_percentile', None)
        self.dcn_link_percentile = getattr(props, 'dcn_link_percentile', None)
        
        self.train_pod_traffics = self.get_pod_traffics(self.topo_name, \
                                                                props.train_start_idx, props.train_end_idx)
        
        self.test_pod_traffics = self.get_pod_traffics(self.topo_name, \
                                                               props.test_start_idx, props.test_end_idx)
        if len(self.train_pod_traffics) == 0:
            print("No input traffic matrices to calculate topology and threshold, use the test")
            self.train_pod_traffics = self.test_pod_traffics
        
        if len(self.test_pod_traffics) <= props.hist_len:
            raise ValueError(f'{self.topo_name} has {len(self.test_pod_traffics)} test frames; '
                             f'at least {props.hist_len + 1} are needed. Adjust --test_end_idx or --hist_len.')
        # Derive the statistic from the same training frames used to initialize the run.
        training = np.asarray(self.train_pod_traffics)
        mean = training.mean(axis=0)
        self.std_ratio = training.std(axis=0) / (mean + 1e-8)
        stats_dir = os.path.join(DATA_DIR, 'analyse_data')
        os.makedirs(stats_dir, exist_ok=True)
        np.save(os.path.join(stats_dir, f'{self.topo_name}_std_ratio.npy'), self.std_ratio)

        self.pod_num, self.spine_num_per_pod = self.topo_info(self.topo_name)
        self.x, self.s= get_topology_and_threshold(props, props.method, self.pod_num, self.port_num_per_port, \
                                                           self.spine_num_per_pod, self.train_pod_traffics, \
                                                           props.link_percentile, np.ones((self.pod_num, self.pod_num)) * normalize_size(self.bandwidth_per_port), \
                                                           props.init_topo_method, self.ai_pods, self.ai_link_percentile, self.dcn_link_percentile)
        # import pdb; pdb.set_trace()
        self.capacity = normalize_size(self.x * self.bandwidth_per_port)

    def get_pod_traffics(self, topo_name, start_idx, end_idx):
        """
        Retrieve the spine traffic data for the given topology name.

        Args:
            topo_name (str): The name of the topology.

        Returns:
            dict: A dictionary containing spine traffic data.
        """
        Data_dir = os.path.join(DATA_DIR, f'{topo_name}')
        if not os.path.isdir(Data_dir):
            raise FileNotFoundError(f'Missing {Data_dir}. Run: python prepare_data.py '
                                    f'{"facebook" if topo_name == "Facebook_pod_a" else "demo"}')
        file_list = sorted((f for f in os.listdir(Data_dir) if f.startswith('t') and f.endswith('.pkl')
                            and f[1:-4].isdigit()), key=lambda x: int(x[1:-4]))[start_idx:end_idx or None]
        _pod_traffics = []
        print(f"Loading traffic matrices from {Data_dir}")
        for file in file_list:
            file_path = os.path.join(Data_dir, file)
            with open(file_path, 'rb') as f:
                traffic = pkl.load(f).astype(np.float64)
                if len(traffic.shape) == 3:
                    idx = np.arange(traffic.shape[0])
                    traffic[idx,idx,:] = 0.0
                    pod_traffic = traffic.sum(axis = -1)
                elif len(traffic.shape) == 2:
                    idx = np.arange(traffic.shape[0])
                    traffic[idx,idx] = 0.0
                    pod_traffic = traffic
                # split_weights = x / (self.x.sum(dim=-1, keepdim=True) + 1e-8)
                # traffic = pod_traffic[:, :, np.newaxis] * split_weights.cpu().numpy()
                # import pdb; pdb.set_trace()
                _pod_traffics.append(normalize_size(pod_traffic))
        return _pod_traffics
    
    def topo_info(self, topo_name):
        traffic_path = os.path.join(DATA_DIR, f'{topo_name}','t1.pkl')
        with open(traffic_path, 'rb') as f:
            traffic = pkl.load(f)
        pod_num = traffic.shape[0]
        if traffic.ndim == 3:
            spine_num_per_pod = traffic.shape[2]
        elif traffic.ndim == 2:
            spine_num_per_pod = 8
        
        return pod_num, spine_num_per_pod
       

