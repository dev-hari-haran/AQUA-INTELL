import os
import scipy.io as sio
import pandas as pd
import numpy as np

def convert_mat_to_dataframe(mat_path: str = 'water_dataset.mat'):
    """
    Parses water_dataset.mat and converts it into a structured Pandas DataFrame.
    """
    if not os.path.exists(mat_path):
        raise FileNotFoundError(f"MAT file not found at {mat_path}")

    data = sio.loadmat(mat_path)
    
    # Extract feature names
    raw_features = data['features'][0]
    feature_names = [f[0][0] if isinstance(f[0], np.ndarray) else str(f[0]) for f in raw_features]
    
    # Extract location IDs
    location_ids = data['location_ids'].flatten()
    
    # Process X_tr (Training Inputs)
    X_tr = data['X_tr'][0]
    Y_tr = data['Y_tr'] # Shape: (37, 423)

    records = []
    for t_step in range(len(X_tr)):
        step_data = X_tr[t_step] # Shape: (37, 11)
        for loc_idx in range(len(location_ids)):
            loc_id = location_ids[loc_idx]
            row_vals = step_data[loc_idx]
            target_val = Y_tr[loc_idx, t_step]
            
            record = {
                'time_step': t_step,
                'location_id': loc_id,
                'target_val': target_val,
                'split': 'train'
            }
            for f_idx in range(len(feature_names)):
                record[f'feat_{f_idx+1}'] = row_vals[f_idx]
            records.append(record)

    df = pd.DataFrame(records)
    print(f"Successfully converted MAT dataset into DataFrame with shape: {df.shape}")
    return df

if __name__ == "__main__":
    df = convert_mat_to_dataframe()
    print("Sample Data Snippet:\n", df.head())
