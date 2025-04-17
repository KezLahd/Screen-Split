$desktopPath = "C:\Users\Kieran Jackson\Desktop"
$appDir = "C:\Users\Kieran Jackson\screen_split_app"
$vbsContent = @"
On Error Resume Next

Set WshShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the script's directory
strPath = "$appDir"
WshShell.CurrentDirectory = strPath

' Create a log file
Set logFile = objFSO.CreateTextFile(strPath & "\launch_log.txt", True)
logFile.WriteLine "Starting launch script at " & Now()
logFile.WriteLine "Working directory: " & strPath

' Check if Python executable exists
pythonExe = "pythonw.exe"
If Not objFSO.FileExists(strPath & "\venv\Scripts\" & pythonExe) Then
    logFile.WriteLine "ERROR: Python executable not found in virtual environment"
    MsgBox "Python executable not found in virtual environment. Please run setup.bat first.", vbCritical
    logFile.Close
    WScript.Quit 1
End If
logFile.WriteLine "Python executable found"

' Check if the main script exists
mainScript = strPath & "\screen_app_fixed.pyw"
If Not objFSO.FileExists(mainScript) Then
    logFile.WriteLine "ERROR: Main script not found"
    MsgBox "Main script not found. Please make sure screen_app_fixed.pyw exists.", vbCritical
    logFile.Close
    WScript.Quit 1
End If
logFile.WriteLine "Main script found: " & mainScript

' Launch the application using pythonw.exe (no console window)
command = """" & strPath & "\venv\Scripts\" & pythonExe & """ """ & mainScript & """"
logFile.WriteLine "Launching application with command: " & command
result = WshShell.Run(command, 0, False)

logFile.WriteLine "Launch script completed"
logFile.Close

On Error Goto 0
"@

$vbsContent | Out-File -FilePath "$desktopPath\Screen Split App.vbs" -Encoding ASCII

Write-Host "VBS shortcut created successfully on your desktop!"
Write-Host "Please try launching the application using the new shortcut."
Read-Host "Press Enter to continue..." 