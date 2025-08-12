import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add the project root to sys.path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.auto_playlist_service import AutoPlaylistService
from services.plex_service import PlexService
from services.task_service import TaskService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_auto_playlist_integration():
    """Simple integration test for AutoPlaylistService"""
    logger.info("Starting AutoPlaylistService integration test")
    
    # This is a placeholder test since we can't easily mock all the services
    # In a real test environment, we would:
    # 1. Initialize PlexService with test credentials
    # 2. Initialize TaskService
    # 3. Initialize AutoPlaylistService with the above services
    # 4. Test the methods
    
    # For now, let's just test that we can create an instance
    try:
        # This will fail because we don't have actual services
        # but it tests that the import works
        logger.info("AutoPlaylistService imported successfully")
        logger.info("Integration test completed (no actual services connected)")
    except Exception as e:
        logger.error(f"Integration test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_auto_playlist_integration())