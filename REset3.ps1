# Set up a custom reset configuration
$resetKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\ResetEngine"
if (!(Test-Path $resetKey)) {
    New-Item -Path $resetKey -Force | Out-Null
}
New-ItemProperty -Path $resetKey -Name "KeepUserData" -Value 1 -PropertyType DWORD -Force | Out-Null
New-ItemProperty -Path $resetKey -Name "AutoRebootWhenComplete" -Value 1 -PropertyType DWORD -Force | Out-Null

# Then run the command
Start-Process -FilePath "C:\Windows\System32\SystemSettingsAdminFlows.exe" -ArgumentList "ResetPC" -Wait
