@echo off
echo Installing required packages...
pip install opencv-python PyQt6 pillow pywin32 mss

echo.
echo Starting Screen Split Application...
python screen_app_debug.pyw

echo.
echo If the app didn't start, press any key to try again...
pause > nul 