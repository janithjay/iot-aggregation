# IoT Data Aggregation Platform

Professional IoT sensor data aggregation system with real-time dashboarding, queue-based processing, and cloud-ready architecture for 5-member distributed team.

## 🏗️ Project Structure

```
├── frontend/              # Professional React-like Web UI (Member 5)
│   ├── index.html        # Dashboard (300+ lines)
│   ├── styles.css        # Design system (2000+ lines)
│   ├── app.js           # Application logic (800+ lines)
│   └── README.md        # Frontend documentation
├── api/                  # Flask REST API (Member 3)
│   ├── app.py           # Endpoints: /list, /data, /summary
│   ├── Dockerfile       # API container
│   └── requirements.txt
├── backend/             # Business logic (Member 2)
│   ├── services.py      # Core processors
│   ├── models.py        # Data models
│   ├── validators.py    # Input validation
│   └── requirements.txt
├── db/                  # Database layer (Member 4)
│   ├── database.py      # DynamoDB access
│   ├── init_table.py    # Schema initialization
│   ├── schema.md        # Table definitions
│   └── test_db.py       # DB tests
├── worker/              # Queue processor (Member 1)
│   ├── worker.py        # RabbitMQ consumer
│   ├── Dockerfile       # Worker container
│   └── requirements.txt
├── shared/              # Shared configuration
│   ├── config.py        # Environment defaults
│   └── queue.py         # Queue utilities
├── tests/               # Integration tests
│   ├── test_api.py
│   ├── test_backend.py
│   ├── test_worker.py
│   └── test_db.py
├── scripts/
│   └── integration_smoke.ps1  # End-to-end validation
├── docker-compose.yml   # Multi-container orchestration
└── AWS_DEPLOYMENT_GUIDE.md  # Production deployment (AWS)
```

## 🚀 Quick Start

### Local Development (Docker)
```powershell
# Start all services
docker compose up --build

# Service URLs
Frontend:  http://localhost:3000
API:       http://localhost:5000
RabbitMQ:  amqp://localhost:5672
```

### Frontend Development (No Docker)
```powershell
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

### Run Integration Tests
```powershell
# Validate full stack
powershell -ExecutionPolicy Bypass -File scripts/integration_smoke.ps1

