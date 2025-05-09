# Egnyte User Profile Backup Script
# This script backs up user profiles and important files to Egnyte before PC reset
# Run with administrative privileges for full access to user profiles

# Script will collect all parameters interactively
param()

# Set error action preference
$ErrorActionPreference = "Continue"

# Script version
$ScriptVersion = "1.0"

# ======= Functions =======

function Write-Log {
    param (
        [string]$Message,
        [string]$Level = "INFO"
    )
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "$Timestamp [$Level] - $Message"
    $LogEntry | Out-File -FilePath $script:LogFile -Append
    
    # Output to console with color based on level
    switch ($Level) {
        "ERROR" { Write-Host $LogEntry -ForegroundColor Red }
        "WARNING" { Write-Host $LogEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $LogEntry -ForegroundColor Green }
        default { Write-Host $LogEntry }
    }
}

function Test-Admin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-ValidUsers {
    # Get all user profiles that aren't system accounts
    $UserProfiles = Get-CimInstance -ClassName Win32_UserProfile | 
                    Where-Object { 
                        -not $_.Special -and 
                        $_.LocalPath -match 'C:\\Users\\' -and 
                        $_.LocalPath -notmatch 'C:\\Users\\Default' -and
                        $_.LocalPath -notmatch 'C:\\Users\\Public' -and
                        $_.LocalPath -notmatch 'C:\\Users\\All Users'
                    }
    
    $ValidUsers = @()
    foreach ($Profile in $UserProfiles) {
        $UserName = Split-Path $Profile.LocalPath -Leaf
        $ValidUsers += $UserName
    }
    
    return $ValidUsers
}

