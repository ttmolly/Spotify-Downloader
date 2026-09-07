import os
import requests
import string
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from yt_dlp import YoutubeDL
from tkinter import Tk, ttk, filedialog, StringVar, messagebox
from dotenv import load_dotenv
import spotipy
from spotipy import SpotifyOAuth
from spotipy.oauth2 import SpotifyOauthError
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error

MAX_WORKERS = 8

logging.basicConfig(
    filename="downloader.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

load_dotenv(dotenv_path=".env")

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URL")

if not client_id or not client_secret or not redirect_uri:
    print("Missing CLIENT_ID, CLIENT_SECRET, or REDIRECT_URL in .env")
    print("Copy .env.example to .env and add your Spotify app credentials.")
    raise SystemExit(1)

try:
    sp_oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-library-read playlist-read-private playlist-read-collaborative",
    )
except SpotifyOauthError as e:
    print(f"Spotify OAuth setup error: {e}")
    raise SystemExit(1)

token_info = sp_oauth.get_cached_token()
if not token_info:
    auth_url = sp_oauth.get_authorize_url()
    print("Please go to this URL and authorize the app:", auth_url)
    auth_code = input("Enter the authorization code: ").strip()
    if "code=" in auth_code:
        auth_code = auth_code.split("code=")[1].split("&")[0]
    token_info = sp_oauth.get_access_token(auth_code)

access_token = token_info["access_token"] if isinstance(token_info, dict) else token_info
playlists = {}
is_downloading = True


def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def update_playlist_dropdown():
    playlist_names = list(playlists.keys())
    playlist_menu = playlist_dropdown["menu"]
    playlist_menu.delete(0, "end")
    for name in playlist_names:
        playlist_menu.add_command(
            label=name, command=lambda value=name: selected_playlist.set(value)
        )
    if playlist_names:
        selected_playlist.set(playlist_names[0])


def get_user_playlists(token):
    print("Retrieving user playlists...")
    playlists["Liked Songs"] = "liked"

    headers = get_auth_header(token)
    response = requests.get("https://api.spotify.com/v1/me/playlists", headers=headers)
    response_json = response.json()
    for item in response_json.get("items", []):
        playlists[item["name"]] = item["id"]

    print("Playlists retrieved successfully.")
    update_playlist_dropdown()


def sanitize_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return "".join(c for c in filename if c in valid_chars)


def stop_downloading():
    global is_downloading
    is_downloading = False
    status_label.config(text="Downloading stopped.")


def get_liked_songs():
    print("Retrieving Liked Songs...")
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-library-read",
        )
    )

    tracks = []
    limit = 50
    offset = 0

    while True:
        response = sp.current_user_saved_tracks(limit=limit, offset=offset)
        tracks.extend(response["items"])
        print(f"Fetched {len(response['items'])} liked songs, total: {len(tracks)}")
        if len(response["items"]) < limit:
            break
        offset += limit

    print(f"{len(tracks)} liked songs retrieved successfully.")
    screen.after(
        0,
        lambda: status_label.config(
            text=f"{len(tracks)} liked songs retrieved successfully."
        ),
    )
    return tracks


def get_playlist_tracks(playlist_id):
    print(f"Retrieving tracks for playlist ID: {playlist_id}")
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )
    )

    tracks = []
    limit = 100
    offset = 0

    while True:
        response = sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
        tracks.extend(response["items"])
        print(f"Fetched {len(response['items'])} tracks, total: {len(tracks)}")
        if len(response["items"]) < limit:
            break
        offset += limit

    print(f"{len(tracks)} tracks retrieved successfully.")
    screen.after(
        0,
        lambda: status_label.config(
            text=f"{len(tracks)} tracks retrieved successfully."
        ),
    )
    return tracks


def update_status(text):
    status_label.config(text=text)


