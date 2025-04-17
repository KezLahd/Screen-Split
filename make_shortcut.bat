@echo off
echo Creating shortcut for Screen Split App...

set "CURRENT_DIR=%~dp0"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "SHORTCUT_PATH=%DESKTOP_DIR%\Screen Split App.lnk"
set "VBS_PATH=%CURRENT_DIR%launch_app.vbs"

echo Current directory: %CURRENT_DIR%
echo Desktop directory: %DESKTOP_DIR%
echo VBS path: %VBS_PATH%

if not exist "%VBS_PATH%" (
    echo ERROR: launch_app.vbs not found!
    echo Expected location: %VBS_PATH%
    pause
    exit /b 1
)

powershell ^
    "$ws = New-Object -ComObject WScript.Shell; ^
    $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); ^
    $s.TargetPath = '%VBS_PATH%'; ^
    $s.WorkingDirectory = '%CURRENT_DIR%'; ^
    $s.Description = 'Screen Split Application'; ^
    $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo Shortcut created successfully!
    echo Location: %SHORTCUT_PATH%
) else (
    echo Failed to create shortcut!
    echo Please check if you have write permissions to your desktop.
)

echo.
echo Press any key to continue...
pause > nul 