# Run unit tests
pytest -q
```

## 📋 Team Roles & Responsibilities

### Member 1: Lead/Integrator + Worker/Processor
- ✅ Worker consumes from RabbitMQ queue `iot-jobs`
- ✅ State transitions: `pending → processing → done|failed`
- ✅ Computes summaries and writes to DynamoDB
- ✅ Job retry logic (MAX_JOB_RETRIES)

### Member 2: Backend Developer
- ✅ Business logic in `backend/services.py`
- ✅ Data models in `backend/models.py`
- ✅ Validation rules in `backend/validators.py`

### Member 3: API Developer
- ✅ REST endpoints: `/list`, `/data`, `/summary`
- ✅ Flask app with error handling
- ✅ Health check endpoint at `/health`

### Member 4: Database Administrator
- ✅ DynamoDB table: `iot_data`
- ✅ Schema: column names in capital simple letters (preserved)
- ✅ Access layer in `db/database.py`

### Member 5: Frontend/DevOps ✅ COMPLETE
#### Frontend (Production-Ready)
- ✅ **Dashboard**: Real-time statistics + charts
- ✅ **Submit Data**: Manual entry + CSV/JSON upload
- ✅ **Analytics**: Search & filter sensor data
- ✅ **History**: Data tables with export to CSV
- ✅ **Design**: Professional dark theme, mobile responsive
- ✅ **Features**: Auto-refresh, error handling, form validation

#### DevOps (Production-Ready)
- ✅ **Local Testing**: Python HTTP server or Docker
- ✅ **Docker Compose**: Complete stack orchestration
- ✅ **AWS Deployment**: 10-step guide in `AWS_DEPLOYMENT_GUIDE.md`
- ✅ **CloudWatch**: Monitoring & alerting configuration
- ✅ **Infrastructure**: S3, Lambda, DynamoDB, SQS, API Gateway, CloudFront

## 🌐 Frontend Features

| Feature | Status | Details |
|---------|--------|---------|
| Dashboard | ✅ | 4 real-time statistics + 2 Chart.js visualizations |
| Data Submission | ✅ | Manual form + CSV/JSON upload with drag-drop |
| Analytics | ✅ | Search, filter, summarize sensor readings |
| Data Export | ✅ | CSV generation with full dataset |
| Mobile Responsive | ✅ | Desktop, tablet, mobile optimized |
| Error Handling | ✅ | Toast notifications + graceful degradation |
| Auto-Refresh | ✅ | Configurable interval (default: 5000ms) |
| API Integration | ✅ | 3 endpoints: `/list`, `/data`, `/summary` |

## ☁️ AWS Deployment

Complete production deployment guide included in **AWS_DEPLOYMENT_GUIDE.md** (10 steps):

1. **AWS Account Setup** - IAM user creation
2. **S3 Buckets** - Frontend + data storage
3. **DynamoDB Table** - iot_data with proper config
4. **SQS Queue** - iot-jobs message queue
5. **Lambda Functions** - API + Worker serverless compute
6. **API Gateway** - REST API endpoint exposure
7. **CloudFront CDN** - Global distribution
8. **CloudWatch** - Logging & monitoring
9. **Environment Configuration** - .env setup
10. **Testing & Verification** - End-to-end validation

**Estimated Time**: 2-3 hours  
**Estimated Cost**: $130-150/month

## 🔐 Database Schema

**Table**: `iot_data` (DynamoDB)
- **Partition Key**: `sensor_id` (String)
- **Sort Key**: `timestamp` (Number)
- **Attributes**: Preserved original naming convention (capital simple letters)

See `db/schema.md` for complete schema definition.

## 📊 API Endpoints

### GET /list
Lists all sensor IDs with recent readings
```json
{
  "sensors": [
    {"sensor_id": "SENSOR_1", "latest": 23.5, "timestamp": 1234567890}
  ]
}
```

### GET /data?sensor_id=SENSOR_1&limit=10
Retrieves sensor data with filtering
```json
{
  "sensor_id": "SENSOR_1",
  "readings": [
    {"value": 23.5, "timestamp": 1234567890}
  ]
}
```

### GET /summary
Aggregated statistics across all sensors
```json
{
  "total_readings": 1542,
  "sensors_active": 8,
  "avg_value": 22.3,
  "min_value": 15.2,
  "max_value": 31.8
}
```

## 🧪 Testing

```powershell
# All tests
pytest -q

# Specific test file
pytest tests/test_api.py -v

# With coverage
pytest --cov=backend --cov=api --cov=worker
```

## 📝 Configuration

Environment variables in `.env`:
```
QUEUE_HOST=rabbitmq
DB_ENDPOINT=http://dynamodb:8000
LOG_LEVEL=INFO
AUTO_REFRESH_INTERVAL=5000
```

## 🐳 Docker Services

| Service | Port | Image | Role |
|---------|------|-------|------|
| frontend | 3000 | nginx/python | Dashboard UI |
| api | 5000 | python:3.11 | REST API |
| worker | - | python:3.11 | Queue processor |
| rabbitmq | 5672 | rabbitmq:3.12 | Message queue |
| dynamodb | 8000 | amazon/dynamodb | Local database |

## 📞 Documentation

- **Frontend Guide**: See `frontend/README.md`
- **AWS Deployment**: See `AWS_DEPLOYMENT_GUIDE.md`
- **Database Schema**: See `db/schema.md`
- **Integration Flow**: See `scripts/integration_smoke.ps1`

## ✅ Data Integrity

- ✅ **Table Names**: Preserved original (`iot_data`)
- ✅ **Column Names**: Original naming convention maintained (capital simple letters)
- ✅ **API Contracts**: Unchanged and backward compatible
- ✅ **Schema Design**: DynamoDB-optimized, no breaking changes

## 🎯 Next Steps

1. **Local Testing**: `docker compose up --build`
2. **AWS Deployment**: Follow `AWS_DEPLOYMENT_GUIDE.md` (10 steps)
3. **Production Monitoring**: CloudWatch dashboards active
4. **Scaling**: Lambda auto-scaling + DynamoDB on-demand

## 📞 Support

Each team member refers to:
- Member 1: `worker/` and `shared/` directories
- Member 2: `backend/` directory
- Member 3: `api/` directory
- Member 4: `db/` directory
- Member 5: `frontend/` directory + AWS deployment

---

**Status**: ✅ Production Ready | **Last Updated**: April 2026 | **Team**: 5 Members Fully Implemented
