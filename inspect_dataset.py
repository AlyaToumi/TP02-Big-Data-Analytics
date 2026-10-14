import pandas as pd
import os

file_path = "data/ARP_MitM_dataset.csv"

print("=== DATASET INFORMATION ===")

# Check file size
file_size = os.path.getsize(file_path) / (1024**3)

print(f"Dataset size: {file_size:.2f} GiB")

# Read only 5 rows
df = pd.read_csv(
    file_path,
    header=None,
    nrows=5
)

print("\nDataset shape (sample):")
print(df.shape)

print("\nFirst 5 rows:")
print(df.head())

print("\nNumber of columns:")
print(len(df.columns))

print("\nData types:")
print(df.dtypes)
