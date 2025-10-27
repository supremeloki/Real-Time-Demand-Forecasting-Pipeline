# 🚀 SnappTech Real-Time Ride Demand Forecasting: System Architecture

This document outlines the high-level architecture of the SnappTech Real-Time Ride Demand Forecasting pipeline. The system is designed for high throughput, low latency, and continuous operational intelligence, crucial for optimizing driver allocation, dynamic pricing, and overall user experience.

**📅 Last Updated:** 2025-10-27

**🔗 GitHub Repository:** [https://github.com/supremeloki/Real-Time-Demand-Forecasting-Pipeline](https://github.com/supremeloki/Real-Time-Demand-Forecasting-Pipeline)

**📧 Contact:** kooroushmasoumi@gmail.com

## 1. High-Level Overview

The architecture is built around several interconnected components that handle data ingestion, feature engineering, model training, real-time inference, monitoring, and operational feedback loops. The core idea is to process ride events and related contextual data in real-time to provide immediate demand forecasts for specific geographic areas (geohashes).

```mermaid
graph TD
    A[Raw Data Sources<br>(Ride Events, GPS, Weather, Holidays)] --> B(Event Streaming & Ingestion<br>Kafka)
    B --> C{Real-Time Feature Engineering<br>Spark Structured Streaming}
    B --> D{Batch Feature Creation<br>Spark Batch Jobs}

    C --> E[Online Feature Store<br>(e.g., Redis, DynamoDB)]
    D --> F[Offline Feature Store / Data Lake<br>(e.g., S3, Delta Lake)]

    F --> G[Model Training & Experimentation<br>(MLflow, Optuna)]
    G --> H[Model Registry<br>(MLflow Model Registry)]

    E --> I[Real-Time Model Inference API<br>(FastAPI, Kubernetes)]
    H --> I

    I --> J[Operational Decision Engines<br>(Driver Allocation, Dynamic Pricing, Revenue Maximization)]
    I --> K[Prediction Monitoring & Feedback<br>(Performance, Confidence, Anomalies)]

    K --> L[MLOps Automation<br>(Retraining Triggers, A/B Testing)]
    J --> B

    L --> G
    L --> H
    L --> I

    subgraph MLOps & Governance
        L
        K
        N[Data Governance & Security<br>(Lineage, Auditing, Anonymization, Ethical Guidance)]
        N --> B
        N --> E
        N --> F
        N --> G
        N --> I
        N --> J
    end
```

## 2. Core Architectural Components

1.  **Data Ingestion & Event Streaming:**
    *   **Kafka (`src/kafka_client/`)**: Serves as the central nervous system for real-time ride events, driver updates, and system feedback. It handles high-volume, low-latency data streams.
    *   **Real-time Weather Integrator (`src/data_ingestion/realtime_weather_integrator.py`)**: Fetches external contextual data to enrich event streams.
    *   **Event Anomaly Simulator (`src/data_ingestion/event_anomaly_simulator.py`)**: Generates synthetic events and can inject anomalies for robust testing.

2.  **Feature Engineering:**
    *   **Spark Structured Streaming (`src/stream_analytics/spark_stream_features.py`)**: Processes Kafka streams to create real-time features (e.g., demand in last 5/15/30 minutes per geohash).
    *   **Batch Processing (`src/batch_processing/batch_feature_creation.py`)**: Generates historical features for model training and offline analysis from data lakes.
    *   **Online/Offline Feature Store (`src/feature_store/`)**: Stores and serves features consistently for both training and inference (e.g., `online_feature_retriever.py`, `backfill_manager.py`).
    *   **Data Quality & Curation (`src/data_quality/`, `src/data_curation/`)**: Includes schema validation (`feature_data_validator.py`, `dynamic_schema_enforcer.py`), anonymization (`data_anonymizer.py`), and sanitization (`data_sanitizer.py`).

3.  **Model Training & Experimentation:**
    *   **Model Training (`src/model_training/train.py`)**: Orchestrates the training of demand forecasting models (e.g., XGBoost).
    *   **MLflow Integration (`src/model_training/hyperparameter_optimizer.py`, `src/mlops_automation/model_experiment_promoter.py`)**: Used for experiment tracking, model versioning, and lifecycle management within the Model Registry.
    *   **Hyperparameter Optimization (`src/model_training/hyperparameter_optimizer.py`)**: Utilizes tools like Optuna to find optimal model parameters.
    *   **Model Governance (`src/model_governance/ethical_guidance_oracle.py`)**: Assesses models for fairness and ethical implications.

4.  **Model Serving (Real-Time Inference):**
    *   **FastAPI Inference API (`src/model_serving/api_app.py`)**: Provides a low-latency endpoint for predictions.
    *   **Kubernetes Deployment (`deployments/kubernetes/k8s_model_deployment.yaml`, `inference_hpa_ingress.yaml`)**: Manages the deployment, scaling, and exposure of the inference service.
    *   **Regional Model Management (`src/model_serving/regional_model_manager.py`)**: Serves different models based on geographic region for tailored predictions.
    *   **Ensemble Predictor (`src/model_serving/ensemble_predictor.py`)**: Combines predictions from multiple models for robustness.
    *   **Explainability Service (`src/model_serving/explainability_service.py`)**: Provides SHAP-based explanations for model predictions.
    *   **Prediction Confidence Scorer (`src/model_serving/prediction_confidence_scorer.py`)**: Quantifies the reliability of each prediction.

5.  **Monitoring & Observability:**
    *   **Data & Model Drift Detection (`model_experiments/monitoring/data_drift_detector.py`, `src/monitoring/concept_drift_detector.py`)**: Identifies shifts in data distributions or model behavior.
    *   **Model Performance Monitoring (`model_experiments/monitoring/model_performance_monitor.py`)**: Tracks prediction accuracy and latency metrics in real-time, comparing them against baselines.
    *   **Real-time Anomaly Detection (`src/monitoring/realtime_anomaly_detector.py`, `src/observability/metric_anomaly_hub.py`)**: Detects unusual patterns in input data or model predictions.
    *   **Prediction Feedback Consumer (`src/kafka_client/prediction_feedback_consumer.py`)**: Consumes actual ride outcomes to close the feedback loop for monitoring and retraining.

6.  **MLOps Automation & Orchestration:**
    *   **Automated Retraining Trigger (`model_experiments/retraining/automated_retraining_trigger.py`)**: Initiates model retraining based on monitoring alerts.
    *   **Model Promotion Workflow (`src/mlops_automation/model_experiment_promoter.py`)**: Manages the lifecycle of models from staging to production, including A/B testing.
    *   **A/B Testing (`model_experiments/ab_testing/lono_interface.py`)**: Facilitates experimentation with different model versions in production.
    *   **Temporal Guardian (`src/workflow_orchestration/chronos_temporal_guardian.py`)**: Manages scheduled tasks and workflows.
    *   **Celestial Alignment Engine (`src/orchestration/celestial_alignment_engine.py`)**: Oversees the holistic health and alignment of all core components.

7.  **Operational Integration:**
    *   **Driver Allocation Optimizer (`src/ops_integration/driver_allocation_optimizer.py`)**: Uses forecasts to recommend optimal driver positioning.
    *   **Dynamic Pricing Service (`src/ops_integration/dynamic_pricing_strategy.py`)**: Adjusts pricing based on predicted demand and supply.
    *   **Revenue Maximizer (`src/ops_integration/revenue_maximizer.py`)**: Integrates forecasts and pricing to project revenue and suggest operational insights.
    *   **Dynamic Price Elasticity Model (`src/optimization/dynamic_price_elasticity_model.py`)**: Learns and applies demand elasticity for smarter pricing.

8.  **Data Governance & Security:**
    *   **Data Lineage Tracker (`src/data_governance/data_lineage_tracker.py`)**: Provides visibility into data origins and transformations.
    *   **Data Access Auditor (`src/security/data_access_auditor.py`)**: Logs and monitors all access to critical data assets and models, alerting on suspicious activities.
    *   **Threat Intelligence Reactor (`src/security/threat_intelligence_reactor.py`)**: Integrates with threat intelligence feeds and automates responses to security incidents.
    *   **Immutable State Ledger (`src/data_integrity/immutable_state_ledger.py`)**: Provides an unalterable record of critical system states and configurations.