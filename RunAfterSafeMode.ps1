# Stop Webroot SecureAnywhere services
sc.exe stop WRSVC
sc.exe stop WRCoreService
sc.exe stop WRSkyClient

# Wait briefly to ensure services are stopped
Start-Sleep -Seconds 5

# Attempt to uninstall from both possible install paths
$webrootPaths = @(
    "${Env:ProgramFiles(x86)}\Webroot\WRSA.exe",
    "${Env:ProgramFiles}\Webroot\WRSA.exe"
)

foreach ($path in $webrootPaths) {
    if (Test-Path $path) {
        Write-Host "Attempting to uninstall Webroot from $path"
        Start-Process -FilePath $path -ArgumentList "-uninstall" -Wait -ErrorAction SilentlyContinue
    } else {
        Write-Host "Webroot executable not found at $path"
    }
}

# Remove Safe Mode boot
Write-Host "Removing Safe Mode boot setting..."
bcdedit /deletevalue safeboot

# Optional: Pause briefly before restart
Start-Sleep -Seconds 5

# Restart system
Write-Host "Restarting system..."
Restart-Computer -Force
