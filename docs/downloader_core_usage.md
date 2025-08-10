# `MusicDownloader` Class Usage Guide

This document provides detailed instructions on how to use the `MusicDownloader` class from `downloader.py`. This class is a client for the `aiapi.vip` music service, allowing you to search, get details, and download music.

## 1. Prerequisites

Before using the class, ensure you have the required library installed:

```bash
pip install requests
```

You will also need an API key from `aiapi.vip`.

## 2. Getting Started

### Importing the Class

First, import the `MusicDownloader` class and the `APIError` exception from the `downloader.py` file into your project.

```python
from downloader import MusicDownloader, APIError
```

### Initialization

To start, create an instance of the `MusicDownloader` class by providing your API key.

```python
try:
    api_key = "YOUR_AIAPI_VIP_KEY"  # Replace with your actual key
    downloader = MusicDownloader(api_key=api_key)
except ValueError as e:
    print(f"Initialization error: {e}")
```

The class will raise a `ValueError` if the `api_key` is empty.

### Error Handling

All methods that interact with the API can raise an `APIError` exception if the request fails or the API returns an error. It's crucial to wrap your calls in a `try...except` block.

```python
try:
    # Method call, e.g., downloader.search(...)
    pass
except APIError as e:
    print(f"An API error occurred: {e}")
    print(f"Status Code: {e.status_code}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

```

## 3. Class Methods

Here are the public methods available in the `MusicDownloader` class.

### `search()`

Searches for songs across different platforms.

-   **Parameters:**
    -   `text` (str): The search keyword (e.g., song title or artist).
    -   `music_type` (str): The music platform. Supported values: `'qq'`, `'kw'`, `'kg'`, `'wy'`, `'mg'`.
    -   `page` (int, optional): The page number of the results. Defaults to `1`.
    -   `size` (int, optional): The number of results per page. Defaults to `10`.
-   **Returns:**
    -   A `dict` containing the search results from the API.
-   **Response Format:**
    -   The actual list of songs is typically in `response['data']['data']`.

    ```json
    {
        "code": 200,
        "data": {
            "data": [
                {
                    "name": "歌曲名",
                    "artist": "歌手",
                    "pic": "封面图片URL",
                    "id": "歌曲ID",
                    "mv": "MV_ID"
                }
            ],
            "total": 100
        },
        "msg": "操作成功"
    }
    ```
-   **Example:**

```python
try:
    search_results = downloader.search(text="明天你好", music_type="qq")
    songs = search_results.get('data', {}).get('data', [])
    if songs:
        print("Found songs:")
        for i, song in enumerate(songs):
            print(f"{i+1}. {song.get('artist')} - {song.get('name')} (ID: {song.get('id')})")
    else:
        print("No songs found.")
except APIError as e:
    print(f"Search failed: {e}")
```

### `get_music_url()`

Retrieves the download URL(s) and other details for a specific song.

-   **Parameters:**
    -   `music_id` (str): The ID of the song, obtained from the `search()` results.
    -   `music_type` (str): The music platform. Supported values: `'qq'`, `'kw'`, `'kg'`, `'wy'`, `'mg'`, `'xm'`.
    -   `info` (bool, optional): If `True`, the response will include detailed song information, such as lyrics. Defaults to `False`.
-   **Returns:**
    -   A `dict` containing song details, including available download links for different qualities.
-   **Response Format:**

    ```json
    {
        "code": 200,
        "gm": "歌曲名",
        "gs": "歌手",
        "data": [
            {
                "size": "4.15Mb",
                "br": 128,
                "format": "mp3",
                "ts": "标准",
                "url": "下载链接"
            }
        ],
        "info": {
            "lyric": [{"time": "00.00", "words": "歌词内容"}],
            "name": "歌曲名",
            "artist": "歌手",
            "pic": "封面图片URL",
            "platform": "qq"
        }
    }
    ```
-   **Example:**

```python
try:
    # Assuming music_id is '75139-002OrhQA0bNYFg' from a previous search
    music_id = "75139-002OrhQA0bNYFg"
    music_type = "qq"
    song_details = downloader.get_music_url(music_id=music_id, music_type=music_type, info=True)

    print(f"Song Name: {song_details.get('gm')}")
    print(f"Artist: {song_details.get('gs')}")
    
    # Print available download links
    for track in song_details.get('data', []):
        print(f"- Quality: {track.get('ts')}, Format: {track.get('format')}, URL: {track.get('url')[:30]}...")

except APIError as e:
    print(f"Failed to get music URL: {e}")
```

### `download_song()`

Downloads a song to a specified directory. This method intelligently selects the best available quality based on your preference and automatically handles file naming.

-   **Parameters:**
    -   `music_id` (str): The ID of the song.
    -   `music_type` (str): The music platform.
    -   `download_dir` (str): The path to the directory where the song will be saved.
    -   `preferred_quality` (str, optional): The desired audio quality. Supported values: `'无损'`, `'高品'`, `'标准'`. Defaults to `'无损'`. The method will automatically fall back to the next best quality if the preferred one is unavailable.
    -   `download_lyrics` (bool, optional): If `True`, it will also download the lyrics as a `.lrc` file. Defaults to `False`.
