import pandas as pd
from scipy.spatial import cKDTree
import numpy as np
from tqdm import tqdm
    
def latlng_to_xyz(lat, lng, R = 6371.0): # R: Earth radius
    lat_r = np.radians(lat)
    lng_r = np.radians(lng)
    x = R * np.cos(lat_r) * np.cos(lng_r)
    y = R * np.cos(lat_r) * np.sin(lng_r)
    z = R * np.sin(lat_r)
    return np.vstack([x, y, z]).T
    
def transform_traffic_data(df, df_stations, radius_km=2.0): 
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
    
    # Converte para coordenadas 3D
    traffic_xyz = latlng_to_xyz(df['lat'].values, df['lng'].values)
    stations_xyz = latlng_to_xyz(df_stations['lat'].values, df_stations['lng'].values)
    
    # Árvore com os pontos de tráfego
    tree = cKDTree(traffic_xyz)
    
    # Para cada estação, encontrar o ponto de tráfego mais próximo
    distances, indices = tree.query(stations_xyz, k=1)  # k=1 → mais próximo
    
    # Recuperar as informações do ponto de tráfego mais próximo
    df_stations['nearest_traffic_distance_km'] = distances      # distância em km
    df_stations['nearest_traffic_observations'] = df.iloc[indices]['observations'].values
    df_stations['nearest_traffic_level'] = df.iloc[indices]['traffic_level'].values

    return df, df_stations