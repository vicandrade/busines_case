import pandas as pd
import ast
import numpy as np

def merge_data(df_swaps, df_stations, df_traffic):
    # 1. Get traffic data
    df_traffic_exploded = df_traffic.explode('nearby_stations')
    df_traffic_exploded = df_traffic_exploded.rename(columns={'nearby_stations': 'swap_station_id'})

    traffic_agg = df_traffic_exploded.groupby('swap_station_id').agg({
        'observations': 'max',
        'traffic_level': 'max'
    }).reset_index()

    df_stations = df_stations.merge(
        df_traffic_exploded.groupby('swap_station_id').agg({
            'observations': 'max',
            'traffic_level': 'max'       
        }).reset_index(),
        left_on='swap_station_id',
        right_on='swap_station_id',
        how='left'
    )

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
        df_stations['swaps_count'] / df_stations['observations'].replace(0, np.nan)
    )
    
    df_stations['observations_per_swaps'] = (
        df_stations['observations'] / df_stations['swaps_count'].replace(0, np.nan)
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