import os
import joblib
import numpy as np
import pandas as pd
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

    print("[1/3] Loading & Preprocessing Water Quality Dataset...")
    df_raw = load_or_generate_training_data()
    preprocessor = TabularPreprocessor()
    df_clean = preprocessor.filter_spikes(preprocessor.validate_ranges(df_raw))
    df_features = preprocessor.extract_features(df_clean)

    feature_cols = [c for c in df_features.columns if c not in ['ts', 'data_quality', 'split']]
    X = df_features[feature_cols]

    print("[2/3] Training Isolation Forest Anomaly Detector...")
    iso_forest = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    iso_forest.fit(X)
    joblib.dump(iso_forest, os.path.join(MODEL_DIR, "isolation_forest.joblib"))

    print("[3/3] Training XGBoost DO 24h Forecaster...")
    y_do_24h = df_features['do_mgl'].shift(-60).ffill()
    xgb_do_forecaster = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05, random_state=42)
    xgb_do_forecaster.fit(X, y_do_24h)
    joblib.dump(xgb_do_forecaster, os.path.join(MODEL_DIR, "xgb_do_forecaster.joblib"))

    print("SUCCESS: Water Quality models trained and serialized successfully!")

if __name__ == "__main__":
    train_water_quality_models()
