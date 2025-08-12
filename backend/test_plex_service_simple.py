import asyncio
import logging
from datetime import datetime, timedelta
from services.plex_service import PlexService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: Please fill in your Plex server details here for testing
PLEX_URL = "http://localhost:32400"  # Example URL, replace with your actual URL
PLEX_TOKEN = "your-plex-token-here"  # Replace with your actual token

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
        
    # Note: Testing scan_and_refresh requires a valid file path on the Plex server
    # which is not feasible in this isolated test script without actual file operations.
    # This method would be tested during the actual download workflow.

if __name__ == "__main__":
    asyncio.run(test_plex_service_extensions())