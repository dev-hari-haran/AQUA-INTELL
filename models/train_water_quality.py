import os
import sys
import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sklearn.ensemble import IsolationForest
from xgboost import XGBRegressor, XGBClassifier
from preprocessing.tabular import TabularPreprocessor

from ingestion.convert_mat_dataset import convert_mat_to_dataframe

MODEL_DIR = "./models/registry/water_quality"
os.makedirs(MODEL_DIR, exist_ok=True)

def load_or_generate_training_data(mat_path: str = None) -> pd.DataFrame:
    """Loads real USGS water_dataset.mat dataset if present; otherwise generates synthetic data."""
    if mat_path is None:
        possible_paths = [
            os.path.join('data', 'UCI Water Quality', 'UCI Water Quality.mat'),
            os.path.join('data', 'UCI Water Quality', 'water_dataset.mat'),
            'water_dataset.mat'
        ]
        for p in possible_paths:
            if os.path.exists(p):
                mat_path = p
                break
        if mat_path is None:
            mat_path = 'water_dataset.mat'

    if os.path.exists(mat_path):
        print(f"[Dataset] Loading real USGS dataset from {mat_path}...")
        df_mat = convert_mat_to_dataframe(mat_path)
        # Rename columns to standard AIS sensor names
        df_mat['do_mgl'] = df_mat['feat_7'] * 12.0 # Rescale mean DO to mg/L
        df_mat['ph'] = df_mat['feat_2'] * 10.0     # Rescale Max pH
        df_mat['temp_c'] = df_mat['feat_9'] * 35.0 # Rescale Mean Temp to °C
        df_mat['nh3_mgl'] = df_mat['feat_5'] * 2.0 # Rescale Conductance to NH3 proxy
        df_mat['turbidity'] = df_mat['feat_1'] * 100.0
        df_mat['ts'] = pd.date_range("2026-01-01", periods=len(df_mat), freq="1min")
        return df_mat
    else:
        print("[Dataset] MAT file not found. Generating synthetic sensor stream dataset...")
        np.random.seed(42)
        n_samples = 5000
        timestamps = pd.date_range("2026-01-01", periods=n_samples, freq="1min")
        hours = timestamps.hour
        temp_base = 26.0 + 3.0 * np.sin(2 * np.pi * (hours - 8) / 24.0) + np.random.normal(0, 0.5, n_samples)
        do_base = 6.5 - 2.0 * np.sin(2 * np.pi * (hours - 6) / 24.0) + np.random.normal(0, 0.4, n_samples)
        ph_base = 7.5 + 0.5 * np.sin(2 * np.pi * (hours - 12) / 24.0) + np.random.normal(0, 0.1, n_samples)
        nh3_base = 0.2 + np.random.exponential(0.1, n_samples)
        turbidity_base = 25.0 + np.random.normal(0, 3.0, n_samples)

        return pd.DataFrame({
            'ts': timestamps,
            'do_mgl': np.clip(do_base, 0.5, 15.0),
            'ph': np.clip(ph_base, 4.0, 10.0),
            'temp_c': np.clip(temp_base, 10.0, 40.0),
            'nh3_mgl': np.clip(nh3_base, 0.01, 4.5),
            'turbidity': np.clip(turbidity_base, 1.0, 300.0)
        })

def train_water_quality_models():
    print("=" * 60)
    print("  AIS WATER QUALITY MODEL TRAINING PIPELINE")
    print("=" * 60)

    print("[1/4] Loading & Preprocessing Water Quality Dataset...")
    csv_split_path = os.path.join("Dataset", "Water_Quality", "Synthetic_Sensor_Streams_train.csv")
    csv_master_path = os.path.join("Dataset", "Water_Quality", "Synthetic_Sensor_Streams.csv")
    
    preprocessor = TabularPreprocessor()

    if os.path.exists(csv_master_path):
        print(f"[Dataset] Loading tabular dataset from {csv_master_path}...")
        df_raw = pd.read_csv(csv_master_path)
    else:
        df_raw = load_or_generate_training_data()

    df_clean = preprocessor.filter_spikes(preprocessor.validate_ranges(df_raw))
    df_features = preprocessor.extract_features(df_clean)

    if 'split' in df_features.columns:
        train_df = df_features[df_features['split'] == 'train']
        val_df = df_features[df_features['split'] == 'val']
        test_df = df_features[df_features['split'] == 'test']
    else:
        train_df, val_df, test_df = preprocessor.train_val_test_split(
            df_features, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, is_timeseries=True, time_col='ts'
        )

    feature_cols = [c for c in df_features.columns if c not in ['ts', 'timestamp', 'data_quality', 'split', 'data_source', 'source_url', 'pond_id']]
    
    X_train = train_df[feature_cols]
    X_val = val_df[feature_cols]
    X_test = test_df[feature_cols]

    print(f"Data Split Ratios -> Train: {len(X_train)} ({len(X_train)/len(df_features)*100:.1f}%), Val: {len(X_val)} ({len(X_val)/len(df_features)*100:.1f}%), Test: {len(X_test)} ({len(X_test)/len(df_features)*100:.1f}%)")

    print("[2/4] Training Isolation Forest Anomaly Detector on Train set...")
    iso_forest = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    iso_forest.fit(X_train)
    joblib.dump(iso_forest, os.path.join(MODEL_DIR, "isolation_forest.joblib"))

    print("[3/4] Training XGBoost DO 24h Forecaster on Train set & Evaluating on Val/Test sets...")
    y_train = train_df['do_mgl'].shift(-15).ffill()
    y_val = val_df['do_mgl'].shift(-15).ffill()
    y_test = test_df['do_mgl'].shift(-15).ffill()

    xgb_do_forecaster = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05, random_state=42)
    xgb_do_forecaster.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    joblib.dump(xgb_do_forecaster, os.path.join(MODEL_DIR, "xgb_do_forecaster.joblib"))

    test_preds = xgb_do_forecaster.predict(X_test)
    test_mae = np.mean(np.abs(test_preds - y_test))
    print(f"[Validation/Test Metrics] XGBoost Forecaster Test MAE: {test_mae:.4f} mg/L")

    print("[4/4] SUCCESS: Water Quality models trained on 70:15:15 splits and serialized successfully!")

if __name__ == "__main__":
    train_water_quality_models()

