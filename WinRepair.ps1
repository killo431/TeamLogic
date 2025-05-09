   function Write-Progress($message) {
        Write-Host $message -ForegroundColor Cyan
    }

    #===============================================================================================================#
    ##############################################Optimize-System####################################################

    function Optimize-System {
        Write-Host "`nOptimizing system performance..." -ForegroundColor Cyan
        Write-Progress "Starting system performance optimization."

        Write-Host "Reviewing startup programs..." -ForegroundColor Yellow
        Get-CimInstance Win32_StartupCommand | Select-Object Command, Location, User | Format-Table -AutoSize

        Write-Host "Running disk cleanup..." -ForegroundColor Yellow
        Start-Process -FilePath cleanmgr.exe -ArgumentList '/sagerun:1' -Wait

        Write-Host "Analyzing drives for fragmentation..." -ForegroundColor Yellow
        $drives = Get-Volume | Where-Object {$_.DriveType -eq 'Fixed' -and $_.FileSystemType -eq 'NTFS'}
        foreach ($drive in $drives) {
            if ($drive.DriveLetter) {
                Write-Host "Optimizing drive $($drive.DriveLetter)..." -ForegroundColor Yellow
                Optimize-Volume -DriveLetter $drive.DriveLetter -Verbose
            }
        }

        Write-Host "Optimizing performance settings..." -ForegroundColor Yellow
        $path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
        if (-not (Test-Path $path)) {
            New-Item -Path $path -Force | Out-Null
        }
        Set-ItemProperty -Path $path -Name "VisualFXSetting" -Value 2 -Type DWORD

        Write-Host "Setting power plan to High Performance..." -ForegroundColor Yellow
        powercfg /setactive SCHEME_MIN

        Write-Host "System optimization completed!" -ForegroundColor Green
        Write-Progress "System optimization completed successfully."
    }

    function Clean-TempFiles {
        Write-Host "`nCleaning temporary files..." -ForegroundColor Cyan
        Write-Progress "Starting temporary files cleanup."

        $tempFolders = @(
            "$env:TEMP",
            "$env:windir\Temp",
            "$env:windir\Prefetch",
            "$env:LOCALAPPDATA\Temp",
            "$env:LOCALAPPDATA\Microsoft\Windows\INetCache\IE",
            "$env:SYSTEMROOT\SoftwareDistribution\Download"
        )

        foreach ($folder in $tempFolders) {
            if (Test-Path $folder) {
                Write-Host "Cleaning $folder..." -ForegroundColor Yellow
                Get-ChildItem -Path $folder -Force -ErrorAction SilentlyContinue | 
                    Where-Object { ($_.LastWriteTime -lt (Get-Date).AddDays(-2)) } | 
                    Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
            }
        }

        wevtutil el | Foreach-Object {wevtutil cl "$_"}
        wsreset.exe
        ipconfig /flushdns

        Write-Host "Temporary files cleaned!" -ForegroundColor Green
        Write-Progress "Temporary files cleaned successfully."
    }

    #===============================================================================================================#
    ##############################################Optimize-Office####################################################
    function Optimize-Office365 {
        Write-Host "`nOptimizing Office 365..." -ForegroundColor Cyan
        Write-Progress "Starting Office 365 optimization."

        $officePath = "$env:ProgramFiles\Microsoft Office\root\Office16"
        if (-not (Test-Path $officePath)) {
            $officePath = "${env:ProgramFiles(x86)}\Microsoft Office\root\Office16"
        }

        if (-not (Test-Path $officePath)) {
            Write-Host "Office 365 installation not found." -ForegroundColor Red
            return
        }

        $officeApps = @('excel', 'word', 'outlook', 'powerpoint')
        foreach ($app in $officeApps) {
            $regPath = "HKCU:\Software\Microsoft\Office\16.0\$app\Graphics"
            if (-not (Test-Path $regPath)) {
                New-Item -Path $regPath -Force | Out-Null
            }
            Set-ItemProperty -Path $regPath -Name "DisableHardwareAcceleration" -Value 1 -Type DWORD
            Set-ItemProperty -Path $regPath -Name "DisableAnimations" -Value 1 -Type DWORD
        }

        $officeCachePath = "$env:LOCALAPPDATA\Microsoft\Office\16.0\OfficeFileCache"
        if (Test-Path $officeCachePath) {
            Remove-Item -Path "$officeCachePath\*" -Force -Recurse -ErrorAction SilentlyContinue
        }

        Write-Host "Office 365 optimization completed!" -ForegroundColor Green
        Write-Progress "Office 365 optimization completed successfully."
    }

    function Reset-WindowsKeepFiles {
        if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
            Write-Warning "This script requires administrative privileges. Attempting to elevate..."
            
            # Build the script path and arguments for elevation
            $ScriptPath = $MyInvocation.MyCommand.Definition
            $Arguments = "-ExecutionPolicy Bypass -File `"$ScriptPath`""
            
            # Start a new elevated PowerShell instance
            Start-Process PowerShell -Verb RunAs -ArgumentList $Arguments
            
            # Exit the current non-elevated instance
            exit
        }

        # If we get here, we're running with admin rights
        Write-Host "Running with administrative privileges" -ForegroundColor Green
        Write-Host "Starting Windows 11 reset process (preserving personal files)..." -ForegroundColor Cyan

        # Log the reset attempt
        $logPath = "$env:TEMP\windows_reset_log.txt"
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "[$timestamp] Windows 11 reset initiated - Preserving user files" | Out-File -FilePath $logPath -Append

        try {
            # Method 1: Use the Reset-PCCommand if available (Windows 10/11)
            if (Get-Command -Name "Reset-PC" -ErrorAction SilentlyContinue) {
                Write-Host "Attempting reset using Reset-PC cmdlet..." -ForegroundColor Yellow
                Reset-PC -KeepUserData -NoReboot
                
                Write-Host "Reset-PC command completed. Initiating restart..." -ForegroundColor Green
                "[$timestamp] Reset-PC command completed" | Out-File -FilePath $logPath -Append
                Start-Process -FilePath "shutdown.exe" -ArgumentList "/r /t 10 /f" -NoNewWindow
            }
            # Method 2: Use systemreset.exe (alternative method)
            elseif (Test-Path -Path "$env:SystemRoot\System32\systemreset.exe") {
                Write-Host "Attempting reset using systemreset.exe..." -ForegroundColor Yellow
                Start-Process -FilePath "$env:SystemRoot\System32\systemreset.exe" -ArgumentList "--factoryreset --keepusers" -Wait
                
                "[$timestamp] systemreset.exe method attempted" | Out-File -FilePath $logPath -Append
            }
            # Method 3: Use reagentc to boot to recovery environment
            else {
                Write-Host "Using recovery environment method..." -ForegroundColor Yellow
                
                # Enable the recovery environment if not already enabled
                $reagentcEnableProcess = Start-Process -FilePath "$env:SystemRoot\System32\reagentc.exe" -ArgumentList "/enable" -PassThru -Wait -NoNewWindow
                
                if ($reagentcEnableProcess.ExitCode -eq 0) {
                    Write-Host "Recovery environment enabled" -ForegroundColor Green
                    
                    # Configure automatic reset with user data preservation
                    Write-Host "Setting up automatic reset with user data preservation" -ForegroundColor Yellow
                    
                    # Create registry key for automatic reset that preserves user data
                    $resetKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\ResetEngine\AutoReset"
                    if (!(Test-Path $resetKey)) {
                        New-Item -Path $resetKey -Force | Out-Null
                    }
                    New-ItemProperty -Path $resetKey -Name "KeepUserData" -Value 1 -PropertyType DWORD -Force | Out-Null
                    
                    # Boot to recovery environment
                    $bootToREProcess = Start-Process -FilePath "$env:SystemRoot\System32\reagentc.exe" -ArgumentList "/boottore" -PassThru -Wait -NoNewWindow
                    
                    if ($bootToREProcess.ExitCode -eq 0) {
                        Write-Host "System will restart to recovery environment and begin reset process..." -ForegroundColor Green
                        "[$timestamp] System configured to boot to recovery environment" | Out-File -FilePath $logPath -Append
                        Start-Process -FilePath "shutdown.exe" -ArgumentList "/r /t 10 /f" -NoNewWindow
                    } else {
                        throw "Failed to configure boot to recovery environment. Exit code: $($bootToREProcess.ExitCode)"
                    }
                } else {
                    throw "Failed to enable recovery environment. Exit code: $($reagentcEnableProcess.ExitCode)"
                }
            }
        } catch {
            Write-Host "Error: Failed to initiate Windows reset: $_" -ForegroundColor Red
            "[$timestamp] ERROR: Reset failed: $_" | Out-File -FilePath $logPath -Append
            Write-Host "Log saved to: $logPath" -ForegroundColor Magenta
        }

        Write-Host "Script complete. If successful, system will restart shortly for reset process." -ForegroundColor Cyan
    }

    # Execute the functions in order
    Write-Host "Starting remote maintenance process..." -ForegroundColor Green
    Optimize-System
    Clean-TempFiles  
    Optimize-Office365
    $resetConfirm = Read-Host "System has been optimized. Do you want to proceed with Windows Reset? (Y/N)"
    if ($resetConfirm -eq 'Y') {
        Reset-WindowsKeepFiles
    } else {
        Write-Host "Windows Reset skipped." -ForegroundColor Yellow
    }
}
