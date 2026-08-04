import os
import sys
import glob
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from preprocessing.tabular import TabularPreprocessor


DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Dataset')

TIMESTAMP_CANDIDATES = [
    'timestamp', 'ts', 'sample_date', 'outbreak_date', 'observation_date', 'date', 'sampling_date'
]

def find_time_column(df: pd.DataFrame) -> str | None:
    for col in TIMESTAMP_CANDIDATES:
        if col in df.columns:
            return col
    return None

def split_all_tabular_datasets():
    print("=" * 70)
    print("  AIS TABULAR DATASET SPLITTER (70% Train : 15% Validation : 15% Test)")
    print("=" * 70)

    preprocessor = TabularPreprocessor()
    csv_files = glob.glob(os.path.join(DATASET_DIR, "**", "*.csv"), recursive=True)

    # Filter out existing split files if re-running
    csv_files = [f for f in csv_files if not (f.endswith('_train.csv') or f.endswith('_val.csv') or f.endswith('_test.csv') or '\\splits\\' in f or '/splits/' in f)]

    print(f"Found {len(csv_files)} target tabular CSV datasets.\n")

    summary_stats = []

    for file_path in csv_files:
        filename = os.path.basename(file_path)
        module_dir = os.path.dirname(file_path)
        base_name, _ = os.path.splitext(filename)

        df = pd.read_csv(file_path)
        time_col = find_time_column(df)
        is_timeseries = time_col is not None

        train_df, val_df, test_df = preprocessor.train_val_test_split(
            df,
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
            is_timeseries=is_timeseries,
            time_col=time_col,
            random_state=42
        )

        # 1. Update master CSV with split column
        combined_df = pd.concat([train_df, val_df, test_df], ignore_index=True)
        combined_df.to_csv(file_path, index=False)

        # 2. Save individual split CSVs in module directory
        train_path = os.path.join(module_dir, f"{base_name}_train.csv")
        val_path = os.path.join(module_dir, f"{base_name}_val.csv")
        test_path = os.path.join(module_dir, f"{base_name}_test.csv")

        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)

        # 3. Save into structured splits/ subdirectories
        splits_dir = os.path.join(module_dir, "splits")
        train_dir = os.path.join(splits_dir, "train")
        val_dir = os.path.join(splits_dir, "val")
        test_dir = os.path.join(splits_dir, "test")

        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(val_dir, exist_ok=True)
        os.makedirs(test_dir, exist_ok=True)

        train_df.to_csv(os.path.join(train_dir, filename), index=False)
        val_df.to_csv(os.path.join(val_dir, filename), index=False)
        test_df.to_csv(os.path.join(test_dir, filename), index=False)

        total_rows = len(df)
        n_train, n_val, n_test = len(train_df), len(val_df), len(test_df)
        pct_train = (n_train / total_rows) * 100
        pct_val = (n_val / total_rows) * 100
        pct_test = (n_test / total_rows) * 100

        summary_stats.append({
            'file': filename,
            'total': total_rows,
            'train': f"{n_train} ({pct_train:.1f}%)",
            'val': f"{n_val} ({pct_val:.1f}%)",
            'test': f"{n_test} ({pct_test:.1f}%)",
            'timeseries': is_timeseries
        })

        print(f"[OK] {filename}:")
        print(f"   - Total Rows : {total_rows}")
        print(f"   - Train (70%): {n_train} rows")
        print(f"   - Val   (15%): {n_val} rows")
        print(f"   - Test  (15%): {n_test} rows")
        print(f"   - Split Type : {'Chronological (Time-series)' if is_timeseries else 'Shuffled (Tabular)'}\n")

    print("=" * 70)
    print("  SUMMARY OF ALL 70:15:15 TABULAR DATASET SPLITS")
    print("=" * 70)
    summary_df = pd.DataFrame(summary_stats)
    print(summary_df.to_string(index=False))
    print("=" * 70)
    print("SUCCESS: All tabular datasets split successfully into train, val, and test subsets!")

if __name__ == "__main__":
    split_all_tabular_datasets()
