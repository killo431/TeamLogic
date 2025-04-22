
# Download the MSI with authentication handling
Write-Host "[-] Attempting to download MSI from https://app.ninjarmm.com/agent/installer/542e1b64-fe34-4e62-9d69-bad16aaed9a3/8.0.2891/NinjaOne-Agent-TEST-MainOffice-WINDOWSDESKTOP.msi"
try {
    # Try with additional headers that might help bypass restrictions
    (New-Object System.Net.WebClient).Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    (New-Object System.Net.WebClient).Headers.Add("Accept", "application/octet-stream")
    (New-Object System.Net.WebClient).DownloadFile("https://app.ninjarmm.com/agent/installer/542e1b64-fe34-4e62-9d69-bad16aaed9a3/8.0.2891/NinjaOne-Agent-TEST-MainOffice-WINDOWSDESKTOP.msi", "C:\Temp\NinjaOne-Agent-TEST-MainOffice-WINDOWSDESKTOP.msi")
} catch {
    Write-Host "[!] Failed to download MSI automatically: $_" -ForegroundColor Red
    Write-Host "[-] The URL may require authentication or a direct download link."
    Write-Host "[-] Please download the installer manually and place it at: C:\Temp\NinjaOne-Agent-TEST-MainOffice-WINDOWSDESKTOP.msi"
    
    # Wait for user to manually download the file
    do {
        Start-Sleep -Seconds 5
        $FileExists = Test-Path "C:\Temp\NinjaOne-Agent-TEST-MainOffice-WINDOWSDESKTOP.msi"
    } until ($FileExists -or (Read-Host "File not found. Try again? (Y/N)").ToUpper() -eq 'N')
    
    if (-not (Test-Path "C:\Temp\NinjaOne-Agent-TEST-MainOffice-WINDOWSDESKTOP.msi")) {
        Write-Host "[!] Installation canceled." -ForegroundColor Red
        exit 1
    }
}
# Install the MSI silently
if (Test-Path "C:\Temp\NinjaOne-Agent-TEST-MainOffice-WINDOWSDESKTOP.msi") {
    Write-Host "[-] Installing MSI silently..."
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", "`"C:\Temp\NinjaOne-Agent-TEST-MainOffice-WINDOWSDESKTOP.msi`"", "/qn" -Wait
    Write-Host "[-] Installation completed successfully." -ForegroundColor Green
} else {
    Write-Host "[!] MSI file not found. Installation failed." -ForegroundColor Red
    exit 1
}

"@

$scriptContent | Set-Content -Path $scriptPath -Encoding UTF8

$id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$p = New-Object System.Security.Principal.WindowsPrincipal($id)
if (-not $p.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[!] This script must be run as an admin." -ForegroundColor Red
    exit 1
}

# Define known possible locations for NinjaRMMAgent
$PossibleLocations = @(
    "${env:ProgramFiles}\NinjaOne\NinjaRMMAgent.exe",
    "${env:ProgramFiles}\NinjaRMM\NinjaRMMAgent.exe",
    "${env:ProgramFiles(x86)}\NinjaOne\NinjaRMMAgent.exe",
    "${env:ProgramFiles(x86)}\NinjaRMM\NinjaRMMAgent.exe"
)

# First, try to directly find the executable
$NinjaExe = ""
foreach ($Location in $PossibleLocations) {
    if (Test-Path -Path $Location) {
        Write-Host "[-] Found NinjaRMMAgent at $Location" -ForegroundColor Yellow
        $NinjaExe = $Location
        break
    }
}

# If not found in known locations, search program directories
if ($NinjaExe -eq "") {
    Write-Host "[x] Searching for NinjaRMMAgent in program directories..." -ForegroundColor Cyan
    
    # Search in Program Files
    Write-Host "[-] Searching in $($env:ProgramFiles)"
    $folders = Get-ChildItem "$($env:ProgramFiles)" -ErrorAction SilentlyContinue
    foreach ($folder in $folders) {
        $testPath = Join-Path -Path "$($env:ProgramFiles)\$($folder)" -ChildPath "NinjaRMMAgent.exe"
        if (Test-Path -Path $testPath) {
            Write-Host "[-] Found NinjaRMMAgent at $testPath" -ForegroundColor Yellow
            $NinjaExe = $testPath
            break
        }
    }
    
    # If still not found, search in Program Files (x86)
    if ($NinjaExe -eq "") {
        Write-Host "[-] Searching in ${env:ProgramFiles(x86)}"
        $folders = Get-ChildItem "${env:ProgramFiles(x86)}" -ErrorAction SilentlyContinue
        foreach ($folder in $folders) {
            $testPath = Join-Path -Path "${env:ProgramFiles(x86)}\$($folder)" -ChildPath "NinjaRMMAgent.exe"
            if (Test-Path -Path $testPath) {
                Write-Host "[-] Found NinjaRMMAgent at $testPath" -ForegroundColor Yellow
                $NinjaExe = $testPath
                break
            }
        }
    }
}

# If still not found, try to find by service
if ($NinjaExe -eq "") {
    Write-Host "[-] Attempting to locate NinjaRMMAgent through its service..." -ForegroundColor Cyan
    $NinjaService = Get-WmiObject -Class Win32_Service -Filter "Name='NinjaRMMAgent'" -ErrorAction SilentlyContinue
    
    if ($NinjaService) {
        $ServicePath = $NinjaService.PathName -replace '"', ''
        if (Test-Path -Path $ServicePath) {
            Write-Host "[-] Found NinjaRMMAgent via service at $ServicePath" -ForegroundColor Yellow
            $NinjaExe = $ServicePath
        }
    }
}

