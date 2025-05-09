# Windows 11 Reset and Optimization Script Generator
# Run as Administrator

# Check for admin privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script requires Administrator privileges. Please restart PowerShell as Administrator."
    Exit
}

# Initialize options array
$selectedOptions = @()
$scriptContent = @()

function Show-Menu {
    Clear-Host
    Write-Host "========== Windows 11 Reset and Optimization ==========" -ForegroundColor Cyan
    Write-Host "Select options to include in your custom script:" -ForegroundColor Yellow
    Write-Host "1: Reset Windows (Keep Files)" -ForegroundColor Green
    Write-Host "2: System Optimization" -ForegroundColor Green
    Write-Host "3: Clean Temporary Files" -ForegroundColor Green
    Write-Host "4: Repair System Files" -ForegroundColor Green
    Write-Host "5: Optimize Office 365" -ForegroundColor Green
    Write-Host "6: Custom Registry Tweaks" -ForegroundColor Green
    Write-Host "7: Network Optimization" -ForegroundColor Green
    Write-Host "8: Generate Script" -ForegroundColor Magenta
    Write-Host "9: Exit" -ForegroundColor Red
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host "Currently selected: $([string]::Join(", ", $selectedOptions))" -ForegroundColor Cyan
}

function Toggle-Option {
    param (
        [int]$option,
        [string]$optionName
    )
    
    if ($selectedOptions -contains $optionName) {
        $selectedOptions.Remove($optionName)
        Write-Host "$optionName removed from script." -ForegroundColor Yellow
    } else {
        $selectedOptions += $optionName
        Write-Host "$optionName added to script." -ForegroundColor Green
    }
}

function Add-ResetWindowsScript {
    $scriptContent += @"
function Reset-WindowsKeepFiles {
    Write-Host "`nPreparing to reset Windows 11 while keeping your personal files..." -ForegroundColor Yellow
    Write-Host "WARNING: All applications will be removed, but your files will be kept." -ForegroundColor Red
    `$confirm = Read-Host "Are you sure you want to continue? (Y/N)"
    
    if (`$confirm -eq "Y" -or `$confirm -eq "y") {
        Write-Host "Starting Windows Reset process. Your computer will restart..." -ForegroundColor Cyan
        systemreset --factoryreset --keepfiles
    } else {
        Write-Host "Reset cancelled." -ForegroundColor Yellow
    }
}

"@
}

function Add-SystemOptimizationScript {
    $scriptContent += @"
function Optimize-System {
    Write-Host "`nOptimizing system performance..." -ForegroundColor Cyan
    
    # Disable unnecessary startup items
    Write-Host "Reviewing startup programs..." -ForegroundColor Yellow
    Get-CimInstance Win32_StartupCommand | Select-Object Command, Location, User | Format-Table -AutoSize
    
    # Disk cleanup
    Write-Host "Running disk cleanup..." -ForegroundColor Yellow
    Start-Process -FilePath cleanmgr.exe -ArgumentList '/sagerun:1' -Wait
    
    # Defragment drives if needed
    Write-Host "Analyzing drives for fragmentation..." -ForegroundColor Yellow
    `$drives = Get-Volume | Where-Object {`$_.DriveType -eq 'Fixed' -and `$_.FileSystemType -eq 'NTFS'}
    foreach (`$drive in `$drives) {
        if (`$drive.DriveLetter) {
            Write-Host "Optimizing drive `$(`$drive.DriveLetter)..." -ForegroundColor Yellow
            Optimize-Volume -DriveLetter `$drive.DriveLetter -Verbose
        }
    }
    
    # Windows performance settings
    Write-Host "Optimizing performance settings..." -ForegroundColor Yellow
    `$path = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects"
    if (-not (Test-Path `$path)) {
        New-Item -Path `$path -Force | Out-Null
    }
    Set-ItemProperty -Path `$path -Name "VisualFXSetting" -Value 2 -Type DWORD
    
    # Power settings optimization
    Write-Host "Setting power plan to High Performance..." -ForegroundColor Yellow
    powercfg /setactive SCHEME_MIN
    
    Write-Host "System optimization completed!" -ForegroundColor Green
}

"@
}

function Add-CleanTempFilesScript {
    $scriptContent += @"
function Clean-TempFiles {
    Write-Host "`nCleaning temporary files..." -ForegroundColor Cyan
    
    # Array of temp folders to clean
    `$tempFolders = @(
        "`$env:TEMP",
        "`$env:windir\\Temp",
        "`$env:windir\\Prefetch",
        "`$env:LOCALAPPDATA\\Temp",
        "`$env:LOCALAPPDATA\\Microsoft\\Windows\\INetCache\\IE",
        "`$env:SYSTEMROOT\\SoftwareDistribution\\Download"
    )
    
    foreach (`$folder in `$tempFolders) {
        if (Test-Path `$folder) {
            Write-Host "Cleaning `$folder..." -ForegroundColor Yellow
            Get-ChildItem -Path `$folder -Force -ErrorAction SilentlyContinue | 
                Where-Object { (`$_.LastWriteTime -lt (Get-Date).AddDays(-2)) } | 
                Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        }
    }
    
    # Clear Event Logs
    Write-Host "Clearing Event Logs..." -ForegroundColor Yellow
    wevtutil el | Foreach-Object {wevtutil cl "`$_"}
    
    # Clear Windows Store cache
    Write-Host "Clearing Windows Store cache..." -ForegroundColor Yellow
    wsreset.exe
    
    # Clear DNS cache
    Write-Host "Clearing DNS cache..." -ForegroundColor Yellow
    ipconfig /flushdns
    
    Write-Host "Temporary files cleaned!" -ForegroundColor Green
}

