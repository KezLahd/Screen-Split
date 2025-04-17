@echo off
echo Installing required packages...
pip install opencv-python PyQt6 pillow pywin32 mss

echo.
echo Creating desktop shortcut...
powershell "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Screen Split App.lnk'); $SC.TargetPath = '%~dp0launch_app.vbs'; $SC.WorkingDirectory = '%~dp0'; $SC.Save()"

echo.
echo Setup complete! You can now run the app from the desktop shortcut.
pause 