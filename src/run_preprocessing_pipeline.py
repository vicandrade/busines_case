import pandas as pd
import logging
logging.basicConfig(level=logging.INFO)

from preprocessing.swaps_transform import transform_swaps_data
from preprocessing.stations_transform import transform_stations_data
from preprocessing.traffic_transform_v3 import transform_traffic_data
from preprocessing.merge_data_v2 import merge_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def main():
    logging.info("Starting data pipeline...")
    logging.info('↓ Loading raw datasets...')
    df_swaps = pd.read_parquet('../data/raw/case_data_science_charging_ops___battery_swap_2025-09-26T17_45_41.358859844Z.parquet', engine='pyarrow')
    df_stations = pd.read_parquet('../data/raw/case_data_science_charging_ops___swap_stations_info_2025-09-26T13_21_20.332938629Z.parquet', engine='pyarrow')
    df_traffic = pd.read_parquet('../data/raw/ds_case_data_2025-09-29T23_51_12.68945565Z.parquet', engine='pyarrow')

    logging.info('☼ Step 1/4: Transforming swaps dataset...')
    df_swaps_processed = transform_swaps_data(df_swaps)
    logging.info('☼ Step 2/4: Transforming stations dataset...')
    df_stations_processed = transform_stations_data(df_stations)
    logging.info('☼ Step 3/4: Transforming traffic dataset...')
    df_traffic_processed = transform_traffic_data(df_traffic)
    logging.info('☼ Step 4/4: Merging datasets and computing final metrics...')
    df_final, df_stations_final = merge_data(df_swaps_processed, df_stations_processed, df_traffic_processed)
    
    logging.info('↑ Saving processed datasets to disk...')
    df_swaps_processed.to_parquet('../data/processed/swaps_processed.parquet', index=False, engine='pyarrow', compression='snappy')
    df_stations_final.to_parquet('../data/processed/stations_processed.parquet', index=False, engine='pyarrow', compression='snappy')
    df_traffic_processed.to_parquet('../data/processed/traffic_processed.parquet', index=False, engine='pyarrow', compression='snappy')
    df_final.to_parquet('../data/processed/merged_data.parquet', index=False, engine='pyarrow', compression='snappy')

    logging.info('✓ Pipeline completed successfully. Processed files stored in: data/processed/')
    
if __name__ == "__main__":
    main()