import pandas as pd

def group_data(df, time_col, id_col):
    # Agora agrupar por gabinete e hora
    df_model = (
        df
        .groupby([id_col, time_col])
        .size()
        .reset_index(name='counts')
    )

    freq = 'h'
    if time_col == 'date':
        freq = 'D'
    # Determinar o intervalo de datas completo
    all_hours = pd.date_range(
        start=df_model[time_col].min(),
        end=df_model[time_col].max(),
        freq=freq
    )
    
    # Para cada cabinet_id, combinar com todas as horas
    cabinets = df_model[id_col].unique()
    full_index = pd.MultiIndex.from_product(
        [cabinets, all_hours],
        names=[id_col, time_col]
    )
    
    # Reindexar e preencher horas faltantes com 0
    df_model = (
        df_model
        .set_index([id_col, time_col])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    
    df_model['hour'] = df_model[time_col].dt.hour
    df_model['day_of_week'] = df_model[time_col].dt.dayofweek   
    df_model['is_weekend']  = (df_model['day_of_week'] >= 5).astype(int)
    df_model['month'] = df_model[time_col].dt.month 
    
    # Lags úteis para capturar autocorrelação
    for lag in [1, 2, 3, 7, 30, 24, 48]:  # 1h, 2h, 1 dia, 2 dias
        df_model[f'lag_{lag}'] = df_model['counts'].shift(lag).fillna(0)
    
    # Converter categóricas em categoria para GLM
    df_model['day_of_week']  = df_model['day_of_week'].astype('category')
    
    # Rolling mean
    df_model['rolling_mean_3'] = df_model['counts'].shift(1).rolling(window=3).mean().fillna(df_model['counts'].mean())
    df_model['rolling_mean_24'] = df_model['counts'].shift(1).rolling(window=24).mean().fillna(df_model['counts'].mean())
    df_model['rolling_mean_7'] = df_model['counts'].shift(1).rolling(window=7).mean().fillna(df_model['counts'].mean())
    df_model['rolling_mean_30'] = df_model['counts'].shift(1).rolling(window=30).mean().fillna(df_model['counts'].mean())

    return df_model


def transform_model_data(df):    
    station_counts = (
        df['swap_station_id']
        .value_counts()
        .reset_index()
        .rename(columns={'index': 'swap_station_id'})
    )
    df = df[df['swap_station_id'].isin(station_counts[:5].swap_station_id)][:].reset_index(drop=True)

    df['created_at'] = pd.to_datetime(df['created_at'])
    df['datetime'] = pd.to_datetime(df['created_at']).dt.floor('h')
    df['date'] = df['created_at'].dt.date 

    df_cabinets_hourly = group_data(df, 'datetime', 'cabinet_id')
    df_cabinets_daily = group_data(df, 'date', 'cabinet_id')
    df_stations_hourly = group_data(df, 'datetime', 'swap_station_id')
    df_stations_daily = group_data(df, 'date', 'swap_station_id')

    return df_cabinets_hourly, df_cabinets_daily, df_stations_hourly, df_stations_daily