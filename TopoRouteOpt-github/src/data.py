"""Prepare small traffic-matrix datasets for the simulator."""

from pathlib import Path
import pickle
import re
from zipfile import ZipFile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data"
FACEBOOK_ARCHIVE = DATA / "rawdata" / "Facebook_pod_a_traffic_matrices_1s.zip"


def _save_frames(name, frames):
    destination = DATA / name
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.glob("t*.pkl")):
        raise FileExistsError(f"{destination} already contains traffic matrices; remove them explicitly to regenerate")
    count = 0
    for count, matrix in enumerate(frames, 1):
        matrix = np.asarray(matrix, dtype=np.float64)
        if matrix.ndim not in (2, 3) or matrix.shape[0] != matrix.shape[1]:
            raise ValueError(f"Frame {count} has an invalid shape: {matrix.shape}")
        with (destination / f"t{count}.pkl").open("wb") as output:
            pickle.dump(matrix, output, protocol=pickle.HIGHEST_PROTOCOL)
    if count == 0:
        raise ValueError("No traffic matrices found")
    return destination, count


def make_demo(frames=64, pods=16, seed=42):
    if frames < 13 or pods < 2:
        raise ValueError("Demo requires at least 13 frames and 2 pods")
    rng = np.random.default_rng(seed)

    def matrices():
        base = rng.uniform(20_000, 80_000, size=(pods, pods))
        np.fill_diagonal(base, 0)
        for step in range(frames):
            matrix = base * rng.lognormal(0, 0.25, size=(pods, pods))
            matrix[:pods // 4, :pods // 4] *= 1.5 if step % 16 < 8 else 0.8
            np.fill_diagonal(matrix, 0)
            yield matrix

    return _save_frames("DemoTraffic", matrices())


def make_dcn(frames=3000, seed=42):
    """Reproduce the 16-pod DCN generator's independent Gaussian demands."""
    if frames < 13:
        raise ValueError("DCN example requires at least 13 frames")
    rng = np.random.RandomState(seed)

    def matrices():
        for _ in range(frames):
            matrix = np.zeros((16, 16), dtype=np.float64)
            for source in range(16):
                for target in range(16):
                    if source != target:
                        matrix[source, target] = max(rng.normal(40_000, 4_000), 0)
            yield matrix

    return _save_frames("DCNTraffic_16pod_8spine", matrices())


def make_facebook(frames=64):
    if not FACEBOOK_ARCHIVE.is_file():
        raise FileNotFoundError(f"Missing source archive: {FACEBOOK_ARCHIVE}")
    with ZipFile(FACEBOOK_ARCHIVE) as archive:
        numbered = []
        for member in archive.namelist():
            match = re.search(r"/t(\d+)\.pkl$", member)
            if match:
                numbered.append((int(match.group(1)), member))
        numbered.sort()
        if not numbered or numbered[0][0] != 1:
            raise ValueError("Archive does not contain t1.pkl")
        selected = numbered[:frames] if frames else numbered

        def matrices():
            for _, member in selected:
                with archive.open(member) as source:
                    yield pickle.load(source)  # Only use a trusted local archive.

        return _save_frames("Facebook_pod_a", matrices())