-   **Returns:**
    -   `None`. It prints status messages to the console during its operation.
-   **Example:**

```python
import os

try:
    music_id = "75139-002OrhQA0bNYFg"
    music_type = "qq"
    download_folder = "./my_music"

    print(f"Downloading song {music_id}...")
    downloader.download_song(
        music_id=music_id,
        music_type=music_type,
        download_dir=download_folder,
        preferred_quality="高品",
        download_lyrics=True
    )
    print(f"Check the '{download_folder}' directory for your downloaded files.")

except APIError as e:
    print(f"Download failed: {e}")
```

### `get_key_info()`

Queries the information associated with your API key, such as remaining usage counts.

-   **Returns:**
    -   A `dict` containing details about your API key.
-   **Response Format:**

    ```json
    {
        "code": 200,
        "data": {
            "keyInfo": [
                {
                    "type": "qq",
                    "count": 10,
                    "time": "2025-08-08 16:49:41"
                }
            ],
            "count": 9986
        },
        "msg": "成功"
    }
    ```
-   **Example:**

```python
try:
    key_info = downloader.get_key_info()
    data = key_info.get('data', {})
    if data:
        print("API Key Info:")
        print(f"  Total Remaining Calls: {data.get('count', 'N/A')}")
        print("  Usage by Platform:")
        for platform_info in data.get('keyInfo', []):
            print(f"    - Platform: {platform_info.get('type')}, Used: {platform_info.get('count')}, Last Used: {platform_info.get('time')}")
except APIError as e:
    print(f"Failed to get key info: {e}")
```

### `get_music_list_by_user_id()`

Fetches a user's public playlists from a specified platform.

-   **Parameters:**
    -   `user_id` (str): The user's ID on the platform (e.g., QQ number, KuGou ID).
    -   `music_type` (str): The music platform. Supported values: `'kg'`, `'qq'`, `'wy'`.
-   **Returns:**
    -   A `dict` containing the user's playlist information.
-   **Response Format:**

    ```json
    {
        "code": 200,
        "data": {
            "list": [
                {
                    "name": "歌单名称",
                    "pic": "封面图片URL",
                    "id": "歌单ID",
                    "count": 723
                }
            ],
            "name": "用户名"
        },
        "msg": "操作成功"
    }
    ```
-   **Example:**

```python
try:
    # Example for KuGou user ID
    playlists_data = downloader.get_music_list_by_user_id(user_id="731635472", music_type="kg")
    user_info = playlists_data.get('data', {})
    if user_info:
        print(f"Playlists for user '{user_info.get('name')}':")
        for playlist in user_info.get('list', []):
            print(f"- {playlist.get('name')} (ID: {playlist.get('id')}, Songs: {playlist.get('count')})")
except APIError as e:
    print(f"Failed to get user playlists: {e}")
```

### `get_hot_music_list()`

Fetches the daily hot playlists for a given platform.

-   **Parameters:**
    -   `music_type` (str): The music platform. Supported values: `'kg'`, `'qq'`, `'wy'`.
    -   `time` (str, optional): The date in `YYYY-MM-DD` format. Defaults to the current day.
-   **Returns:**
    -   A `dict` containing a list of hot playlists.
-   **Response Format:**

    ```json
    {
        "code": 200,
        "data": [
            {
                "id": "歌单ID",
                "url": "封面图片URL",
                "title": "歌单标题",
                "platform": "2"
            }
        ],
        "msg": "操作成功"
    }
    ```
-   **Example:**

```python
try:
    hot_playlists_data = downloader.get_hot_music_list(music_type="qq")
    playlists = hot_playlists_data.get('data', [])
    if playlists:
        print("Today's Hot Playlists on QQ Music:")
        for playlist in playlists[:5]: # Displaying first 5
            print(f"- {playlist.get('title')} (ID: {playlist.get('id')})")
except APIError as e:
    print(f"Failed to get hot playlists: {e}")
```

### `get_banner()`

Fetches banner images from a platform's homepage.

-   **Parameters:**
    -   `music_type` (str): The music platform. Supported values: `'kg'`, `'qq'`, `'wy'`.
    -   `time` (str, optional): The date in `YYYY-MM-DD` format. Defaults to the current day.
-   **Returns:**
    -   A `dict` containing a list of banner items.
-   **Response Format:**

    ```json
    {
        "code": 200,
        "data": [
            {
                "id": "轮播图ID",
                "url": "图片URL",
                "platform": "2"
            }
        ],
        "msg": "操作成功"
    }
    ```
-   **Example:**

```python
try:
    banner_data = downloader.get_banner(music_type="wy")
    banners = banner_data.get('data', [])
    if banners:
        print("Banners from NetEase Cloud Music:")
        for banner in banners:
            print(f"- Banner ID: {banner.get('id')}, Image URL: {banner.get('url')}")
except APIError as e:
    print(f"Failed to get banners: {e}")
```

Refer to the source code docstrings for more details on these methods.