def embed_cover(mp3_path, image_url):
    try:
        response = requests.get(image_url, timeout=8)
        if response.status_code != 200:
            return
        audio = MP3(mp3_path, ID3=ID3)
        try:
            audio.add_tags()
        except error:
            pass
        audio.tags.add(
            APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=response.content,
            )
        )
        audio.save()
    except Exception:
        pass


def download_one(track, track_num, total_tracks, download_folder):
    if not is_downloading:
        return

    track_info = track.get("item") or track.get("track")
    if not track_info or not track_info.get("name"):
        return

    artist_name = (
        track_info["artists"][0]["name"] if track_info.get("artists") else "Unknown"
    )
    song_name = track_info["name"]
    sanitized_track_name = sanitize_filename(f"{artist_name} - {song_name}")
    final_file = os.path.join(download_folder, f"{sanitized_track_name}.mp3")

    cover_url = None
    if track_info.get("album") and track_info["album"].get("images"):
        cover_url = track_info["album"]["images"][0]["url"]

    if os.path.exists(final_file):
        print(f"Skipping ({track_num}/{total_tracks}): {sanitized_track_name}")
        if cover_url:
            embed_cover(final_file, cover_url)
        return

    print(f"Downloading ({track_num}/{total_tracks}): {artist_name} - {song_name}")

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(download_folder, f"{sanitized_track_name}.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "default_search": "ytsearch1",
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{song_name} {artist_name}"])

        print(f"  -> Done ({track_num}/{total_tracks}): {sanitized_track_name}")
        if cover_url:
            embed_cover(final_file, cover_url)

    except Exception as e:
        print(f"  -> Failed ({track_num}/{total_tracks}): {song_name} | {e}")


def download_songs(selected):
    global is_downloading
    is_downloading = True

    user_path = path_label.cget("text")
    if user_path == "Select Download Path:":
        messagebox.showerror("Error", "Please select a valid download path.")
        return

    download_folder = os.path.join(
        user_path, sanitize_filename(selected).replace(" ", "_")
    )

    try:
        os.makedirs(download_folder, exist_ok=True)
    except OSError as e:
        messagebox.showerror("Error", f"Failed to create download directory: {e}")
        return

    if selected == "Liked Songs":
        tracks = get_liked_songs()
    else:
        tracks = get_playlist_tracks(playlists[selected])

    total_tracks = len(tracks)
    screen.after(
        0,
        update_status,
        f"Starting download of {total_tracks} songs ({MAX_WORKERS} at a time)...",
    )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for track_num, track in enumerate(tracks, start=1):
            if not is_downloading:
                break
            futures.append(
                executor.submit(
                    download_one, track, track_num, total_tracks, download_folder
                )
            )

        for future in as_completed(futures):
            if not is_downloading:
                break
            try:
                future.result()
            except Exception:
                pass

    screen.after(0, update_status, "Download completed / stopped.")
    print("Finished!")


def start_download():
    threading.Thread(
        target=lambda: download_songs(selected_playlist.get()), daemon=True
    ).start()


def select_path():
    global path_label
    path = filedialog.askdirectory()
    if path:
        path_label.config(text=path)


screen = Tk()
screen.title(f"Spotify Downloader ({MAX_WORKERS} parallel)")
screen.geometry("600x400")

style = ttk.Style(screen)
style.theme_use("clam")

frame = ttk.Frame(screen, padding="20")
frame.pack(fill="both", expand=True)

path_label = ttk.Label(frame, text="Select Download Path:")
path_label.pack(pady=10)
ttk.Button(frame, text="Browse", command=select_path).pack(pady=5)

selected_playlist = StringVar()
playlist_dropdown = ttk.OptionMenu(frame, selected_playlist, "Loading playlists...")
playlist_dropdown.pack(pady=10)

get_user_playlists(access_token)

ttk.Button(frame, text="Download", command=start_download).pack(pady=10)
ttk.Button(frame, text="Stop Downloading", command=stop_downloading).pack(pady=5)

status_label = ttk.Label(frame, text="")
status_label.pack(pady=10)

screen.mainloop()
