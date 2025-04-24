# Revert Changes - Power Settings

# --- ENABLE HIBERNATION ---
powercfg -hibernate on

# --- SYSTEM SLEEP & HARD DRIVE SLEEP: ENABLED ---
powercfg -change -standby-timeout-ac 15    # Default AC standby timeout
powercfg -change -standby-timeout-dc 10    # Default DC standby timeout
powercfg -change -disk-timeout-ac 20       # Default AC disk timeout
powercfg -change -disk-timeout-dc 20       # Default DC disk timeout

# --- CPU THROTTLING: Default Power Plan ---
powercfg -restoredefaultschemes

# --- SCREEN TIMEOUT (DEFAULT) ---
powercfg -change -monitor-timeout-ac 15    # Default AC monitor timeout
powercfg -change -monitor-timeout-dc 10    # Default DC monitor timeout

# --- NIC POWER SETTINGS: RESTORE TO DEFAULT ---
Get-NetAdapter | ForEach-Object {
    $nic = $_
    Write-Output "Restoring NIC settings for: $($nic.Name)"
    
    # Disable wake support if it was enabled previously
    powercfg -devicedisablewake "$($nic.Name)" | Out-Null
    
    # Restore default power management settings
    try {
        $device = Get-PnpDevice -FriendlyName $nic.Name
        $instanceId = $device.InstanceId
        $powerMgmtKey = "HKLM\SYSTEM\CurrentControlSet\Enum\$instanceId\Device Parameters\PowerManagement"
        if (Test-Path $powerMgmtKey) {
            Set-ItemProperty -Path $powerMgmtKey -Name "PnPCapabilities" -Value 0 -Force
            Write-Output "Restored PnPCapabilities to 0 (enabled NIC power down) for $($nic.Name)"
        }
    } catch {
        Write-Output "Could not revert PnPCapabilities for $($nic.Name): $_"
    }

    # Reset Intel NIC (if any)
    $intelRegPath = "HKLM\SYSTEM\CurrentControlSet\Control\Class"
    Get-ChildItem -Path $intelRegPath -Recurse -ErrorAction SilentlyContinue | Where-Object {
        ($_ | Get-ItemProperty -ErrorAction SilentlyContinue).DriverDesc -like "*Intel*" -and
        ($_ | Get-ItemProperty -ErrorAction SilentlyContinue).* -ne $null
    } | ForEach-Object {
        try {
            # Reset Intel-specific settings
            Set-ItemProperty -Path $_.PSPath -Name "EEELinkAdvertisement" -Value "1" -Force -ErrorAction SilentlyContinue # Enable Energy Efficient Ethernet
            Set-ItemProperty -Path $_.PSPath -Name "SipsEnabled" -Value "1" -Force -ErrorAction SilentlyContinue # Enable System Idle Power Saver
            Write-Output "Restored Intel energy-saving settings for adapter: $($_.PSChildName)"
        } catch {
            Write-Output "Could not reset Intel power settings: $_"
        }
    }

    # Reset MSI or Realtek NIC (if any)
    if ($nic.DriverDesc -like "*MSI*" -or $nic.DriverDesc -like "*Realtek*") {
        try {
            # Reset MSI/Realtek energy-saving settings
            Set-ItemProperty -Path $_.PSPath -Name "EEELinkAdvertisement" -Value "1" -Force -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $_.PSPath -Name "SipsEnabled" -Value "1" -Force -ErrorAction SilentlyContinue
            Write-Output "Restored MSI/Realtek energy-saving settings for adapter: $($_.PSChildName)"
        } catch {
            Write-Output "Could not reset MSI/Realtek power settings: $_"
        }
    }
}

Write-Output "✅ All changes have been reverted to the default power settings."
