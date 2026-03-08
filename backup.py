import os
import time
import operations
import sys
import subprocess
import msvcrt
import ctypes

# Windows Constants
GENERIC_WRITE = 0x40000000
GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
FSCTL_LOCK_VOLUME = 0x00090018
FSCTL_DISMOUNT_VOLUME = 0x00090020


def ultra_safe_flash(image_path, physical_drive_path):
    """
    Uses the Windows Kernel API exclusively to handle the drive.
    This bypasses Python's file descriptors to avoid Errno 9.
    """
    CHUNK_SIZE = 1024 * 1024 * 8  # 8MB for stability

    print(f"🔗 Opening {physical_drive_path} via Kernel32...")

    # 1. Open the device using Windows API directly
    handle = ctypes.windll.kernel32.CreateFileW(
        physical_drive_path,
        GENERIC_WRITE | GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        0,
        None
    )

    if handle == -1:
        print("❌ Failed to get a handle. Are you Admin?")
        return

    try:
        # 2. Force Lock and Dismount
        dummy = ctypes.c_ulong()
        ctypes.windll.kernel32.DeviceIoControl(handle, FSCTL_LOCK_VOLUME, None, 0, None, 0, ctypes.byref(dummy), None)
        ctypes.windll.kernel32.DeviceIoControl(handle, FSCTL_DISMOUNT_VOLUME, None, 0, None, 0, ctypes.byref(dummy),
                                               None)

        print("🔒 Drive locked. Writing data...")

        with open(image_path, 'rb') as img:
            while True:
                data = img.read(CHUNK_SIZE)
                if not data:
                    break

                # 3. Write using the Windows WriteFile API
                written = ctypes.c_ulong(0)
                success = ctypes.windll.kernel32.WriteFile(
                    handle, data, len(data), ctypes.byref(written), None
                )

                if not success:
                    error_code = ctypes.windll.kernel32.GetLastError()
                    print(f"\n❌ Write failed at byte {img.tell()}. Windows Error: {error_code}")
                    return

                print("⚡", end="", flush=True)

        print("\n✅ Flash Successful!")

    finally:
        # 4. Clean up
        ctypes.windll.kernel32.CloseHandle(handle)

# --- USAGE ---
# Windows Example (Remember to run IDE/Terminal as Admin!):
# flash_usb_hyper_fast("E:/base_templates/ubuntu_server.img", "\\\\.\\PhysicalDrive1")

# Linux Example (Remember to run with sudo!):
# flash_usb_hyper_fast("/home/user/base_templates/ubuntu_server.img", "/dev/sdb")
if __name__ == "__main__":
    # print("🔍 Scanning for available USB drives...\n")
    # available_drives = operations.get_removable_drives()
    #
    # if not available_drives:
    #     print("❌ No USB drives detected. Please plug one in and restart.")
    #     sys.exit(0)
    #
    # print("Select the TARGET USB drive:")
    # for i, drive in enumerate(available_drives):
    #     print(f" [{i}] {drive.device} (Mounted at: {drive.mountpoint})")
    #
    # try:
    #     choice = int(input("\nEnter the number of the target drive: "))
    #     if choice < 0 or choice >= len(available_drives):
    #         print("❌ Invalid selection.")
    #         sys.exit(1)
    #
    #     selected_drive = available_drives[choice]
    #
    #     image_file = input("\nEnter the full path to your .img or .iso file: ")
    #
    #     burn_image_to_usb(image_file, selected_drive)
    #
    # except ValueError:
    #     print("❌ Please enter a valid number.")
    ultra_safe_flash(r"C:\work\Glida\usb_backup_0.img", r"\\.\PhysicalDrive1")


