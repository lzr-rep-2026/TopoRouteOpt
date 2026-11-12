import os
import re
import numpy as np
import pickle as pkl

# -------------------------------
# Parameters.
# -------------------------------
input_txt = "../rawdata/sim_traffic_matrix_list.txt"
output_dir = "../SimTraffic_ai"  
pod_num = 16
spine_num_per_pod = 8  

os.makedirs(output_dir, exist_ok=True)

# -------------------------------
# Read the full file, including line breaks.
# -------------------------------
with open(input_txt, "r", encoding="utf-8") as f:
    content = f.read()

# -------------------------------
# Match each frame as timestamp followed by a list.
# -------------------------------
pattern = re.compile(r"(\d+(?:\.\d+)?),\[(.*?)\](?=\s*\d|$)", re.DOTALL)
matches = pattern.findall(content)

if not matches:
    raise RuntimeError("❌ 未匹配到任何 traffic 数据，请检查文件格式。")

# -------------------------------
# Parse each frame and save it as a pickle file.
# -------------------------------
target_len = pod_num * pod_num * spine_num_per_pod

for idx, (time_str, data_str) in enumerate(matches, start=1):
    # Remove extra symbols, spaces, and commas.
    cleaned = re.sub(r"[\s,]+", " ", data_str.strip())
    values = np.fromstring(cleaned, sep=" ")

    if len(values) != target_len:
        raise ValueError(
            f"❌ 第 {idx} 帧长度不匹配: {len(values)} != {target_len} "
            f"({pod_num}*{pod_num}*{spine_num_per_pod})"
        )

    # Restore [pod, pod, spine] matrix dimensions.
    matrix = values.reshape(pod_num, pod_num, spine_num_per_pod)

    # Aggregate across the spine dimension.
    pod_matrix = np.sum(matrix, axis=2)

    # Convert units by multiplying by one million.
    pod_matrix *= 1_000_000.0

    # Save one pickle file per frame.
    save_path = os.path.join(output_dir, f"t{idx}.pkl")
    with open(save_path, "wb") as f:
        pkl.dump(pod_matrix, f)

    print(f"✅ Saved {save_path}  shape={pod_matrix.shape}")

print(f"\n🎯 共保存 {len(matches)} 个帧至目录 {output_dir}")
