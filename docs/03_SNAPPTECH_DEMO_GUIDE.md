# 🎯 SnappTech Real-Time Ride Demand Forecasting: Demo Guide

This guide outlines how to set up and demonstrate the Real-Time Ride Demand Forecasting pipeline. It focuses on showcasing the MLOps capabilities, real-time feature engineering, model serving, and monitoring.

**📅 Last Updated:** 2025-10-27

**🔗 GitHub Repository:** [https://github.com/supremeloki/Real-Time-Demand-Forecasting-Pipeline](https://github.com/supremeloki/Real-Time-Demand-Forecasting-Pipeline)

**📧 Contact:** kooroushmasoumi@gmail.com

## 1. Prerequisites

*   Docker & Docker Compose (for local Kafka/Spark/MLflow setup)
*   Python 3.10+
*   `pip`
*   `kubectl` (if deploying to a Kubernetes cluster)
*   Access to a web browser for MLflow UI and potential dashboard visualization.

## 2. Local Setup (Docker Compose)

The easiest way to get all dependencies (Kafka, Zookeeper, MLflow, Spark Master/Worker) running locally is via Docker Compose.

1.  **Navigate to the `deployments/docker` directory.**
2.  **Create a `docker-compose.yaml` (example provided in repository):**
    ```yaml
    version: '3.8'
    services:
      zookeeper:
        image: 'bitnami/zookeeper:3.8.3'
        ports:
          - '2181:2181'
        environment:
          - ALLOW_ANONYMOUS_LOGIN=yes
      kafka:
        image: 'bitnami/kafka:3.5.1'
        ports:
          - '9092:9092'
        environment:
          - KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181
          - KAFKA_CFG_LISTENERS=PLAINTEXT://:9092
          - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://127.0.0.1:9092
          - ALLOW_PLAINTEXT_LISTENER=yes
        depends_on:
          - zookeeper
      mlflow:
        image: 'mlflow/mlflow:latest'
        ports:
          - '5000:5000'
        environment:
          - MLFLOW_TRACKING_URI=http://0.0.0.0:5000
          - MLFLOW_BACKEND_STORE_URI=sqlite:///mlruns.db
          - MLFLOW_DEFAULT_ARTIFACT_ROOT=/mlflow_artifacts
        volumes:
          - ./mlruns_data:/mlflow_artifacts
          - ./mlruns.db:/mlruns.db
      spark-master:
        image: 'bitnami/spark:3.4.1'
        command: ['/opt/bitnami/spark/bin/spark-shell', '--master', 'spark://0.0.0.0:7077']
        ports:
          - '8080:8080' # Spark Master UI
          - '7077:7077' # Spark Master
        environment:
          - SPARK_MODE=master
          - SPARK_RPC_AUTHENTICATION_ENABLED=no
          - SPARK_RPC_ENCRYPTION_ENABLED=no
          - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
          - SPARK_SSL_ENABLED=no
      spark-worker:
        image: 'bitnami/spark:3.4.1'
        command: ['/opt/bitnami/spark/bin/spark-shell', '--master', 'spark://spark-master:7077']
        depends_on:
          - spark-master
        environment:
          - SPARK_MODE=worker
          - SPARK_MASTER_URL=spark://spark-master:7077
          - SPARK_WORKER_CORES=1
          - SPARK_WORKER_MEMORY=1G
          - SPARK_RPC_AUTHENTICATION_ENABLED=no
          - SPARK_RPC_ENCRYPTION_ENABLED=no
          - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
          - SPARK_SSL_ENABLED=no
    ```
3.  **Start the services:**
    ```bash
    docker-compose up -d
    ```
    Verify Kafka, MLflow (http://localhost:5000), and Spark Master (http://localhost:8080) are running.

## 3. Data Simulation & Batch Feature Creation

The `src/data_artifacts/tehran_traffic_simulator/generate_snapp_data.py` script generates realistic (synthetic) ride events for Tehran. These events are used to create historical batch features for model training.

1.  **Generate Raw Data & Batch Features:**
    ```bash
    python src/data_artifacts/tehran_traffic_simulator/generate_snapp_data.py
    python src/batch_processing/batch_feature_creation.py
    ```
    This will produce `synthetic_snapp_data.csv` and `batch_processed_features.csv` in `data_artifacts/sample_data/`.

## 4. Model Training & MLflow

Train the demand forecasting model and observe MLflow integration.

1.  **Run Model Training:**
    ```bash
    python src/model_training/train.py
    ```
    This script will:
    *   Load batch features.
    *   Train an XGBoost model.
    *   Log parameters, metrics, and the model artifact to MLflow.
    *   Register the model in the MLflow Model Registry.
2.  **Promote Model to Production (Manual/Simulated):**
    After training, open the MLflow UI (http://localhost:5000). Navigate to the "Models" section, select your `demand_forecaster_dev` model, choose the latest version, and transition its stage to "Production." This action is crucial for the inference API to load the correct model.

## 5. Real-Time Feature Engineering (Spark Structured Streaming)

Demonstrate how real-time features are generated from Kafka events using Spark.

1.  **Start Spark Stream Processor (in a new terminal):**
    ```bash
    docker exec -it <spark-worker-container-id> /opt/bitnami/spark/bin/spark-submit \
      --master spark://spark-master:7077 \
      --driver-class-path /opt/bitnami/spark/jars/spark-sql-kafka-0-10_2.12-3.4.1.jar,/opt/bitnami/spark/jars/kafka-clients-2.8.1.jar \
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 \
      /app/src/stream_analytics/spark_stream_features.py
    ```
    *(Replace `<spark-worker-container-id>` with the actual ID from `docker ps`)*
2.  **Simulate Real-Time Event Ingestion to Kafka:**
    *(In another new terminal)*
    ```bash
    python -c "from src.kafka_client.kafka_producer import SnappKafkaProducer; from src.data_artifacts.tehran_traffic_simulator.generate_snapp_data import SnappDataGenerator; from datetime import datetime, timedelta; import time; config = SnappKafkaProducer().config; producer = SnappKafkaProducer(); generator = SnappDataGenerator(datetime.now(), datetime.now() + timedelta(minutes=1)); events = generator.generate_events(num_events_per_15min=5); print(f'Sending {len(events)} events to Kafka...'); for _, event in events.iterrows(): producer.send_message(config.get('kafka.input_topic'), event.to_dict()); time.sleep(0.1); producer.flush(); producer.close(); print('Events sent.')"
    ```
    Observe the Spark stream processor logs for feature generation.

## 6. Model Serving API (FastAPI)

Run the inference API to serve real-time demand predictions.

1.  **Build and Run Docker Container for Inference API:**
    ```bash
    docker build -t snapp-demand-forecast-inference:local -f deployments/docker/Dockerfile.inference .
    docker run -p 8000:80 --network host -e APP_ENV=dev -e MLFLOW_TRACKING_URI=http://localhost:5000 snapp-demand-forecast-inference:local
    ```
    *(Alternatively, run directly from project root for quick dev iteration)*
    ```bash
    uvicorn src.model_serving.api_app:app --host 0.0.0.0 --port 8000 --reload
    ```
2.  **Test the API (using `curl` or browser for Swagger UI):**
    *   **Health Check:** `http://localhost:8000/health`
    *   **Swagger UI:** `http://localhost:8000/docs`
    *   **Example Prediction (via `curl`):**
        ```bash
        curl -X POST "http://localhost:8000/predict_single" -H "Content-Type: application/json" -d '{
          "hour_of_day": 9,
          "day_of_week": 2,
          "is_weekend": 0,
          "is_holiday": 0,
          "peak_hour_indicator": 1,
          "demand_current_5min": 15.0,
          "demand_last_15min": 40.0,
          "demand_last_30min": 75.0,
          "demand_last_hour": 150.0,
          "demand_last_1440min": 160.0
        }'
        ```

## 7. Model Monitoring & A/B Testing

Showcase data drift detection, model performance monitoring, and LONO A/B testing.

1.  **Run Data Drift Detection:**
    ```bash
    python model_experiments/monitoring/data_drift_detector.py
    ```
    This generates a `drift_report_*.json` in `model_experiments/monitoring/`.
2.  **Run Model Performance Monitoring:**
    ```bash
    python model_experiments/monitoring/model_performance_monitor.py
    ```
    This generates a `performance_report_*.json` in `model_experiments/monitoring/`.
3.  **Simulate LONO A/B Testing:**
    ```bash
    python model_experiments/ab_testing/lono_interface.py
    ```
    This script simulates routing requests to different model versions based on configured traffic splits.

## 8. Clean Up

Stop Docker containers:
```bash
docker-compose down
```
Remove generated data artifacts and MLflow runs if desired.

```bash
rm -rf data_artifacts/sample_data/*.csv model_experiments/monitoring/*.json model_experiments/ab_testing/*.json /tmp/spark-checkpoint /tmp/mlruns_dev
