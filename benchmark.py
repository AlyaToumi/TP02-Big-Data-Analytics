
import os
import csv
import matplotlib.pyplot as plt

# ==========================================
# TP02: PERFORMANCE BENCHMARK
# ==========================================

RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Actual experimental results
methods = [
    "Standard Pandas",
    "Pandas Chunking",
    "Dask DataFrame"
]

execution_times = [63.62, 64.01, 97.44]
peak_memory = [2401.39, 173.70, 342.88]

print("=" * 55)
print("TP02: PERFORMANCE BENCHMARK")
print("=" * 55)

# ==========================================
# 1. SAVE BENCHMARK DATA
# ==========================================

csv_path = os.path.join(
    RESULTS_DIR, "benchmark_results.csv"
)

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "Method",
        "Execution_Time_Seconds",
        "Observed_Peak_RAM_MB"
    ])

    for method, elapsed, memory in zip(
        methods, execution_times, peak_memory
    ):
        writer.writerow([method, elapsed, memory])

print("Benchmark CSV saved:", csv_path)

# ==========================================
# 2. EXECUTION TIME COMPARISON
# ==========================================

plt.figure(figsize=(10, 6))

bars = plt.bar(
    methods,
    execution_times,
    color=["#3B82F6", "#10B981", "#F59E0B"]
)

plt.title("Execution Time Comparison - TP02")
plt.ylabel("Execution Time (seconds)")
plt.xlabel("Processing Method")

for bar, value in zip(bars, execution_times):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1,
        f"{value:.2f} s",
        ha="center",
        fontsize=11
    )

plt.ylim(0, max(execution_times) * 1.20)
plt.grid(axis="y", alpha=0.25)
plt.tight_layout()

plt.savefig(
    os.path.join(RESULTS_DIR, "execution_time.png"),
    dpi=200
)

plt.close()

print("Execution time chart saved.")

# ==========================================
# 3. MEMORY COMPARISON
# ==========================================

plt.figure(figsize=(10, 6))

bars = plt.bar(
    methods,
    peak_memory,
    color=["#3B82F6", "#10B981", "#F59E0B"]
)

plt.title("Observed Peak Memory Comparison - TP02")
plt.ylabel("Observed Peak RAM (MB)")
plt.xlabel("Processing Method")

for bar, value in zip(bars, peak_memory):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 30,
        f"{value:.2f} MB",
        ha="center",
        fontsize=11
    )

plt.ylim(0, max(peak_memory) * 1.20)
plt.grid(axis="y", alpha=0.25)
plt.tight_layout()

plt.savefig(
    os.path.join(RESULTS_DIR, "memory_usage.png"),
    dpi=200
)

plt.close()

print("Memory comparison chart saved.")

# ==========================================
# 4. PERFORMANCE SUMMARY
# ==========================================

print("\n" + "=" * 55)
print("FINAL COMPARISON")
print("=" * 55)

for method, elapsed, memory in zip(
    methods, execution_times, peak_memory
):
    print(f"\nMethod: {method}")
    print(f"Execution time: {elapsed:.2f} seconds")
    print(f"Observed peak RAM: {memory:.2f} MB")

print("\nFastest observed loading/execution time:",
      methods[execution_times.index(min(execution_times))])

print("Lowest observed memory:",
      methods[peak_memory.index(min(peak_memory))])

print("\nNote: Benchmark methods have different workloads")
print("and memory measurement approaches.")
print("Results are descriptive, not fully controlled.")

print("\nAll benchmark files saved in results/")
print("=" * 55)