"@
}

function Add-RepairSystemFilesScript {
    $scriptContent += @"
function Repair-SystemFiles {
    Write-Host "`nRepairing system files..." -ForegroundColor Cyan
    
    # Run SFC
    Write-Host "Running System File Checker..." -ForegroundColor Yellow
    Start-Process -FilePath "sfc.exe" -ArgumentList "/scannow" -Wait -NoNewWindow
    
    # Run DISM
    Write-Host "Running DISM to repair Windows image..." -ForegroundColor Yellow
    Start-Process -FilePath "DISM.exe" -ArgumentList "/Online /Cleanup-Image /RestoreHealth" -Wait -NoNewWindow
    
    # Reset Windows Update components
    Write-Host "Resetting Windows Update components..." -ForegroundColor Yellow
    Stop-Service -Name BITS, wuauserv, appidsvc, cryptsvc -Force
    Remove-Item "`$env:ALLUSERSPROFILE\\Application Data\\Microsoft\\Network\\Downloader\\*" -Force -ErrorAction SilentlyContinue
    Remove-Item "`$env:SYSTEMROOT\\SoftwareDistribution\\*" -Force -Recurse -ErrorAction SilentlyContinue
    Remove-Item "`$env:SYSTEMROOT\\System32\\catroot2\\*" -Force -Recurse -ErrorAction SilentlyContinue
    Start-Service -Name BITS, wuauserv, appidsvc, cryptsvc
    
    Write-Host "System file repair completed!" -ForegroundColor Green
}

"@
}

