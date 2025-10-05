import pandas as pd
import ast
import numpy as np
from scipy.spatial import cKDTree
from tqdm import tqdm

# -----------------------
# Função: converter lat/lon para coordenadas cartesianas
# -----------------------
def latlng_to_xyz(lat, lon):
    earth_radius = 6371.0
    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    x = earth_radius * np.cos(lat_r) * np.cos(lon_r)
    y = earth_radius * np.cos(lat_r) * np.sin(lon_r)
    z = earth_radius * np.sin(lat_r)
    return np.vstack([x, y, z]).T

def merge_data(df_swaps, df_stations, df_traffic, radius_km = 0.3):
    # 2. Get cabinet counts (recent)
    last_week = df_swaps['created_at'].dt.isocalendar().week.max()
    last_year = df_swaps['created_at'].dt.isocalendar().year.max()
    df_swaps_recent = df_swaps[
        (df_swaps['created_at'].dt.isocalendar().year == last_year) &
        (df_swaps['created_at'].dt.isocalendar().week == last_week)
    ]
    cabinet_counts = df_swaps_recent.groupby('swap_station_id')['cabinet_id'].nunique().reset_index()
    cabinet_counts = cabinet_counts.rename(columns={'cabinet_id': 'cabinet_number'})

    df_stations = df_stations.merge(
        cabinet_counts,
        on='swap_station_id',
        how='left'
    )
    df_stations['cabinet_number'] = df_stations['cabinet_number'].fillna(0).astype(int)

    # 3. Get swaps statistics
    daily_counts = df_swaps.groupby(['swap_station_id', 'day']).size().reset_index(name='swaps_count')
    daily_stats = daily_counts.groupby('swap_station_id')['swaps_count'].agg(
        swaps_per_day_mean='mean',
        swaps_per_day_median='median',
        swaps_per_day_max='max'
    ).reset_index()

    hourly_counts = df_swaps.groupby(['swap_station_id', 'day', 'hour']).size().reset_index(name='swaps_count')
    
    hourly_stats = hourly_counts.groupby('swap_station_id')['swaps_count'].agg(
        swaps_per_hour_mean='mean',
        swaps_per_hour_median='median',
        swaps_per_hour_max='max'
    ).reset_index()

    df_stations = df_stations.merge(daily_stats, on='swap_station_id', how='left')
    df_stations = df_stations.merge(hourly_stats, on='swap_station_id', how='left')


    # -----------------------
    # Pré-processamento
    # -----------------------
    traffic_xyz = latlng_to_xyz(df_traffic['lat'].values, df_traffic['lng'].values)
    stations_xyz = latlng_to_xyz(df_stations['lat'].values, df_stations['lng'].values)
    
    tree = cKDTree(traffic_xyz)
    
    # -----------------------
    # Iterar sobre as estações
    # -----------------------

    results = []
    
    for i in tqdm(range(len(df_stations)), desc="Processing stations"):
        station_point = stations_xyz[i]
    
        # Encontrar pontos de tráfego dentro do raio
        idxs = tree.query_ball_point(station_point, r=radius_km)
    
        if idxs:  # se encontrou pontos
            nearby_points = (
                df_traffic.iloc[idxs]
                .sort_values('observations', ascending=False)
                .head(5)            # pega os 20 maiores
            )
        
            nearby_obs = nearby_points['observations']
    
            max_idx = nearby_obs.idxmax()
            min_idx = nearby_obs.idxmin()
    
            results.append({
                'swap_station_id': df_stations.iloc[i]['swap_station_id'],
                'obs_max': nearby_obs.max(),
                'obs_min': nearby_obs.min(),
                'obs_mean': nearby_obs.mean(),
                'obs_sum': nearby_obs.sum(),
                'obs_q75': nearby_obs.quantile(0.75),
                'id_max': df_traffic.loc[max_idx, 'traffic_point_id'],
                'id_min': df_traffic.loc[min_idx, 'traffic_point_id'],
                'n_points_in_radius': len(idxs)
            })
        else:  # sem pontos no raio
            results.append({
                'swap_station_id': df_stations.iloc[i]['swap_station_id'],
                'obs_max': np.nan,
                'obs_min': np.nan,
                'obs_mean': np.nan,
                'obs_sum': nearby_obs.sum(),
                'obs_q75': nearby_obs.quantile(0.75),
                'id_max': None,
                'id_min': None,
                'n_points_in_radius': 0
            })
    
    df_station_traffic_summary = pd.DataFrame(results)
    
    # -----------------------
    # Unir com df_stations
    # -----------------------
    df_stations = df_stations.merge(df_station_traffic_summary, on='swap_station_id', how='left')

    # 4. Get swaps/observations calculations
    start_week = pd.Timestamp('2025-02-10')
    end_week = pd.Timestamp('2025-02-16')

    swaps_week = df_swaps[(df_swaps['created_at'] >= start_week) & 
                          (df_swaps['created_at'] <= end_week)]
    
    swaps_count_week = swaps_week.groupby('swap_station_id').size().reset_index(name='swaps_count')

    df_stations = df_stations.merge(
        swaps_count_week,
        on='swap_station_id',
        how='left'
    )
    
    df_stations['swaps_per_observation'] = (
        df_stations['swaps_count'] / df_stations['obs_q75'].replace(0, np.nan)
    )
    
    df_stations['observations_per_swaps'] = (
        df_stations['obs_q75'] / df_stations['swaps_count'].replace(0, np.nan)
    )
    
    df_stations['swaps_per_cabinet'] = (
        df_stations['swaps_per_day_mean'] / df_stations['cabinet_number'].replace(0, np.nan)
    )

    df_stations = df_stations.fillna(0)
        
    # 5. Merge all the data
    df_final = df_stations.merge(
        df_swaps,
        on='swap_station_id',
        how='left'
    )

    return df_final, df_stations