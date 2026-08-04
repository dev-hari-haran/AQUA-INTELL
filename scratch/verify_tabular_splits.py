import os
import glob
import pandas as pd

DATASET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Dataset'))

def test_tabular_splits():
    print("=" * 70)
    print("  VERIFYING TABULAR DATASETS 70:15:15 SPLIT INTEGRITY")
    print("=" * 70)

    csv_files = glob.glob(os.path.join(DATASET_DIR, "**", "*.csv"), recursive=True)
    master_csv_files = [
        f for f in csv_files 
        if not (f.endswith('_train.csv') or f.endswith('_val.csv') or f.endswith('_test.csv') or '\\splits\\' in f or '/splits/' in f)
    ]

    assert len(master_csv_files) == 13, f"Expected 13 master tabular CSV datasets, found {len(master_csv_files)}"

    for master_file in master_csv_files:
        base_path, _ = os.path.splitext(master_file)
        filename = os.path.basename(master_file)
        
        train_file = f"{base_path}_train.csv"
        val_file = f"{base_path}_val.csv"
        test_file = f"{base_path}_test.csv"

        assert os.path.exists(train_file), f"Missing train split for {filename}"
        assert os.path.exists(val_file), f"Missing val split for {filename}"
        assert os.path.exists(test_file), f"Missing test split for {filename}"

        master_df = pd.read_csv(master_file)
        train_df = pd.read_csv(train_file)
        val_df = pd.read_csv(val_file)
        test_df = pd.read_csv(test_file)

        # Verify split column exists in master
        assert 'split' in master_df.columns, f"Master CSV {filename} missing 'split' column"
        
        total_rows = len(master_df)
        sum_split_rows = len(train_df) + len(val_df) + len(test_df)
        assert sum_split_rows == total_rows, f"Row count mismatch for {filename}: {total_rows} vs {sum_split_rows}"

        print(f"[VERIFIED] {filename:<45} Total: {total_rows:3d} | Train: {len(train_df):3d} | Val: {len(val_df):3d} | Test: {len(test_df):3d}")

    print("=" * 70)
    print("ALL 13 TABULAR DATASETS SUCCESSFULLY VERIFIED!")

if __name__ == "__main__":
    test_tabular_splits()
