import pandas as pd
import numpy as np
from prophet import Prophet

# Função de previsão: Prophet
def make_predictions(df, time_col, id_col):
    df_preds = pd.DataFrame()
    for id in df[id_col].unique():
        df_sub = df[df[id_col] == id].copy().reset_index(drop=True)

        freq = 'D'
        horizon = 7
        if time_col == 'datetime':
            freq = 'h'
            horizon = 24*7

        prophet_df = df_sub[[time_col, 'counts']].rename(columns={time_col:'ds', 'counts':'y'})

        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            interval_width=0.95
        )
        
        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=horizon, freq=freq)

        forecast = model.predict(future)

        forecast['predicted'] = forecast['yhat']
        forecast['upper_interval'] = forecast['yhat_upper']
        forecast['lower_interval'] = forecast['yhat_lower']

        df_pred = pd.merge(
            df_sub,
            forecast[['ds','predicted', 'upper_interval', 'lower_interval']],
            left_on=time_col,
            right_on='ds',
            how='outer'
        ).drop(columns=[time_col])

        for col in ['predicted', 'upper_interval', 'lower_interval']:
            df_pred.loc[df_pred['ds']>prophet_df['ds'].max(), col] = df_pred[col]*1.1
            df_pred[col] = df_pred[col].fillna(np.nan).round()
    
            df_pred.loc[df_pred[col]<0, col] = 0
    
        df_pred[id_col] = id
        df_pred['id'] = id
        
        # Ordenar por tempo
        df_pred = df_pred.sort_values('ds').reset_index(drop=True)
        
        df_preds = pd.concat([df_preds, df_pred])

    return df_preds

def predict_ids(df_cabinets_hourly, df_cabinets_daily, df_stations_hourly, df_stations_daily):
    pred_cabinets_hourly = make_predictions(df_cabinets_hourly, 'datetime', 'cabinet_id')
    pred_cabinets_daily = make_predictions(df_cabinets_daily, 'date', 'cabinet_id')
    pred_stations_hourly = make_predictions(df_stations_hourly, 'datetime', 'swap_station_id')
    pred_stations_daily = make_predictions(df_stations_daily, 'date', 'swap_station_id')

    return pred_cabinets_hourly, pred_cabinets_daily, pred_stations_hourly, pred_stations_daily
    
    