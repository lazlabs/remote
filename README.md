# Movie Room Remote

A single-file smart home theater remote control PWA built for Home Assistant. Tap two buttons and your entire theater room configures itself — TV on, right input, correct audio system, lights dimmed. Control Kodi, launch apps on your gaming PC, voice input, and a full D-pad remote. Works on any phone, tablet, or iPad pinned to the home screen.

Built by **LAZLAB Creations** · © 2025 All rights reserved.

---

## What's in this repo

| File | What it does |
|------|-------------|
| `theater-remote.html` | **The entire app** — open this in a browser or host on GitHub Pages |
| `pc-agent.py` | Tiny Python server that runs on your gaming PC — lets the app launch Kodi, Chrome, etc. |
| `install-agent.bat` | Double-click installer — registers the PC agent as a Windows startup task |
| `ha-automations.yaml` | Ready-to-paste Home Assistant automation YAML for all four modes |
| `manifest.json` | PWA manifest so the app installs cleanly to iPhone/Android home screens |

---

## Quick start

### 1. Host the app
Push this repo to GitHub and enable GitHub Pages (Settings → Pages → Deploy from branch → main → / root). Your app URL will be `https://yourusername.github.io/your-repo-name/theater-remote.html`.

Or just open `theater-remote.html` directly in a browser on your local network.

### 2. Set up Home Assistant automations
Open `ha-automations.yaml` and replace the entity IDs with your actual ones (find them in HA → Developer Tools → States). Then import each automation block in HA → Settings → Automations → ⋮ → Import from YAML.

Webhook IDs to use (must match exactly):
- Casual TV: `casual_tv_on`
- Movie Night: `movie_night_on`
- Power Off: `all_off`

### 3. Connect the app to HA
Open the app → tap ⚙ Settings → enter your HA URL (e.g. `http://homeassistant.local:8123`) and a Long-Lived Access Token (HA Profile → scroll to bottom → Long-Lived Access Tokens → Create Token).

### 4. Install to your home screen (optional)
On iPhone/iPad: Share → Add to Home Screen. On Android: browser menu → Add to Home Screen / Install App. The app runs full-screen with no browser chrome.

---

## PC Agent setup (for Kodi / gaming PC control)

Only needed if you want to control your gaming PC from the remote.

**Prerequisites:** Python 3.x installed with "Add to PATH" checked.

**Steps:**
1. Copy `pc-agent.py` and `install-agent.bat` to a folder on your PC (e.g. `C:\MovieRoom\`)
2. Right-click `install-agent.bat` → Run as administrator
3. Find your PC's IP: Win+R → `cmd` → `ipconfig` → look for IPv4 Address
4. In the app: Settings → Kodi & PC Agent → PC Agent URL → `http://192.168.1.X:9876`
5. Tap Ping Agent to confirm

Edit `APP_MAP` near the top of `pc-agent.py` to match your installed app paths.

---

## Kodi setup (for local movie library)

1. In Kodi: Settings → Services → Control → enable **Allow remote control via HTTP** → port `8080`
2. In the app: Settings → Kodi & PC Agent → Kodi URL → `http://192.168.1.X:8080/jsonrpc`
3. Tap Ping Kodi to confirm
4. For your movie library: Kodi → Settings → Media → Library → Add Videos → browse to your movies folder → let it scan

---

## Four activity modes

| Mode | TV Input | Audio | Lights |
|------|----------|-------|--------|
| Casual TV | HDMI 1 (Fire TV) | Sonos eARC | 60% |
| Movie Night | HDMI 2 (PC) | Yamaha 7.2 | 10% |
| Movie Library | HDMI 2 (Kodi) | Yamaha 7.2 | 10% |
| Stream Mode | HDMI 2 (Browser) | Yamaha 7.2 | 30% |

---

## Features

- **Two-tap room control** — everything configures itself
- **Live Now Playing** — polls Kodi for real title and poster art
- **Contextual volume** — single slider switches target between Sonos and Yamaha automatically
- **Kodi D-pad** — full navigation with keyboard and voice input
- **PC Shortcuts strip** — launch any app on your PC with one tap
- **Kiosk mode** — lock the app to a dedicated tablet, PIN-protected exit
- **Dark + light theme** — follows system preference, toggleable
- **Connection diagnostics** — tells you exactly what's failing (mixed content, CORS, bad token)
- **Setup wizard** — step-by-step with inline help for every field
- **Import / export config** — back up and restore all settings as JSON
- **PWA** — installs to home screen, works offline for UI

---

## Compatibility

- **Home Assistant:** 2023.x or later (REST API + Webhooks)
- **Browser:** Safari 15+, Chrome 100+, Firefox 100+
- **Kodi:** 19 (Matrix) or later
- **PC Agent:** Windows 10/11 with Python 3.8+

---

*LAZLAB Creations — johnlaz.github.io*