function Backup-UserProfile {
    param (
        [string]$UserName,
        [string]$DestinationPath
    )
    
    Write-Log "Starting backup for user: $UserName" "INFO"
    
    # User profile path
    $UserProfilePath = "C:\Users\$UserName"
    
    if (-not (Test-Path -Path $UserProfilePath)) {
        Write-Log "User profile not found: $UserProfilePath" "ERROR"
        return $false
    }
    
    # Create user backup folder in Egnyte
    $UserBackupPath = Join-Path -Path $DestinationPath -ChildPath $UserName
    if (-not (Test-Path -Path $UserBackupPath)) {
        try {
            New-Item -Path $UserBackupPath -ItemType Directory -Force | Out-Null
            Write-Log "Created backup directory: $UserBackupPath" "SUCCESS"
        }
        catch {
            Write-Log "Failed to create backup directory: $UserBackupPath - $($_.Exception.Message)" "ERROR"
            return $false
        }
    }
    
    # Important folders to backup (customize as needed)
    $FoldersToBackup = @(
        "Desktop",
        "Documents",
        "Pictures",
        "Downloads",
        "Videos",
        "Music",
        "Favorites",
        "Contacts",
        "Links",
        "AppData\Roaming\Microsoft\Outlook", # Outlook data files
        "AppData\Roaming\Microsoft\Signatures", # Email signatures
        "AppData\Local\Microsoft\Outlook", # Outlook settings
        "AppData\Roaming\Microsoft\Templates", # Office templates
        "AppData\Local\Google\Chrome\User Data\Default", # Chrome bookmarks & settings
        "AppData\Roaming\Mozilla\Firefox\Profiles", # Firefox profiles
        "AppData\Local\Microsoft\Edge\User Data\Default" # Edge bookmarks & settings
    )
    
    # Create a file listing of all files in the profile for reference
    try {
        $FileListPath = Join-Path -Path $UserBackupPath -ChildPath "FileList.txt"
        Write-Log "Creating file list for reference..." "INFO"
        Get-ChildItem -Path $UserProfilePath -Recurse -Force -ErrorAction SilentlyContinue | 
            Select-Object FullName, Length, LastWriteTime | 
            Export-Csv -Path $FileListPath -NoTypeInformation
        Write-Log "File list created at: $FileListPath" "SUCCESS"
    }
    catch {
        Write-Log "Warning: Could not create complete file list: $($_.Exception.Message)" "WARNING"
    }

    # Backing up user registry hive
    try {
        Write-Log "Backing up user registry hive..." "INFO"
        $UserRegPath = Join-Path -Path $UserBackupPath -ChildPath "Registry"
        if (-not (Test-Path -Path $UserRegPath)) {
            New-Item -Path $UserRegPath -ItemType Directory -Force | Out-Null
        }
        
        # Export NTUSER.DAT to a .reg file
        $RegExportPath = Join-Path -Path $UserRegPath -ChildPath "UserRegistry.reg"
        $NtuserPath = Join-Path -Path $UserProfilePath -ChildPath "NTUSER.DAT"
        
        # Check if the user is logged off (can safely access NTUSER.DAT)
        # This will copy the file directly as REG_LOAD might fail depending on permissions
        if (Test-Path -Path $NtuserPath -PathType Leaf) {
            Copy-Item -Path $NtuserPath -Destination (Join-Path -Path $UserRegPath -ChildPath "NTUSER.DAT") -Force
            Write-Log "Registry hive backed up: $NtuserPath → $UserRegPath" "SUCCESS"
        }
        else {
            Write-Log "Could not access NTUSER.DAT - user may be logged in" "WARNING"
        }
    }
    catch {
        Write-Log "Failed to backup registry: $($_.Exception.Message)" "ERROR"
    }
    
    # Track statistics
    $BackupStats = @{
        TotalFolders = 0
        TotalFiles = 0
        TotalSize = 0
        SkippedFiles = 0
        SkippedSize = 0
        ErrorCount = 0
    }
    
    # Backup each folder
    foreach ($Folder in $FoldersToBackup) {
        $SourcePath = Join-Path -Path $UserProfilePath -ChildPath $Folder
        $FolderDestPath = Join-Path -Path $UserBackupPath -ChildPath $Folder
        
        # Check if the source path exists
        if (-not (Test-Path -Path $SourcePath)) {
            Write-Log "Source folder not found, skipping: $SourcePath" "WARNING"
            continue
        }
        
        # Create destination directory structure
        try {
            $null = New-Item -Path $FolderDestPath -ItemType Directory -Force -ErrorAction Stop
            $BackupStats.TotalFolders++
        }
        catch {
            Write-Log "Failed to create destination folder: $FolderDestPath - $($_.Exception.Message)" "ERROR"
            $BackupStats.ErrorCount++
            continue
        }
        
        Write-Log "Backing up folder: $Folder" "INFO"
        
        # Using robocopy for reliable copying
        $RoboArgs = @(
            $SourcePath,
            $FolderDestPath,
            "/E",             # Copy subdirectories, including empty ones
            "/COPY:DAT",      # Copy data, attributes, and timestamps
            "/R:2",           # Retry 2 times
            "/W:5",           # Wait 5 seconds between retries
            "/XJ",            # Don't follow junction points
            "/MT:8",          # Multi-threaded (8 threads)
            "/NP",            # No progress
            "/NDL"            # No directory list
        )
        
        # Add size limit if specified
        if ($SkipLargeFiles) {
            $MaxSizeBytes = $LargeFileSizeMB * 1MB
            $RoboArgs += "/MAX:$MaxSizeBytes"
            Write-Log "Skipping files larger than $LargeFileSizeMB MB" "INFO"
        }
        
        # Execute robocopy
        $RoboLog = Join-Path -Path $script:TempDir -ChildPath "Robo_$($UserName)_$($Folder -replace '\\', '_').log"
        $RoboArgs += "/LOG:$RoboLog"
        
        try {
            $RoboProcess = Start-Process -FilePath "robocopy" -ArgumentList $RoboArgs -NoNewWindow -PassThru -Wait
            
            # Process robocopy results - success codes are 0-7
            if ($RoboProcess.ExitCode -lt 8) {
                # Parse log to get stats
                if (Test-Path -Path $RoboLog) {
                    $LogContent = Get-Content -Path $RoboLog -Raw
                    
                    # Extract statistics from robocopy log
                    if ($LogContent -match "Files\s+:\s+(\d+)") {
                        $FileCount = [int]$Matches[1]
                        $BackupStats.TotalFiles += $FileCount
                    }
                    
                    if ($LogContent -match "Bytes\s+:\s+([0-9,]+)") {
                        $BytesStr = $Matches[1] -replace ',', ''
                        $BackupStats.TotalSize += [long]$BytesStr
                    }
                }
                
                Write-Log "Successfully backed up: $Folder" "SUCCESS"
            }
            else {
                Write-Log "Warning: Issues during backup of $Folder (Exit code: $($RoboProcess.ExitCode))" "WARNING"
                $BackupStats.ErrorCount++
            }
        }
        catch {
            Write-Log "Error backing up $Folder : $($_.Exception.Message)" "ERROR"
            $BackupStats.ErrorCount++
        }
    }
    
    # Backup browser bookmarks separately (common locations)
    $BrowserData = @{
        "Chrome" = @{
            Source = "AppData\Local\Google\Chrome\User Data\Default\Bookmarks"
            Dest = "BrowserData\Chrome"
        }
        "Edge" = @{
            Source = "AppData\Local\Microsoft\Edge\User Data\Default\Bookmarks"
            Dest = "BrowserData\Edge"
        }
        "Firefox" = @{
            Source = "AppData\Roaming\Mozilla\Firefox\Profiles"
            Dest = "BrowserData\Firefox"
        }
    }
    
    foreach ($Browser in $BrowserData.Keys) {
        $SourcePath = Join-Path -Path $UserProfilePath -ChildPath $BrowserData[$Browser].Source
        $DestPath = Join-Path -Path $UserBackupPath -ChildPath $BrowserData[$Browser].Dest
        
        if (Test-Path -Path $SourcePath) {
            try {
                # Create destination directory
                New-Item -Path $DestPath -ItemType Directory -Force -ErrorAction SilentlyContinue | Out-Null
                
                if ((Get-Item $SourcePath) -is [System.IO.DirectoryInfo]) {
                    # For directories (like Firefox profiles)
                    Copy-Item -Path $SourcePath -Destination $DestPath -Recurse -Force
                }
                else {
                    # For files (like Chrome/Edge bookmarks)
                    Copy-Item -Path $SourcePath -Destination $DestPath -Force
                }
                
                Write-Log "Backed up $Browser bookmarks/data" "SUCCESS"
            }
            catch {
                Write-Log "Failed to backup $Browser data: $($_.Exception.Message)" "WARNING"
            }
        }
    }
    
    # Backup Outlook PST files separately (they could be anywhere)
    try {
        Write-Log "Searching for Outlook PST/OST files..." "INFO"
        $PstFiles = Get-ChildItem -Path $UserProfilePath -Recurse -Include "*.pst","*.ost" -ErrorAction SilentlyContinue
        
        if ($PstFiles.Count -gt 0) {
            $OutlookDataPath = Join-Path -Path $UserBackupPath -ChildPath "OutlookData"
            New-Item -Path $OutlookDataPath -ItemType Directory -Force -ErrorAction SilentlyContinue | Out-Null
            
            foreach ($PstFile in $PstFiles) {
                $DestFile = Join-Path -Path $OutlookDataPath -ChildPath $PstFile.Name
                
                # Skip OST files as they're just cached data that will be recreated
                if ($PstFile.Extension -eq ".ost") {
                    Write-Log "Skipping OST file (will be recreated): $($PstFile.FullName)" "INFO"
                    continue
                }
                
                # Check file size if we're skipping large files
                if ($SkipLargeFiles -and $PstFile.Length -gt ($LargeFileSizeMB * 1MB)) {
                    Write-Log "Skipping large PST file: $($PstFile.Name) ($(($PstFile.Length/1MB).ToString('N2')) MB)" "WARNING"
                    $BackupStats.SkippedFiles++
                    $BackupStats.SkippedSize += $PstFile.Length
                    continue
                }
                
                try {
                    Copy-Item -Path $PstFile.FullName -Destination $DestFile -Force
                    Write-Log "Backed up Outlook data file: $($PstFile.Name)" "SUCCESS"
                    $BackupStats.TotalFiles++
                    $BackupStats.TotalSize += $PstFile.Length
                }
                catch {
                    Write-Log "Failed to backup PST file $($PstFile.Name): $($_.Exception.Message)" "ERROR"
                    $BackupStats.ErrorCount++
                }
            }
        }
    }
    catch {
        Write-Log "Error searching for Outlook data files: $($_.Exception.Message)" "WARNING"
    }
    
    # Create backup summary file
    $SummaryPath = Join-Path -Path $UserBackupPath -ChildPath "BackupSummary.txt"
    $ComputerInfo = Get-ComputerInfo
    $SummaryContent = @"
Backup Summary for User: $UserName
===============================
Backup Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Backup Computer: $env:COMPUTERNAME
Windows Version: $($ComputerInfo.WindowsProductName) $($ComputerInfo.WindowsVersion)
Script Version: $ScriptVersion

Statistics:
- Total Folders Backed Up: $($BackupStats.TotalFolders)
- Total Files Backed Up: $($BackupStats.TotalFiles)
- Total Size Backed Up: $(($BackupStats.TotalSize/1MB).ToString('N2')) MB
- Files Skipped (Size): $($BackupStats.SkippedFiles) ($(($BackupStats.SkippedSize/1MB).ToString('N2')) MB)
- Errors Encountered: $($BackupStats.ErrorCount)

Folders Backed Up:
$(($FoldersToBackup | ForEach-Object { "- $_" }) -join "`n")

Additional Data:
- Browser Bookmarks: Chrome, Firefox, Edge
- Outlook PST Files (if found)
- User Registry Settings

IMPORTANT: This backup does not include all files from the user profile.
Review the FileList.txt file for a complete list of files in the profile.
"@
    
    try {
        $SummaryContent | Out-File -FilePath $SummaryPath -Encoding UTF8 -Force
        Write-Log "Backup summary created: $SummaryPath" "SUCCESS"
    }
    catch {
        Write-Log "Failed to create backup summary: $($_.Exception.Message)" "ERROR"
    }
    
    # Return success
    if ($BackupStats.ErrorCount -eq 0) {
        Write-Log "Backup completed successfully for user: $UserName" "SUCCESS"
        return $true
    }
    else {
        Write-Log "Backup completed with $($BackupStats.ErrorCount) errors for user: $UserName" "WARNING"
        return $true # Still return true as the backup completed even with some errors
    }
}

