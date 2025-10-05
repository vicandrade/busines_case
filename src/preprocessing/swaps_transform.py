import pandas as pd

# Funções auxiliares
def get_period(h):
    if 5 <= h < 12:
        return 'morning'
    elif 12 <= h < 18:
        return 'afternoon'
    elif 18 <= h < 24:
        return 'evening'
    else:
        return 'night'  # 0-5h

def rush_hour(h):
    return 'rush' if h in [8,9,17,18,19] else 'off_peak'

# Função de processamento
def transform_swaps_data(df):
    # 1. Remove duplicates
    df = df.drop_duplicates()

    # 2. Remove null data
    df = df.dropna(subset=['swap_station_id', 'cabinet_id'])

    # 3. Drop columns
    df = df.drop(columns=['battery_in_id', 'battery_out_id'])
    
    # 4. Process date columns
    df['created_at'] = pd.to_datetime(df['created_at'], format='%B %d, %Y, %I:%M %p')
    df['ended_at'] = pd.to_datetime(df['ended_at'], format='%B %d, %Y, %I:%M %p')

    # 5. Sort Values
    df = df.sort_values(['swap_station_id', 'created_at'])[:].reset_index(drop=True)

    # 6. Process numeric columns
    num_cols = ['cabinet_id', 'swap_station_id', 'rider_id', 'battery_in_level', 'battery_out_level']	
    for col in num_cols:
        df[col] = df[col].astype(str).str.replace(',', '').astype(int)

    # 7. Normalize status column
    df['status'] = df['status'].str.lower()

    # 8. Create "battery charged" feature
    df['battery_charged'] = df['battery_out_level'] - df['battery_in_level']

    # 9. Create time features
    df['day'] = df['created_at'].dt.date
    df['month'] = df['created_at'].dt.month
    df['hour'] = df['created_at'].dt.hour
    df['day_period'] = df['hour'].apply(get_period)
    df['charging_duration_min'] = (df['ended_at'] - df['created_at']).dt.total_seconds() / 60
    df['day_of_week'] = df['created_at'].dt.strftime('%a').str.lower()
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['rush_period'] = df['hour'].apply(rush_hour)

    return df