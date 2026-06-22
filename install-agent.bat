@echo off
:: Movie Room Remote — PC Agent Installer
:: Run this as Administrator to register the agent as a Windows startup task.
:: It will start automatically when you log in.

setlocal

set AGENT_NAME=MovieRoomPCAgent
set AGENT_DIR=%~dp0
set AGENT_SCRIPT=%AGENT_DIR%pc-agent.py

echo.
echo ==========================================
echo  Movie Room Remote — PC Agent Installer
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Download Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo [1/3] Python found.

:: Install pyautogui for keyboard control (optional but recommended)
echo [2/3] Installing pyautogui (for keyboard/mouse control)...
pip install pyautogui --quiet

:: Register as scheduled task (runs at login, stays in background)
echo [3/3] Registering startup task "%AGENT_NAME%"...

:: Remove old task if it exists
schtasks /delete /tn "%AGENT_NAME%" /f >nul 2>&1

:: Create new task
schtasks /create ^
  /tn "%AGENT_NAME%" ^
  /tr "pythonw \"%AGENT_SCRIPT%\"" ^
  /sc onlogon ^
  /delay 0000:30 ^
  /rl limited ^
  /f

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo  SUCCESS! PC Agent installed.
    echo ==========================================
    echo.
    echo The agent will start automatically when you log in.
    echo To start it now without rebooting, run:
    echo.
    echo   python "%AGENT_SCRIPT%"
    echo.
    echo Default port: 9876
    echo.
    echo NEXT STEPS:
    echo  1. Find your PC's local IP: run ipconfig, look for 192.168.x.x
    echo  2. In the Movie Room app, open Settings ^> Kodi ^& PC Agent
    echo  3. Set PC Agent URL to: http://192.168.x.x:9876
    echo  4. Tap "Ping Agent" to confirm connection
    echo.
    echo CUSTOMIZE APPS:
    echo  Edit pc-agent.py and update the APP_MAP paths at the top
    echo  to match where your apps are installed.
    echo.
) else (
    echo.
    echo WARNING: Could not create scheduled task.
    echo You may need to run this script as Administrator.
    echo.
    echo Alternative: Add a shortcut to pc-agent.py in your
    echo Startup folder: shell:startup
    echo.
)

echo Press any key to start the agent now for testing...
pause >nul
start "Movie Room PC Agent" python "%AGENT_SCRIPT%"
echo Agent started. Check your taskbar for the console window.
echo.
pause
