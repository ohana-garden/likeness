"""
Volunteer Hub - Main Application Entry Point
Voice-first AI coordination platform for community resource matching
"""
import uvicorn
from volunteer_hub.config import settings


def main():
    """Run the application"""
    uvicorn.run(
        "volunteer_hub.web.api.endpoints:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()
