import os
import re
import shutil
from pathlib import Path
import pickle
import numpy as np

def extract_number(filename):
    """Extract the numeric index from a filename."""
    match = re.search(r't(\d+)\.pkl', filename)
    if match:
        return int(match.group(1))
    return 0

def reorganize_by_odd_even(source_dir, target_dir):
    """
    Reorder traffic matrices by index parity.
    Place odd-indexed files before even-indexed files.
    
    Args:
        source_dir: Source directory.
        target_dir: Destination directory.
    """
    # Create the destination directory if needed.
    Path(target_dir).mkdir(exist_ok=True, parents=True)

    
    # List and sort all pickle files.
    files = [f for f in os.listdir(source_dir) if f.endswith('.pkl')]
    
    # Extract numeric indices for sorting.
    files.sort(key=extract_number)
    
    odd_files = []
    even_files = []
    
    # Separate files by odd and even indices.
    for file in files:
        num = extract_number(file)
        if num % 2 == 1:  # Odd indices.
            odd_files.append(file)
        else:  # Even indices.
            even_files.append(file)
    
    # Renumber and copy odd files first, then even files.
    new_index = 1
    
    # Process odd-indexed files.
    for file in odd_files:
        new_filename = f"t{new_index}.pkl"
        source_path = os.path.join(source_dir, file)
        dest_path = os.path.join(target_dir, new_filename)
        print(f"复制 {file} 到 {new_filename} (奇数索引)")
        
        # Copy without changing file contents.
        shutil.copy2(source_path, dest_path)
        new_index += 1
    
    # Process even-indexed files.
    for file in even_files:
        new_filename = f"t{new_index}.pkl"
        source_path = os.path.join(source_dir, file)
        dest_path = os.path.join(target_dir, new_filename)
        print(f"复制 {file} 到 {new_filename} (偶数索引)")
        
        # Copy without changing file contents.
        shutil.copy2(source_path, dest_path)
        new_index += 1
    
    print(f"共处理了 {len(odd_files)} 个奇数文件和 {len(even_files)} 个偶数文件")
    print(f"总共重新排序了 {new_index-1} 个文件")

if __name__ == "__main__":
    # Source data directory.
    source_directory = "../rawdata/Facebook_pod_a_traffic_matrices_1s"
    
    # Destination directory; it may be newly created.
    target_directory = "../Facebook_pod_a_two_days"
    
    # Run the file reordering.
    reorganize_by_odd_even(source_directory, target_directory)
    print("处理完成!")
