# Create a SilverMill shortcut on the desktop so admin can start from desktop.
# Run from the SilverMill folder, or pass the folder as first argument.

$ErrorActionPreference = "Stop"
$ProjectDir = if ($args[0]) { $args[0] } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$ProjectDir = [System.IO.Path]::GetFullPath($ProjectDir)

$BatPath = Join-Path $ProjectDir "Start SilverMill.bat"
$IcoPath = Join-Path $ProjectDir "SilverMill.ico"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "SilverMill.lnk"

if (-not (Test-Path $BatPath)) {
    Write-Host "Not found: Start SilverMill.bat in $ProjectDir"
    exit 1
}

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $BatPath
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Start SilverMill - double-click to run the application"
$Shortcut.WindowStyle = 1  # Normal window (so admin can see server and press Ctrl+C to stop)

if (Test-Path $IcoPath) {
    $Shortcut.IconLocation = "$IcoPath,0"
}

$Shortcut.Save()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($WshShell) | Out-Null

Write-Host "Desktop shortcut created: $ShortcutPath"
Write-Host "You can now start SilverMill from your Desktop."
