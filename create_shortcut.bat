@echo off
echo Creating VBS shortcut...

set "DESKTOP=%USERPROFILE%\Desktop"
set "APP_DIR=C:\Users\Kieran Jackson\screen_split_app"

echo Set WshShell = CreateObject("WScript.Shell") > "%DESKTOP%\Screen Split App.vbs"
echo WshShell.CurrentDirectory = "%APP_DIR%" >> "%DESKTOP%\Screen Split App.vbs"
echo WshShell.Run "pythonw.exe screen_app_fixed.pyw", 0, False >> "%DESKTOP%\Screen Split App.vbs"

echo.
echo VBS shortcut created successfully on your desktop!
echo Please try launching the application using the new shortcut.
echo.
pause 