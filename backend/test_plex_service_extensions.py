import asyncio
import logging
from datetime import datetime, timedelta
from services.plex_service import PlexService
from core.security import decrypt_token
from core.database import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_plex_service_extensions():
    """Test the new methods for PlexService"""
    
    # 1. Get Plex server settings from database (assuming server ID 1 for testing)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT url, token, server_type, verify_ssl FROM settings WHERE id = ?", (1,))
    row = cursor.fetchone()
    conn.close()

    if not row or row['server_type'] != 'plex':
        logger.error("Plex server settings not found or incorrect type for server ID 1.")
        return

    base_url = row['url']
    encrypted_token = row['token']
    verify_ssl = bool(row['verify_ssl'])
    
    # Decrypt token
    token = decrypt_token(encrypted_token)
    
    # 2. Initialize PlexService
    try:
        plex_service = await PlexService.create_instance(base_url, token, verify_ssl)
        logger.info("PlexService initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize PlexService: {e}")
        return

    # 3. Get music library
    try:
        music_library = await plex_service.get_music_library()
        if not music_library:
            logger.error("Failed to get music library.")
            return
        logger.info(f"Music library obtained: {music_library.title}")
    except Exception as e:
        logger.error(f"Failed to get music library: {e}")
        return

    # 4. Test find_newly_added_tracks (last 1 day)
    try:
        since_time = datetime.now() - timedelta(days=1)
        new_tracks = await asyncio.to_thread(
            plex_service._find_newly_added_tracks_sync, 
            music_library, 
            since_time
        )
        logger.info(f"Found {len(new_tracks)} newly added tracks in the last day.")
        for track in new_tracks[:5]:  # Log first 5 tracks
            logger.info(f"  - {track.title} by {track.grandparentTitle} (Added: {track.addedAt})")
    except Exception as e:
        logger.error(f"Failed to find newly added tracks: {e}")
        
    # Note: Testing scan_and_refresh requires a valid file path on the Plex server
    # which is not feasible in this isolated test script without actual file operations.
    # This method would be tested during the actual download workflow.

if __name__ == "__main__":
    asyncio.run(test_plex_service_extensions())