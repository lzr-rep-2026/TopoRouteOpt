"""Summarize one or more numeric result files produced by run_main.py."""

import argparse
import math
from pathlib import Path
from statistics import mean, median, pstdev


def summarize(path):
    values = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            try:
                value = float(line)
            except ValueError as exc:
                raise ValueError(f"{path}:{number} is not a number") from exc
            if not math.isfinite(value):
                raise ValueError(f"{path}:{number} is not finite")
            values.append(value)
    if not values:
        raise ValueError(f"{path} contains no values")
    ordered = sorted(values)
    percentile = lambda p: ordered[round((len(ordered) - 1) * p / 100)]
    return len(values), mean(values), median(values), pstdev(values), percentile(95), max(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="Numeric test_results*.txt files")
    args = parser.parse_args()
    print("file\tcount\tmean\tmedian\tstd\tp95\tmax")
    for path in args.files:
        count, average, middle, std, p95, maximum = summarize(path)
        print(f"{path}\t{count}\t{average:.6g}\t{middle:.6g}\t{std:.6g}\t{p95:.6g}\t{maximum:.6g}")


if __name__ == "__main__":
    main()
