import pandas as pd
import logging
logging.basicConfig(level=logging.INFO)

from modeling.transform_model_data import transform_model_data
from modeling.make_predictions import predict_ids

def main():
    logging.info("Starting modeling pipeline...")
    logging.info('↓ Loading processed dataset...')
    df = pd.read_parquet('../data/processed/merged_data.parquet', engine='pyarrow')

    logging.info('☼ Transforming processed dataset...')
    df_cabinets_hourly, df_cabinets_daily, df_stations_hourly, df_stations_daily = transform_model_data(df)
    
    logging.info('☼ Making predictions...')
    pred_cabinets_hourly, pred_cabinets_daily, pred_stations_hourly, pred_stations_daily = predict_ids(df_cabinets_hourly, df_cabinets_daily, df_stations_hourly, df_stations_daily)

    logging.info('↑ Saving model datasets to disk...')
    pred_cabinets_hourly.to_parquet('../data/model/pred_cabinets_hourly.parquet', index=False, engine='pyarrow', compression='snappy')
    pred_cabinets_daily.to_parquet('../data/model/pred_cabinets_daily.parquet', index=False, engine='pyarrow', compression='snappy')
    pred_stations_hourly.to_parquet('../data/model/pred_stations_hourly.parquet', index=False, engine='pyarrow', compression='snappy')
    pred_stations_daily.to_parquet('../data/model/pred_stations_daily.parquet', index=False, engine='pyarrow', compression='snappy')

    logging.info('✓ Modeling pipeline completed successfully. Predictions files stored in: data/modeling/')
    
if __name__ == "__main__":
    main()