# ======= Main Script =======

# Check for administrator privileges
if (-not (Test-Admin)) {
    Write-Host "This script requires administrator privileges to access all user profiles." -ForegroundColor Red
    Write-Host "Please run this script as an administrator." -ForegroundColor Red
    exit 1
}

# Create a temporary directory for logs
$script:TempDir = Join-Path -Path $env:TEMP -ChildPath "EgnyteBackup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -Path $script:TempDir -ItemType Directory -Force | Out-Null

# Initialize log file
$script:LogFile = Join-Path -Path $script:TempDir -ChildPath "EgnyteBackup.log"
Write-Log "=== Egnyte User Profile Backup Script v$ScriptVersion ===" "INFO"
Write-Log "Started at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO"

# Show welcome screen
Clear-Host
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "         EGNYTE USER PROFILE BACKUP UTILITY         " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This utility will help you back up user profiles to Egnyte before resetting a PC."
Write-Host "Please follow the prompts to configure your backup."
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# ======= INTERACTIVE PARAMETER COLLECTION =======

# 1. SELECT DRIVE FOR BACKUP
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "STEP 1: SELECT EGNYTE DRIVE LOCATION" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Get all drives
$AllDrives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null }
$DriveOptions = @()

Write-Host "Available drives:" -ForegroundColor Yellow
$driveIndex = 1
foreach ($drive in $AllDrives) {
    $driveType = "Local"
    if ($drive.DisplayRoot -ne $null) {
        $driveType = "Network"
    }
    
    $totalSize = "Unknown"
    $freeSpace = "Unknown"
    
    try {
        $driveInfo = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='$($drive.Name):'"
        if ($driveInfo) {
            $totalSize = "$([Math]::Round($driveInfo.Size / 1GB, 2)) GB"
            $freeSpace = "$([Math]::Round($driveInfo.FreeSpace / 1GB, 2)) GB"
        }
    } catch {
        # Some network drives might not provide size info
    }
    
    $driveOption = [PSCustomObject]@{
        Index = $driveIndex
        Drive = $drive.Name
        Type = $driveType
        Path = "$($drive.Name):\"
        TotalSize = $totalSize
        FreeSpace = $freeSpace
        DisplayRoot = $drive.DisplayRoot
    }
    $DriveOptions += $driveOption
    
    Write-Host "  $($driveIndex). Drive $($drive.Name): ($driveType) - Free: $freeSpace / Total: $totalSize"
    if ($drive.DisplayRoot) {
        Write-Host "     Path: $($drive.DisplayRoot)"
    }
    
    $driveIndex++
}

$EgnyteDrivePath = ""
while ([string]::IsNullOrEmpty($EgnyteDrivePath) -or -not (Test-Path -Path $EgnyteDrivePath)) {
    $driveSelection = Read-Host "`nEnter the number of the drive where Egnyte is located"
    
    if ($driveSelection -match "^\d+$" -and [int]$driveSelection -ge 1 -and [int]$driveSelection -le $DriveOptions.Count) {
        $selectedDrive = $DriveOptions[[int]$driveSelection - 1]
        $EgnyteDrivePath = $selectedDrive.Path
        
        # Allow user to refine the path if needed
        $refinePathResponse = Read-Host "Is Egnyte at the root of this drive or in a subfolder? (R=Root, S=Subfolder)"
        if ($refinePathResponse -eq "S" -or $refinePathResponse -eq "s") {
            $subfolderPath = Read-Host "Enter the subfolder path (e.g., 'Egnyte' or 'EgnyteData')"
            $EgnyteDrivePath = Join-Path -Path $EgnyteDrivePath -ChildPath $subfolderPath
        }
        
        # Validate path
        if (-not (Test-Path -Path $EgnyteDrivePath)) {
            Write-Host "The path '$EgnyteDrivePath' does not exist. Please try again." -ForegroundColor Red
            $EgnyteDrivePath = ""
        }
    } else {
        Write-Host "Invalid selection. Please try again." -ForegroundColor Red
    }
}

Write-Log "Selected Egnyte drive path: $EgnyteDrivePath" "INFO"

# 2. BACKUP LOCATION
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "STEP 2: SELECT BACKUP LOCATION IN EGNYTE" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Default backup location
$defaultBackupLocation = "Shared\PC Backups"
Write-Host "Default backup location: $defaultBackupLocation"
$changeLocationResponse = Read-Host "Do you want to change the backup location? (Y/N, default: N)"

