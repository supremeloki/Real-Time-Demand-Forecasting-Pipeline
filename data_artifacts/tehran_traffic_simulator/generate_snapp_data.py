import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

class SnappDataGenerator:
    def __init__(self, start_time, end_time, grid_size_km=1.0, tehran_center=(35.72, 51.39)):
        self.start_time = start_time
        self.end_time = end_time
        self.grid_size_km = grid_size_km
        self.tehran_center = tehran_center
        self.tehran_area_lat = (tehran_center[0] - 0.15, tehran_center[0] + 0.15)
        self.tehran_area_lon = (tehran_center[1] - 0.25, tehran_center[1] + 0.25)

    def _generate_location(self):
        lat = random.uniform(self.tehran_area_lat[0], self.tehran_area_lat[1])
        lon = random.uniform(self.tehran_area_lon[0], self.tehran_area_lon[1])
        return lat, lon

    def _generate_time_features(self, dt):
        hour = dt.hour
        day_of_week = dt.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        is_holiday = 1 if (dt.month == 3 and 20 <= dt.day <= 24) or \
                          (dt.month == 8 and dt.day == 19) else 0 # Example: Nowruz, Tasua/Ashura approximation
        peak_hour_indicator = 1 if (7 <= hour <= 9) or (17 <= hour <= 20) else 0
        return hour, day_of_week, is_weekend, is_holiday, peak_hour_indicator

    def _generate_demand_pattern(self, dt, lat, lon):
        base_demand = 10 + 5 * np.sin(dt.hour / 24 * 2 * np.pi)
        if 7 <= dt.hour <= 9 or 17 <= dt.hour <= 20: # Peak hours
            base_demand *= 1.5
        if dt.weekday() >= 5: # Weekend
            base_demand *= 0.8
        
        # Simulate local density
        dist_from_center = np.sqrt((lat - self.tehran_center[0])**2 + (lon - self.tehran_center[1])**2)
        base_demand *= (1 - dist_from_center * 2) # Higher near center

        return max(0, int(base_demand + np.random.normal(0, 3)))

    def generate_events(self, num_events_per_15min=5):
        current_time = self.start_time
        events = []
        while current_time < self.end_time:
            for _ in range(random.randint(num_events_per_15min - 2, num_events_per_15min + 3)):
                pickup_lat, pickup_lon = self._generate_location()
                dropoff_lat, dropoff_lon = self._generate_location()
                hour, day_of_week, is_weekend, is_holiday, peak_hour = self._generate_time_features(current_time)
                
                event = {
                    "event_timestamp": current_time.isoformat(),
                    "pickup_latitude": pickup_lat,
                    "pickup_longitude": pickup_lon,
                    "dropoff_latitude": dropoff_lat,
                    "dropoff_longitude": dropoff_lon,
                    "hour_of_day": hour,
                    "day_of_week": day_of_week,
                    "is_weekend": is_weekend,
                    "is_holiday": is_holiday,
                    "peak_hour_indicator": peak_hour,
                    "demand_at_pickup": self._generate_demand_pattern(current_time, pickup_lat, pickup_lon) # Proxy for local demand
                }
                events.append(event)
            current_time += timedelta(minutes=random.randint(5, 20)) # Irregular event intervals

        return pd.DataFrame(events)

if __name__ == "__main__":
    start = datetime(2025, 10, 1, 0, 0, 0)
    end = datetime(2025, 10, 3, 0, 0, 0)
    generator = SnappDataGenerator(start, end)
    synthetic_data = generator.generate_events(num_events_per_15min=10)
    synthetic_data.to_csv("data_artifacts/sample_data/synthetic_snapp_data.csv", index=False)
    print(f"Generated {len(synthetic_data)} synthetic events.")
