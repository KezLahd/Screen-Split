Set objShell = CreateObject("WScript.Shell")
appPath = "C:\Users\Kieran Jackson\screen_split_app"
objShell.CurrentDirectory = appPath
objShell.Run "cmd /c """ & appPath & "\venv\Scripts\activate.bat"" && python screen_app_debug.pyw", 0, False 