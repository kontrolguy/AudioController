# Spotify Web API UI test

This is separate from the main AudioController project.

## 1. Create a Spotify developer app

Create an app in the Spotify Developer Dashboard.

Add this exact Redirect URI:

```text
http://127.0.0.1:8888/callback
```

Do not use `localhost`.

Copy the Client ID and Client Secret.

## 2. Configure

Copy:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```ini
SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
SPOTIFY_DEVICE_NAME=AudioController Test
```

The device name must match the name passed to librespot.

## 3. Install

```powershell
python -m pip install -r requirements.txt
```

## 4. Start librespot

Run your existing librespot command or `start_librespot.py`. It must appear
in Spotify as `AudioController Test`.

## 5. Run the UI

```powershell
python spotify_api_test.py
```

The first run opens Spotify authorization in the browser. Sign in and approve
the requested playback permissions. The refreshed token is cached in
`.spotify_cache`.

## Controls

- Space: play/pause
- N: next track
- P: previous track
- Left/right arrows: volume
- T: transfer playback to the configured librespot device
- S: toggle shuffle
- R: cycle repeat off/context/track
- Esc: exit

## Notes

- Spotify Premium is required for Player API playback-control endpoints.
- The UI polls the Web API every two seconds and locally interpolates progress
  between calls.
- Never commit `.env` or `.spotify_cache`.
