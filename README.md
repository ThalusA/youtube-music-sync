# YouTube Music Playlist Downloader

This project is a Python script that downloads songs from a specified YouTube Music playlist. It leverages the [ytmusicapi](https://github.com/sigma67/ytmusicapi) for interacting with YouTube Music, and [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading audio tracks. The script also provides detailed progress reporting with [tqdm](https://github.com/tqdm/tqdm) and robust error handling with retry capabilities.

## Features

- **Playlist Retrieval:**  
  Uses `get_playlist` with a provided `PLAYLIST_ID` from your environment to fetch all songs in a YouTube Music playlist.

- **Download Management:**  
  Downloads each song using yt-dlp, converts them to high-quality MP3 files, and saves them to a specified folder.

- **Playlist File Update:**  
  Appends the file paths of successfully downloaded songs to an M3U playlist file for easy access.

- **Progress Reporting:**  
  Provides detailed progress bars for both individual downloads and overall progress, while ensuring log messages don’t interfere with the progress display using `logging_redirect_tqdm`.

- **Error Handling & Retry:**  
  Detects download errors (including network issues) and stores the failed URLs. If a cookie file is provided, it retries failed downloads with cookies enabled.

- **Configurable Environment:**  
  All required configuration (such as OAuth credentials, file paths, and playlist ID) is loaded from an environment file. You can specify which env file to use via a command-line parameter.

## Requirements

- Python 3.6 or later
- [ytmusicapi](https://github.com/sigma67/ytmusicapi)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [tqdm](https://pypi.org/project/tqdm/)

You can install the required packages using pip:

```bash
pip install ytmusicapi yt-dlp python-dotenv tqdm
```

## Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/ytmusic-playlist-downloader.git
   cd ytmusic-playlist-downloader
   ```

2. **Configure Environment Variables:**

   Copy the provided `.env.example` file to `.env` and fill in the required values:

   ```env
   # Your OAuth2 client ID for the YouTube Music API
   OAUTH2_CLIENT_ID=

   # Your OAuth2 client secret for the YouTube Music API
   OAUTH2_CLIENT_SECRET=

   # Path to your OAuth2 credentials file (generated via ytmusicapi)
   OAUTH2_FILEPATH=

   # (Optional) Path to your cookies file used by yt-dlp for downloads with cookies enabled
   COOKIES_FILEPATH=

   # Directory where the downloaded music files will be stored
   MUSIC_FOLDERPATH=

   # The ID of the YouTube Music playlist you want to download songs from
   PLAYLIST_ID=

   # Path to the M3U playlist file where downloaded song paths will be appended
   PLAYLIST_FILEPATH=
   ```

## Usage

Run the script using Python. You can optionally specify an alternative environment file with the `--env-file` parameter (default is `.env`):

```bash
python download_songs.py --env-file /path/to/your/.env
```

### What the Script Does

1. **Initialization:**  
   - Loads configuration from the provided env file.
   - Initializes the YouTube Music API using OAuth credentials.

2. **Playlist Processing:**  
   - Retrieves the songs from the playlist specified by `PLAYLIST_ID`.
   - Scans the download directory for already downloaded files.

3. **Download Queue & Execution:**  
   - Builds a download queue filtering out songs that have already been downloaded.
   - Downloads songs while displaying an individual progress bar for each song and an overall progress bar.
   - Logs all events using `logging_redirect_tqdm` to ensure log messages and progress bars do not clash.

4. **Error Handling & Retry:**  
   - If any downloads fail (status `error`), the script stores their URLs.
   - If a cookies file is provided, it retries the failed downloads with cookies enabled.

## Logging & Progress

The script uses Python’s logging system combined with `tqdm.contrib.logging.logging_redirect_tqdm` to ensure that progress bars are displayed correctly. All major events (such as starting downloads, queuing songs, errors, and retries) are logged with timestamps for easy debugging.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
