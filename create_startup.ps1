$WshShell = New-Object -ComObject WScript.Shell
$StartupPath = [Environment]::GetFolderPath('Startup')
$Shortcut = $WshShell.CreateShortcut("$StartupPath\Monitor.lnk")
$Shortcut.TargetPath = "E:\Code\Python\monitor\start_monitor.vbs"
$Shortcut.WorkingDirectory = "E:\Code\Python\monitor"
$Shortcut.Save()
Write-Host "Startup shortcut created at: $StartupPath\Monitor.lnk"
