import logging
from datetime import datetime, timedelta
import random
import time

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DriverAllocationOptimizer:
    def __init__(self, demand_forecaster_client):
        self.demand_forecaster_client = (
            demand_forecaster_client  # Client to interact with prediction API
        )
        self.active_drivers_per_geohash = {}  # Mock of real-time driver availability
        logging.info("DriverAllocationOptimizer initialized.")

    def _get_active_drivers(self, geohash_id: str) -> int:
        # Simulate fetching real-time active driver count for a geohash
        # In production, this would come from a real-time driver tracking system
        if geohash_id not in self.active_drivers_per_geohash:
            self.active_drivers_per_geohash[geohash_id] = random.randint(5, 20)
        # Simulate minor fluctuations
        self.active_drivers_per_geohash[geohash_id] += random.choice([-1, 0, 1])
        self.active_drivers_per_geohash[geohash_id] = max(
            1, self.active_drivers_per_geohash[geohash_id]
        )
        return self.active_drivers_per_geohash[geohash_id]

    def _calculate_demand_supply_gap(
        self, predicted_demand: float, active_drivers: int
    ) -> float:
        # Simple heuristic: demand per driver
        # A more complex model would consider capacity, wait times, etc.
        if active_drivers == 0:
            return predicted_demand  # Infinite gap if no drivers
        return predicted_demand / active_drivers - 2.0  # Target 2 rides per driver

    def optimize_allocation_for_geohash(
        self, geohash_id: str, forecast_horizon_mins: int = 15
    ) -> dict:
        logging.info(f"Optimizing driver allocation for geohash: {geohash_id}")

        # 1. Get real-time features and predict demand
        # This would call the model serving API or a feature store to get latest features
        # and then make a prediction.
        # For this mock, we'll simulate the prediction directly.

        # Mock features (could be fetched from OnlineFeatureStoreClient)
        mock_features = {
            "hour_of_day": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "is_weekend": 1 if datetime.now().weekday() >= 5 else 0,
            "is_holiday": 0,
            "peak_hour_indicator": (
                1
                if 7 <= datetime.now().hour < 10 or 16 <= datetime.now().hour < 19
                else 0
            ),
            "demand_current_5min": random.uniform(5, 30),
            "demand_last_15min": random.uniform(20, 80),
            "demand_last_30min": random.uniform(40, 150),
            "demand_last_hour": random.uniform(100, 300),
            "demand_last_1440min": random.uniform(120, 350),
        }

        # Simulate calling the demand forecaster client
        # predicted_demand = self.demand_forecaster_client.predict(geohash_id, mock_features)
        predicted_demand = random.uniform(20, 100)  # Mock prediction for next 15 mins
        logging.info(
            f"Predicted demand for {geohash_id} in next {forecast_horizon_mins} mins: {predicted_demand:.2f}"
        )

        # 2. Get current active drivers
        active_drivers = self._get_active_drivers(geohash_id)
        logging.info(f"Active drivers in {geohash_id}: {active_drivers}")

        # 3. Calculate demand-supply gap
        demand_supply_gap_score = self._calculate_demand_supply_gap(
            predicted_demand, active_drivers
        )

        # 4. Determine recommendation
        if demand_supply_gap_score > 2.0:  # High demand, low supply
            recommendation = "INCREASE_DRIVERS"
            target_drivers = int(predicted_demand / 1.5)  # Target 1.5 rides per driver
            incentive_level = "HIGH"
            logging.warning(
                f"High demand-supply gap in {geohash_id}. Recommend increasing drivers."
            )
        elif demand_supply_gap_score < -1.0:  # Low demand, high supply
            recommendation = "OPTIMIZE_EXISTING_DRIVERS"
            target_drivers = active_drivers
            incentive_level = "LOW"
            logging.info(
                f"Low demand-supply gap in {geohash_id}. Optimize existing drivers."
            )
        else:
            recommendation = "MAINTAIN_CURRENT"
            target_drivers = active_drivers
            incentive_level = "MEDIUM"
            logging.info(
                f"Balanced demand-supply in {geohash_id}. Maintain current state."
            )

        return {
            "geohash_id": geohash_id,
            "predicted_demand": predicted_demand,
            "active_drivers": active_drivers,
            "demand_supply_gap_score": round(demand_supply_gap_score, 2),
            "recommendation": recommendation,
            "target_drivers": target_drivers,
            "incentive_level": incentive_level,
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    # Mock Demand Forecaster Client (would be src.model_serving.prediction_logic.PredictionLogic in reality)
    class MockDemandForecasterClient:
        def predict(self, geohash_id: str, features: dict) -> float:
            # Simulate a prediction based on some features
            return features["demand_current_5min"] * random.uniform(
                3, 5
            )  # Scale 5-min demand to 15-min forecast

    mock_forecaster = MockDemandForecasterClient()
    optimizer = DriverAllocationOptimizer(mock_forecaster)

    # Simulate optimization for a few geohashes
    geohashes_to_optimize = ["dr5ru", "dr5ry", "dr5rz", "dr5r7"]

    print("--- Simulating Driver Allocation Optimization ---")
    for _ in range(3):  # Run a few rounds to see changes
        for gh in geohashes_to_optimize:
            result = optimizer.optimize_allocation_for_geohash(gh)
            print(
                f"\nOptimization Result for {result['geohash_id']} at {result['timestamp']}:"
            )
            print(f"  Predicted Demand: {result['predicted_demand']:.2f}")
            print(f"  Active Drivers: {result['active_drivers']}")
            print(
                f"  Recommendation: {result['recommendation']} (Target: {result['target_drivers']} drivers, Incentive: {result['incentive_level']})"
            )
        time.sleep(1)
