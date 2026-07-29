from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers import water_quality, disease, genai

app = FastAPI(
    title=settings.APP_NAME,
    description="Aquaculture Intelligence System (AIS) - Microservices AI Gateway",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(water_quality.router)
app.include_router(disease.router)
app.include_router(genai.router)

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "system": settings.APP_NAME,
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "database_host": settings.DB_HOST,
        "redis_host": settings.REDIS_HOST,
        "mqtt_host": settings.MQTT_BROKER_HOST
    }
