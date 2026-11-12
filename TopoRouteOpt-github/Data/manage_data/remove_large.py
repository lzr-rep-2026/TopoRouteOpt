import os

data_dir = "../Facebook_pod_b"

# Find and sort all t*.pkl files.
files = sorted([f for f in os.listdir(data_dir) if f.startswith("t") and f.endswith(".pkl")],
               key=lambda x: int(x[1:-4]))  # Sort by numeric index.

# Remove the first and last file.
if len(files) >= 2:
    os.remove(os.path.join(data_dir, files[0]))     # Remove t1.pkl.
    os.remove(os.path.join(data_dir, files[-1]))    # Remove the final file.
else:
    print("文件数量不足，无法删除首尾。")
    exit()

# List and sort the remaining files again.
remaining_files = sorted([f for f in os.listdir(data_dir) if f.startswith("t") and f.endswith(".pkl")],
                         key=lambda x: int(x[1:-4]))

# Renumber the files.
for new_idx, filename in enumerate(remaining_files, start=1):
    old_path = os.path.join(data_dir, filename)
    new_path = os.path.join(data_dir, f"t{new_idx}.pkl")
    os.rename(old_path, new_path)

print("重命名完成。")
