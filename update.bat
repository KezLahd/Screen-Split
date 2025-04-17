@echo off
setlocal enabledelayedexpansion

echo Updating Screen Split App...

:: Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
set "INSTALL_DIR=%APPDATA%\Screen Split App"

:: Create installation directory if it doesn't exist
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy new files
echo Copying new files...
xcopy /Y /E "%SCRIPT_DIR%\*" "%INSTALL_DIR%\"

:: Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Screen Split App.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\screen-split.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

:: Clean up temporary files
echo Cleaning up...
rd /s /q "%SCRIPT_DIR%"

echo Update complete!
pause 