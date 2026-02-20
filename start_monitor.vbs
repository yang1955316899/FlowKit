Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "E:\Code\Python\monitor"
WshShell.Run "E:\Code\Python\monitor\.venv\Scripts\pythonw.exe E:\Code\Python\monitor\main.py", 0, False