# Enable Sleep and Hibernate
powercfg -change standby-timeout-ac 30  # Set to 30 minutes for AC
powercfg -change standby-timeout-dc 15  # Set to 15 minutes for DC
powercfg -h on  # Enable hibernation

# Set Display to stay on indefinitely
powercfg -change monitor-timeout-ac 0  # Turn off the display timeout (infinite time)
powercfg -change monitor-timeout-dc 0  # Turn off the display timeout (infinite time)

# Enable Hard Drive Sleep
powercfg -change disk-timeout-ac 15  # Set to 15 minutes for AC
powercfg -change disk-timeout-dc 10  # Set to 10 minutes for DC

# Enable Power Saving for NIC (Network Interface Card)
# Get the network adapters and loop through them
$networkAdapters = Get-WmiObject -Class Win32_NetworkAdapter | Where-Object { $_.NetEnabled -eq $true }

foreach ($adapter in $networkAdapters) {
    $adapterName = $adapter.Name
    Write-Host "Enabling power saving for NIC: $adapterName"

    # Enable power management for the NIC
    $powerManagement = Get-WmiObject -Class Win32_NetworkAdapterConfiguration | Where-Object { $_.Description -eq $adapterName }
    
    # Enable the device to be turned off to save power
    $powerManagement | ForEach-Object {
        $_.SetPowerState(1, $null) # Enable power saving mode for the NIC
    }
}

Write-Host "Power settings have been reverted to default."
