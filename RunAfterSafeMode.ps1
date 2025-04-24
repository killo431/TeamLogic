# Define the path to WRSA.exe
cmd.exe /c "C:\Program Files (x86)\Webroot\WRSA.exe" -uninstall /silent

# Remove Safe Mode boot setting
Write-Host "Removing Safe Mode boot setting..."
bcdedit /deletevalue safeboot

# Optional: Wait before reboot (e.g., allow uninstall to complete fully)
Start-Sleep -Seconds 60

# Reboot system into normal mode