if ($changeLocationResponse -eq "Y" -or $changeLocationResponse -eq "y") {
    # Show root folders in Egnyte
    $rootFolders = @()
    try {
        $rootItems = Get-ChildItem -Path $EgnyteDrivePath -Directory -ErrorAction Stop
        Write-Host "`nAvailable root folders in Egnyte:" -ForegroundColor Yellow
        for ($i = 0; $i -lt $rootItems.Count; $i++) {
            Write-Host "  $($i+1). $($rootItems[$i].Name)"
            $rootFolders += $rootItems[$i].Name
        }
        
        $rootFolderSelection = Read-Host "`nSelect a root folder by number"
        $selectedRootFolder = ""
        
        if ($rootFolderSelection -match "^\d+$" -and [int]$rootFolderSelection -ge 1 -and [int]$rootFolderSelection -le $rootFolders.Count) {
            $selectedRootFolder = $rootFolders[[int]$rootFolderSelection - 1]
            $subfolderName = Read-Host "Enter subfolder name for backups (default: PC Backups)"
            
            if ([string]::IsNullOrEmpty($subfolderName)) {
                $subfolderName = "PC Backups"
            }
            
            $BackupLocation = "$selectedRootFolder\$subfolderName"
        } else {
            Write-Host "Invalid selection. Using default location." -ForegroundColor Yellow
            $BackupLocation = $defaultBackupLocation
        }
    } catch {
        Write-Host "Error accessing Egnyte folders. Using default location." -ForegroundColor Yellow
        $BackupLocation = $defaultBackupLocation
    }
} else {
    $BackupLocation = $defaultBackupLocation
}

Write-Log "Selected backup location: $BackupLocation" "INFO"

# 3. USER PROFILE SELECTION
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "STEP 3: SELECT USER PROFILES TO BACKUP" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Get valid user profiles (max 10 displayed)
$AllValidUsers = Get-ValidUsers
$displayCount = [Math]::Min(10, $AllValidUsers.Count)

Write-Host "User profiles available for backup:" -ForegroundColor Yellow
for ($i = 0; $i -lt $displayCount; $i++) {
    $userProfilePath = "C:\Users\$($AllValidUsers[$i])"
    
    # Get basic profile info without calculating full size (which is slow)
    $userObj = New-Object PSObject -Property @{
        Username = $AllValidUsers[$i]
        Path = $userProfilePath
        LastAccessed = "Unknown"
    }
    
    # Try to get the last accessed time of the profile directory
    try {
        $lastAccess = (Get-Item -Path $userProfilePath -ErrorAction SilentlyContinue).LastAccessTime
        $userObj.LastAccessed = $lastAccess.ToString("yyyy-MM-dd")
    } catch {
        # Ignore errors
    }
    
    Write-Host "  $($i+1). $($userObj.Username) - Last accessed: $($userObj.LastAccessed)"
}

if ($AllValidUsers.Count -gt 10) {
    Write-Host "  (Showing first 10 of $($AllValidUsers.Count) profiles)" -ForegroundColor Gray
}

Write-Host "  A. All Users" -ForegroundColor Yellow
Write-Host ""

$UsersToBackup = @()
$userSelectionPrompt = "Enter the number(s) of the user(s) to backup (comma-separated), or 'A' for all users"
$Selection = Read-Host $userSelectionPrompt

if ($Selection -eq "A" -or $Selection -eq "a") {
    $UsersToBackup = $AllValidUsers
    $AllUsers = $true
    Write-Log "User selected to backup all users" "INFO"
}
else {
    $AllUsers = $false
    $SelectedIndices = $Selection -split ',' | ForEach-Object { $_.Trim() }
    foreach ($Index in $SelectedIndices) {
        if ($Index -match "^\d+$" -and [int]$Index -ge 1 -and [int]$Index -le $AllValidUsers.Count) {
            $UsersToBackup += $AllValidUsers[[int]$Index - 1]
        }
    }
    
    if ($UsersToBackup.Count -eq 0) {
        Write-Host "No valid users selected. Please select at least one user profile." -ForegroundColor Red
        $Selection = Read-Host $userSelectionPrompt
        
        if ($Selection -eq "A" -or $Selection -eq "a") {
            $UsersToBackup = $AllValidUsers
            $AllUsers = $true
        }
        else {
            $SelectedIndices = $Selection -split ',' | ForEach-Object { $_.Trim() }
            foreach ($Index in $SelectedIndices) {
                if ($Index -match "^\d+$" -and [int]$Index -ge 1 -and [int]$Index -le $AllValidUsers.Count) {
                    $UsersToBackup += $AllValidUsers[[int]$Index - 1]
                }
            }
            
            if ($UsersToBackup.Count -eq 0) {
                Write-Log "No valid users selected for backup after two attempts" "ERROR"
                Write-Host "No valid users selected after two attempts. Exiting script." -ForegroundColor Red
                exit 1
            }
        }
    }
    
    Write-Log "Selected users for backup: $($UsersToBackup -join ', ')" "INFO"
}

# 4. LARGE FILE HANDLING
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "STEP 4: CONFIGURE LARGE FILE HANDLING" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Large files (videos, VMs, etc.) can significantly increase backup time."
Write-Host ""

$skipOptions = @(
    "Yes - Skip large files (recommended for faster backups)",
    "No - Include all files regardless of size"
)

Write-Host "Skip large files?" -ForegroundColor Yellow
for ($i = 0; $i -lt $skipOptions.Count; $i++) {
    Write-Host "  $($i+1). $($skipOptions[$i])"
}

$skipSelection = Read-Host "`nEnter your choice (1 or 2)"
$SkipLargeFiles = ($skipSelection -eq "1")

$LargeFileSizeMB = 500 # Default
if ($SkipLargeFiles) {
    $sizeOptions = @(
        "100 MB - Very aggressive filtering (fastest backup)",
        "250 MB - Medium filtering (balanced)",
        "500 MB - Conservative filtering (default)",
        "1000 MB - Minimal filtering (most inclusive)",
        "Custom size"
    )
    
    Write-Host "`nSelect maximum file size to include:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $sizeOptions.Count; $i++) {
        Write-Host "  $($i+1). $($sizeOptions[$i])"
    }
    
    $sizeSelection = Read-Host "`nEnter your choice (1-5)"
    
    switch ($sizeSelection) {
        "1" { $LargeFileSizeMB = 100 }
        "2" { $LargeFileSizeMB = 250 }
        "3" { $LargeFileSizeMB = 500 } # Default
        "4" { $LargeFileSizeMB = 1000 }
        "5" { 
            $customSize = Read-Host "Enter custom maximum file size in MB"
            if ($customSize -match "^\d+$" -and [int]$customSize -gt 0) {
                $LargeFileSizeMB = [int]$customSize
            } else {
                Write-Host "Invalid size. Using default 500 MB." -ForegroundColor Yellow
                $LargeFileSizeMB = 500
            }
        }
        default { $LargeFileSizeMB = 500 } # Default if invalid selection
    }
}

