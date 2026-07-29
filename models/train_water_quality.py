import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from xgboost import XGBRegressor, XGBClassifier
from preprocessing.tabular import TabularPreprocessor

MODEL_DIR = "./models/registry/water_quality"
os.makedirs(MODEL_DIR, exist_ok=True)

def generate_synthetic_training_data(n_samples: int = 5000) -> pd.DataFrame:
    np.random.seed(42)
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

    print("[1/3] Preprocessing Sensor Stream Dataset...")
    df_raw = generate_synthetic_training_data(n_samples=5000)
    preprocessor = TabularPreprocessor()
    df_clean = preprocessor.filter_spikes(preprocessor.validate_ranges(df_raw))
    df_features = preprocessor.extract_features(df_clean)

    feature_cols = [c for c in df_features.columns if c not in ['ts', 'data_quality']]
    X = df_features[feature_cols]

    print("[2/3] Training Isolation Forest Anomaly Detector...")
    iso_forest = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    iso_forest.fit(X)
    joblib.dump(iso_forest, os.path.join(MODEL_DIR, "isolation_forest.joblib"))

    print("[3/3] Training XGBoost DO 24h Forecaster...")
    y_do_24h = df_features['do_mgl'].shift(-1440).fillna(method='ffill')
    xgb_do_forecaster = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05, random_state=42)
    xgb_do_forecaster.fit(X, y_do_24h)
    joblib.dump(xgb_do_forecaster, os.path.join(MODEL_DIR, "xgb_do_forecaster.joblib"))

    print("SUCCESS: Water Quality models trained and serialized successfully!")

if __name__ == "__main__":
    train_water_quality_models()
