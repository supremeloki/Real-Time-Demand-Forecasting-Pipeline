import logging
from typing import Dict, Any, List
import numpy as np
import random
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DynamicPriceElasticityModel:
    """
    Estimates the price elasticity of demand for ride-hailing services in real-time,
    allowing for more nuanced dynamic pricing strategies.
    """

    def __init__(
        self,
        initial_elasticity: float = -0.8,  # Baseline elasticity (e.g., -0.8 means 10% price increase -> 8% demand drop)
        learning_rate: float = 0.01,
        min_elasticity: float = -2.5,
        max_elasticity: float = -0.1,
    ):

        self.current_elasticity: Dict[str, float] = {}  # Store elasticity per geohash
        self.initial_elasticity = initial_elasticity
        self.learning_rate = learning_rate
        self.min_elasticity = min_elasticity
        self.max_elasticity = max_elasticity

        self.historical_data: Dict[str, List[Dict[str, Any]]] = (
            {}
        )  # Store (price_multiplier, demand, completed_rides)
        logging.info(
            f"DynamicPriceElasticityModel initialized with initial elasticity: {initial_elasticity}"
        )

    def _get_current_elasticity(self, geohash_id: str) -> float:
        """Returns the current estimated elasticity for a geohash, or the initial value."""
        return self.current_elasticity.get(geohash_id, self.initial_elasticity)

    def update_elasticity(
        self,
        geohash_id: str,
        old_price_multiplier: float,
        new_price_multiplier: float,
        observed_demand_change: float,
    ):  # Percentage change in demand (e.g., 0.1 for 10% increase)
        """
        Updates the price elasticity estimate for a geohash based on observed changes.
        This is a simplified adaptive learning approach.
        """
        if old_price_multiplier == 0 or new_price_multiplier == 0:
            logging.warning("Cannot update elasticity with zero price multiplier.")
            return

        price_change_ratio = (
            new_price_multiplier - old_price_multiplier
        ) / old_price_multiplier
        if price_change_ratio == 0:
            logging.debug("No price change, skipping elasticity update.")
            return

        # Calculate observed elasticity
        observed_elasticity = (
            observed_demand_change / price_change_ratio
            if price_change_ratio != 0
            else self.initial_elasticity
        )

        # Simple exponential moving average (EMA) update
        current_eta = self._get_current_elasticity(geohash_id)
        new_eta = (
            current_eta * (1 - self.learning_rate)
            + observed_elasticity * self.learning_rate
        )

        # Clamp elasticity within reasonable bounds
        new_eta = max(self.min_elasticity, min(self.max_elasticity, new_eta))

        self.current_elasticity[geohash_id] = new_eta
        logging.info(
            f"Elasticity for {geohash_id} updated: {current_eta:.2f} -> {new_eta:.2f} (Observed: {observed_elasticity:.2f})"
        )

    def predict_demand_impact(
        self,
        geohash_id: str,
        current_demand: float,
        price_multiplier_change_percentage: float,
    ) -> float:
        """
        Predicts the percentage change in demand given a proposed price multiplier change.
        """
        elasticity = self._get_current_elasticity(geohash_id)
        predicted_demand_change = elasticity * price_multiplier_change_percentage

        logging.debug(
            f"Predicted demand change for {geohash_id} with {price_multiplier_change_percentage*100:.1f}% price change: {predicted_demand_change*100:.1f}%"
        )
        return current_demand * (1 + predicted_demand_change)


if __name__ == "__main__":
    elasticity_model = DynamicPriceElasticityModel(
        initial_elasticity=-0.7, learning_rate=0.1
    )

    geohash = "dr5ru"
    initial_demand = 100.0
    initial_price_multiplier = 1.0

    print("--- Simulating Dynamic Price Elasticity Learning ---")

    # Simulate first price change
    print(
        f"\nInitial state for {geohash}: Demand={initial_demand:.1f}, Price Multiplier={initial_price_multiplier:.1f}, Elasticity={elasticity_model._get_current_elasticity(geohash):.2f}"
    )

    # Increase price by 20%
    proposed_price_multiplier_1 = initial_price_multiplier * 1.2

    # Simulate observed demand change (e.g., -15% due to price increase, so demand drops to 85)
    observed_demand_1 = initial_demand * (1 - 0.15)  # 15% drop

    # Calculate observed demand change percentage
    observed_demand_change_percent_1 = (
        observed_demand_1 - initial_demand
    ) / initial_demand

    print(
        f"Price increased to {proposed_price_multiplier_1:.1f}. Observed demand: {observed_demand_1:.1f}"
    )
    elasticity_model.update_elasticity(
        geohash_id=geohash,
        old_price_multiplier=initial_price_multiplier,
        new_price_multiplier=proposed_price_multiplier_1,
        observed_demand_change=observed_demand_change_percent_1,
    )
    print(
        f"Updated Elasticity for {geohash}: {elasticity_model._get_current_elasticity(geohash):.2f}"
    )

    predicted_demand_after_10_percent_inc = elasticity_model.predict_demand_impact(
        geohash, observed_demand_1, 0.1
    )
    print(
        f"If price increases by 10% from current, predicted demand: {predicted_demand_after_10_percent_inc:.1f}"
    )

    # Simulate a second price change and update
    print("\n--- Second Update Cycle ---")
    current_demand_2 = observed_demand_1
    current_price_multiplier_2 = proposed_price_multiplier_1

    # Decrease price by 10% from previous
    proposed_price_multiplier_2 = current_price_multiplier_2 * 0.9

    # Simulate observed demand change (e.g., +8% due to price decrease, so demand increases)
    observed_demand_2 = current_demand_2 * (1 + 0.08)
    observed_demand_change_percent_2 = (
        observed_demand_2 - current_demand_2
    ) / current_demand_2

    print(
        f"Price decreased to {proposed_price_multiplier_2:.1f}. Observed demand: {observed_demand_2:.1f}"
    )
    elasticity_model.update_elasticity(
        geohash_id=geohash,
        old_price_multiplier=current_price_multiplier_2,
        new_price_multiplier=proposed_price_multiplier_2,
        observed_demand_change=observed_demand_change_percent_2,
    )
    print(
        f"Updated Elasticity for {geohash}: {elasticity_model._get_current_elasticity(geohash):.2f}"
    )
