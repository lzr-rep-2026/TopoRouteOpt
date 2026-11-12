"""Create traffic matrices from a small synthetic example or a trusted raw archive."""

import argparse
from src.data import make_dcn, make_demo, make_facebook


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=("dcn", "demo", "facebook"), nargs="?", default="dcn")
    parser.add_argument("--frames", type=int, default=3000, help="Number of matrices to prepare (0 = all for Facebook)")
    parser.add_argument("--pods", type=int, default=16, help="Pod count for synthetic demo")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for synthetic demo")
    args = parser.parse_args()
    if args.frames < 0:
        parser.error("--frames must be non-negative")
    if args.dataset == "dcn":
        destination, count = make_dcn(args.frames, args.seed)
    elif args.dataset == "demo":
        destination, count = make_demo(args.frames, args.pods, args.seed)
    else:
        destination, count = make_facebook(args.frames)
    print(f"Prepared {count} traffic matrices in {destination}")


if __name__ == "__main__":
    main()
