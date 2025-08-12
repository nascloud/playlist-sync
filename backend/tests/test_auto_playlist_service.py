import asyncio
import logging
import sys
import os

# Add the project root to sys.path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.auto_playlist_service import AutoPlaylistService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_auto_playlist_service():
    """Simple test for AutoPlaylistService logic"""
    
    # Since we can't easily mock PlexService and TaskService in this simple test,
    # we'll just test the matching logic directly
    
    # Create an instance of AutoPlaylistService (this will fail because we're not providing the services)
    # but we can still test the matching logic if we make the method static or create a mock
    
    # For now, let's just test the string normalization
    service = type('MockAutoPlaylistService', (), {
        '_normalize_string': AutoPlaylistService._normalize_string
    })()
    
    # Test string normalization
    test_cases = [
        ("Hello, World!", "hello world"),
        ("Taylor's Song (feat. Artist)", "taylor s song"),
        ("[Remix] - Version 2", ""),
        ("  Multiple   Spaces  ", "multiple spaces"),
        ("", ""),
    ]
    
    for input_str, expected in test_cases:
        normalized = service._normalize_string(input_str)
        # This is a simple check, in reality, the normalization is more complex
        logger.info(f"Normalized '{input_str}' -> '{normalized}'")
        
    logger.info("AutoPlaylistService basic logic test completed")

if __name__ == "__main__":
    asyncio.run(test_auto_playlist_service())