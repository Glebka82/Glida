@echo off
set "ISO_PATH=C:\work\Glida\pic.iso"
set "USB_DRIVE=E:"

echo --- Mounting ISO ---
:: Use PowerShell to mount the ISO and get its drive letter
for /f "tokens=*" %%a in ('powershell -Command "(Mount-DiskImage -ImagePath '%ISO_PATH%' -PassThru | Get-Volume).DriveLetter"') do set "ISO_DRIVE=%%a:"

if "%ISO_DRIVE%:"==":" (
    echo Error: Failed to mount ISO.
    pause
    exit /b
)

echo ISO mounted at %ISO_DRIVE%
echo --- Copying Files to %USB_DRIVE% ---

:: Robocopy is the best tool for "burning" file-level ISOs
robocopy %ISO_DRIVE%\ %USB_DRIVE%\ /MIR /MT:16 /R:5 /W:5

echo --- Unmounting ISO ---
powershell -Command "Dismount-DiskImage -ImagePath '%ISO_PATH%'"

echo Done! Your disk is ready.
pause