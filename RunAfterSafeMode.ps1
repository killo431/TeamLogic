# Stop Webroot services
sc.exe stop WRSVC
sc.exe stop WRCoreService
sc.exe stop WRSkyClient

# Wait briefly to ensure services are stopped
Start-Sleep -Seconds 5

# Define the path to WRSA.exe
$webrootPath = "C:\Program Files (x86)\Webroot\WRSA.exe"

if (Test-Path $webrootPath) {
    Write-Host "Found Webroot at $webrootPath. Attempting silent uninstall..."
    
    # Run the uninstall with license key and silent flag
    Start-Process -FilePath $webrootPath -ArgumentList "/autouninstall=EAD3-KSYA-B887-2BCB-4D18 /silent" -Wait
} else {
    Write-Host "Webroot executable not found at $webrootPath"
}

# Remove Safe Mode boot setting
Write-Host "Removing Safe Mode boot setting..."
bcdedit /deletevalue safeboot

# Optional: Wait before reboot (e.g., allow uninstall to complete fully)
Start-Sleep -Seconds 60

# Reboot system into normal mode
Write-Host "Restarting system..."
Restart-Computer -Force
