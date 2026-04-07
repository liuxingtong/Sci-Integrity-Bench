@echo off
title AI Scientist Live Viz

cd /d "%~dp0"
echo.
echo === AI Scientist Live Viz ===
echo Starting viz server on http://127.0.0.1:8765 ...
start "VizServer" cmd /K "cd /d "%~dp0" && python serve.py --port 8765"
timeout /t 3 /nobreak >nul

echo Opening Live Monitor in browser...
start "" "http://127.0.0.1:8765/live"
echo.
echo Starting meta-runner with --viz ...
cd /d "%~dp0..\.."
python -m meta_benchmark.meta_runner --viz
echo.
pause
