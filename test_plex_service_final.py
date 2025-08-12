import asyncio
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to sys.path so we can import modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.plex_service import PlexService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Plex server details from environment variables
PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")

if not PLEX_URL or not PLEX_TOKEN:
    logger.error("PLEX_URL and PLEX_TOKEN must be set in the .env file.")
    sys.exit(1)

async def test_plex_service_extensions():
    """Test the new methods for PlexService"""
    
    # 1. Initialize PlexService
    try:
        plex_service = await PlexService.create_instance(PLEX_URL, PLEX_TOKEN, verify_ssl=False)
        logger.info("PlexService initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize PlexService: {e}")
        return

    # 2. Get music library
    try:
        music_library = await plex_service.get_music_library()
        if not music_library:
            logger.error("Failed to get music library.")
            return
        logger.info(f"Music library obtained: {music_library.title}")
    except Exception as e:
        logger.error(f"Failed to get music library: {e}")
        return

    # 3. Test find_newly_added_tracks (last 1 day)
    try:
        since_time = datetime.now() - timedelta(days=1)
        new_tracks = await plex_service.find_newly_added_tracks(music_library, since_time)
        logger.info(f"Found {len(new_tracks)} newly added tracks in the last day.")
        for track in new_tracks[:5]:  # Log first 5 tracks
            logger.info(f"  - {track.title} by {track.grandparentTitle} (Added: {track.addedAt})")
    except Exception as e:
        logger.error(f"Failed to find newly added tracks: {e}", exc_info=True)
        
    # 4. Test scan_and_refresh (without a specific path - refreshes entire library)
    try:
        result = await plex_service.scan_and_refresh(music_library)
        logger.info(f"Full library scan and refresh request sent with result: {result}")
    except Exception as e:
        logger.error(f"Failed to request full library scan and refresh: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_plex_service_extensions())