@echo off
echo Installing required packages...
pip install PyQt6 opencv-python pillow pywin32 mss

echo.
echo Starting the application...
python screen_app_debug.pyw
pause 