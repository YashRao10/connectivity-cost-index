# Registers the connectivity logger as a Windows Scheduled Task, running
# every 30 minutes -- the Windows equivalent of logger/com.yashrao.connectivity-logger.plist
# (launchd, macOS). NOT run automatically; execute manually to install:
#
#   powershell -ExecutionPolicy Bypass -File logger\register_windows_task.ps1
#
# To remove: Unregister-ScheduledTask -TaskName "ConnectivityLogger-HomeDesktop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = (Get-Command python).Source
$script = Join-Path $repoRoot "logger\collect_sample.py"

$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$script`" --label home-desktop" -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration ([TimeSpan]::MaxValue)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 2)

Register-ScheduledTask -TaskName "ConnectivityLogger-HomeDesktop" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "Connectivity Cost Index: logs download/upload/latency/jitter/loss every 30 min"

Write-Host "Registered. Check with: Get-ScheduledTask -TaskName ConnectivityLogger-HomeDesktop"
