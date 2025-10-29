import logging
from typing import Dict, Any
from datetime import datetime
import random

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class RevenueMaximizer:
    """
    Integrates predicted demand, pricing multipliers, and estimated driver allocation
    to forecast potential revenue and suggest operational adjustments.
    """

    def __init__(self, base_ride_fare: float = 5.0):
        self.base_ride_fare = base_ride_fare
        logging.info(
            f"RevenueMaximizer initialized with base_ride_fare={base_ride_fare}"
        )

    def _estimate_completed_rides(
        self,
        predicted_demand: float,
        active_drivers: int,
        driver_capacity_per_hour: float = 3.0,
    ) -> float:
        """
        Estimates the number of rides that can be completed given demand and supply.
        Simplified model: assumes a driver can complete 'driver_capacity_per_hour' rides.
        """
        max_possible_rides_by_supply = active_drivers * driver_capacity_per_hour
        # Actual completed rides will be limited by either demand or supply
        return min(predicted_demand, max_possible_rides_by_supply)

    def calculate_projected_revenue(
        self,
        geohash_id: str,
        predicted_demand: float,
        active_drivers: int,
        pricing_multiplier: float,
        forecast_horizon_hours: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Calculates projected revenue for a specific geohash and forecast horizon.
        """
        logging.info(
            f"Calculating revenue for {geohash_id}: Demand={predicted_demand:.2f}, Drivers={active_drivers}, Multiplier={pricing_multiplier:.2f}"
        )

        # Scale predicted demand for the given forecast horizon (assuming predicted_demand is typically per 15-min or 30-min window)
        # Assuming predicted_demand is 15-minute forecast, scale to full hour
        scaled_demand = predicted_demand * (
            forecast_horizon_hours / 0.25
        )  # 0.25 hours = 15 minutes

        estimated_completed_rides = self._estimate_completed_rides(
            scaled_demand, active_drivers
        )

        projected_revenue = (
            estimated_completed_rides * self.base_ride_fare * pricing_multiplier
        )

        # Determine operational insight based on the gap between demand and completed rides
        demand_completion_ratio = (
            estimated_completed_rides / scaled_demand if scaled_demand > 0 else 1.0
        )

        operational_insight = "OPTIMAL_BALANCE"
        if demand_completion_ratio < 0.7:
            operational_insight = "DEMAND_SURPLUS_UNDER_STAFFED"
        elif (
            demand_completion_ratio > 1.2
        ):  # Implies more supply than demand (simplified)
            operational_insight = "SUPPLY_SURPLUS_OVER_STAFFED"

        logging.info(
            f"Projected revenue for {geohash_id}: {projected_revenue:.2f} (Completed Rides: {estimated_completed_rides:.1f})"
        )

        return {
            "geohash_id": geohash_id,
            "timestamp": datetime.now().isoformat(),
            "predicted_demand_scaled": round(scaled_demand, 2),
            "active_drivers": active_drivers,
            "pricing_multiplier": round(pricing_multiplier, 2),
            "estimated_completed_rides": round(estimated_completed_rides, 1),
            "projected_revenue": round(projected_revenue, 2),
            "operational_insight": operational_insight,
        }


if __name__ == "__main__":
    revenue_maximizer = RevenueMaximizer(base_ride_fare=6.5)

    geohashes_to_analyze = ["dr5ru", "dr5ry", "dr5rz"]

    print("--- Simulating Revenue Maximization ---")
    for _ in range(3):  # Simulate a few time steps
        print(f"\n--- Simulation Round {_ + 1} ---")
        for gh in geohashes_to_analyze:
            # Simulate inputs (these would come from other services)
            simulated_predicted_demand = random.uniform(20, 150)  # 15-min forecast
            simulated_active_drivers = random.randint(5, 40)
            simulated_pricing_multiplier = random.uniform(0.9, 2.5)

            revenue_analysis = revenue_maximizer.calculate_projected_revenue(
                geohash_id=gh,
                predicted_demand=simulated_predicted_demand,
                active_drivers=simulated_active_drivers,
                pricing_multiplier=simulated_pricing_multiplier,
                forecast_horizon_hours=1.0,  # Project for the next hour
            )
            print(
                f"  {revenue_analysis['geohash_id']}: Demand={revenue_analysis['predicted_demand_scaled']:.1f} (1hr), Drivers={revenue_analysis['active_drivers']}, Multiplier={revenue_analysis['pricing_multiplier']:.2f}"
            )
            print(
                f"    -> Est. Rides={revenue_analysis['estimated_completed_rides']:.1f}, Projected Revenue=${revenue_analysis['projected_revenue']:.2f}, Insight: {revenue_analysis['operational_insight']}"
            )
        # time.sleep(0.5)
