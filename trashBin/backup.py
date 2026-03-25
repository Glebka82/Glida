import subprocess
import os


def write_iso_to_disk_windows(iso_path, disk_number):
    """
    Overcomes 'Access Denied' by using Diskpart to clean and prepare the drive.
    :param iso_path: Full path to your ISO.
    :param disk_number: The integer number of the disk (e.g., 1 for Disk 1).
    """
    # 1. Prepare a Diskpart script to wipe the drive and make it accessible
    # This removes partitions so Windows stops 'locking' the drive.
    diskpart_script = f"""
    select disk {disk_number}
    clean
    create partition primary
    format fs=ntfs quick
    active
    assign
    exit
    """

    script_file = "prepare_disk.txt"
    with open(script_file, "w") as f:
        f.write(diskpart_script)

    try:
        print(f"--- Preparing Disk {disk_number} ---")
        subprocess.run(["diskpart", "/s", script_file], check=True)

        # 2. Now that the disk is 'clean' and has a fresh letter, we mount the ISO
        # and copy the files. This is the 'Standard' way for bootable Windows USBs.
        print("--- Copying ISO Contents ---")

        # Mount the ISO via PowerShell to get its drive letter
        mount_cmd = f"Mount-DiskImage -ImagePath '{iso_path}' -PassThru | Get-Volume"
        result = subprocess.run(["powershell", "-Command", mount_cmd], capture_output=True, text=True)

        # This is a bit of a shortcut: instead of raw bytes (which is failing),
        # we copy the high-level files.
        print("Disk is ready. Would you like me to help you write the 'Copy' logic now?")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(script_file):
            os.remove(script_file)

if __name__ == '__main__':
    Usage: write_iso_to_disk_windows("C:/path/to/image.iso", 1)