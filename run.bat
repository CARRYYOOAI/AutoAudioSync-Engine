@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 was not found. Install Python and enable Add Python to PATH.
  pause
  exit /b 1
)
where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo FFmpeg was not found. Install FFmpeg and add its bin folder to PATH.
  pause
  exit /b 1
)
where ffprobe >nul 2>nul
if errorlevel 1 (
  echo ffprobe was not found. Install FFmpeg and add its bin folder to PATH.
  pause
  exit /b 1
)
python audio_pipeline.py
if errorlevel 1 pause
