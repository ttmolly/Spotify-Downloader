# Spotify Downloader

Download your Spotify **playlists** and **Liked Songs** as MP3 files with album covers.

This is an updated version of [Noko7/Spotify-Downloader](https://github.com/Noko7/Spotify-Downloader) with:

- Liked Songs support
- Album cover embedding
- Parallel downloads (8 at a time)
- Skip already downloaded tracks (safe to resume)
- Fix for the current Spotify API track structure

Works on **macOS**, **Linux**, and **Windows**.

> Only download music you have the right to keep. This tool is for personal use.

---

## Features

- GUI to pick a folder and playlist
- **Liked Songs** appears at the top of the playlist list
- Saves MP3s at 192 kbps
- Embeds Spotify album art into each file
- Skips songs that already exist in the output folder
- Downloads 8 tracks at once (change `MAX_WORKERS` in `main.py` if you want)

---

## Requirements

- Python 3.10+ (3.11 or 3.12 is easiest)
- FFmpeg
- A Spotify account (Premium is required to create a new Spotify developer app)
- Spotify API credentials (Client ID + Client Secret)

Optional but recommended:
- Deno (helps yt-dlp download from YouTube more reliably)

---

## 1. Create a Spotify app

1. Go to [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Log in and click **Create app**
3. Fill in:
   - **App name:** `Spotify Downloader` (or anything)
   - **App description:** `Download my playlists`
   - **Website:** leave empty
   - **Redirect URI:** `http://127.0.0.1:8888/callback`
     - Use `127.0.0.1`, not `localhost`
   - Check **Web API** only
   - Accept the Developer Terms
4. Save the app
5. Open **Settings** and copy:
   - Client ID
   - Client Secret (click **View client secret**)

---

## 2. Install on macOS

```bash
# Homebrew (if you do not have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install python python-tk ffmpeg deno git

git clone https://github.com/ttmolly/Spotify-Downloader.git
cd Spotify-Downloader

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

## 3. Install on Linux (Debian / Ubuntu / similar)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-tk ffmpeg git

# Optional: Deno (recommended)
curl -fsSL https://deno.land/install.sh | sh

git clone https://github.com/ttmolly/Spotify-Downloader.git
cd Spotify-Downloader

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Fedora:

```bash
sudo dnf install python3 python3-tkinter ffmpeg git
```

Arch:

```bash
sudo pacman -S python python-pip tk ffmpeg git
```

---

## 4. Install on Windows

1. Install [Python](https://www.python.org/downloads/)  
   During setup, check **Add python.exe to PATH**.
2. Install [Git](https://git-scm.com/download/win).
3. Install FFmpeg:
   - Easiest: install [winget](https://learn.microsoft.com/windows/package-manager/winget/) then run:

```powershell
winget install Gyan.FFmpeg
winget install DenoLand.Deno
```

Or download FFmpeg from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/) and add the `bin` folder to PATH.

Then in **Command Prompt** or **PowerShell**:

```powershell
git clone https://github.com/ttmolly/Spotify-Downloader.git
cd Spotify-Downloader

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

If `python` is not found, try `py` instead.

---

## 5. Create your `.env` file

In the project folder, copy the example file and edit it.

**macOS / Linux:**

```bash
cp .env.example .env
nano .env
```

**Windows (Command Prompt):**

```cmd
copy .env.example .env
notepad .env
```

Put your real values in:

```env
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URL=http://127.0.0.1:8888/callback
```

The Redirect URI in `.env` must match the one in the Spotify dashboard **exactly**.

---

## 6. Run the app

Make sure the virtual environment is active, then:

**macOS / Linux:**

```bash
python main.py
```

**Windows:**

```powershell
python main.py
```

First run:

1. A link is printed in the terminal. Open it in your browser.
2. Log in to Spotify and click **Agree**.
3. The page will look broken (`127.0.0.1` cannot connect). That is normal.
4. Copy **only the long code** from the address bar  
   (the part after `code=` and before `&`).
5. Paste that code into the terminal and press Enter.
6. A small window opens.

In the window:

1. Click **Browse** and pick a download folder.
2. Choose **Liked Songs** or any playlist.
3. Click **Download**.

Songs are saved in a subfolder named after the playlist, for example:

```
YourFolder/Liked_Songs/
```

---

## Resume / same folder

The app skips files that already exist.

If you stop and start again, pick the **same parent folder** you used the first time (the folder that contains `Liked_Songs`), not the inner folder.

---

## Common problems

### `externally-managed-environment` (macOS / Linux)

Use a virtual environment (`python3 -m venv venv`) instead of installing packages system-wide.

### `No module named '_tkinter'` (macOS)

```bash
brew install python-tk
```

Then recreate the venv.

### `No module named 'tkinter'` (Linux)

```bash
sudo apt install python3-tk
```

### FFmpeg not found

Install FFmpeg and make sure it is on PATH. Test with:

```bash
ffmpeg -version
```

### `Invalid authorization code`

Codes expire in about a minute and can only be used once. Run the app again and paste a **fresh** code, not the full URL.

### `HTTP Error 403` from YouTube

Normal sometimes. The app tries another source. Installing Deno and updating yt-dlp helps:

```bash
pip install -U yt-dlp
```

If many songs fail in a row, lower `MAX_WORKERS` in `main.py` from `8` to `5` or `3`.

### Liked Songs / playlists not loading

Check that your Spotify app Redirect URI is exactly:

```
http://127.0.0.1:8888/callback
```

Delete the `.cache` file in the project folder and authorize again.

---

## Change download speed

In `main.py` find:

```python
MAX_WORKERS = 8
```

- `3` to `5` = safer
- `8` = faster (good default)
- `10+` = more YouTube blocks

---

## Credits

Based on [Noko7/Spotify-Downloader](https://github.com/Noko7/Spotify-Downloader).
