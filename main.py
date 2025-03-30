#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
from ytmusicapi import YTMusic, OAuthCredentials
from yt_dlp import YoutubeDL

# Global progress bars, playlist filepath, and list for failed URLs
global_progress_bar = None
individual_progress_bar = None
PLAYLIST_FILEPATH = None
failed_urls = []  # List to store failed download URLs


def setup_logging():
    """Configure logging to display timestamps and log levels."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_configuration():
    """Load configuration from environment variables."""
    config = {
        "client_id": os.getenv("OAUTH2_CLIENT_ID"),
        "client_secret": os.getenv("OAUTH2_CLIENT_SECRET"),
        "oauth2_filepath": os.getenv("OAUTH2_FILEPATH"),
        "cookies_filepath": os.getenv("COOKIES_FILEPATH"),  # Optional
        "music_folderpath": os.getenv("MUSIC_FOLDERPATH"),
        "playlist_filepath": os.getenv("PLAYLIST_FILEPATH"),
        "playlist_id": os.getenv("PLAYLIST_ID"),
    }
    # Only enforce required values except cookies_filepath.
    missing = [
        key
        for key, value in config.items()
        if key != "cookies_filepath" and value is None
    ]
    if missing:
        logging.error(f"Missing environment variables: {', '.join(missing)}")
        raise ValueError(
            "Configuration incomplete. Please set the missing environment variables."
        )
    return config


def initialize_api(config):
    """Initialize the YouTube Music API using OAuth credentials."""
    logging.info("Initializing YouTube Music API...")
    return YTMusic(
        config["oauth2_filepath"],
        oauth_credentials=OAuthCredentials(
            client_id=config["client_id"], client_secret=config["client_secret"]
        ),
    )


def get_playlist(api, playlist_id, limit=5000):
    """Retrieve songs from the specified playlist using its playlist ID."""
    logging.info(f"Retrieving playlist '{playlist_id}' from YouTube Music...")
    data = api.get_playlist(playlist_id, limit=limit)
    tracks = data.get("tracks", [])
    logging.info(f"Retrieved {len(tracks)} songs from playlist.")
    return tracks


def get_already_downloaded(music_folderpath):
    """Scan the music folder and return a list of already downloaded MP3 filenames."""
    logging.info("Scanning for already downloaded songs...")
    downloaded = [
        file.name for file in Path(music_folderpath).glob("*.mp3") if file.is_file()
    ]
    logging.info(f"Found {len(downloaded)} downloaded song(s).")
    return downloaded


def build_download_queue(tracks, already_downloaded):
    """Build a list of song URLs to download, filtering out songs already downloaded."""
    logging.info("Building the download queue...")
    queue = []
    for track in tracks:
        title = track.get("title", "Unknown Title")
        video_id = track.get("videoId")
        if not video_id:
            logging.warning(f"Skipping track '{title}' (missing video ID).")
            continue
        # Check if the song is already downloaded (using video ID in filename)
        if not any(f"[{video_id}]" in filename for filename in already_downloaded):
            url = f"https://music.youtube.com/watch?v={video_id}"
            queue.append(url)
            logging.info(f"Queued: {title}")
        else:
            logging.info(f"Already downloaded: {title}")
    logging.info(f"Total new songs to download: {len(queue)}")
    return queue


def create_youtube_dl_options(config, use_cookies=False):
    """Create configuration options for yt-dlp.

    If `use_cookies` is True and a cookies_filepath is provided in config,
    the cookiefile option will be added.
    """
    opts = {
        "format": "mp3/bestaudio/best",
        "paths": {"home": config["music_folderpath"]},
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            },
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata"},
        ],
        "progress_hooks": [progress_hook],
        "ignoreerrors": True,
    }
    if use_cookies and config.get("cookies_filepath"):
        opts["cookiefile"] = config["cookies_filepath"]
    return opts


def update_playlist(filename, title):
    """Append the downloaded song's path to the M3U playlist file."""
    global PLAYLIST_FILEPATH
    entry = f"/srv/music/{filename}\n"
    with open(PLAYLIST_FILEPATH, "a", encoding="utf-8") as playlist:
        playlist.write(entry)
    tqdm.write(f"Added '{title}' to playlist.")


