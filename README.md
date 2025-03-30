# YouTube Music Playlist Downloader

This tool downloads songs from your chosen YouTube Music playlist and saves them as high-quality MP3s on your computer.

## Setup

1. **Clone the Repository:**  
   Download or clone the project to your local machine.

2. **Configure Environment Variables:**  
   Copy the provided `.env.example` file to `.env` and fill in the required values:
   - Your YouTube Music API credentials.
   - The ID of the playlist you want to download.
   - Paths for storing downloaded music and updating your playlist file.
   - (Optional) Path to your cookies file for improved download success.

## Usage

Run the script with Python. You can specify a custom environment file if needed:

```bash
python main.py --env-file /path/to/your/.env
```

The tool will fetch your playlist, download any new songs, and update your local playlist file with the new entries.

Enjoy building your music library!
