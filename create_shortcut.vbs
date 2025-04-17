Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get paths
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
desktopPath = WshShell.SpecialFolders("Desktop")

' Create shortcut
Set shortcut = WshShell.CreateShortcut(fso.BuildPath(desktopPath, "Screen Split App.lnk"))
shortcut.TargetPath = "pythonw.exe"
shortcut.Arguments = "screen_app_debug.pyw"
shortcut.WorkingDirectory = strPath
shortcut.WindowStyle = 1  ' Normal window
shortcut.Save

MsgBox "Shortcut created on desktop!", vbInformation 