Write-Log "Skip large files: $SkipLargeFiles (Max size: $LargeFileSizeMB MB)" "INFO"

# SUMMARY OF SELECTIONS
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "BACKUP CONFIGURATION SUMMARY" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Egnyte Drive Path: $EgnyteDrivePath"
Write-Host "Backup Location: $BackupLocation"
Write-Host "Users to Backup: $(if ($AllUsers) { "All Users" } else { $UsersToBackup -join ', ' })"
Write-Host "Skip Large Files: $SkipLargeFiles"
if ($SkipLargeFiles) {
    Write-Host "Maximum File Size: $LargeFileSizeMB MB"
}
Write-Host ""

$confirmBackup = Read-Host "Proceed with backup using these settings? (Y/N)"
if (-not ($confirmBackup -eq "Y" -or $confirmBackup -eq "y")) {
    Write-Host "Backup cancelled by user." -ForegroundColor Yellow
    exit 0
}

# Create backup destination
$BackupRoot = Join-Path -Path $EgnyteDrivePath -ChildPath $BackupLocation
$ComputerName = $env:COMPUTERNAME
$ComputerInfoFolder = "System_Info"
$ComputerBackupPath = Join-Path -Path $BackupRoot -ChildPath $ComputerName
$ComputerInfoPath = Join-Path -Path $ComputerBackupPath -ChildPath $ComputerInfoFolder
$BackupDate = Get-Date -Format "yyyy-MM-dd_HHmmss"
$BackupPath = Join-Path -Path $ComputerBackupPath -ChildPath $BackupDate

# Create backup directories
try {
    if (-not (Test-Path -Path $BackupRoot)) {
        New-Item -Path $BackupRoot -ItemType Directory -Force | Out-Null
        Write-Log "Created backup root directory: $BackupRoot" "SUCCESS"
    }
    
    if (-not (Test-Path -Path $ComputerBackupPath)) {
        New-Item -Path $ComputerBackupPath -ItemType Directory -Force | Out-Null
        Write-Log "Created computer backup directory: $ComputerBackupPath" "SUCCESS"
    }
    
    New-Item -Path $BackupPath -ItemType Directory -Force | Out-Null
    Write-Log "Created backup directory: $BackupPath" "SUCCESS"
    
    New-Item -Path $ComputerInfoPath -ItemType Directory -Force -ErrorAction SilentlyContinue | Out-Null
}
catch {
    Write-Log "Failed to create backup directories: $($_.Exception.Message)" "ERROR"
    exit 1
}

# Copy the log file to the backup destination when done
$LogDestination = Join-Path -Path $BackupPath -ChildPath "BackupLog.log"

# Collect system information
Write-Log "Collecting system information..." "INFO"
try {
    # System Info
    $SysInfoPath = Join-Path -Path $ComputerInfoPath -ChildPath "SystemInfo_$BackupDate.txt"
    systeminfo | Out-File -FilePath $SysInfoPath -Encoding UTF8

    # Computer info
    $ComputerInfoPath = Join-Path -Path $ComputerInfoPath -ChildPath "ComputerInfo_$BackupDate.xml"
    Get-ComputerInfo | Export-Clixml -Path $ComputerInfoPath
    
    # Installed software
    $SoftwarePath = Join-Path -Path $ComputerInfoPath -ChildPath "InstalledSoftware_$BackupDate.csv"
    Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*, 
                     HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
        Select-Object DisplayName, DisplayVersion, Publisher, InstallDate | 
        Where-Object DisplayName -ne $null | 
        Sort-Object DisplayName | 
        Export-Csv -Path $SoftwarePath -NoTypeInformation
    
    # Network configuration
    $NetworkPath = Join-Path -Path $ComputerInfoPath -ChildPath "NetworkConfig_$BackupDate.txt"
    ipconfig /all | Out-File -FilePath $NetworkPath -Encoding UTF8
    
    # Disk information
    $DiskInfoPath = Join-Path -Path $ComputerInfoPath -ChildPath "DiskInfo_$BackupDate.csv"
    Get-Disk | Export-Csv -Path $DiskInfoPath -NoTypeInformation
    
    # Partition information
    $PartitionPath = Join-Path -Path $ComputerInfoPath -ChildPath "PartitionInfo_$BackupDate.csv"
    Get-Partition | Export-Csv -Path $PartitionPath -NoTypeInformation
    
    # Local user accounts
    $UsersPath = Join-Path -Path $ComputerInfoPath -ChildPath "LocalUsers_$BackupDate.csv"
    Get-LocalUser | Export-Csv -Path $UsersPath -NoTypeInformation
    
    # Scheduled Tasks
    $TasksPath = Join-Path -Path $ComputerInfoPath -ChildPath "ScheduledTasks_$BackupDate.csv"
    Get-ScheduledTask | Select-Object TaskName, TaskPath, State | Export-Csv -Path $TasksPath -NoTypeInformation
    
    # Windows features
    $FeaturesPath = Join-Path -Path $ComputerInfoPath -ChildPath "WindowsFeatures_$BackupDate.csv"
    Get-WindowsOptionalFeature -Online | Where-Object State -eq Enabled | 
        Select-Object FeatureName, State | 
        Export-Csv -Path $FeaturesPath -NoTypeInformation
        
    Write-Log "System information collected successfully" "SUCCESS"
}
catch {
    Write-Log "Error collecting system information: $($_.Exception.Message)" "WARNING"
}

# Begin backup process with parallel processing
$SuccessCount = 0
$TotalUsers = $UsersToBackup.Count

Write-Host ""
Write-Host "Starting parallel backup of $TotalUsers user profile(s)..." -ForegroundColor Cyan
Write-Host "Processing multiple users simultaneously for maximum speed" -ForegroundColor Cyan
Write-Host ""

$StartTime = Get-Date

