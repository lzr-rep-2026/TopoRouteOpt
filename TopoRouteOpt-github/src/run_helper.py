import argparse
# hidden_dim, hidden_layer
def add_default_args(parser):

    parser.add_argument('--topo_name', type=str, default='DCNTraffic_16pod_8spine')
    
    parser.add_argument('--mode', type=str, default = 'test')
    parser.add_argument('--batch_size', type=int, default = 1)
    parser.add_argument('--epochs', type=int, default = 1)
    parser.add_argument('--hidden_layer', type=int, default = 3)
    parser.add_argument('--hidden_dim', type=int, default = 128)
    parser.add_argument('--lr', type=float, default = 0.001)
    parser.add_argument('--method', type=str, default='TROD_linkpct')
    parser.add_argument('--init_topo_method', type=str, default='Uniform_Topo')

    parser.add_argument('--hist_len', type=int, default = 12)
    parser.add_argument('--spread', type=float, default = 0.5)

    parser.add_argument('--train_start_idx', type=int, default = 0)
    parser.add_argument('--train_end_idx', type=int, default = 0)
    parser.add_argument('--val_start_idx', type=int, default = 0)
    parser.add_argument('--val_end_idx', type=int, default = 0)
    parser.add_argument('--test_start_idx', type=int, default = 0)
    parser.add_argument('--test_end_idx', type=int, default=3000)

    parser.add_argument('--link_percentile', type=float, default = 0.8)
    parser.add_argument('--bandwidth_per_port', type=int, default=2000)

    parser.add_argument('--std_multiplier', type=float, default = 3)

    parser.add_argument('--centralized_tpe_len', type=int, default = 2000)
    parser.add_argument('--centralized_TE_trigger', type=str, default = 'yes')

    parser.add_argument('--max_links', type=int, default = 64)
    parser.add_argument('--min_links', type=int, default = 1)
    parser.add_argument('--custom_name', type=str, default = '')

    parser.add_argument('--add_link_hist_len', type=int, default = 12)
    parser.add_argument('--remove_link_hist_len', type=int, default = 60)
    parser.add_argument('--add_thr', type=float, default = 0.9)
    parser.add_argument('--remove_thr', type=float, default=0.9)
    parser.add_argument('--remove_strict', type=int, default = 0)
    parser.add_argument('--change_all', type=int, default = 0)
    parser.add_argument('--port_num_per_pod', type=int, default=512)

    # Additional options for split-pod experiments.
    parser.add_argument('--ai_link_percentile', type=float, default = 0.9)
    parser.add_argument('--dcn_link_percentile', type=float, default = 0.8)
    parser.add_argument('--ai_add_thr', type=float, default = 0.9)
    parser.add_argument('--dcn_add_thr', type=float, default = 0.9)
    parser.add_argument('--ai_remove_thr', type=float, default=0.9)
    parser.add_argument('--dcn_remove_thr', type=float, default=0.9)
    parser.add_argument('--ai_pods', type=int, nargs='+', default=[],
                        help="List of AI pod indices, e.g. --ai_pods 0 1 2 3")


    return parser

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser = add_default_args(parser)
    
    return parser.parse_args(args)
