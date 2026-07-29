# Aquaculture Intelligence System (AIS)
## Technical Issues & Feature Backlog Tracker (`mvpv1`)

This document tracks all open technical issues, pending module endpoints, infrastructure tasks, and model training dependencies in the current `mvpv1` repository.

---

## 📌 Issue Overview Matrix

| Issue ID | Severity | Category | Target Module / Area | Description |
| :--- | :--- | :--- | :--- | :--- |
| **ISSUE-01** | High | User Task / ML | Model Registry | Train and serialize model weight files (`.joblib`, `.onnx`, `.tflite`, `.pt`) via training scripts. |
| **ISSUE-02** | High | Backend / API | Growth, Feed, Satellite | Scaffold missing REST API routers (`growth.py`, `feed.py`, `satellite.py`) and register in `main.py`. |
| **ISSUE-03** | Medium | Backend / DB | Database Layer | Implement async SQLAlchemy database session dependency injection for live PostgreSQL/TimescaleDB queries. |
| **ISSUE-04** | Medium | Remote Sensing | Satellite Module | Integrate Sentinel Hub API OAuth & Celery background worker for weekly Sentinel-2 GeoTIFF downloads. |
| **ISSUE-05** | Medium | Frontend / UI | PWA Web Client | Implement Leaflet.js map layer controls and PWA Camera Widget component in `frontend/app.js`. |
| **ISSUE-06** | Low | Gen AI / PDF | Auto-Reporting | Implement ReportLab PDF generator functions for `/generate/weekly-report` and `/generate/cycle-plan`. |

---

## 🔍 Detailed Issue Breakdown & Remediation Guidelines

### ISSUE-01: Model Weights Serialization (`User Task`)
- **Category**: Machine Learning / Model Registry
- **Status**: Pending User Execution
- **Description**: The model registry directories (`./models/registry/water_quality/`, `./models/registry/disease/`, etc.) currently do not contain binary model weight files because dataset training is performed by the user for hyperparameter control.
- **Action Required**:
  - Run `python models/train_water_quality.py` to produce `isolation_forest.joblib` and `xgb_do_forecaster.joblib`.
  - Scaffold and run training scripts for EfficientNet-B2, YOLOv8, XGBoost Growth, and U-Net Segmentation.

---

### ISSUE-02: Complete Remaining Module API Routers
- **Category**: Backend Microservices
- **Status**: Open Development
- **Description**: While `water_quality.py`, `disease.py`, and `genai.py` routes are registered in `backend/main.py`, the remaining 3 module routers need full endpoint handlers:
  - `backend/routers/growth.py`: `/stocking/record`, `/predict/growth`, `/predict/harvest-date`
  - `backend/routers/feed.py`: `/optimize/feed`, `/track/fcr`
  - `backend/routers/satellite.py`: `/satellite/pond-map/{farm_id}`, `/drone/analyze`
- **Action Required**: Create router files under `backend/routers/` and include them in `backend/main.py`.

---

### ISSUE-03: Async Database Session Dependency Injection
- **Category**: Database & ORM Integration
- **Status**: Open Development
- **Description**: Migration scripts (`001_initial_schema.sql`) create TimescaleDB hypertables, but FastAPI endpoints currently use staging state. Live database queries require async SQLAlchemy `get_db` dependency injection.
- **Action Required**: Implement `backend/database/connection.py` using `async_sessionmaker` and `asyncpg`.

---

### ISSUE-04: Sentinel Hub API Ingestion & Celery Background Tasks
- **Category**: Remote Sensing / Background Processing
- **Status**: Open Development
- **Description**: Satellite imagery ingestion requires valid Sentinel Hub API credentials (`SENTINEL_CLIENT_ID`, `SENTINEL_CLIENT_SECRET`) and a Celery worker to handle asynchronous GeoTIFF tile downloads.
- **Action Required**: Build `modules/satellite/ingest.py` and configure Celery worker process.

---

### ISSUE-05: Leaflet.js Satellite Overlay & Camera Widget UI Components
- **Category**: Frontend Web Client
- **Status**: Open Development
- **Description**: `frontend/index.html` currently features live Chart.js water quality charts. Full PWA capability requires wiring the Leaflet.js interactive satellite map and camera photo scanner in `frontend/app.js`.
- **Action Required**: Add Leaflet.js library script to `index.html` and implement tile layer controls in `app.js`.

---

### ISSUE-06: ReportLab Weekly PDF Report & Cycle Plan Engine
- **Category**: Document Generation / Gen AI
- **Status**: Open Development
- **Description**: Endpoint `/generate/weekly-report/{pond_id}` requires ReportLab canvas rendering logic to produce downloadable PDF health summaries for farmers and MPEDA compliance exports.
- **Action Required**: Implement `backend/services/pdf_generator.py` using ReportLab Platypus elements.
