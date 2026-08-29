@echo off
title StealthClip - Stop
echo Stopping StealthClip if it is running...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^py.*\.exe$|^python.*\.exe$' -and $_.CommandLine -like '*main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo Done. If it was running, it is now stopped.
pause