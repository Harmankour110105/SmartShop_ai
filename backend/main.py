from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from db import connect_to_db, close_db_connection
from queryhandler import router as query_router
from cart import router as cart_router
from auth import router as auth_router
from speech_recognition_handler import router as speech_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="SmartShop API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add startup and shutdown events
@app.on_event("startup")
async def startup():
    logger.info("Initializing database connection...")
    await connect_to_db()
    logger.info("Database initialized successfully!")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Closing database connection...")
    await close_db_connection()
    logger.info("Database connection closed!")

# Include routers
app.include_router(auth_router)
app.include_router(query_router)
app.include_router(cart_router)
app.include_router(speech_router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to SmartShop API"}
