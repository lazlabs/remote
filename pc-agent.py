"""
Movie Room Remote — PC Agent v1.1
==================================
Does two jobs:
  1. LOCAL WEB SERVER — serves theater-remote.html at http://[your-ip]:9876/
     When you access the app from this URL instead of GitHub Pages, Chrome
     never shows the "access local network" permission prompt — app and HA
     are both on your LAN so there's no cross-origin gate.

  2. COMMAND EXECUTOR — accepts POST /run commands from the remote app
     to launch Kodi, Chrome, send keystrokes, etc.

SETUP:
  1. Put this file and theater-remote.html in the same folder, e.g. C:\MovieRoom\
  2. Also put manifest.json, sw.js, icon.svg, icon-192.svg in that folder
  3. Run install-agent.bat (as Administrator) to register as a startup task
  4. Find your PC IP: Win+R → cmd → ipconfig → look for IPv4 Address
  5. Access the app at: http://192.168.1.X:9876/
  6. In app Settings → Kodi & PC Agent, set PC Agent URL to: http://192.168.1.X:9876

DEFAULT PORT: 9876  (set PC_AGENT_PORT env var to override)
"""

import http.server
import json
import mimetypes
import os
import subprocess
import time

PORT = int(os.environ.get('PC_AGENT_PORT', 9876))

# Folder this script lives in — also where we look for HTML/asset files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── APP COMMANDS ─────────────────────────────────────────────────────────────
# Map command strings → executable paths on Windows.
# Edit these to match where your apps are installed.
APP_MAP = {
    'kodi':    r'C:\Program Files\Kodi\Kodi.exe',
    'chrome':  r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'firefox': r'C:\Program Files\Mozilla Firefox\firefox.exe',
    'vlc':     r'C:\Program Files\VideoLAN\VLC\vlc.exe',
    'steam':   r'C:\Program Files (x86)\Steam\steam.exe',
    'plex':    r'C:\Program Files\Plex\Plex.exe',
    'spotify': r'C:\Users\{}\AppData\Roaming\Spotify\Spotify.exe'.format(
                   os.environ.get('USERNAME', '')),
    # Phone mirror — uncomment whichever you use:
    # 'mirror': r'C:\Program Files\scrcpy\scrcpy.exe',      # Android (free)
    # 'mirror': r'C:\Program Files\LonelyScreen\LonelyScreen.exe',  # AirPlay
    'mirror':  r'C:\Program Files\scrcpy\scrcpy.exe',
}

# ── KEYBOARD MAP ─────────────────────────────────────────────────────────────
KEY_MAP = {
    'UP': 'up', 'DOWN': 'down', 'LEFT': 'left', 'RIGHT': 'right',
    'RETURN': 'enter', 'BACKSPACE': 'backspace', 'SUPER': 'win',
    'F12': 'f12', 'ESCAPE': 'esc', 'SPACE': 'space',
}

# ── STATIC FILES SERVED ──────────────────────────────────────────────────────
# Files in SCRIPT_DIR that will be served at their filename as URL path.
SERVEABLE_EXTENSIONS = {
    '.html', '.js', '.json', '.svg', '.png', '.ico',
    '.css', '.txt', '.yaml', '.yml', '.bat', '.py',
}


class AgentHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Only log errors
        status = str(args[1]) if len(args) > 1 else ''
        if status.startswith('4') or status.startswith('5'):
            print(f'[Agent] {fmt % args}')

    def send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, content_type):
        try:
            with open(path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(data))
            # Critical: tell Chrome this is a private-network resource
            # that explicitly allows cross-origin private network access.
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Private-Network', 'true')
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Private-Network', 'true')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.split('?')[0]  # strip query string

        # ── /ping → health check ──────────────────────────────────────────
        if path == '/ping':
            self.send_json(200, {
                'status': 'ok',
                'agent': 'movie-room-pc-agent',
                'version': '1.1',
                'serving': os.path.exists(os.path.join(SCRIPT_DIR, 'theater-remote.html')),
            })
            return

        # ── / or /index.html → serve the app ─────────────────────────────
        if path in ('/', '/index.html', ''):
            app_path = os.path.join(SCRIPT_DIR, 'theater-remote.html')
            if os.path.exists(app_path):
                self.send_file(app_path, 'text/html; charset=utf-8')
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'theater-remote.html not found in agent folder')
            return

        # ── /filename.ext → serve static assets ──────────────────────────
        filename = path.lstrip('/')
        ext = os.path.splitext(filename)[1].lower()
        if ext in SERVEABLE_EXTENSIONS and '/' not in filename and '..' not in filename:
            file_path = os.path.join(SCRIPT_DIR, filename)
            if os.path.exists(file_path):
                mime = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                self.send_file(file_path, mime)
                return

        self.send_response(404)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != '/run':
            self.send_json(404, {'error': 'not found'})
            return

        length = int(self.headers.get('Content-Length', 0))
        try:
            body    = json.loads(self.rfile.read(length))
            command = body.get('command', '').strip()
        except Exception:
            self.send_json(400, {'error': 'invalid json'})
            return

        result = self.handle_command(command)
        self.send_json(200, result)

    def handle_command(self, command):
        print(f'[Agent] Command: {command}')

        # key: prefix → send keystroke
        if command.startswith('key:'):
            key    = command[4:].strip()
            mapped = KEY_MAP.get(key, key.lower())
            try:
                import pyautogui
                pyautogui.press(mapped)
                return {'ok': True, 'action': 'key', 'key': mapped}
            except ImportError:
                ps = f'$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys("{{{mapped.upper()}}}")'
                subprocess.Popen(['powershell', '-Command', ps], shell=True)
                return {'ok': True, 'action': 'key_ps', 'key': mapped}

        # type: prefix → type text
        if command.startswith('type:'):
            text = command[5:]
            try:
                import pyautogui
                time.sleep(0.1)
                pyautogui.typewrite(text, interval=0.03)
                return {'ok': True, 'action': 'type', 'text': text}
            except ImportError:
                safe = text.replace("'", "''")
                ps   = f"$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys('{safe}')"
                subprocess.Popen(['powershell', '-Command', ps], shell=True)
                return {'ok': True, 'action': 'type_ps', 'text': text}

        # volume: prefix → system volume via nircmd
        if command.startswith('volume:'):
            try:
                level = int(command.split(':')[1])
                subprocess.Popen(['nircmd', 'setsysvolume', str(int(level / 100 * 65535))])
                return {'ok': True, 'action': 'volume', 'level': level}
            except Exception as e:
                return {'ok': False, 'error': str(e)}

        # named app → launch
        if command in APP_MAP:
            path = APP_MAP[command]
            if os.path.exists(path):
                try:
                    subprocess.Popen([path])
                    return {'ok': True, 'action': 'launch', 'app': command}
                except Exception as e:
                    return {'ok': False, 'error': str(e)}
            else:
                try:
                    subprocess.Popen(command, shell=True)
                    return {'ok': True, 'action': 'launch_shell', 'command': command}
                except Exception as e:
                    return {'ok': False, 'error': f'Not found at {path}: {e}'}

        # shell: prefix → arbitrary shell command
        if command.startswith('shell:'):
            try:
                subprocess.Popen(command[6:], shell=True)
                return {'ok': True, 'action': 'shell'}
            except Exception as e:
                return {'ok': False, 'error': str(e)}

        return {'ok': False, 'error': f'Unknown command: {command}'}


def main():
    server = http.server.ThreadingHTTPServer(('0.0.0.0', PORT), AgentHandler)
    local_ip = _get_local_ip()
    print()
    print('=' * 52)
    print('  Movie Room PC Agent v1.1')
    print('=' * 52)
    print(f'  Agent URL:   http://{local_ip}:{PORT}')
    print(f'  App URL:     http://{local_ip}:{PORT}/')
    print(f'  Ping:        http://{local_ip}:{PORT}/ping')
    print()
    if os.path.exists(os.path.join(SCRIPT_DIR, 'theater-remote.html')):
        print(f'  ✓ theater-remote.html found — app is being served')
        print(f'  → Access app at http://{local_ip}:{PORT}/')
        print(f'    (No "allow network access" prompts from this URL!)')
    else:
        print('  ✗ theater-remote.html not found in this folder')
        print('    Copy it here to serve the app locally')
    print()
    print('  Press Ctrl+C to stop')
    print('=' * 52)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n[Agent] Stopped.')
        server.shutdown()


def _get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


if __name__ == '__main__':
    main()
