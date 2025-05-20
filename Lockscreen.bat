@echo off
echo Setting lock screen with forced locking and visible screensaver to 300 seconds...

:: Set screen timeout to 300 seconds for both AC and DC power
powercfg /setacvalueindex SCHEME_CURRENT SUB_VIDEO VIDEOIDLE 300
powercfg /setdcvalueindex SCHEME_CURRENT SUB_VIDEO VIDEOIDLE 300

:: Set the screen to lock after timeout
powercfg /setacvalueindex SCHEME_CURRENT SUB_NONE CONSOLELOCK 300
powercfg /setdcvalueindex SCHEME_CURRENT SUB_NONE CONSOLELOCK 300

:: Apply the changes
powercfg /setactive SCHEME_CURRENT

:: Enable screensaver with 300-second timeout and require password
reg add "HKCU\Control Panel\Desktop" /v ScreenSaveActive /t REG_SZ /d 1 /f
reg add "HKCU\Control Panel\Desktop" /v ScreenSaveTimeOut /t REG_SZ /d 300 /f
reg add "HKCU\Control Panel\Desktop" /v ScreenSaverIsSecure /t REG_SZ /d 1 /f

:: Set Bubbles screensaver (more visually obvious)
reg add "HKCU\Control Panel\Desktop" /v SCRNSAVE.EXE /t REG_SZ /d "C:\Windows\System32\Bubbles.scr" /f

:: Create policy paths if they don't exist
reg add "HKCU\Software\Policies\Microsoft\Windows\Control Panel\Desktop" /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Personalization" /f

:: Set additional lock policies
reg add "HKCU\Software\Policies\Microsoft\Windows\Control Panel\Desktop" /v ScreenSaverIsSecure /t REG_SZ /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Personalization" /v NoLockScreen /t REG_DWORD /d 0 /f

:: Set the lock screen timeout in the registry (in seconds)
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v InactivityTimeoutSecs /t REG_DWORD /d 300 /f

:: Display current screensaver settings for verification
echo Current screensaver settings:
reg query "HKCU\Control Panel\Desktop" /v SCRNSAVE.EXE
reg query "HKCU\Control Panel\Desktop" /v ScreenSaveActive
reg query "HKCU\Control Panel\Desktop" /v ScreenSaveTimeOut

echo Configuration complete. Your PC should now properly lock and show bubbles screensaver after 300 seconds.
