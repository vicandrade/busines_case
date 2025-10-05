import pandas as pd
from scipy.spatial import cKDTree
import numpy as np
from tqdm import tqdm
    
def transform_traffic_data(df): 
    # 2. Normalize observations column
    df['observations'] = (
        df['observations']
        .astype(str)
        .str
        .replace(',', '')
        .astype(int)
        )

    # 2. Create labels for traffic level
    df['traffic_level'] = 'low'
    df.loc[df['observations']>=20, 'traffic_level'] = 'medium'
    df.loc[df['observations']>=100, 'traffic_level'] = 'high'
    df.loc[df['observations']>=1000, 'traffic_level'] = 'intense'
    df.loc[df['observations']>=3000, 'traffic_level'] = 'very_intense'

    df = df.sort_values('observations', ascending=False)  # coloca o maior primeiro
    df = df.drop_duplicates(subset=['lat', 'lng'], keep='first')[:].reset_index(drop=True)
    
    # 3. Process date (week_observed) column
    df['week_observed'] = pd.to_datetime(df['week_observed'], format='%B %d, %Y')

    df['traffic_point_id'] = np.arange(len(df))

    return df