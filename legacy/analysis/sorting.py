# Read, sort, and save values.
input_file = "../MixTraffic_16pod/performance_upper_bound/300000/test_results.txt"       # Original file.
output_file = "sorted_mlus.txt"     # Sorted output file.

# Read and convert to numbers.
with open(input_file, "r") as f:
    numbers = [float(line.strip()) for line in f if line.strip()]

# Sort in descending order.
numbers.sort(reverse=True)

# Save the sorted values.
with open(output_file, "w") as f:
    for num in numbers:
        f.write(f"{num}\n")

print(f"已将排序结果保存到 {output_file}")