def progress_hook(d):
    """Hook to update tqdm progress bars during downloads.

    Handles "downloading", "finished", and "error" statuses.
    In the error case, logs the error and stores the failed URL for retry.
    """
    global individual_progress_bar, global_progress_bar, failed_urls
    status = d.get("status")

    if status == "downloading":
        if individual_progress_bar is None:
            total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            title = d.get("info_dict", {}).get("title", "Downloading")
            individual_progress_bar = tqdm(
                total=total_bytes,
                unit="B",
                unit_scale=True,
                desc=f"Downloading: {title}",
                position=1,
                leave=False,
            )
        else:
            downloaded_bytes = d.get("downloaded_bytes", 0)
            individual_progress_bar.update(downloaded_bytes - individual_progress_bar.n)

    elif status == "finished":
        if individual_progress_bar:
            individual_progress_bar.close()
            individual_progress_bar = None
        global_progress_bar.update(1)
        filepath = d.get("filename", "")
        filename = f"{Path(filepath).stem}.mp3"
        title = d.get("info_dict", {}).get("title", "Unknown Title")
        update_playlist(filename, title)
        tqdm.write(f"Finished downloading: {title}")

    elif status == "error":
        # Close individual progress bar if it's open
        if individual_progress_bar:
            individual_progress_bar.close()
            individual_progress_bar = None
        error_msg = d.get("error", "Unknown error")
        failed_url = d.get("info_dict", {}).get("webpage_url")
        logging.error(f"Error downloading {failed_url}: {error_msg}")
        if failed_url and failed_url not in failed_urls:
            failed_urls.append(failed_url)
        global_progress_bar.update(1)


def download_songs(songs_to_download, youtube_dl_opts):
    """Download songs using yt-dlp and update progress bars."""
    global global_progress_bar
    total_songs = len(songs_to_download)
    global_progress_bar = tqdm(
        total=total_songs, unit="song", desc="Overall Progress", position=0
    )
    with YoutubeDL(youtube_dl_opts) as ydl:
        ydl.download(songs_to_download)
    global_progress_bar.close()


def main():
    setup_logging()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Download liked songs from YouTube Music."
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to the environment file to load (default: .env)",
    )
    args = parser.parse_args()

    # Load environment variables from the specified file
    load_dotenv(dotenv_path=args.env_file)
    logging.info(f"Loaded environment variables from {args.env_file}")

    try:
        config = load_configuration()
    except ValueError:
        logging.error("Exiting due to configuration error.")
        sys.exit(1)

    global PLAYLIST_FILEPATH
    PLAYLIST_FILEPATH = config["playlist_filepath"]

    with logging_redirect_tqdm():
        yt_api = initialize_api(config)
        tracks = get_playlist(yt_api, config["playlist_id"], limit=5000)
        downloaded_files = get_already_downloaded(config["music_folderpath"])
        songs_to_download = build_download_queue(tracks, downloaded_files)

        if not songs_to_download:
            logging.info("No new songs to download. Exiting.")
            sys.exit(0)

        # First attempt: download without cookies enabled
        ytdl_opts = create_youtube_dl_options(config, use_cookies=False)
        logging.info("Starting downloads (first attempt)...")
        download_songs(songs_to_download, ytdl_opts)
        logging.info("First download attempt completed.")

        # If there were errors and a cookies file is provided, retry failed downloads.
        if failed_urls and config.get("cookies_filepath"):
            retry_list = failed_urls.copy()
            # Clear the failed_urls list for the retry attempt.
            failed_urls.clear()
            logging.info(
                f"Retrying {len(retry_list)} failed downloads with cookies enabled..."
            )
            ytdl_opts_retry = create_youtube_dl_options(config, use_cookies=True)
            download_songs(retry_list, ytdl_opts_retry)
            if failed_urls:
                logging.error(
                    f"After retry, {len(failed_urls)} downloads still failed: {failed_urls}"
                )
            else:
                logging.info("All failed downloads succeeded on retry.")
        elif failed_urls:
            logging.error(
                f"Downloads failed for {len(failed_urls)} songs: {failed_urls}"
            )

        logging.info("All downloads completed.")


if __name__ == "__main__":
    main()