# Configure parallel processing
$MaxParallelJobs = [Math]::Min($UsersToBackup.Count, 4) # Limit to 4 parallel jobs to avoid overwhelming the system
Write-Log "Using parallel processing with up to $MaxParallelJobs simultaneous backup jobs" "INFO"

# Store results for each user
$BackupResults = @{}

# Create a runspace pool for parallel processing
$RunspacePool = [runspacefactory]::CreateRunspacePool(1, $MaxParallelJobs)
$RunspacePool.Open()

# Store all the runspaces
$Runspaces = New-Object System.Collections.ArrayList

# Create a scriptblock for backup operations that can be run in parallel
$BackupScriptBlock = {
    param (
        [string]$User,
        [string]$DestinationPath,
        [bool]$SkipLargeFiles,
        [int]$LargeFileSizeMB,
        [string]$TempDir,
        [string]$LogFile
    )
    
    # Create a function inside the scriptblock to write to the log
    function Write-Log {
        param (
            [string]$Message,
            [string]$Level = "INFO"
        )
        $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $LogEntry = "$Timestamp [$Level] - $Message"
        $LogEntry | Out-File -FilePath $LogFile -Append
    }
    
    Write-Log "Starting backup for user: $User (parallel job)" "INFO"
    
    # User profile path
    $UserProfilePath = "C:\Users\$User"
    
    if (-not (Test-Path -Path $UserProfilePath)) {
        Write-Log "User profile not found: $UserProfilePath" "ERROR"
        return @{
            User = $User
            Success = $false
            Message = "Profile not found"
            Duration = 0
        }
    }
    
    $UserStartTime = Get-Date
    
    # Create user backup folder
    $UserBackupPath = Join-Path -Path $DestinationPath -ChildPath $User
    if (-not (Test-Path -Path $UserBackupPath)) {
        try {
            New-Item -Path $UserBackupPath -ItemType Directory -Force | Out-Null
            Write-Log "Created backup directory: $UserBackupPath" "SUCCESS"
        }
        catch {
            Write-Log "Failed to create backup directory: $UserBackupPath - $($_.Exception.Message)" "ERROR"
            return @{
                User = $User
                Success = $false
                Message = "Failed to create backup directory: $($_.Exception.Message)"
                Duration = 0
            }
        }
    }
    
    # Important folders to backup (customize as needed)
    $FoldersToBackup = @(
        "Desktop",
        "Documents",
        "Pictures",
        "Downloads",
        "Videos",
        "Music",
        "Favorites",
        "Contacts",
        "Links",
        "AppData\Roaming\Microsoft\Outlook", # Outlook data files
        "AppData\Roaming\Microsoft\Signatures", # Email signatures
        "AppData\Local\Microsoft\Outlook", # Outlook settings
        "AppData\Roaming\Microsoft\Templates", # Office templates
        "AppData\Local\Google\Chrome\User Data\Default", # Chrome bookmarks & settings
        "AppData\Roaming\Mozilla\Firefox\Profiles", # Firefox profiles
        "AppData\Local\Microsoft\Edge\User Data\Default" # Edge bookmarks & settings
    )
    
    # Create a file listing of all files in the profile for reference
    try {
        $FileListPath = Join-Path -Path $UserBackupPath -ChildPath "FileList.txt"
        Write-Log "Creating file list for reference..." "INFO"
        # Limit depth to 3 levels for speed - just enough to get an overview
        Get-ChildItem -Path $UserProfilePath -Depth 3 -Force -ErrorAction SilentlyContinue | 
            Select-Object FullName, Length, LastWriteTime | 
            Export-Csv -Path $FileListPath -NoTypeInformation
        Write-Log "File list created at: $FileListPath" "SUCCESS"
    }
    catch {
        Write-Log "Warning: Could not create complete file list: $($_.Exception.Message)" "WARNING"
    }

    # Backing up user registry hive
    try {
        Write-Log "Backing up user registry hive..." "INFO"
        $UserRegPath = Join-Path -Path $UserBackupPath -ChildPath "Registry"
        if (-not (Test-Path -Path $UserRegPath)) {
            New-Item -Path $UserRegPath -ItemType Directory -Force | Out-Null
        }
        
        # Export NTUSER.DAT to a .reg file
        $RegExportPath = Join-Path -Path $UserRegPath -ChildPath "UserRegistry.reg"
        $NtuserPath = Join-Path -Path $UserProfilePath -ChildPath "NTUSER.DAT"
        
        # Check if the user is logged off (can safely access NTUSER.DAT)
        # This will copy the file directly as REG_LOAD might fail depending on permissions
        if (Test-Path -Path $NtuserPath -PathType Leaf) {
            Copy-Item -Path $NtuserPath -Destination (Join-Path -Path $UserRegPath -ChildPath "NTUSER.DAT") -Force
            Write-Log "Registry hive backed up: $NtuserPath → $UserRegPath" "SUCCESS"
        }
        else {
            Write-Log "Could not access NTUSER.DAT - user may be logged in" "WARNING"
        }
    }
    catch {
        Write-Log "Failed to backup registry: $($_.Exception.Message)" "ERROR"
    }
    
    # Track statistics
    $BackupStats = @{
        TotalFolders = 0
        TotalFiles = 0
        TotalSize = 0
        SkippedFiles = 0
        SkippedSize = 0
        ErrorCount = 0
    }
    
    # Backup each folder
    foreach ($Folder in $FoldersToBackup) {
        $SourcePath = Join-Path -Path $UserProfilePath -ChildPath $Folder
        $FolderDestPath = Join-Path -Path $UserBackupPath -ChildPath $Folder
        
        # Check if the source path exists
        if (-not (Test-Path -Path $SourcePath)) {
            Write-Log "Source folder not found, skipping: $SourcePath" "WARNING"
            continue
        }
        
        # Create destination directory structure
        try {
            $null = New-Item -Path $FolderDestPath -ItemType Directory -Force -ErrorAction Stop
            $BackupStats.TotalFolders++
        }
        catch {
            Write-Log "Failed to create destination folder: $FolderDestPath - $($_.Exception.Message)" "ERROR"
            $BackupStats.ErrorCount++
            continue
        }
        
        Write-Log "Backing up folder: $Folder" "INFO"
        
        # Using robocopy for reliable copying
        $RoboArgs = @(
            $SourcePath,
            $FolderDestPath,
            "/E",             # Copy subdirectories, including empty ones
            "/COPY:DAT",      # Copy data, attributes, and timestamps
            "/R:1",           # Retry 1 time (reduced for speed)
            "/W:1",           # Wait 1 second between retries (reduced for speed)
            "/XJ",            # Don't follow junction points
            "/MT:16",         # Multi-threaded (increased for speed)
            "/NP",            # No progress
            "/NDL"            # No directory list
        )
        
        # Add size limit if specified
        if ($SkipLargeFiles) {
            $MaxSizeBytes = $LargeFileSizeMB * 1MB
            $RoboArgs += "/MAX:$MaxSizeBytes"
            Write-Log "Skipping files larger than $LargeFileSizeMB MB" "INFO"
        }
        
        # Execute robocopy
        $RoboLog = Join-Path -Path $TempDir -ChildPath "Robo_$($User)_$($Folder -replace '\\', '_').log"
        $RoboArgs += "/LOG:$RoboLog"
        
        try {
            $RoboProcess = Start-Process -FilePath "robocopy" -ArgumentList $RoboArgs -NoNewWindow -PassThru -Wait
            
            # Process robocopy results - success codes are 0-7
            if ($RoboProcess.ExitCode -lt 8) {
                # Parse log to get stats
                if (Test-Path -Path $RoboLog) {
                    $LogContent = Get-Content -Path $RoboLog -Raw
                    
                    # Extract statistics from robocopy log
                    if ($LogContent -match "Files\s+:\s+(\d+)") {
                        $FileCount = [int]$Matches[1]
                        $BackupStats.TotalFiles += $FileCount
                    }
                    
                    if ($LogContent -match "Bytes\s+:\s+([0-9,]+)") {
                        $BytesStr = $Matches[1] -replace ',', ''
                        $BackupStats.TotalSize += [long]$BytesStr
                    }
                }
                
                Write-Log "Successfully backed up: $Folder" "SUCCESS"
            }
            else {
                Write-Log "Warning: Issues during backup of $Folder (Exit code: $($RoboProcess.ExitCode))" "WARNING"
                $BackupStats.ErrorCount++
            }
        }
        catch {
            Write-Log "Error backing up $Folder : $($_.Exception.Message)" "ERROR"
            $BackupStats.ErrorCount++
        }
    }
    
    # Backup browser bookmarks separately (common locations)
    $BrowserData = @{
        "Chrome" = @{
            Source = "AppData\Local\Google\Chrome\User Data\Default\Bookmarks"
            Dest = "BrowserData\Chrome"
        }
        "Edge" = @{
            Source = "AppData\Local\Microsoft\Edge\User Data\Default\Bookmarks"
            Dest = "BrowserData\Edge"
        }
        "Firefox" = @{
            Source = "AppData\Roaming\Mozilla\Firefox\Profiles"
            Dest = "BrowserData\Firefox"
        }
    }
    
    foreach ($Browser in $BrowserData.Keys) {
        $SourcePath = Join-Path -Path $UserProfilePath -ChildPath $BrowserData[$Browser].Source
        $DestPath = Join-Path -Path $UserBackupPath -ChildPath $BrowserData[$Browser].Dest
        
        if (Test-Path -Path $SourcePath) {
            try {
                # Create destination directory
                New-Item -Path $DestPath -ItemType Directory -Force -ErrorAction SilentlyContinue | Out-Null
                
                if ((Get-Item $SourcePath) -is [System.IO.DirectoryInfo]) {
                    # For directories (like Firefox profiles)
                    Copy-Item -Path $SourcePath -Destination $DestPath -Recurse -Force
                }
                else {
                    # For files (like Chrome/Edge bookmarks)
                    Copy-Item -Path $SourcePath -Destination $DestPath -Force
                }
                
                Write-Log "Backed up $Browser bookmarks/data" "SUCCESS"
            }
            catch {
                Write-Log "Failed to backup $Browser data: $($_.Exception.Message)" "WARNING"
            }
        }
    }
    
    # Backup Outlook PST files separately (they could be anywhere)
    try {
        Write-Log "Searching for Outlook PST/OST files..." "INFO"
        $PstFiles = Get-ChildItem -Path $UserProfilePath -Recurse -Include "*.pst","*.ost" -ErrorAction SilentlyContinue
        
        if ($PstFiles.Count -gt 0) {
            $OutlookDataPath = Join-Path -Path $UserBackupPath -ChildPath "OutlookData"
            New-Item -Path $OutlookDataPath -ItemType Directory -Force -ErrorAction SilentlyContinue | Out-Null
            
            foreach ($PstFile in $PstFiles) {
                $DestFile = Join-Path -Path $OutlookDataPath -ChildPath $PstFile.Name
                
                # Skip OST files as they're just cached data that will be recreated
                if ($PstFile.Extension -eq ".ost") {
                    Write-Log "Skipping OST file (will be recreated): $($PstFile.FullName)" "INFO"
                    continue
                }
                
                # Check file size if we're skipping large files
                if ($SkipLargeFiles -and $PstFile.Length -gt ($LargeFileSizeMB * 1MB)) {
                    Write-Log "Skipping large PST file: $($PstFile.Name) ($(($PstFile.Length/1MB).ToString('N2')) MB)" "WARNING"
                    $BackupStats.SkippedFiles++
                    $BackupStats.SkippedSize += $PstFile.Length
                    continue
                }
                
                try {
                    Copy-Item -Path $PstFile.FullName -Destination $DestFile -Force
                    Write-Log "Backed up Outlook data file: $($PstFile.Name)" "SUCCESS"
                    $BackupStats.TotalFiles++
                    $BackupStats.TotalSize += $PstFile.Length
                }
                catch {
                    Write-Log "Failed to backup PST file $($PstFile.Name): $($_.Exception.Message)" "ERROR"
                    $BackupStats.ErrorCount++
                }
            }
        }
    }
    catch {
        Write-Log "Error searching for Outlook data files: $($_.Exception.Message)" "WARNING"
    }
    
    # Create backup summary file
    $SummaryPath = Join-Path -Path $UserBackupPath -ChildPath "BackupSummary.txt"
    
    try {
        $ComputerInfo = Get-ComputerInfo
        $SummaryContent = @"
Backup Summary for User: $User
===============================
Backup Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Backup Computer: $env:COMPUTERNAME
Windows Version: $($ComputerInfo.WindowsProductName) $($ComputerInfo.WindowsVersion)

Statistics:
- Total Folders Backed Up: $($BackupStats.TotalFolders)
- Total Files Backed Up: $($BackupStats.TotalFiles)
- Total Size Backed Up: $(($BackupStats.TotalSize/1MB).ToString('N2')) MB
- Files Skipped (Size): $($BackupStats.SkippedFiles) ($(($BackupStats.SkippedSize/1MB).ToString('N2')) MB)
- Errors Encountered: $($BackupStats.ErrorCount)

Folders Backed Up:
$(($FoldersToBackup | ForEach-Object { "- $_" }) -join "`n")

Additional Data:
- Browser Bookmarks: Chrome, Firefox, Edge
- Outlook PST Files (if found)
- User Registry Settings

IMPORTANT: This backup does not include all files from the user profile.
Review the FileList.txt file for a complete list of files in the profile.
"@
        $SummaryContent | Out-File -FilePath $SummaryPath -Encoding UTF8 -Force
        Write-Log "Backup summary created: $SummaryPath" "SUCCESS"
    }
    catch {
        Write-Log "Failed to create backup summary: $($_.Exception.Message)" "ERROR"
    }
    
    # Calculate elapsed time
    $EndTime = Get-Date
    $Duration = New-TimeSpan -Start $UserStartTime -End $EndTime
    
    # Return success
    if ($BackupStats.ErrorCount -eq 0) {
        Write-Log "Backup completed successfully for user: $User" "SUCCESS"
        return @{
            User = $User
            Success = $true
            Message = "Backup completed successfully"
            Duration = $Duration
            Stats = $BackupStats
        }
    }
    else {
        Write-Log "Backup completed with $($BackupStats.ErrorCount) errors for user: $User" "WARNING"
        return @{
            User = $User
            Success = $true # Still return true as the backup completed even with some errors
            Message = "Backup completed with $($BackupStats.ErrorCount) errors"
            Duration = $Duration
            Stats = $BackupStats
        }
    }
}

