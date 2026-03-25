@echo off
set "ISO_PATH=%~1"
set "USB_DRIVE=%~2:"

echo Mounting ISO: %ISO_PATH%

:: Mount the ISO and capture the assigned virtual drive letter
for /f "tokens=*" %%a in ('powershell -Command "(Mount-DiskImage -ImagePath '%ISO_PATH%' -PassThru | Get-Volume).DriveLetter"') do set "ISO_DRIVE=%%a:"

if "%ISO_DRIVE%:"==":" (
    echo Error: Failed to mount the ISO.
    exit /b 1
)

echo ISO successfully mounted at %ISO_DRIVE%
echo Copying files to target USB (%USB_DRIVE%)...

:: Run Robocopy.
:: /MIR mirrors the directory structure. /MT:16 uses 16 threads for speed.
:: /NDL /NFL /NJH /NJS suppresses the spammy output so it looks clean in the terminal.
robocopy %ISO_DRIVE%\ %USB_DRIVE%\ /MIR /MT:16 /R:3 /W:3 /NDL /NFL /NJH /NJS

echo Unmounting ISO...
powershell -Command "Dismount-DiskImage -ImagePath '%ISO_PATH%' | Out-Null"

echo Burn Process Complete!
exit /b 0