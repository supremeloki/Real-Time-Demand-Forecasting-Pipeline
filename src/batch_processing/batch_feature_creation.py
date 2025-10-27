import sys
import os
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'src'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.config_reader import ConfigReader
from src.utils.logging_setup import setup_logging
import importlib.util
import os

# Get absolute path to avoid relative path issues
snapp_data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data_artifacts', 'tehran_traffic_simulator', 'generate_snapp_data.py')
spec = importlib.util.spec_from_file_location("generate_snapp_data", snapp_data_path)
generate_snapp_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_snapp_data)
SnappDataGenerator = generate_snapp_data.SnappDataGenerator

logger = setup_logging(__name__)

class BatchFeatureCreator:
    def __init__(self, env: str = "dev"):
        self.config = ConfigReader(env)
        self.synthetic_data_path = self.config.get("data_paths.synthetic_data")
        self.grid_size_km = self.config.get("features_params.feature_engineering.grid_size_km")
        self.lookback_windows_min = self.config.get("features_params.feature_engineering.lookback_windows_min")
        self.target_variable = self.config.get("features_params.target_variable")

    def _load_raw_data(self):
        if self.synthetic_data_path and "synthetic_snapp_data" in self.synthetic_data_path:
            logger.info("Generating synthetic data for batch feature creation.")
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now()
            generator = SnappDataGenerator(start_date, end_date)
            df = generator.generate_events(num_events_per_15min=20)
        else:
            logger.info(f"Loading raw data from {self.synthetic_data_path}")
            df = pd.read_csv(self.synthetic_data_path)
        
        df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])
        df = df.sort_values('event_timestamp').reset_index(drop=True)
        return df

    def _calculate_grid_ids(self, df):
        df['grid_id_latitude'] = (df['pickup_latitude'] / (self.grid_size_km / 111.0)).astype(int)
        # Approximate cos(latitude) for longitude grid sizing, more precise for real-world
        df['cos_lat'] = np.cos(np.radians(df['pickup_latitude']))
        df['grid_id_longitude'] = (df['pickup_longitude'] / (self.grid_size_km / (111.0 * df['cos_lat']))).astype(int)
        return df.drop(columns=['cos_lat'])

    def _aggregate_time_series_features(self, df):
        # Simple aggregation without MultiIndex
        df_agg = df.copy()
        df_agg['event_timestamp'] = pd.to_datetime(df_agg['event_timestamp'])
        df_agg['timestamp_15min'] = df_agg['event_timestamp'].dt.floor('15min')

        # Group by grid and 15min intervals
        grouped = df_agg.groupby(['grid_id_latitude', 'grid_id_longitude', 'timestamp_15min']).agg({
            'demand_at_pickup': ['count', 'sum']
        }).reset_index()

        # Flatten columns
        grouped.columns = ['grid_id_latitude', 'grid_id_longitude', 'event_timestamp', 'raw_demand_count', 'demand_sum']

        # Time features
        grouped['feature_window_start'] = grouped['event_timestamp']
        grouped['feature_window_end'] = grouped['event_timestamp'] + pd.Timedelta(minutes=15)
        grouped['hour_of_day'] = grouped['event_timestamp'].dt.hour
        grouped['day_of_week'] = grouped['event_timestamp'].dt.dayofweek
        grouped['is_weekend'] = (grouped['day_of_week'] >= 5).astype(int)
        grouped['is_holiday'] = 0
        grouped['peak_hour_indicator'] = ((grouped['hour_of_day'] >= 7) & (grouped['hour_of_day'] <= 9)) | \
                                       ((grouped['hour_of_day'] >= 17) & (grouped['hour_of_day'] <= 20)).astype(int)

        # Sort for rolling calculations
        grouped = grouped.sort_values(['grid_id_latitude', 'grid_id_longitude', 'event_timestamp'])

        # Lookback features - use expanding window instead of rolling
        for window_size in self.lookback_windows_min:
            window_periods = window_size // 15
            grouped[f'demand_last_{window_size}min'] = grouped.groupby(['grid_id_latitude', 'grid_id_longitude'])['demand_sum'] \
                .transform(lambda x: x.expanding(window_periods).sum().shift(1).fillna(0))

        # Target: next period demand
        grouped[self.target_variable] = grouped.groupby(['grid_id_latitude', 'grid_id_longitude'])['demand_sum'].shift(-1).fillna(0)

        return grouped.set_index('event_timestamp')

    def generate_batch_features(self):
        logger.info("Starting batch feature creation.")
        raw_df = self._load_raw_data()
        df_with_grids = self._calculate_grid_ids(raw_df)
        final_features_df = self._aggregate_time_series_features(df_with_grids)
        
        # Filter out rows where target is 0 due to end of data
        final_features_df = final_features_df[final_features_df[self.target_variable] > 0]

        logger.info(f"Generated {len(final_features_df)} batch features.")
        return final_features_df.drop(columns=['raw_demand_count', 'demand_sum'])

if __name__ == "__main__":
    feature_creator = BatchFeatureCreator(env="dev")
    features_df = feature_creator.generate_batch_features()
    output_path = "data_artifacts/sample_data/batch_processed_features.csv"
    features_df.to_csv(output_path, index=False)
    logger.info(f"Batch features saved to {output_path}")
