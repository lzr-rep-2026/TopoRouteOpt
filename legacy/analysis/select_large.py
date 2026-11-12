in_path = "../MixTraffic_16pod/TROD_linkpct/Uniform_Topo/300000/test_results_1.txt"
out_path = "../MixTraffic_16pod/TROD_linkpct/Uniform_Topo/300000/1_large_mlus.txt"
with open(in_path, "r", encoding="utf-8") as f_in, open(out_path, "w", encoding="utf-8") as f_out:
    for lineno, line in enumerate(f_in, start=1):  # Line numbers start at one.
        try:
            num = float(line.strip())  # Convert to a number.
        except ValueError:
            continue  # Skip values that are not numbers.
        if num > 1:
            f_out.write(f"{lineno}\t{num}\n")  # Separate the line number and value with a tab.

# line_numbers = set()

# with open(in_path, "r", encoding="utf-8") as f_in:
#     for lineno, line in enumerate(f_in, start=1):  # Line numbers start at one.
#         try:
#             num = float(line.strip())  # Convert to a number.
#         except ValueError:
#             continue  # Skip values that are not numbers.
#         if num > 1:
#             line_numbers.add(lineno)

# Write the selected line numbers as a set, e.g. {1, 3, 5}.
# with open(out_path, "w", encoding="utf-8") as f_out:
#     f_out.write("{" + ", ".join(map(str, sorted(line_numbers))) + "}")