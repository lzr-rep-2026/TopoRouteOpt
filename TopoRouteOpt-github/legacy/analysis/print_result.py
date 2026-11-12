result_files = [
    #('../DCNTraffic_16pod_8spine/performance_upper_bound/512/2000/test_results.txt', 'performance_upper_bound'),
    ('../DCNTraffic_16pod_8spine/VLB/Uniform_Topo/512/1500/test_results.txt', 'VLB'),
    # ('../DCNTraffic_16pod_8spine/TROD_linkpct/Uniform_Topo/512/2000/test_hop_count_results.txt', 'TROD_linkpct'),
    # ('../DCNTraffic_16pod_8spine/TROD_linkpct_centralized_TPE/Uniform_Topo/512/2000/test_hop_count_results.txt', 'centralized_TPE'),
    ('../DCNTraffic_16pod_8spine/TROD_linkpct_distributed_TPE/Uniform_Topo/512/1500/test_results_add1_sub30_all0.5_all0.8.txt', 'dis_1_30_all0.7_all0.8'),
]

# result_files = [
#     #('../DCNTraffic_16pod_8spine/performance_upper_bound/512/2000/test_results.txt', 'performance_upper_bound'),
#     ('../Facebook_pod_a/VLB/TROD_Topo/6000/test_results.txt', 'VLB'),
#     # ('../DCNTraffic_16pod_8spine/TROD_linkpct/Uniform_Topo/512/2000/test_hop_count_results.txt', 'TROD_linkpct'),
#     # ('../DCNTraffic_16pod_8spine/TROD_linkpct_centralized_TPE/Uniform_Topo/512/2000/test_hop_count_results.txt', 'centralized_TPE'),
#     ('../Facebook_pod_a/TROD_linkpct_distributed_TPE/TROD_Topo/6000/test_results_add1_sub1800_all0.8_all0.8.txt', 'dis_1_30_all0.7_all0.8'),
# ]

def get_percentile(numbers_sorted, percentile):
    n = len(numbers_sorted)
    idx = int(round(percentile / 100 * (n - 1)))
    return numbers_sorted[idx]

def get_stats(numbers):
    count = len(numbers)
    mean = sum(numbers) / count
    minimum = min(numbers)
    maximum = max(numbers)
    numbers_sorted = sorted(numbers)
    
    # median = p50
    if count % 2 == 1:
        median = numbers_sorted[count // 2]
    else:
        median = (numbers_sorted[count // 2 - 1] + numbers_sorted[count // 2]) / 2

    # std
    var = sum((x - mean)**2 for x in numbers) / count
    std = var ** 0.5

    # percentiles
    p50 = median
    p90 = get_percentile(numbers_sorted, 90)
    p95 = get_percentile(numbers_sorted, 95)
    p99 = get_percentile(numbers_sorted, 99)

    return count, mean, median, minimum, maximum, std, p50, p90, p95, p99


with open('hop_count.txt', 'w') as out:
    for filename, tag in result_files:
        numbers = []
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        numbers.append(float(line))
        except FileNotFoundError:
            out.write(f"文件: {filename} ({tag}) 找不到文件\n\n")
            continue

        if numbers:
            count, mean, median, minimum, maximum, std, p50, p90, p95, p99 = get_stats(numbers)
            out.write(f"文件: {filename} ({tag})\n")
            out.write(f"  count: {count}\n")
            out.write(f"  mean: {mean}\n")
            out.write(f"  median(p50): {median}\n")
            out.write(f"  min: {minimum}\n")
            out.write(f"  max: {maximum}\n")
            out.write(f"  std: {std}\n")
            out.write(f"  p50: {p50}\n")
            out.write(f"  p90: {p90}\n")
            out.write(f"  p95: {p95}\n")
            out.write(f"  p99: {p99}\n")
            out.write("\n")
        else:
            out.write(f"文件: {filename} ({tag}) 没有数据\n\n")