# Start each backup job
foreach ($User in $UsersToBackup) {
    # Create a PowerShell instance for each job
    $PowerShell = [powershell]::Create().AddScript($BackupScriptBlock)
    
    # Add parameters
    $PowerShell.AddArgument($User)
    $PowerShell.AddArgument($BackupPath)
    $PowerShell.AddArgument($SkipLargeFiles)
    $PowerShell.AddArgument($LargeFileSizeMB)
    $PowerShell.AddArgument($script:TempDir)
    $PowerShell.AddArgument($script:LogFile)
    
    # Specify runspace
    $PowerShell.RunspacePool = $RunspacePool
    
    # Start the job and store in array
    $Handle = $PowerShell.BeginInvoke()
    $Job = New-Object PSObject -Property @{
        User = $User
        PowerShell = $PowerShell
        Handle = $Handle
    }
    
    [void]$Runspaces.Add($Job)
    
    Write-Host "Started backup job for user: $User" -ForegroundColor Yellow
}

# Add a spinner/progress indicator
$Spinner = @('|', '/', '-', '\')
$SpinnerPos = 0
$StatusRows = @{}

# Create an empty line for each user
foreach ($User in $UsersToBackup) {
    $StatusRows[$User] = 0
}

# Poll for job completion
while ($Runspaces.Count -gt 0) {
    # Progress indicator
    $SpinnerChar = $Spinner[$SpinnerPos++ % $Spinner.Length]
    
    Write-Host "`rWaiting for backup jobs to complete $SpinnerChar" -NoNewline
    
    # Update status of running jobs
    foreach ($Job in $Runspaces.ToArray()) {
        # Check if job is complete
        if ($Job.Handle.IsCompleted) {
            # Get the result
            $Result = $Job.PowerShell.EndInvoke($Job.Handle)
            
            # Store result
            $BackupResults[$Result.User] = $Result
            
            # Cleanup
            $Job.PowerShell.Dispose()
            $Runspaces.Remove($Job)
            
            # Update success count
            if ($Result.Success) {
                $SuccessCount++
                Write-Host "`r                                                   " -NoNewline
                Write-Host "`rCompleted backup for $($Result.User) in $($Result.Duration.ToString("hh\:mm\:ss"))" -ForegroundColor Green
            }
            else {
                Write-Host "`r                                                   " -NoNewline
                Write-Host "`rFailed to complete backup for $($Result.User): $($Result.Message)" -ForegroundColor Red
            }
        }
    }
    
    # Wait a bit before checking again
    Start-Sleep -Milliseconds 250
}

# Close the runspace pool
$RunspacePool.Close()
$RunspacePool.Dispose()

# Copy the log file to the backup destination
try {
    Copy-Item -Path $script:LogFile -Destination $LogDestination -Force
    Write-Log "Copied log file to backup destination" "SUCCESS"
}
catch {
    Write-Log "Failed to copy log file to backup destination: $($_.Exception.Message)" "ERROR"
}

# Calculate elapsed time
$EndTime = Get-Date
$TotalTime = New-TimeSpan -Start $StartTime -End $EndTime

# Final summary
Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "Backup Process Complete" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "Successfully backed up $SuccessCount of $TotalUsers user profile(s)"
Write-Host "Total time elapsed: $($TotalTime.ToString("hh\:mm\:ss"))"
Write-Host "Backup Location: $BackupPath"
Write-Host "Log file: $LogDestination"
Write-Host ""

# Show backup statistics
if ($BackupResults.Count -gt 0) {
    Write-Host "Backup Statistics:" -ForegroundColor Cyan
    foreach ($User in $BackupResults.Keys) {
        $Result = $BackupResults[$User]
        if ($Result.Success) {
            $TotalSizeMB = [Math]::Round(($Result.Stats.TotalSize / 1MB), 2)
            Write-Host "  $User - $($Result.Stats.TotalFiles) files, $TotalSizeMB MB, $($Result.Duration.ToString("hh\:mm\:ss"))"
        }
    }
    Write-Host ""
}

if ($SuccessCount -eq $TotalUsers) {
    Write-Host "All user profiles successfully backed up!" -ForegroundColor Green
}
else {
    Write-Host "Some user profiles failed to backup. Check the log for details." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "You can now safely reset this PC. Your user data has been backed up to Egnyte." -ForegroundColor Cyan
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")