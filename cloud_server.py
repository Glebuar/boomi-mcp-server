#!/usr/bin/env python3
"""
Boomi MCP Cloud Server - Production-ready FastAPI deployment.

This server wraps the core MCP functionality with FastAPI for cloud deployment:
- Health checks for load balancers
- CORS support for web clients
- Proper logging and monitoring
- Graceful shutdown handling
- Production-ready middleware
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging for cloud environments
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import the existing MCP server
# We'll modify server.py to export the mcp instance
try:
    # Add current directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent))
    from server import mcp, DB_PATH, JWT_ALG, JWT_ISSUER, JWT_AUDIENCE
    logger.info("Successfully imported MCP server")
except ImportError as e:
    logger.error(f"Failed to import MCP server: {e}")
    sys.exit(1)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown.
    """
    logger.info("Starting Boomi MCP Cloud Server")
    logger.info(f"JWT Algorithm: {JWT_ALG}")
    logger.info(f"JWT Issuer: {JWT_ISSUER}")
    logger.info(f"JWT Audience: {JWT_AUDIENCE}")
    logger.info(f"Secrets DB: {DB_PATH}")

    # Startup
    yield

    # Shutdown
    logger.info("Shutting down Boomi MCP Cloud Server")


# Create FastAPI application
app = FastAPI(
    title="Boomi MCP Cloud Server",
    description="Production-ready MCP server for Boomi API integration",
    version="1.0.0",
    lifespan=app_lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# Add CORS middleware for web clients
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoints for load balancers
@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and orchestrators.
    Returns 200 OK if the server is running.
    """
    return {"status": "healthy", "service": "boomi-mcp"}


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint - verifies server can handle requests.
    Checks database connectivity and other dependencies.
    """
    try:
        # Test database connection
        import sqlite3
        con = sqlite3.connect(DB_PATH)
        con.execute("SELECT 1").fetchone()
        con.close()

        return {"status": "ready", "service": "boomi-mcp"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )


@app.get("/metrics")
async def metrics():
    """
    Metrics endpoint for monitoring systems.
    Returns basic operational metrics.
    """
    import sqlite3

    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.execute("SELECT COUNT(DISTINCT sub) FROM secrets")
        user_count = cur.fetchone()[0]
        cur = con.execute("SELECT COUNT(*) FROM secrets")
        profile_count = cur.fetchone()[0]
        con.close()

        return {
            "users_with_credentials": user_count,
            "total_profiles": profile_count,
            "jwt_algorithm": JWT_ALG,
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {"error": str(e)}


@app.get("/")
async def root():
    """
    Root endpoint with server information.
    """
    return {
        "service": "Boomi MCP Cloud Server",
        "version": "1.0.0",
        "mcp_endpoint": "/mcp",
        "documentation": "/docs",
        "health": "/health",
        "ready": "/ready",
        "metrics": "/metrics",
    }


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests (excluding sensitive data).
    """
    logger.info(f"Request: {request.method} {request.url.path}")

    response = await call_next(request)

    logger.info(f"Response: {request.method} {request.url.path} - Status: {response.status_code}")

    return response


# Mount the MCP server
try:
    # Create the MCP ASGI application
    mcp_path = os.getenv("MCP_PATH", "/mcp")

    # Get the MCP HTTP app
    mcp_app = mcp.http_app(path=mcp_path)

    # Mount it to FastAPI
    app.mount(mcp_path, mcp_app)

    logger.info(f"MCP server mounted at {mcp_path}")
except Exception as e:
    logger.error(f"Failed to mount MCP server: {e}")
    raise


if __name__ == "__main__":
    # Cloud deployment configuration
    host = os.getenv("MCP_HOST", "0.0.0.0")  # Listen on all interfaces for cloud
    port = int(os.getenv("MCP_PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))  # Single worker for SQLite

    # Production server configuration
    uvicorn_config = {
        "host": host,
        "port": port,
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": True,
        "proxy_headers": True,  # Important for cloud deployments behind load balancers
        "forwarded_allow_ips": "*",  # Trust proxy headers
    }

    logger.info(f"Starting cloud server on {host}:{port}")
    logger.info(f"Workers: {workers}")

    if workers > 1:
        logger.warning("Multiple workers with SQLite may cause locking issues!")
        logger.warning("Consider using a cloud secret manager for production")

    # Run the server
    uvicorn.run(
        "cloud_server:app",
        **uvicorn_config,
    )
