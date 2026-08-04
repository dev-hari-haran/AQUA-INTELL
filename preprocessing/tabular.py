import numpy as np
import pandas as pd

class TabularPreprocessor:
    """
    Sensor & Tabular Data Preprocessing Engine
    Implements range validation, Z-score spike filtering, missing value imputation,
    diurnal cyclical encoding, and rolling features.
    """
    PARAM_BOUNDS = {
        'do_mgl': (0.0, 20.0),
        'ph': (3.0, 11.0),
        'temp_c': (5.0, 45.0),
        'nh3_mgl': (0.0, 5.0),
        'turbidity': (0.0, 500.0)
    }

    def validate_ranges(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if 'data_quality' not in df.columns:
            df['data_quality'] = 'VALID'

        for col, (low, high) in self.PARAM_BOUNDS.items():
            if col in df.columns:
                invalid_mask = (df[col] < low) | (df[col] > high)
                df.loc[invalid_mask, 'data_quality'] = 'INVALID'
                df.loc[invalid_mask, col] = np.nan
        return df

    def filter_spikes(self, df: pd.DataFrame, window: int = 120, threshold: float = 3.5) -> pd.DataFrame:
        df = df.copy()
        numeric_cols = [c for c in self.PARAM_BOUNDS.keys() if c in df.columns]
        
        for col in numeric_cols:
            rolling_mean = df[col].rolling(window=window, min_periods=10).mean()
            rolling_std = df[col].rolling(window=window, min_periods=10).std().replace(0, 1e-5)
            z_scores = np.abs((df[col] - rolling_mean) / rolling_std)
            
            spike_mask = z_scores > threshold
            local_median = df[col].rolling(window=window, min_periods=1).median()
            df.loc[spike_mask, col] = local_median[spike_mask]
        return df

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if 'ts' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['ts']):
            df['ts'] = pd.to_datetime(df['ts'])

        if 'ts' in df.columns:
            hour = df['ts'].dt.hour
            day_of_year = df['ts'].dt.dayofyear
            df['hour_sin'] = np.sin(2 * np.pi * hour / 24.0)
            df['hour_cos'] = np.cos(2 * np.pi * hour / 24.0)
            df['day_sin'] = np.sin(2 * np.pi * day_of_year / 365.25)
            df['day_cos'] = np.cos(2 * np.pi * day_of_year / 365.25)

        numeric_cols = [c for c in self.PARAM_BOUNDS.keys() if c in df.columns]
        for col in numeric_cols:
            df[f'{col}_mean_15m'] = df[col].rolling(15, min_periods=1).mean()
            df[f'{col}_std_15m'] = df[col].rolling(15, min_periods=1).std().fillna(0)
            df[f'{col}_mean_1h'] = df[col].rolling(60, min_periods=1).mean()
            df[f'{col}_mean_6h'] = df[col].rolling(360, min_periods=1).mean()

        return df.bfill().fillna(0)

    def train_val_test_split(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        is_timeseries: bool = False,
        time_col: str = None,
        random_state: int = 42
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Splits tabular dataset into Train, Validation, and Test subsets according to given ratios.
        
        Args:
            df: Input pandas DataFrame
            train_ratio: Proportion for training set (default 0.70)
            val_ratio: Proportion for validation set (default 0.15)
            test_ratio: Proportion for test set (default 0.15)
            is_timeseries: If True, performs chronological split without shuffling
            time_col: Column name for sorting timestamps if time-series
            random_state: Random state seed for reproducible non-timeseries split
            
        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-5, "Ratios must sum to 1.0"
        df = df.copy()

        if is_timeseries:
            if time_col and time_col in df.columns:
                parsed_ts = pd.to_datetime(df[time_col], errors='coerce')
                if parsed_ts.notna().any():
                    df[time_col] = parsed_ts
                    df = df.sort_values(by=time_col).reset_index(drop=True)


            n = len(df)
            train_end = int(n * train_ratio)
            val_end = train_end + int(n * val_ratio)

            train_df = df.iloc[:train_end].copy()
            val_df = df.iloc[train_end:val_end].copy()
            test_df = df.iloc[val_end:].copy()
        else:
            df_shuffled = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
            n = len(df_shuffled)
            train_end = int(n * train_ratio)
            val_end = train_end + int(n * val_ratio)

            train_df = df_shuffled.iloc[:train_end].copy()
            val_df = df_shuffled.iloc[train_end:val_end].copy()
            test_df = df_shuffled.iloc[val_end:].copy()

        train_df['split'] = 'train'
        val_df['split'] = 'val'
        test_df['split'] = 'test'

        return train_df, val_df, test_df

