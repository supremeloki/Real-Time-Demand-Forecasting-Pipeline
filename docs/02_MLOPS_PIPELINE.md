# 🔄 SnappTech Real-Time Ride Demand Forecasting: MLOps Pipeline

This document details the Machine Learning Operations (MLOps) pipeline for the SnappTech Real-Time Ride Demand Forecasting system. The pipeline is designed for automation, continuous integration/delivery (CI/CD), continuous training (CT), and continuous monitoring (CM) to ensure the model remains accurate, reliable, and relevant in a dynamic real-world environment.

**📅 Last Updated:** 2025-10-27

**🔗 GitHub Repository:** [https://github.com/supremeloki/Real-Time-Demand-Forecasting-Pipeline](https://github.com/supremeloki/Real-Time-Demand-Forecasting-Pipeline)

**📧 Contact:** kooroushmasoumi@gmail.com

## 1. MLOps Lifecycle Overview

The MLOps pipeline encompasses the entire lifecycle of the machine learning model, from data acquisition and feature engineering to model deployment, monitoring, and automated retraining.

```mermaid
graph TD
    A[Data Ingestion<br>(Raw Ride Events)] --> B(Data Validation<br>& Anonymization)
    B --> C{Feature Engineering<br>(Batch & Real-Time)}
    C --> D[Feature Store<br>(Online & Offline)]
    D --> E[Model Training<br>& Experimentation]
    E --> F[Model Evaluation<br>& Versioning]
    F --> G[Model Registry<br>(Staging)]
    G --> H[A/B Testing<br>& Model Promotion]
    H --> I[Model Deployment<br>(Kubernetes Inference API)]
    I --> J[Real-Time Predictions]
    J --> K[Operational Decision Systems<br>(Pricing, Driver Allocation)]
    J --> L[Monitoring<br>(Data, Model, Performance)]
    L --> M[Feedback Loop<br>(Actual vs. Predicted)]
    M --> L
    L --> N[Automated Retraining Trigger<br>(Drift, Performance Degradation)]
    N --> E

    subgraph CI/CD & Orchestration
        O[Code Changes] --> P{Build & Test}
        P --> E
        H --> Q[Automated Deployment]
        Q --> I
        R[Chronos Temporal Guardian<br>& Celestial Alignment] --> L
        R --> N
        R --> Q
    end

    subgraph Governance & Security
        S[Data Lineage] --> B
        S --> C
        S --> D
        S --> F
        T[Data Access Audit] --> D
        T --> I
        U[Ethical Guidance Oracle] --> J
        V[Threat Intelligence Reactor] --> T
        W[Immutable State Ledger] --> G
        W --> I
    end
```

## 2. Pipeline Stages

### 2.1. Data Ingestion & Validation

*   **Raw Event Collection (`src/kafka_client/kafka_producer.py`)**: Real-time ride events are ingested into Apache Kafka topics.
*   **Real-time Schema Validation (`src/data_validation/realtime_schema_validator.py`, `src/data_curation/dynamic_schema_enforcer.py`)**: Incoming raw data is validated against predefined schemas to ensure data quality at the source.
*   **Data Anonymization (`src/data_curation/data_anonymizer.py`)**: Sensitive PII (Personally Identifiable Information) fields are anonymized or masked to comply with privacy regulations.
*   **Event Anomaly Simulation (`src/data_ingestion/event_anomaly_simulator.py`)**: Used for testing the robustness of downstream anomaly detection systems by injecting synthetic anomalies.

### 2.2. Feature Engineering

*   **Batch Feature Creation (`src/batch_processing/batch_feature_creation.py`)**: Historical features are generated from raw data in batch jobs (e.g., daily) for model training.
*   **Real-Time Stream Processing (`src/stream_analytics/spark_stream_features.py`)**: Spark Structured Streaming jobs consume raw Kafka events to compute real-time features (e.g., current demand per geohash in the last 5 minutes).
*   **Online/Offline Feature Store (`src/feature_store/`)**: Features are stored in a dedicated Feature Store (e.g., `src/feature_store/online_feature_retriever.py` for online retrieval, `src/feature_store/backfill_manager.py` for offline population) to ensure consistency between training and inference.
*   **Data Sanitization (`src/data_curation/data_sanitizer.py`)**: Cleanses data by handling missing values and removing outliers before features are used.
*   **Schema Evolution Management (`src/data_quality/feature_schema_evolution_manager.py`)**: Manages and tracks changes to feature schemas to prevent breaking changes in the pipeline.

### 2.3. Model Training & Experimentation (CT - Continuous Training)

*   **Model Training (`src/model_training/train.py`, `src/model_training/algorithms/xgboost_model.py`)**: Models (e.g., XGBoost) are trained on the curated batch features.
*   **Hyperparameter Optimization (`src/model_training/hyperparameter_optimizer.py`)**: Optuna is used to optimize model hyperparameters, improving prediction accuracy.
*   **MLflow Integration (`src/model_training/train.py`, `src/mlops_automation/model_experiment_promoter.py`)**: All training runs, parameters, metrics, and model artifacts are tracked using MLflow for reproducibility and comparison. Models are registered in the MLflow Model Registry.
*   **Automated Retraining Trigger (`model_experiments/retraining/automated_retraining_trigger.py`)**: Triggers new training cycles based on predefined conditions (e.g., data drift, performance degradation).
*   **Model Governance (`src/model_governance/ethical_guidance_oracle.py`)**: Assesses model predictions for fairness and ethical biases.

### 2.4. Model Deployment & Serving (CI/CD - Continuous Integration/Continuous Deployment)

*   **Dockerization (`deployments/docker/Dockerfile.inference`)**: The inference API and model dependencies are packaged into Docker images for consistent deployment.
*   **Kubernetes Deployment (`deployments/kubernetes/k8s_model_deployment.yaml`, `deployments/kubernetes/inference_hpa_ingress.yaml`)**: Models are deployed as a FastAPI service on Kubernetes, leveraging features like Horizontal Pod Autoscaling (HPA) for dynamic scaling and Ingress for external access.
*   **Regional Model Management (`src/model_serving/regional_model_manager.py`)**: Allows deployment and serving of region-specific models alongside a global model.
*   **Ensemble Prediction (`src/model_serving/ensemble_predictor.py`)**: Combines predictions from multiple models for enhanced robustness and accuracy.
*   **Prediction Explainability (`src/model_serving/explainability_service.py`)**: Provides insights into why a model made a particular prediction (e.g., using SHAP values).
*   **Prediction Confidence Scoring (`src/model_serving/prediction_confidence_scorer.py`)**: Attaches a confidence score to each prediction, aiding downstream decision systems.
*   **Model Experiment Promoter (`src/mlops_automation/model_experiment_promoter.py`)**: Manages model transitions between Staging and Production in the MLflow Model Registry.
*   **A/B Testing (`model_experiments/ab_testing/lono_interface.py`)**: Facilitates controlled experimentation with new model versions in a live production environment.

### 2.5. Monitoring & Observability (CM - Continuous Monitoring)

*   **Data Drift Detection (`model_experiments/monitoring/data_drift_detector.py`, `src/monitoring/concept_drift_detector.py`)**: Continuously monitors feature distributions and identifies significant shifts that could impact model performance.
*   **Model Performance Monitoring (`model_experiments/monitoring/model_performance_monitor.py`)**: Tracks prediction accuracy and latency metrics in real-time, comparing them against baselines.
*   **Real-time Anomaly Detection (`src/monitoring/realtime_anomaly_detector.py`, `src/observability/metric_anomaly_hub.py`)**: Detects unusual patterns in incoming data streams, model predictions, or system metrics.
*   **Prediction Feedback Loop (`src/kafka_client/prediction_feedback_consumer.py`)**: Consumes actual ride outcomes to calculate real prediction errors, providing crucial data for monitoring and future retraining.
*   **Metric Anomaly Hub (`src/observability/metric_anomaly_hub.py`)**: Centralizes alerts from various detectors for unified incident response.

### 2.6. MLOps Orchestration & Optimization

*   **Chronos Temporal Guardian (`src/workflow_orchestration/chronos_temporal_guardian.py`)**: Manages the scheduling and execution of various MLOps tasks.
*   **Celestial Alignment Engine (`src/orchestration/celestial_alignment_engine.py`)**: Provides a holistic view of the system's health and triggers high-level remediation actions.
*   **Dynamic Resource Guardian (`src/cloud_ops/dynamic_resource_guardian.py`)**: Automatically scales cloud resources (e.g., Kubernetes pods, Spark clusters) up or down based on real-time load and cost considerations.
*   **Harmony Synchronizer (`src/data_integrity/harmony_synchronizer.py`)**: Ensures state consistency across distributed components.
*   **Oracle Parameter Nexus (`src/configuration/oracle_parameter_nexus.py`)**: Centralized management for dynamic configuration parameters and feature toggles.

### 2.7. Data Governance & Security

*   **Data Lineage Tracking (`src/data_governance/data_lineage_tracker.py`)**: Tracks the flow of data through the entire pipeline, from source to model output, crucial for debugging and compliance.
*   **Data Access Auditor (`src/security/data_access_auditor.py`)**: Logs and monitors all access to critical data assets and models, alerting on suspicious activities.
*   **Threat Intelligence Reactor (`src/security/threat_intelligence_reactor.py`)**: Integrates with threat intelligence feeds and automates responses to security incidents.
*   **Immutable State Ledger (`src/data_integrity/immutable_state_ledger.py`)**: Provides an unalterable record of critical system and model states, ensuring integrity and auditability.