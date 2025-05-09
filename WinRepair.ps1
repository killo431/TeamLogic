Add-Type -AssemblyName PresentationFramework

function Show-VerbosePopup($message) {
    [System.Windows.MessageBox]::Show($message, "Verbose Information", 'OK', 'Information')
}

function Reset-WindowsKeepFiles {
    Write-Host "`nPreparing to reset Windows while keeping personal files..." -ForegroundColor Yellow
    Show-VerbosePopup "Preparing to reset Windows while keeping personal files."
    systemreset -cleanpc
}

function Optimize-System {
    Write-Host "`nOptimizing system performance..." -ForegroundColor Cyan
    Show-VerbosePopup "Starting system performance optimization."

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
    Show-VerbosePopup "System optimization completed successfully."
}

function Clean-TempFiles {
    Write-Host "`nCleaning temporary files..." -ForegroundColor Cyan
    Show-VerbosePopup "Starting temporary files cleanup."

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
    Show-VerbosePopup "Temporary files cleaned successfully."
}

function Optimize-Office365 {
    Write-Host "`nOptimizing Office 365..." -ForegroundColor Cyan
    Show-VerbosePopup "Starting Office 365 optimization."

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
    Show-VerbosePopup "Office 365 optimization completed successfully."
}

Optimize-System
Clean-TempFiles
Optimize-Office365
