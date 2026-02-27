$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Home\Desktop\Pos-Assistant.lnk")
$Shortcut.TargetPath = "c:\Users\GibboTech\Downloads\Pos-Asistant"
$Shortcut.Save()
