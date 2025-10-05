import pandas as pd
from scipy.spatial import cKDTree

def transform_stations_data(df):
    # 1. Remove duplicates
    df = df.drop_duplicates()

    # 2. Rename columns
    df = df.rename(
        columns={
            'Endereço': 'address',
            'latitude': 'lat',
            'longitude': 'lng'
        }
    )
    
    # 3. Adjust ID
    df['swap_station_id'] = df['swap_station_id'].astype(str).str.replace(',', '').astype(int)
    
    # 4. Neighborhood name extraction
    df = df[~df['address'].str.contains('Santiago Metropolitan Region')]
    df = df[~df['address'].str.contains('- PA')][:].reset_index(drop=True)
    df['neighborhood'] = df['address'].str.extract(r'-\s*([^,]+),')

    # 5. Stations naming
    df = df.sort_values(by=['neighborhood', 'swap_station_id'])
    df['number'] = (df.groupby('neighborhood').cumcount() + 1).astype(int)
    df['swap_station_name'] = (
        'Estação ' + df['neighborhood'].str.title() + ' ' + df['number'].astype(str)
    )
    df = df.drop(columns=['number'])

    # 6. Geospatial features
    coords = df[['lat', 'lng']].to_numpy()

    tree = cKDTree(coords)

    distances, indices = tree.query(coords, k=2)

    df['nearest_station_distance_km'] = (distances[:,1] * 111).round(4)  # ~111 km/degree
    df['nearest_station_id'] = df.iloc[indices[:,1]].swap_station_id.values
    df['nearest_station_name'] = df.iloc[indices[:,1]].swap_station_name.values
    
    return df