function Add-OptimizeOfficeScript {
    $scriptContent += @"
function Optimize-Office365 {
    Write-Host "`nOptimizing Office 365..." -ForegroundColor Cyan
    
    # Check if Office 365 is installed
    `$officePath = "`$env:ProgramFiles\\Microsoft Office\\root\\Office16"
    if (-not (Test-Path `$officePath)) {
        `$officePath = "`${env:ProgramFiles(x86)}\\Microsoft Office\\root\\Office16"
        if (-not (Test-Path `$officePath)) {
            Write-Host "Office 365 installation not found." -ForegroundColor Red
            return
        }
    }
    
    # Disable hardware graphics acceleration (often improves stability)
    Write-Host "Configuring Office graphics settings..." -ForegroundColor Yellow
    `$officeApps = @('excel', 'word', 'outlook', 'powerpoint')
    foreach (`$app in `$officeApps) {
        `$regPath = "HKCU:\\Software\\Microsoft\\Office\\16.0\\`$app\\Graphics"
        if (-not (Test-Path `$regPath)) {
            New-Item -Path `$regPath -Force | Out-Null
        }
        Set-ItemProperty -Path `$regPath -Name "DisableHardwareAcceleration" -Value 1 -Type DWORD
        Set-ItemProperty -Path `$regPath -Name "DisableAnimations" -Value 1 -Type DWORD
    }
    
    # Clear Office cache
    Write-Host "Clearing Office cache..." -ForegroundColor Yellow
    `$officeCachePath = "`$env:LOCALAPPDATA\\Microsoft\\Office\\16.0\\OfficeFileCache"
    if (Test-Path `$officeCachePath) {
        Remove-Item -Path "`$officeCachePath\\*" -Force -Recurse -ErrorAction SilentlyContinue
    }
    
    # Optimize Outlook
    Write-Host "Optimizing Outlook settings..." -ForegroundColor Yellow
    `$outlookRegPath = "HKCU:\\Software\\Microsoft\\Office\\16.0\\Outlook\\Preferences"
    if (-not (Test-Path `$outlookRegPath)) {
        New-Item -Path `$outlookRegPath -Force | Out-Null
    }
    # Disable RSS feeds
    Set-ItemProperty -Path `$outlookRegPath -Name "EnableRss" -Value 0 -Type DWORD
    
    # Turn off hardware graphics acceleration in Outlook
    `$outlookGraphicsPath = "HKCU:\\Software\\Microsoft\\Office\\16.0\\Outlook\\Graphics"
    if (-not (Test-Path `$outlookGraphicsPath)) {
        New-Item -Path `$outlookGraphicsPath -Force | Out-Null
    }
    Set-ItemProperty -Path `$outlookGraphicsPath -Name "DisableHardwareAcceleration" -Value 1 -Type DWORD
    
    Write-Host "Office 365 optimization completed!" -ForegroundColor Green
}

"@
}

function Add-RegistryTweaksScript {
    $scriptContent += @"
function Apply-RegistryTweaks {
    Write-Host "`nApplying performance registry tweaks..." -ForegroundColor Cyan
    
    # Disable animations
    Write-Host "Disabling unnecessary animations..." -ForegroundColor Yellow
    `$animPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects"
    if (-not (Test-Path `$animPath)) {
        New-Item -Path `$animPath -Force | Out-Null
    }
    Set-ItemProperty -Path `$animPath -Name "VisualFXSetting" -Value 2 -Type DWORD
    
    # Disable transparency
    Write-Host "Disabling transparency effects..." -ForegroundColor Yellow
    `$personalizePath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
    if (-not (Test-Path `$personalizePath)) {
        New-Item -Path `$personalizePath -Force | Out-Null
    }
    Set-ItemProperty -Path `$personalizePath -Name "EnableTransparency" -Value 0 -Type DWORD
    
    # Optimize SSD if present
    Write-Host "Optimizing settings for SSD drives..." -ForegroundColor Yellow
    `$drives = Get-PhysicalDisk | Where-Object MediaType -eq "SSD"
    if (`$drives) {
        # Disable Prefetch and Superfetch for SSDs
        `$prefetchPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters"
        Set-ItemProperty -Path `$prefetchPath -Name "EnablePrefetcher" -Value 0 -Type DWORD
        Set-ItemProperty -Path `$prefetchPath -Name "EnableSuperfetch" -Value 0 -Type DWORD
        
        # Disable scheduled defrag for SSDs
        `$defragPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\OptimalLayout"
        if (-not (Test-Path `$defragPath)) {
            New-Item -Path `$defragPath -Force | Out-Null
        }
        Set-ItemProperty -Path `$defragPath -Name "EnableAutoLayout" -Value 0 -Type DWORD
    }
    
    # Speed up menu show delay
    Write-Host "Optimizing menu response times..." -ForegroundColor Yellow
    `$menuPath = "HKCU:\\Control Panel\\Desktop"
    Set-ItemProperty -Path `$menuPath -Name "MenuShowDelay" -Value 8 -Type STRING
    
    # Disable startup delay
    Write-Host "Disabling startup delay..." -ForegroundColor Yellow
    `$startupDelayPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Serialize"
    if (-not (Test-Path `$startupDelayPath)) {
        New-Item -Path `$startupDelayPath -Force | Out-Null
    }
    Set-ItemProperty -Path `$startupDelayPath -Name "StartupDelayInMSec" -Value 0 -Type DWORD
    
    Write-Host "Registry tweaks applied!" -ForegroundColor Green
}

"@
}

function Add-NetworkOptimizationScript {
    $scriptContent += @"
function Optimize-Network {
    Write-Host "`nOptimizing network settings..." -ForegroundColor Cyan
    
    # Reset network adapter
    Write-Host "Resetting network adapters..." -ForegroundColor Yellow
    ipconfig /release
    ipconfig /renew
    ipconfig /flushdns
    
    # Reset TCP/IP stack
    Write-Host "Resetting TCP/IP stack..." -ForegroundColor Yellow
    netsh int ip reset
    netsh winsock reset
    
    # Set DNS to Google and Cloudflare (optional - commented out)
    <#
    Write-Host "Setting DNS servers to Google and Cloudflare..." -ForegroundColor Yellow
    `$adapters = Get-NetAdapter | Where-Object Status -eq "Up"
    foreach (`$adapter in `$adapters) {
        Set-DnsClientServerAddress -InterfaceIndex `$adapter.InterfaceIndex -ServerAddresses ("8.8.8.8","1.1.1.1")
    }
    #>
    
    # Enable network auto-tuning
    Write-Host "Enabling TCP auto-tuning..." -ForegroundColor Yellow
    netsh int tcp set global autotuninglevel=normal
    
    # Optimize TCP settings
    Write-Host "Optimizing TCP settings..." -ForegroundColor Yellow
    netsh int tcp set global ecncapability=enabled
    
    # Configure network throttling index
    Write-Host "Optimizing network throttling..." -ForegroundColor Yellow
    `$throttlingPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Psched"
    if (-not (Test-Path `$throttlingPath)) {
        New-Item -Path `$throttlingPath -Force | Out-Null
    }
    Set-ItemProperty -Path `$throttlingPath -Name "NonBestEffortLimit" -Value 0 -Type DWORD
    
    Write-Host "Network optimization completed!" -ForegroundColor Green
}

"@
}

function Create-MasterScript {
    # Script header
    $header = @"
# Windows 11 Reset and Optimization Script
# Generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# Run as Administrator

# Check for admin privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script requires Administrator privileges. Please restart PowerShell as Administrator."
    Exit
}

"@

    # Main menu function
    $mainMenu = @"
function Show-Menu {
    Clear-Host
    Write-Host "========== Windows 11 Reset and Optimization ==========" -ForegroundColor Cyan
"@

    # Add menu options based on selected features
    if ($selectedOptions -contains "ResetWindows") {
        $mainMenu += @'
    Write-Host "1: Reset Windows (Keep Files)" -ForegroundColor Green
'@
    }
    
    if ($selectedOptions -contains "SystemOptimization") {
        $mainMenu += @'
    Write-Host "2: Perform System Optimization" -ForegroundColor Green
'@
    }
    
    if ($selectedOptions -contains "CleanTempFiles") {
        $mainMenu += @'
    Write-Host "3: Clean Temporary Files" -ForegroundColor Green
'@
    }
    
    if ($selectedOptions -contains "RepairSystemFiles") {
        $mainMenu += @'
    Write-Host "4: Repair System Files" -ForegroundColor Green
'@
    }
    
    if ($selectedOptions -contains "OptimizeOffice") {
        $mainMenu += @'
    Write-Host "5: Optimize Office 365" -ForegroundColor Green
'@
    }
    
    if ($selectedOptions -contains "RegistryTweaks") {
        $mainMenu += @'
    Write-Host "6: Apply Registry Tweaks" -ForegroundColor Green
'@
    }
    
    if ($selectedOptions -contains "NetworkOptimization") {
        $mainMenu += @'
    Write-Host "7: Optimize Network" -ForegroundColor Green
'@
    }
    
    # Always add Run All option
    $mainMenu += @'
    Write-Host "8: Run All Optimizations" -ForegroundColor Magenta
    Write-Host "9: Exit" -ForegroundColor Red
    Write-Host "=======================================================" -ForegroundColor Cyan
}

'@

    # Add function definitions based on selected options
    foreach ($option in $selectedOptions) {
        switch ($option) {
            "ResetWindows" { Add-ResetWindowsScript }
            "SystemOptimization" { Add-SystemOptimizationScript }
            "CleanTempFiles" { Add-CleanTempFilesScript }
            "RepairSystemFiles" { Add-RepairSystemFilesScript }
            "OptimizeOffice" { Add-OptimizeOfficeScript }
            "RegistryTweaks" { Add-RegistryTweaksScript }
            "NetworkOptimization" { Add-NetworkOptimizationScript }
        }
    }

    # Always add Run-AllOptimizations function
    $runAllFunction = @"
function Run-AllOptimizations {
    Write-Host "`nRunning all selected optimizations..." -ForegroundColor Cyan
    
"@

    if ($selectedOptions -contains "ResetWindows") {
        $runAllFunction += "    Reset-WindowsKeepFiles`n"
    }
    if ($selectedOptions -contains "SystemOptimization") {
        $runAllFunction += "    Optimize-System`n"
    }
    if ($selectedOptions -contains "CleanTempFiles") {
        $runAllFunction += "    Clean-TempFiles`n"
    }
    if ($selectedOptions -contains "RepairSystemFiles") {
        $runAllFunction += "    Repair-SystemFiles`n"
    }
    if ($selectedOptions -contains "OptimizeOffice") {
        $runAllFunction += "    Optimize-Office365`n"
    }
    if ($selectedOptions -contains "RegistryTweaks") {
        $runAllFunction += "    Apply-RegistryTweaks`n"
    }
    if ($selectedOptions -contains "NetworkOptimization") {
        $runAllFunction += "    Optimize-Network`n"
    }
    
    $runAllFunction += @"
    Write-Host "All optimizations completed!" -ForegroundColor Green
}

"@

    # Create main execution logic
    $mainExecution = @"
# Main script execution
do {
    Show-Menu
    `$selection = Read-Host "Please make a selection"
    
    switch (`$selection) {

"@

    # Add case statements for each selected option
    $caseCounter = 1
    if ($selectedOptions -contains "ResetWindows") {
        $mainExecution += @"
        '$caseCounter' { Reset-WindowsKeepFiles }
"@
        $caseCounter++
    }
    
    if ($selectedOptions -contains "SystemOptimization") {
        $mainExecution += @"
        '$caseCounter' { Optimize-System }
"@
        $caseCounter++
    }
    
    if ($selectedOptions -contains "CleanTempFiles") {
        $mainExecution += @"
        '$caseCounter' { Clean-TempFiles }
"@
        $caseCounter++
    }
    
    if ($selectedOptions -contains "RepairSystemFiles") {
        $mainExecution += @"
        '$caseCounter' { Repair-SystemFiles }
"@
        $caseCounter++
    }
    
    if ($selectedOptions -contains "OptimizeOffice") {
        $mainExecution += @"
        '$caseCounter' { Optimize-Office365 }
"@
        $caseCounter++
    }
    
    if ($selectedOptions -contains "RegistryTweaks") {
        $mainExecution += @"
        '$caseCounter' { Apply-RegistryTweaks }
"@
        $caseCounter++
    }
    
    if ($selectedOptions -contains "NetworkOptimization") {
        $mainExecution += @"
        '$caseCounter' { Optimize-Network }
"@
        $caseCounter++
    }
    
    # Always add Run All option
    $mainExecution += @"
        '8' { Run-AllOptimizations }
        '9' { Write-Host "Exiting..." -ForegroundColor Red; Exit }
        default { Write-Host "Invalid selection. Please try again." -ForegroundColor Red }
    }
    
    if (`$selection -ne '9') {
        Write-Host "`nPress any key to return to menu..."
        `$null = `$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
} while (`$selection -ne '9')
"@

    # Combine all parts of the script
    $completeScript = $header + $mainMenu + $scriptContent + $runAllFunction + $mainExecution
    
    return $completeScript
}

function Generate-ScriptFile {
    if ($selectedOptions.Count -eq 0) {
        Write-Host "No options selected. Please select at least one option." -ForegroundColor Red
        return
    }
    
    # Generate the script
    $scriptContent = Create-MasterScript
    
    # Ask for location (using simpler input method)
    Write-Host "`nWhere would you like to save the script?" -ForegroundColor Cyan
    Write-Host "1: Desktop" -ForegroundColor Yellow
    Write-Host "2: Documents" -ForegroundColor Yellow
    Write-Host "3: Custom path" -ForegroundColor Yellow
    
    $locationChoice = Read-Host "Enter choice (1-3)"
    
    switch ($locationChoice) {
        "1" { 
            $savePath = [Environment]::GetFolderPath("Desktop")
        }
        "2" { 
            $savePath = [Environment]::GetFolderPath("MyDocuments")
        }
        "3" { 
            $savePath = Read-Host "Enter the full path where you'd like to save the script (e.g., D:\Scripts)"
            if (-not (Test-Path $savePath)) {
                $createDir = Read-Host "Path doesn't exist. Create it? (Y/N)"
                if ($createDir -eq "Y" -or $createDir -eq "y") {
                    New-Item -Path $savePath -ItemType Directory -Force | Out-Null
                } else {
                    Write-Host "Script generation cancelled." -ForegroundColor Yellow
                    return
                }
            }
        }
        default { 
            $savePath = [Environment]::GetFolderPath("Desktop")
            Write-Host "Invalid choice. Using Desktop as default." -ForegroundColor Yellow
        }
    }
    
    # Ask for filename
    $defaultName = "Windows11_Optimizer_$(Get-Date -Format 'yyyyMMdd').ps1"
    $fileName = Read-Host "Enter script filename (default: $defaultName)"
    
    if ([string]::IsNullOrWhiteSpace($fileName)) {
        $fileName = $defaultName
    }
    
    if (-not $fileName.EndsWith(".ps1")) {
        $fileName += ".ps1"
    }
    
    # Full path for the script
    $scriptPath = Join-Path -Path $savePath -ChildPath $fileName
    
    # Write the script to file
    $scriptContent | Out-File -FilePath $scriptPath -Encoding utf8
    
    Write-Host "`nScript generated successfully!" -ForegroundColor Green
    Write-Host "Saved to: $scriptPath" -ForegroundColor Cyan
    
    # Ask if user wants to run the script now
    $runNow = Read-Host "`nDo you want to run the script now? (Y/N)"
    if ($runNow -eq "Y" -or $runNow -eq "y") {
        & $scriptPath
    } else {
        Write-Host "You can run the script later by right-clicking the file and selecting 'Run with PowerShell'" -ForegroundColor Yellow
    }
}

# Main execution loop
do {
    Show-Menu
    $selection = Read-Host "Please make a selection"
    
    switch ($selection) {
        '1' { Toggle-Option -option 1 -optionName "ResetWindows" }
        '2' { Toggle-Option -option 2 -optionName "SystemOptimization" }
        '3' { Toggle-Option -option 3 -optionName "CleanTempFiles" }
        '4' { Toggle-Option -option 4 -optionName "RepairSystemFiles" }
        '5' { Toggle-Option -option 5 -optionName "OptimizeOffice" }
        '6' { Toggle-Option -option 6 -optionName "RegistryTweaks" }
        '7' { Toggle-Option -option 7 -optionName "NetworkOptimization" }
        '8' { Generate-ScriptFile }
        '9' { Write-Host "Exiting..." -ForegroundColor Red; Exit }
        default { Write-Host "Invalid selection. Please try again." -ForegroundColor Red }
    }
    
    if ($selection -ne '8' -and $selection -ne '9') {
        Write-Host "`nPress any key to return to menu..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
} while ($selection -ne '9')