# If agent was found, proceed with uninstallation
$UninstallSuccess = $false
if ($NinjaExe -ne "") {
    Write-Host "[-] Ninja Agent was found, proceeding with uninstallation." -ForegroundColor Green
    
    # Try to stop the service
    Write-Host "[-] Stopping NinjaRMMAgent service..."
    Stop-Service -Name NinjaRMMAgent -Force -ErrorAction SilentlyContinue
    
    # Wait for the service to stop (with timeout)
    $serviceStopTimeout = 30
    $stopTime = 0
    while ($stopTime -lt $serviceStopTimeout) {
        $service = Get-Service -Name NinjaRMMAgent -ErrorAction SilentlyContinue
        if (-not $service -or $service.Status -ne "Running") {
            Write-Host "[-] NinjaRMMAgent service stopped successfully." -ForegroundColor Green
            break
        }
        
        Write-Host "[o] Waiting for NinjaRMMAgent service to stop ($stopTime/$serviceStopTimeout seconds)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 1
        $stopTime++
    }
    
    if ($stopTime -ge $serviceStopTimeout) {
        Write-Host "[!] Warning: Service did not stop in time. Attempting to continue anyway." -ForegroundColor Red
    }
    
    # Try disabling uninstall prevention
    Write-Host "[-] Executing $NinjaExe --disableUninstallPrevention"
    $process = Start-Process -FilePath $NinjaExe -ArgumentList "--disableUninstallPrevention" -Wait -PassThru -NoNewWindow -ErrorAction SilentlyContinue
    
    if ($process -and $process.ExitCode -eq 0) {
        Write-Host "[-] Successfully disabled uninstall prevention." -ForegroundColor Green
    } else {
        Write-Host "[!] Warning: Could not disable uninstall prevention or check exit code. Attempting to continue anyway." -ForegroundColor Red
    }
    
    # Check for the uninstaller
    Write-Host "[-] Checking for uninstaller..."
    $NinjaDir = Split-Path -Path $NinjaExe -Parent
    $Uninstaller = Join-Path -Path $NinjaDir -ChildPath "uninstall.exe"
    
    if (Test-Path -Path $Uninstaller) {
        Write-Host "[-] Uninstaller found at $Uninstaller, executing..." -ForegroundColor Green
        $process = Start-Process -FilePath $Uninstaller -ArgumentList "--mode", "unattended" -Wait -PassThru -NoNewWindow -ErrorAction SilentlyContinue
        
        if ($process -and $process.ExitCode -eq 0) {
            Write-Host "[-] Uninstall was successful. Performing cleanup." -ForegroundColor Green
            Remove-Item -Path $NinjaDir -Force -Recurse -ErrorAction SilentlyContinue
            Remove-Item -Path "$($env:ProgramData)\NinjaRMMAgent\" -Force -Recurse -ErrorAction SilentlyContinue
            $UninstallSuccess = $true
        } else {
            Write-Host "[!] Uninstaller reported failure or could not check exit code." -ForegroundColor Red
        }
    } else {
        Write-Host "[!] Uninstaller not found at expected location: $Uninstaller" -ForegroundColor Red
        
        # Try alternative uninstallation via registry
        Write-Host "[-] Attempting alternative uninstallation method..." -ForegroundColor Yellow
        $UninstallString = (Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
                          Where-Object { $_.DisplayName -like "*NinjaRMM*" -or $_.DisplayName -like "*NinjaOne*" }).UninstallString
        
        if (-not $UninstallString) {
            $UninstallString = (Get-ItemProperty HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | 
                              Where-Object { $_.DisplayName -like "*NinjaRMM*" -or $_.DisplayName -like "*NinjaOne*" }).UninstallString
        }
        
        if ($UninstallString) {
            Write-Host "[-] Found uninstall string: $UninstallString" -ForegroundColor Yellow
            
            # Extract MSI product code if available
            if ($UninstallString -match "{[A-Z0-9\-]+}") {
                $ProductCode = $matches[0]
                Write-Host "[-] Uninstalling using product code: $ProductCode" -ForegroundColor Yellow
                $process = Start-Process -FilePath "msiexec.exe" -ArgumentList "/x", $ProductCode, "/qn" -Wait -PassThru
                
                if ($process.ExitCode -eq 0) {
                    Write-Host "[-] Uninstallation via MSI was successful." -ForegroundColor Green
                    $UninstallSuccess = $true
                } else {
                    Write-Host "[!] MSI uninstallation failed with exit code: $($process.ExitCode)" -ForegroundColor Red
                }
            } else {
                Write-Host "[!] Could not extract product code from uninstall string." -ForegroundColor Red
            }
        } else {
            Write-Host "[!] No uninstallation information found in registry." -ForegroundColor Red
        }
    }
} else {
    Write-Host "[!] Couldn't find NinjaRMMAgent executable. Agent may not be installed." -ForegroundColor Yellow
}

# Wait between uninstall and install steps
Write-Host "[-] Waiting 20 seconds before proceeding with installation..." -ForegroundColor Cyan
$waitSeconds = 20
for ($i = 1; $i -le $waitSeconds; $i++) {
    Write-Host "[-] Waiting... $i/$waitSeconds seconds" -ForegroundColor Cyan
    Start-Sleep -Seconds 1
}
Write-Host "[-] Wait completed. Proceeding with installation." -ForegroundColor Green
