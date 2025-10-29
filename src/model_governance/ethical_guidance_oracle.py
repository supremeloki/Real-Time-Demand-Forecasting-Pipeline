import time
import random
from typing import Dict, Any, List


class EthicalGuidanceOracle:
    def __init__(
        self, fairness_metrics: List[str] | None = None, bias_threshold: float = 0.1
    ):
        self._fairness_metrics = (
            fairness_metrics
            if fairness_metrics
            else ["gender_bias", "age_group_disparity"]
        )
        self._bias_threshold = bias_threshold

    def _assess_fairness(self, prediction_context: Dict[str, Any]) -> Dict[str, float]:
        fairness_scores = {}
        for metric in self._fairness_metrics:
            score = random.uniform(0.0, 0.2)
            if "gender" in prediction_context:
                score += (
                    0.05 if prediction_context["gender"] == "female" else -0.02
                ) * random.uniform(0.5, 1.5)
            fairness_scores[metric] = max(0.0, min(0.5, score))
        return fairness_scores

    def provide_guidance(
        self, prediction_context: Dict[str, Any], model_prediction: float
    ) -> Dict[str, Any]:
        fairness_assessment = self._assess_fairness(prediction_context)

        ethical_concerns = [
            metric
            for metric, score in fairness_assessment.items()
            if score > self._bias_threshold
        ]

        guidance_score = 1.0 - sum(fairness_assessment.values()) / (
            len(self._fairness_metrics) + 1e-6
        )
        guidance_score = max(0.0, min(1.0, guidance_score))

        status = "ETHICAL_ALIGNMENT"
        if ethical_concerns:
            status = "BIAS_DETECTED"
            if guidance_score < 0.5:
                status = "CRITICAL_ETHICAL_RISK"

        return {
            "timestamp": time.time(),
            "context": prediction_context,
            "prediction": model_prediction,
            "fairness_assessment": fairness_assessment,
            "ethical_concerns": ethical_concerns,
            "guidance_score": round(guidance_score, 2),
            "status": status,
        }


if __name__ == "__main__":
    oracle = EthicalGuidanceOracle(bias_threshold=0.15)

    print("--- Simulating Ethical Guidance Oracle ---")

    context_1 = {"user_segment": "high_value", "gender": "male", "age": 35}
    prediction_1 = random.uniform(50, 100)
    guidance_1 = oracle.provide_guidance(context_1, prediction_1)
    print("\n--- Prediction 1 ---")
    for k, v in guidance_1.items():
        print(f"  {k}: {v}")

    context_2 = {"user_segment": "new_user", "gender": "female", "age": 22}
    prediction_2 = random.uniform(20, 70)
    guidance_2 = oracle.provide_guidance(context_2, prediction_2)
    print("\n--- Prediction 2 ---")
    for k, v in guidance_2.items():
        print(f"  {k}: {v}")

    context_3 = {"user_segment": "low_income", "gender": "other", "age": 50}
    prediction_3 = random.uniform(10, 40)
    guidance_3 = oracle.provide_guidance(context_3, prediction_3)
    print("\n--- Prediction 3 ---")
    for k, v in guidance_3.items():
        print(f"  {k}: {v}")
