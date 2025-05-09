function Invoke-SystemReset {
    [CmdletBinding()]
    param (
        [Parameter()]
        [switch]$KeepUserData,
        
        [Parameter()]
        [switch]$NoReboot,
        
        [Parameter()]
        [switch]$CloudReset,
        
        [Parameter()]
        [switch]$CleanPCOnly
    )
    
    $exePath = "C:\Windows\System32\SystemSettingsAdminFlows.exe"
    if (-not (Test-Path $exePath)) {
        Write-Error "SystemSettingsAdminFlows.exe not found at expected location"
        return
    }
    
    $argumentList = ""
    if ($CloudReset) {
        $argumentList = "CloudReset"
    } else {
        $argumentList = "ResetPC"
    }
    
    if ($KeepUserData) {
        $argumentList += " -KeepUserData"
    }
    
    if ($NoReboot) {
        $argumentList += " -NoReboot"
    }
    
    if ($CleanPCOnly) {
        $argumentList += " -CleanPCOnly"
    }
    
    Write-Host "Executing: $exePath $argumentList" -ForegroundColor Yellow
    Start-Process -FilePath $exePath -ArgumentList $argumentList -Wait
}
