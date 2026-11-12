"""Generate the 16-pod DCN workload used by the simulator."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data import make_dcn


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=int, default=3000)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    destination, count = make_dcn(args.frames, args.seed)
    print(f'Prepared {count} traffic matrices in {destination}')


if __name__ == '__main__':
    main()
