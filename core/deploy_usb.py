import json
import subprocess
import os
import time

import subprocess
import json

import subprocess
import json


def get_usb_info_by_label(target_label):
    print(f"Searching for USB with label: '{target_label}'...")

    # 1. Force UTF-8 so Cyrillic names like 'USB-дисковод' don't get erased
    # 2. Explicitly use 'FileSystemLabel'
    ps_cmd = """
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
    $volumes = Get-Volume | Where-Object { $_.DriveLetter -ne $null };
    $output = @();
    foreach ($vol in $volumes) {
        $part = Get-Partition -DriveLetter $vol.DriveLetter -ErrorAction SilentlyContinue;
        $output += [PSCustomObject]@{
            Label = $vol.FileSystemLabel;
            DriveLetter = $vol.DriveLetter;
            DiskNum = $part.DiskNumber
        }
    };
    $output | ConvertTo-Json -Compress
    """

    try:
        # We MUST tell Python to read the output as utf-8
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            encoding="utf-8",
            check=True
        )

        if not result.stdout.strip():
            print("No volumes found.")
            return None, None

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        for entry in data:
            current_label = entry.get("Label")

            # --- DEBUG LINE: Shows you exactly what Windows sees ---
            print(f"Debug -> Drive {entry.get('DriveLetter')}: has Label: '{current_label}'")

            if current_label and current_label.strip().upper() == target_label.strip().upper():
                return entry.get("DiskNum"), entry.get("DriveLetter")

    except Exception as e:
        print(f"Error scanning disks: {e}")

    return None, None


def run_diskpart_format(disk_number, force_letter, target_label="FFlash"):
    """Handles the destructive cleaning and formatting with lock-bypassing."""
    print(f"⚠️ Wiping Disk {disk_number} and assigning to {force_letter}:...")

    # 1. FORCE UNMOUNT to kill Windows Explorer / Antivirus locks
    # This prevents the "Access Denied" error on subsequent burns.
    print(f"Dropping Windows locks on {force_letter}:...")
    # 'mountvol E: /D' deletes the volume mount point, forcing Windows to let go.
    subprocess.run(["mountvol", f"{force_letter}:", "/D"], capture_output=True)
    time.sleep(2)  # Give Windows a second to release the handle

    # 2. Robust Diskpart Script
    # 'attributes disk clear readonly' will rescue your currently broken drive
    commands = f"""
select disk {disk_number}
attributes disk clear readonly
clean
create partition primary
format fs=exfat label="{target_label}" quick
assign letter={force_letter}
exit
"""
    script_path = "temp_diskpart.txt"
    try:
        with open(script_path, "w") as f:
            f.write(commands)

        # Execute Diskpart
        subprocess.run(["diskpart", "/s", script_path], check=True)
        time.sleep(3)  # Wait for Windows to mount the new partition
        return True

    except subprocess.CalledProcessError as e:
        print(f"Diskpart failed: {e}")
        print("TIP: Make sure you are not viewing the USB drive in File Explorer!")
        return False

    finally:
        if os.path.exists(script_path):
            os.remove(script_path)


def deploy_to_usb(target_label, iso_path, bat_file_path="C:/work/Glida/scripts/burn.bat"):
    """Main Orchestrator"""

    # 1. Dynamic Discovery
    disk_num, current_letter = get_usb_info_by_label(target_label)

    if disk_num is None:
        print(f"❌ Error: Could not find a USB drive labeled '{target_label}'.")
        return

    # Safety: We almost never want to wipe Disk 0 (System Drive)
    if disk_num == 0:
        print("❌ CRITICAL SAFETY: Found target on Disk 0. Aborting to prevent OS wipe.")
        return

    print(f"✅ Found {target_label} on Disk {disk_num} (Currently {current_letter}:)")

    # 2. Format
    # We use the 'current_letter' found by discovery to keep things consistent
    if not run_diskpart_format(disk_num, current_letter, target_label):
        return

    # 3. Burn/Copy
    if not os.path.exists(bat_file_path):
        print(f"❌ Error: {bat_file_path} not found!")
        return

    print("--- Handing over to Robocopy ---")
    try:
        subprocess.run([bat_file_path, iso_path, current_letter], check=True)
        print(f"\n✨ Successfully deployed to {target_label} ({current_letter}:)")
    except subprocess.CalledProcessError:
        print("❌ Error during file copy process.")