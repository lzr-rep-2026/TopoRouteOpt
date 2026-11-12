"""Compare per-frame maximum link utilization from multiple experiment files."""

import argparse
from pathlib import Path


def read_values(path):
    values = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            try:
                values.append(float(line))
            except ValueError as exc:
                raise ValueError(f"{path}:{number} is not numeric") from exc
    if not values:
        raise ValueError(f"{path} has no numeric values")
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--series", action="append", required=True, metavar="NAME=FILE",
                        help="Add a method and its test_results file; repeat for each method")
    parser.add_argument("--skip-first", action="append", default=[], metavar="NAME=N",
                        help="Discard N warm-up frames from a series before comparison")
    parser.add_argument("--output", type=Path, default=Path("Result/comparison.png"))
    parser.add_argument("--title", default="Maximum link utilization by method")
    args = parser.parse_args()

    skips = {}
    for item in args.skip_first:
        if "=" not in item:
            parser.error("--skip-first must be NAME=N")
        name, value = item.split("=", 1)
        try:
            skips[name] = int(value)
        except ValueError:
            parser.error(f"Invalid warm-up frame count: {item}")
        if skips[name] < 0:
            parser.error("Warm-up frame count cannot be negative")

    series = []
    for item in args.series:
        if "=" not in item:
            parser.error("--series must be NAME=FILE")
        name, filename = item.split("=", 1)
        if not name or not filename:
            parser.error("--series must be NAME=FILE")
        values = read_values(Path(filename))[skips.get(name, 0):]
        if not values:
            parser.error(f"No frames remain for {name} after skipping warm-up")
        series.append((name, values))

    unknown = set(skips) - {name for name, _ in series}
    if unknown:
        parser.error(f"--skip-first refers to unknown series: {', '.join(sorted(unknown))}")
    lengths = {len(values) for _, values in series}
    if len(lengths) != 1:
        parser.error("Series have different frame counts after warm-up; choose matching inputs and skips")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), layout="constrained")
    for name, values in series:
        axes[0].plot(range(len(values)), values, label=name, linewidth=1, alpha=0.8)
    axes[0].set(title="Per-frame MLU", xlabel="Frame after warm-up", ylabel="Maximum link utilization")
    axes[0].legend()
    axes[0].grid(alpha=0.2)
    axes[1].boxplot([values for _, values in series], showfliers=False)
    axes[1].set_xticks(range(1, len(series) + 1), [name for name, _ in series])
    axes[1].set(title="MLU distribution", ylabel="Maximum link utilization")
    axes[1].tick_params(axis="x", rotation=25)
    axes[1].grid(axis="y", alpha=0.2)
    fig.suptitle(args.title)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    print(f"Saved {args.output} ({lengths.pop()} aligned frames per method)")


if __name__ == "__main__":
    main()
