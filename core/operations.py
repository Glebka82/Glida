import psutil
import os
import json
import subprocess
import re

json_path_platform = "configs/disk_name.json"

def get_removable_drives():
    drives = []
    for partition in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'removable' in partition.opts:
                drives.append(partition)
        else:
            if partition.mountpoint.startswith(('/media/', '/run/media/', '/Volumes/')):
                drives.append(partition)
    return drives


import subprocess


def find_drive_from_ui_string(drive_string):
    """
    Extracts the drive letter from a string like "GLEB (D:)"
    and finds the raw PhysicalDrive path.
    """
    print(f"🔍 Analyzing input string: '{drive_string}'...")

    # 1. The Regex Magic
    # This looks for any single letter (A-Z or a-z) that is immediately
    # followed by a colon ':'.
    match = re.search(r'([A-Za-z]):', drive_string)

    if not match:
        print(f"❌ Error: Could not find a drive letter (like 'D:') inside '{drive_string}'.")
        return None

    # Extract the matched letter and make sure it is uppercase
    letter = match.group(1).upper()
    print(f"🎯 Extracted Drive Letter: {letter}")

    # 2. Ask Windows for the physical disk number
    ps_cmd = f"(Get-Partition -DriveLetter {letter}).DiskNumber"

    try:
        # Run PowerShell silently
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, check=True
        )

        disk_number = result.stdout.strip()

        # 3. Format it for our raw flasher
        if disk_number.isdigit():
            physical_path = fr"\\.\PhysicalDrive{disk_number}"
            print(f"✅ Success! {drive_string} is mapped to -> {physical_path}")
            return physical_path
        else:
            print(f"❌ Windows could not find the physical hardware for Drive {letter}:")
            return None

    except subprocess.CalledProcessError:
        print(f"❌ Error querying Windows for Drive {letter}:. Is the USB plugged in?")
        return None

def get_first_user_from_disk(disk_name):
    try:
        with open(json_path_platform, 'r', encoding='utf-8') as file:

            data = json.load(file)

            first_user = data[disk_name][0]

            print(f"✅ Found user '{first_user}' on {disk_name}")
            return first_user

    except FileNotFoundError:
        print(f"❌ Error: The file {json_path_platform} was not found.")
    except KeyError:
        print(f"❌ Error: The key '{disk_name}' does not exist in the JSON.")
    except IndexError:
        print(f"❌ Error: The list for '{disk_name}' is empty!")
