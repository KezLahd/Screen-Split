On Error Resume Next

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the script's directory
strPath = fso.GetParentFolderName(WScript.ScriptFullName)

' Change to the correct directory
WshShell.CurrentDirectory = strPath

' Run the app using pythonw from PATH
WshShell.Run "pythonw.exe screen_app_debug.pyw", 0, False

' Give the app a moment to start
WScript.Sleep 2000

' Check if the process is running
Set objWMIService = GetObject("winmgmts:")
Set colProcesses = objWMIService.ExecQuery("Select * From Win32_Process Where CommandLine Like '%" & Replace(strPath & "\screen_app_debug.pyw", "\", "\\") & "%'")

If colProcesses.Count = 0 Then
    MsgBox "The application failed to start. Command used: pythonw.exe screen_app_debug.pyw", vbCritical
End If 